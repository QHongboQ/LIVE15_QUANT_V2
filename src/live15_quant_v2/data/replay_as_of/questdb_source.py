"""Read-only QuestDB implementation of the Replay As-Of source seam."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, NoReturn

import questdb

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.data_truth.models import (
    EventIdentity,
    TradeNotAcceptedReason,
    TruthDecision,
    TruthDecisionCategory,
)
from live15_quant_v2.data.replay_as_of.availability import (
    SUPPORTED_PROOF_SCHEMA_VERSION,
    AvailabilityKind,
)
from live15_quant_v2.data.replay_as_of.models import (
    AvailabilityReference,
    ReplayAsOfError,
    ReplayErrorCode,
)
from live15_quant_v2.data.replay_as_of.source import (
    ReplayCandidateScope,
    ReplaySourceRecord,
    SourceAuthorityIdentities,
)
from live15_quant_v2.data.storage.capture import CaptureFact

_TABLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_EVIDENCE_COLUMNS = {
    "capture_id": "VARCHAR",
    "asset": "SYMBOL",
    "provider": "SYMBOL",
    "source_id": "VARCHAR",
    "channel": "SYMBOL",
    "message_type": "VARCHAR",
    "event_subtype": "VARCHAR",
    "sid": "LONG",
    "seq": "LONG",
    "provider_timestamp": "TIMESTAMP_NS",
    "schema_version": "VARCHAR",
    "payload": "VARCHAR",
    "received_timestamp": "TIMESTAMP_NS",
}
_TRUTH_COLUMNS = {
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
_AVAILABILITY_COLUMNS = {
    "kind": "VARCHAR",
    "capture_id": "VARCHAR",
    "policy_version": "VARCHAR",
    "available_at_ns": "TIMESTAMP_NS",
    "proof_schema_version": "VARCHAR",
    "source_authority_identity": "VARCHAR",
    "written_at_ns": "TIMESTAMP_NS",
}


class QuestDBReplaySource:
    """Read the explicitly configured physical authorities without mutating them."""

    def __init__(
        self,
        connection_string: str,
        *,
        evidence_table: str,
        truth_decision_table: str,
        availability_table: str,
        evidence_authority_identity: str,
        truth_decision_authority_identity: str,
        availability_authority_identity: str,
    ) -> None:
        for value in (evidence_table, truth_decision_table, availability_table):
            if not isinstance(value, str) or not _TABLE_NAME.fullmatch(value):
                raise ValueError("table names must be simple SQL identifiers")
        for value in (
            evidence_authority_identity,
            truth_decision_authority_identity,
            availability_authority_identity,
        ):
            if not isinstance(value, str) or not value:
                raise ValueError("authority identities must be non-empty text")
        self._connection_string = connection_string
        self._evidence_table = evidence_table
        self._truth_table = truth_decision_table
        self._availability_table = availability_table
        self._evidence_authority_identity = evidence_authority_identity
        self._truth_decision_authority_identity = truth_decision_authority_identity
        self._availability_authority_identity = availability_authority_identity
        self._authorities = SourceAuthorityIdentities(
            _identity(
                "evidence",
                evidence_authority_identity,
                evidence_table,
                _EVIDENCE_COLUMNS,
            ),
            _identity(
                "truth-decision",
                truth_decision_authority_identity,
                truth_decision_table,
                _TRUTH_COLUMNS,
            ),
            _identity(
                "availability",
                availability_authority_identity,
                availability_table,
                _AVAILABILITY_COLUMNS,
            ),
        )
        self._database: questdb.QuestDB | None = None
        self._schema_ready = False

    def close(self) -> None:
        if self._database is not None:
            self._database.close()
            self._database = None
            self._schema_ready = False

    def source_authorities(self) -> SourceAuthorityIdentities:
        self._database_for_read()
        return self._authorities

    def candidate_records(
        self, scope: ReplayCandidateScope
    ) -> tuple[ReplaySourceRecord, ...]:
        self._database_for_read()
        rows = self._rows(
            f"SELECT policy_version, subject_capture_id, category, contributing_capture_ids, reason, "
            f"event_provider, event_source_id, event_message_type, event_trade_id FROM {self._truth_table} "
            "WHERE policy_version = $1",
            [scope.authority_policy_version],
        )
        records: list[ReplaySourceRecord] = []
        seen: set[str] = set()
        for row in rows:
            decision = self._decode_decision(row)
            if decision.subject_capture_id in seen:
                self._error(
                    ReplayErrorCode.AUTHORITY_CONFLICT,
                    "multiple authority rows for one subject",
                )
            seen.add(decision.subject_capture_id)
            fact = self._one_fact(decision.subject_capture_id)
            evidence = self._availability(
                AvailabilityKind.EVIDENCE, fact.capture_id, None
            )
            authority = self._availability(
                AvailabilityKind.AUTHORITY,
                decision.subject_capture_id,
                decision.policy_version,
            )
            records.append(ReplaySourceRecord(fact, decision, evidence, authority))
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    record.truth_decision.policy_version,
                    record.truth_decision.subject_capture_id,
                ),
            )
        )

    def _database_for_read(self) -> questdb.QuestDB:
        if self._database is None:
            try:
                self._database = questdb.connect(
                    self._connection_string, auto_flush=False
                )
            except (OSError, questdb.QuestDBError) as error:
                self._source("QuestDB connection failed", error)
        if not self._schema_ready:
            self._verify_schema()
            self._schema_ready = True
        return self._database

    def _verify_schema(self) -> None:
        tables = self._metadata(
            "SELECT table_name, designatedTimestamp, partitionBy, walEnabled, dedup FROM tables()"
        )
        self._verify_table(tables, self._evidence_table, "received_timestamp", True)
        self._verify_table(tables, self._truth_table, "physical_written_at", False)
        self._verify_table(tables, self._availability_table, "written_at_ns", False)
        self._verify_columns(
            self._evidence_table,
            _EVIDENCE_COLUMNS,
            {"received_timestamp", "capture_id"},
        )
        self._verify_columns(self._truth_table, _TRUTH_COLUMNS, set())
        self._verify_columns(self._availability_table, _AVAILABILITY_COLUMNS, set())

    def _verify_table(
        self, tables: list[dict[str, Any]], name: str, timestamp: str, dedup: bool
    ) -> None:
        matches = [row for row in tables if row.get("table_name") == name]
        if len(matches) != 1:
            self._source("configured source table is unavailable")
        table = matches[0]
        if (
            table.get("designatedTimestamp") != timestamp
            or table.get("partitionBy") != "DAY"
            or table.get("walEnabled") is not True
            or table.get("dedup") is not dedup
        ):
            self._source("configured source table has incompatible schema")

    def _verify_columns(
        self, table: str, expected: dict[str, str], upsert_keys: set[str]
    ) -> None:
        columns = {
            row.get("column"): row
            for row in self._metadata(
                f"SELECT \"column\", type, designated, upsertKey FROM table_columns('{table}')"
            )
        }
        if set(columns) != set(expected):
            self._source("configured source table has incompatible columns")
        for name, column_type in expected.items():
            metadata = columns.get(name, {})
            if metadata.get("type") != column_type:
                self._source("configured source column has incompatible type")
            if metadata.get("designated") is not (
                name in {"received_timestamp", "physical_written_at", "written_at_ns"}
            ):
                self._source("configured source designated timestamp is incompatible")
            if metadata.get("upsertKey") is not (name in upsert_keys):
                self._source("configured source replacement keys are incompatible")

    def _one_fact(self, capture_id: str) -> CaptureFact:
        rows = self._rows(
            f"SELECT capture_id, asset, provider, source_id, channel, message_type, event_subtype, sid, seq, "
            f"provider_timestamp, schema_version, payload, received_timestamp FROM {self._evidence_table} WHERE capture_id = $1",
            [capture_id],
        )
        if len(rows) != 1:
            self._error(
                ReplayErrorCode.MALFORMED_EVIDENCE, "evidence must exist exactly once"
            )
        fact = self._decode_fact(rows[0])
        if fact.capture_id != capture_id:
            self._error(
                ReplayErrorCode.MALFORMED_EVIDENCE,
                "evidence row contradicts the requested capture",
            )
        return fact

    def _availability(
        self, kind: AvailabilityKind, capture_id: str, policy_version: str | None
    ) -> AvailabilityReference:
        predicate, binds = (
            ("policy_version IS NULL", [kind.value, capture_id])
            if policy_version is None
            else ("policy_version = $3", [kind.value, capture_id, policy_version])
        )
        rows = self._rows(
            f"SELECT kind, capture_id, policy_version, available_at_ns, proof_schema_version, source_authority_identity "
            f"FROM {self._availability_table} WHERE kind = $1 AND capture_id = $2 AND {predicate}",
            binds,
        )
        if not rows:
            return AvailabilityReference(None, None)
        if len(rows) != 1:
            self._error(
                ReplayErrorCode.AVAILABILITY_EVIDENCE_MISSING,
                "availability marker is not unique",
            )
        row = rows[0]
        try:
            stored_kind = AvailabilityKind(row["kind"])
            stored_policy = _nullable(row["policy_version"])
            available_at_ns = _timestamp(row["available_at_ns"])
            expected_identity = (
                self._evidence_authority_identity
                if kind is AvailabilityKind.EVIDENCE
                else self._truth_decision_authority_identity
            )
            if (
                stored_kind is not kind
                or row["capture_id"] != capture_id
                or stored_policy != policy_version
                or row["proof_schema_version"] != SUPPORTED_PROOF_SCHEMA_VERSION
                or row["source_authority_identity"] != expected_identity
            ):
                raise ValueError(
                    "availability marker does not bind the requested source"
                )
            reference = _marker_reference(
                kind,
                capture_id,
                policy_version,
                available_at_ns,
                row["proof_schema_version"],
                row["source_authority_identity"],
            )
            return AvailabilityReference(available_at_ns, reference)
        except (KeyError, TypeError, ValueError) as error:
            self._error(
                ReplayErrorCode.AVAILABILITY_EVIDENCE_MISSING,
                "availability marker is malformed",
                error,
            )

    def _decode_fact(self, row: dict[str, Any]) -> CaptureFact:
        try:
            capture_id = _nonempty_text(row["capture_id"])
            fact = CaptureFact(
                capture_id,
                AssetId(_text(row["asset"])),
                _text(row["provider"]),
                _text(row["source_id"]),
                _text(row["channel"]),
                _text(row["message_type"]),
                _nullable_text(row["event_subtype"]),
                _integer(row["sid"]),
                _nullable_integer(row["seq"]),
                _nullable_integer(row["provider_timestamp"]),
                _timestamp(row["received_timestamp"]),
                _text(row["schema_version"]),
                _text(row["payload"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            self._error(
                ReplayErrorCode.MALFORMED_EVIDENCE, "evidence row is malformed", error
            )
        return fact

    def _decode_decision(self, row: dict[str, Any]) -> TruthDecision:
        try:
            policy = _text(row["policy_version"])
            subject = _text(row["subject_capture_id"])
            contribution = json.loads(_text(row["contributing_capture_ids"]))
            if not isinstance(contribution, list) or not all(
                isinstance(value, str) for value in contribution
            ):
                raise ValueError("contributing capture IDs must be a JSON string list")
            event_values = tuple(
                _nullable_text(row[name])
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
                raise ValueError("event identity must be complete or null")
            event = None if event_values[0] is None else EventIdentity(*event_values)  # type: ignore[arg-type]
            return TruthDecision(
                subject,
                TruthDecisionCategory(_text(row["category"])),
                policy,
                tuple(contribution),
                None
                if _nullable(row["reason"]) is None
                else TradeNotAcceptedReason(_text(row["reason"])),
                event,
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            self._error(
                ReplayErrorCode.MALFORMED_AUTHORITY,
                "truth-decision row is malformed",
                error,
            )

    def _rows(self, sql: str, binds: list[Any]) -> list[dict[str, Any]]:
        try:
            return (
                self._database_for_read()
                .query(sql, binds)
                .to_pandas()
                .to_dict(orient="records")
            )
        except (OSError, questdb.QuestDBError) as error:
            self._source("QuestDB read failed", error)

    def _metadata(self, sql: str) -> list[dict[str, Any]]:
        try:
            database = self._database
            if database is None:
                self._source("QuestDB metadata database is unavailable")
            assert database is not None
            return database.query(sql, []).to_pandas().to_dict(orient="records")
        except (OSError, questdb.QuestDBError) as error:
            self._source("QuestDB metadata read failed", error)

    @staticmethod
    def _error(
        code: ReplayErrorCode, message: str, error: BaseException | None = None
    ) -> NoReturn:
        exception = ReplayAsOfError(code, message)
        if error is None:
            raise exception
        raise exception from error

    def _source(self, message: str, error: BaseException | None = None) -> NoReturn:
        self._error(ReplayErrorCode.SOURCE_UNAVAILABLE, message, error)


def _identity(
    role: str, logical_identity: str, table: str, columns: dict[str, str]
) -> str:
    payload = json.dumps(
        {
            "role": role,
            "logical_identity": logical_identity,
            "table": table,
            "schema": columns,
            "version": "replay-as-of-source/v1",
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _marker_reference(
    kind: AvailabilityKind,
    capture_id: str,
    policy_version: str | None,
    available_at_ns: int,
    proof: str,
    identity: str,
) -> str:
    payload = json.dumps(
        {
            "kind": kind.value,
            "capture_id": capture_id,
            "policy_version": policy_version,
            "available_at_ns": available_at_ns,
            "proof": proof,
            "identity": identity,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _nullable(value: Any) -> Any:
    if (
        value is None
        or (isinstance(value, float) and math.isnan(value))
        or type(value).__name__ == "NaTType"
    ):
        return None
    return value


def _text(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("expected text")
    return value


def _nonempty_text(value: Any) -> str:
    value = _text(value)
    if not value:
        raise ValueError("expected non-empty text")
    return value


def _nullable_text(value: Any) -> str | None:
    value = _nullable(value)
    if value is None:
        return None
    return _text(value)


def _integer(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("expected integer")
    return value


def _nullable_integer(value: Any) -> int | None:
    value = _nullable(value)
    return None if value is None else _integer(value)


def _timestamp(value: Any) -> int:
    value = getattr(value, "value", value)
    return _integer(value)
