"""QuestDB implementation support for the provider-neutral history seam."""

import json
import math
import re
import time
from collections.abc import Iterator
from typing import Any, NoReturn

import questdb

from live15_quant_v2.data.data_truth.history import (
    TruthDecisionAppendInDoubtError,
    TruthDecisionAppendRejectedError,
    TruthDecisionInvariantError,
    TruthDecisionVerificationError,
)
from live15_quant_v2.data.data_truth.models import (
    EventAnchor,
    EventIdentity,
    TradeNotAcceptedReason,
    TruthDecision,
    TruthDecisionCategory,
)
from live15_quant_v2.data.storage.hot_store.port import HotStore

_TABLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_REQUIRED_COLUMNS = {
    "policy_version": "VARCHAR",
    "subject_capture_id": "VARCHAR",
    "category": "VARCHAR",
    "contributing_capture_ids": "VARCHAR",
    "reason": "VARCHAR",
    "event_provider": "VARCHAR",
    "event_source_id": "VARCHAR",
    "event_message_type": "VARCHAR",
    "event_trade_id": "VARCHAR",
    "physical_written_at": "TIMESTAMP_NS",
}
_DECISION_COLUMNS = (
    "policy_version, subject_capture_id, category, contributing_capture_ids, reason, "
    "event_provider, event_source_id, event_message_type, event_trade_id"
)


class _SchemaIncompatibleError(RuntimeError):
    """Internal marker for a table that cannot safely provide history authority."""


class QuestDBTruthDecisionHistory:
    """Persistent append-only TruthDecision authority backed by QuestDB."""

    def __init__(
        self,
        connection_string: str,
        *,
        table_name: str,
        hot_store: HotStore,
        acknowledgement_timeout_millis: int,
    ) -> None:
        if not _TABLE_NAME.fullmatch(table_name):
            raise ValueError("table_name must be a simple SQL identifier")
        if not isinstance(acknowledgement_timeout_millis, int) or isinstance(
            acknowledgement_timeout_millis, bool
        ):
            raise TypeError("acknowledgement_timeout_millis must be an int")
        if acknowledgement_timeout_millis < 0:
            raise ValueError("acknowledgement_timeout_millis must be non-negative")

        self._connection_string = connection_string
        self._table_name = table_name
        self._hot_store = hot_store
        self._acknowledgement_timeout_millis = acknowledgement_timeout_millis
        self._database: questdb.QuestDB | None = None
        self._schema_ready = False

    def close(self) -> None:
        """Release the QuestDB client without publishing or reconciling work."""
        if self._database is not None:
            self._database.close()
            self._database = None
            self._schema_ready = False

    def find_subject_decision(
        self, policy_version: str, capture_id: str
    ) -> TruthDecision | None:
        """Return the one authoritative decision for an exact subject key."""
        try:
            rows = self._rows(
                f"SELECT {_DECISION_COLUMNS} FROM {self._table_name} "
                "WHERE policy_version = $1 AND subject_capture_id = $2",
                [policy_version, capture_id],
            )
        except (OSError, questdb.QuestDBError, _SchemaIncompatibleError) as error:
            raise TruthDecisionVerificationError("TruthDecision subject lookup failed") from error
        return self._one_decision_or_none(rows, "subject key")

    def find_accepted_event(self, event_identity: EventIdentity) -> EventAnchor | None:
        """Return the accepted decision and immutable evidence for an exact event."""
        try:
            rows = self._rows(
                f"SELECT {_DECISION_COLUMNS} FROM {self._table_name} "
                "WHERE category = $1 AND event_provider = $2 AND event_source_id = $3 "
                "AND event_message_type = $4 AND event_trade_id = $5",
                [
                    TruthDecisionCategory.ACCEPTED.value,
                    event_identity.provider,
                    event_identity.source_id,
                    event_identity.message_type,
                    event_identity.trade_id,
                ],
            )
        except (OSError, questdb.QuestDBError, _SchemaIncompatibleError) as error:
            raise TruthDecisionVerificationError("TruthDecision event lookup failed") from error
        decision = self._one_decision_or_none(rows, "accepted event")
        if decision is None:
            return None
        if (
            decision.category is not TruthDecisionCategory.ACCEPTED
            or decision.event_identity != event_identity
        ):
            raise TruthDecisionInvariantError("accepted event lookup returned mismatched authority")
        try:
            accepted_fact = self._hot_store.read_capture(decision.subject_capture_id)
        except Exception as error:
            raise TruthDecisionVerificationError(
                "accepted event evidence could not be retrieved"
            ) from error
        if accepted_fact is None:
            raise TruthDecisionVerificationError("accepted event evidence is absent")
        if accepted_fact.capture_id != decision.subject_capture_id:
            raise TruthDecisionInvariantError("accepted event evidence contradicts authority")
        return EventAnchor(event_identity, decision, accepted_fact)

    def append(self, decision: TruthDecision) -> None:
        """Make one physical append attempt and classify its upstream outcome."""
        sender: Any | None = None
        try:
            database = self._database_for_use()
            sender = database.sender()
        except (OSError, questdb.QuestDBError, _SchemaIncompatibleError) as error:
            self._raise_pre_publication_error(error)

        try:
            database_dropped_before = database.error_events_dropped
            sender_dropped_before = sender.error_events_dropped()
            sender.row(
                self._table_name,
                columns=self._fields(decision),
                at=questdb.TimestampNanos(time.time_ns()),
            )
            fsn = sender.flush_and_get_fsn()
        except (OSError, questdb.QuestDBError) as error:
            self._close_sender(sender)
            self._raise_pre_publication_error(error)

        if fsn is None:
            self._close_sender(sender)
            raise TruthDecisionAppendInDoubtError("QuestDB did not provide an append FSN")

        try:
            acknowledged = sender.await_acked_fsn(
                fsn, timeout_millis=self._acknowledgement_timeout_millis
            )
            rejection = self._rejection_for_fsn(sender, fsn)
            diagnostics_lost = (
                sender.error_events_dropped() != sender_dropped_before
                or database.error_events_dropped != database_dropped_before
            )
        except (OSError, questdb.QuestDBError) as error:
            self._close_sender(sender)
            raise TruthDecisionAppendInDoubtError(
                "QuestDB append acknowledgement could not be observed"
            ) from error

        self._close_sender(sender)
        if diagnostics_lost:
            raise TruthDecisionAppendInDoubtError("QuestDB append diagnostics were lost")
        if rejection == "terminal":
            raise TruthDecisionAppendRejectedError("QuestDB terminally rejected append")
        if rejection == "pending":
            raise TruthDecisionAppendInDoubtError("QuestDB append rejection remains pending")
        if not acknowledged:
            raise TruthDecisionAppendInDoubtError("QuestDB did not acknowledge append")
        self._wait_for_wal_visibility(database)

    def _wait_for_wal_visibility(self, database: questdb.QuestDB) -> None:
        """Require the acknowledged WAL transaction to be query-visible once."""
        try:
            rows = database.query(
                f"SELECT wait_wal_table('{self._table_name}')", []
            ).to_pandas().to_dict(orient="records")
        except (OSError, questdb.QuestDBError) as error:
            raise TruthDecisionAppendInDoubtError(
                "QuestDB WAL visibility could not be observed"
            ) from error
        if (
            len(rows) != 1
            or len(rows[0]) != 1
            or next(iter(rows[0].values())) is not True
        ):
            raise TruthDecisionAppendInDoubtError(
                "QuestDB WAL visibility barrier did not return exactly true"
            )

    def _database_for_use(self) -> questdb.QuestDB:
        if self._database is None:
            self._database = questdb.connect(self._connection_string)
        if not self._schema_ready:
            if not self._table_exists():
                self._database.execute(self._create_table_sql())
            self._verify_schema()
            self._schema_ready = True
        return self._database

    def _table_exists(self) -> bool:
        return any(
            row.get("table_name") == self._table_name
            for row in self._metadata_rows(
                "SELECT table_name, designatedTimestamp, partitionBy, walEnabled, dedup "
                "FROM tables()",
                [],
            )
        )

    def _verify_schema(self) -> None:
        table_rows = [
            row
            for row in self._metadata_rows(
                "SELECT table_name, designatedTimestamp, partitionBy, walEnabled, dedup "
                "FROM tables()",
                [],
            )
            if row.get("table_name") == self._table_name
        ]
        if len(table_rows) != 1:
            self._schema_incompatible("explicit history table is absent after creation")
        table = table_rows[0]
        requirements = {
            "WAL": table.get("walEnabled") is True,
            "designated timestamp": table.get("designatedTimestamp")
            == "physical_written_at",
            "DAY partitioning": table.get("partitionBy") == "DAY",
            "dedup disabled": table.get("dedup") is False,
        }
        failures = [name for name, passed in requirements.items() if not passed]
        if failures:
            self._schema_incompatible(", ".join(failures))

        columns = self._columns_metadata()
        for column_name, expected_type in _REQUIRED_COLUMNS.items():
            metadata = columns.get(column_name)
            if metadata is None or metadata.get("type") != expected_type:
                self._schema_incompatible(f"{column_name} must be {expected_type}")
        if columns["physical_written_at"].get("designated") is not True:
            self._schema_incompatible("physical_written_at must be designated")
        if any(metadata.get("upsertKey") is True for metadata in columns.values()):
            self._schema_incompatible("history table has replacement keys")

    def _columns_metadata(self) -> dict[str, dict[str, Any]]:
        return {
            row["column"]: row
            for row in self._metadata_rows(
                f"SELECT \"column\", type, designated, upsertKey "
                f"FROM table_columns('{self._table_name}')",
                [],
            )
            if isinstance(row.get("column"), str)
        }

    def _metadata_rows(self, sql: str, binds: list[Any]) -> list[dict[str, Any]]:
        if self._database is None:
            raise RuntimeError("QuestDB connection is unavailable")
        return self._database.query(sql, binds).to_pandas().to_dict(orient="records")

    def _rows(self, sql: str, binds: list[Any]) -> list[dict[str, Any]]:
        return self._database_for_use().query(sql, binds).to_pandas().to_dict(orient="records")

    @staticmethod
    def _one_decision_or_none(rows: list[dict[str, Any]], lookup_name: str) -> TruthDecision | None:
        if not rows:
            return None
        if len(rows) != 1:
            raise TruthDecisionInvariantError(
                f"TruthDecision authority has multiple rows for {lookup_name}"
            )
        try:
            return QuestDBTruthDecisionHistory._decode(rows[0])
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise TruthDecisionInvariantError("stored TruthDecision is malformed") from error

    @staticmethod
    def _decode(row: dict[str, Any]) -> TruthDecision:
        policy_version = QuestDBTruthDecisionHistory._required_text(row, "policy_version")
        subject_capture_id = QuestDBTruthDecisionHistory._required_text(row, "subject_capture_id")
        category = TruthDecisionCategory(
            QuestDBTruthDecisionHistory._required_text(row, "category")
        )
        contributing_text = QuestDBTruthDecisionHistory._required_text(
            row, "contributing_capture_ids"
        )
        contributing_capture_ids = json.loads(contributing_text)
        if not isinstance(contributing_capture_ids, list) or not all(
            isinstance(capture_id, str) for capture_id in contributing_capture_ids
        ):
            raise TypeError("stored contributing capture IDs are invalid")
        reason_text = QuestDBTruthDecisionHistory._optional_text(row, "reason")
        event_values = tuple(
            QuestDBTruthDecisionHistory._optional_text(row, name)
            for name in (
                "event_provider",
                "event_source_id",
                "event_message_type",
                "event_trade_id",
            )
        )
        if any(value is None for value in event_values) and any(
            value is not None for value in event_values
        ):
            raise TypeError("stored EventIdentity is partial")
        event_identity = (
            None
            if all(value is None for value in event_values)
            else EventIdentity(*event_values)  # type: ignore[arg-type]
        )
        return TruthDecision(
            subject_capture_id=subject_capture_id,
            category=category,
            policy_version=policy_version,
            contributing_capture_ids=tuple(contributing_capture_ids),
            reason=None if reason_text is None else TradeNotAcceptedReason(reason_text),
            event_identity=event_identity,
        )

    @staticmethod
    def _fields(decision: TruthDecision) -> dict[str, Any]:
        event_identity = decision.event_identity
        return {
            "policy_version": decision.policy_version,
            "subject_capture_id": decision.subject_capture_id,
            "category": decision.category.value,
            "contributing_capture_ids": json.dumps(
                decision.contributing_capture_ids, separators=(",", ":")
            ),
            "reason": None if decision.reason is None else decision.reason.value,
            "event_provider": None if event_identity is None else event_identity.provider,
            "event_source_id": None if event_identity is None else event_identity.source_id,
            "event_message_type": None if event_identity is None else event_identity.message_type,
            "event_trade_id": None if event_identity is None else event_identity.trade_id,
        }

    @staticmethod
    def _required_text(row: dict[str, Any], field_name: str) -> str:
        value = row.get(field_name)
        if not isinstance(value, str):
            raise TypeError(f"stored {field_name} is not text")
        return value

    @staticmethod
    def _optional_text(row: dict[str, Any], field_name: str) -> str | None:
        value = row.get(field_name)
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        if not isinstance(value, str):
            raise TypeError(f"stored {field_name} is not text")
        return value

    def _create_table_sql(self) -> str:
        return (
            f"CREATE TABLE {self._table_name} ("
            "policy_version VARCHAR, subject_capture_id VARCHAR, category VARCHAR, "
            "contributing_capture_ids VARCHAR, reason VARCHAR, event_provider VARCHAR, "
            "event_source_id VARCHAR, event_message_type VARCHAR, event_trade_id VARCHAR, "
            "physical_written_at TIMESTAMP_NS"
            ") TIMESTAMP(physical_written_at) PARTITION BY DAY WAL"
        )

    def _schema_incompatible(self, detail: str) -> NoReturn:
        raise _SchemaIncompatibleError(f"QuestDB TruthDecision history schema: {detail}")

    @staticmethod
    def _raise_pre_publication_error(error: BaseException) -> NoReturn:
        if getattr(error, "in_doubt", False):
            raise TruthDecisionAppendInDoubtError("QuestDB append is in doubt") from error
        raise TruthDecisionAppendRejectedError("QuestDB rejected append before publication") from error

    @staticmethod
    def _close_sender(sender: Any) -> None:
        sender.close(flush=False)

    @staticmethod
    def _rejection_for_fsn(sender: Any, fsn: int) -> str | None:
        rejection: str | None = None
        for error in _sender_errors(sender):
            if not error.from_fsn <= fsn <= error.to_fsn:
                continue
            if error.applied_policy is questdb.SenderErrorPolicy.Terminal:
                return "terminal"
            rejection = "pending"
        return rejection


def _sender_errors(sender: Any) -> Iterator[Any]:
    while (error := sender.poll_error()) is not None:
        yield error
