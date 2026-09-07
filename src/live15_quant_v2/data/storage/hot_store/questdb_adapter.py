"""QuestDB implementation of the provider-neutral Hot Store seam."""

import re
from collections.abc import Sequence
from typing import Any, NoReturn

import pandas as pd  # type: ignore[import-untyped]
import questdb

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.hot_store.models import CaptureRange
from live15_quant_v2.data.storage.hot_store.port import (
    AppendReceipt,
    BatchTooLargeError,
    HotStoreUnavailableError,
    HotStoreWriteRejectedError,
)

_TABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_REQUIRED_UPSERT_KEYS = frozenset({"received_timestamp", "capture_id"})
_REQUIRED_COLUMNS = {
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
_APPROVED_COMPATIBILITY_COLUMNS = frozenset(
    {"source_id", "message_type", "event_subtype"}
)


class StoredCaptureFactIncompatibleError(RuntimeError):
    """Raised when a stored row cannot satisfy the shared CaptureFact contract."""


class QuestDBHotStoreMigrationRequiredError(RuntimeError):
    """Raised when an existing QuestDB table cannot safely serve as Hot Store."""


class QuestDBHotStore:
    """Persist raw capture facts through the official QuestDB Python client."""

    max_batch_rows = 500

    def __init__(self, connection_string: str, *, table_name: str = "hot_capture_facts") -> None:
        if not _TABLE_NAME.fullmatch(table_name):
            raise ValueError("table_name must be a simple SQL identifier")
        self._connection_string = connection_string
        self._table_name = table_name
        self._database: questdb.QuestDB | None = None
        self._schema_ready = False

    def close(self) -> None:
        """Close the underlying client connection when this adapter is no longer needed."""
        if self._database is not None:
            self._database.close()
            self._database = None
            self._schema_ready = False

    def append_batch(self, facts: Sequence[CaptureFact]) -> AppendReceipt:
        """Append at most 500 facts and require a server acknowledgement."""
        if len(facts) > self.max_batch_rows:
            raise BatchTooLargeError(
                f"Hot Store batches are limited to {self.max_batch_rows} facts"
            )
        if not facts:
            return AppendReceipt(appended_count=0)

        database = self._database_for_use()
        try:
            with database.sender() as sender:
                for fact in facts:
                    sender.row(
                        self._table_name,
                        columns={
                            "capture_id": fact.capture_id,
                            "asset": fact.asset.value,
                            "provider": fact.provider,
                            "source_id": fact.source_id,
                            "channel": fact.channel,
                            "message_type": fact.message_type,
                            "event_subtype": fact.event_subtype,
                            "sid": fact.sid,
                            "seq": fact.seq,
                            "provider_timestamp": (
                                None
                                if fact.provider_timestamp is None
                                else questdb.TimestampNanos(fact.provider_timestamp)
                            ),
                            "schema_version": fact.schema_version,
                            "payload": fact.payload,
                        },
                        at=questdb.TimestampNanos(fact.received_timestamp),
                    )
                frame_sequence_number = sender.flush_and_get_fsn()
                acknowledged = (
                    frame_sequence_number is not None
                    and sender.await_acked_fsn(frame_sequence_number, timeout_millis=15_000)
                )
        except (OSError, questdb.QuestDBError) as error:
            raise HotStoreWriteRejectedError("QuestDB rejected the capture batch") from error

        if not acknowledged:
            raise HotStoreWriteRejectedError("QuestDB did not acknowledge the capture batch")
        return AppendReceipt(appended_count=len(facts))

    def read_capture(self, capture_id: str) -> CaptureFact | None:
        """Read one raw capture by its capture identity."""
        rows = self._rows(
            f"SELECT {self._columns()} FROM {self._table_name} "
            "WHERE capture_id = $1",
            [capture_id],
        )
        if not rows:
            return None
        if len(rows) != 1:
            raise RuntimeError("capture_id is not uniquely retrievable")
        return self._capture_fact(rows[0])

    def read_range(self, capture_range: CaptureRange) -> list[CaptureFact]:
        """Read raw facts by received time and optional asset/channel filters."""
        predicates = ["received_timestamp >= $1", "received_timestamp <= $2"]
        binds: list[Any] = [capture_range.received_start, capture_range.received_end]
        if capture_range.asset is not None:
            predicates.append(f"asset = ${len(binds) + 1}")
            binds.append(capture_range.asset)
        if capture_range.channel is not None:
            predicates.append(f"channel = ${len(binds) + 1}")
            binds.append(capture_range.channel)
        rows = self._rows(
            f"SELECT {self._columns()} FROM {self._table_name} WHERE "
            f"{' AND '.join(predicates)} ORDER BY {capture_range.order_by.value}",
            binds,
        )
        return [self._capture_fact(row) for row in rows]

    def _database_for_use(self) -> questdb.QuestDB:
        if self._database is None:
            try:
                self._database = questdb.connect(self._connection_string)
            except (OSError, questdb.QuestDBError) as error:
                raise HotStoreUnavailableError("QuestDB is unavailable") from error
        if not self._schema_ready:
            try:
                if not self._table_exists():
                    self._database.execute(
                        f"CREATE TABLE IF NOT EXISTS {self._table_name} ("
                        "capture_id VARCHAR, asset SYMBOL, provider SYMBOL, source_id VARCHAR, "
                        "channel SYMBOL, message_type VARCHAR, event_subtype VARCHAR, "
                        "sid LONG, seq LONG, provider_timestamp TIMESTAMP_NS, "
                        "schema_version VARCHAR, payload VARCHAR, received_timestamp TIMESTAMP_NS"
                        ") TIMESTAMP(received_timestamp) PARTITION BY DAY WAL "
                        "DEDUP UPSERT KEYS(received_timestamp, capture_id)"
                    )
                self._verify_core_physical_configuration()
                self._verify_existing_columns_are_compatible()
                self._apply_approved_metadata_compatibility()
                self._verify_capture_fact_schema()
            except (OSError, questdb.QuestDBError) as error:
                raise HotStoreUnavailableError("QuestDB schema is unavailable") from error
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

    def _verify_core_physical_configuration(self) -> None:
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
            raise QuestDBHotStoreMigrationRequiredError(
                "QuestDB Hot Store table is absent after creation"
            )
        table = table_rows[0]
        requirements = {
            "WAL enabled": table.get("walEnabled") is True,
            "DEDUP enabled": table.get("dedup") is True,
            "designated timestamp received_timestamp": (
                table.get("designatedTimestamp") == "received_timestamp"
            ),
            "DAY partitioning": table.get("partitionBy") == "DAY",
        }
        failures = [name for name, satisfied in requirements.items() if not satisfied]
        if failures:
            self._migration_required(", ".join(failures))

        columns = self._columns_metadata()
        received_timestamp = columns.get("received_timestamp")
        capture_id = columns.get("capture_id")
        if received_timestamp is None:
            self._migration_required("missing received_timestamp column")
        if capture_id is None:
            self._migration_required("missing capture_id column")
        if received_timestamp.get("type") != "TIMESTAMP_NS":
            self._migration_required("received_timestamp must be TIMESTAMP_NS")
        if received_timestamp.get("designated") is not True:
            self._migration_required("received_timestamp must be designated")
        if capture_id.get("type") != "VARCHAR":
            self._migration_required("capture_id must be VARCHAR")

        upsert_keys = {
            column_name
            for column_name, metadata in columns.items()
            if metadata.get("upsertKey") is True
        }
        if upsert_keys != _REQUIRED_UPSERT_KEYS:
            self._migration_required(
                "UPSERT keys must be exactly received_timestamp and capture_id"
            )

    def _verify_existing_columns_are_compatible(self) -> None:
        columns = self._columns_metadata()
        for column_name, expected_type in _REQUIRED_COLUMNS.items():
            metadata = columns.get(column_name)
            if metadata is None:
                if column_name in _APPROVED_COMPATIBILITY_COLUMNS:
                    continue
                self._migration_required(f"missing required {column_name} column")
            if metadata.get("type") != expected_type:
                self._migration_required(
                    f"{column_name} must be {expected_type}"
                )

    def _apply_approved_metadata_compatibility(self) -> None:
        database = self._database
        if database is None:
            raise RuntimeError("QuestDB connection is unavailable")
        for column_name in ("source_id", "message_type", "event_subtype"):
            database.execute(
                f"ALTER TABLE {self._table_name} ADD COLUMN IF NOT EXISTS {column_name} VARCHAR"
            )

    def _verify_capture_fact_schema(self) -> None:
        columns = self._columns_metadata()
        for column_name, expected_type in _REQUIRED_COLUMNS.items():
            metadata = columns.get(column_name)
            if metadata is None or metadata.get("type") != expected_type:
                self._migration_required(
                    f"{column_name} must be present as {expected_type}"
                )

    def _columns_metadata(self) -> dict[str, dict[str, Any]]:
        rows = self._metadata_rows(
            f"SELECT \"column\", type, designated, upsertKey "
            f"FROM table_columns('{self._table_name}')",
            [],
        )
        return {
            row["column"]: row
            for row in rows
            if isinstance(row.get("column"), str)
        }

    def _metadata_rows(self, sql: str, binds: list[Any]) -> list[dict[str, Any]]:
        database = self._database
        if database is None:
            raise RuntimeError("QuestDB connection is unavailable")
        return database.query(sql, binds).to_pandas().to_dict(orient="records")

    def _migration_required(self, detail: str) -> NoReturn:
        raise QuestDBHotStoreMigrationRequiredError(
            f"QuestDB Hot Store table requires explicit migration: {detail}"
        )

    def _rows(self, sql: str, binds: list[Any]) -> list[dict[str, Any]]:
        try:
            result = self._database_for_use().query(sql, binds)
            return result.to_pandas().to_dict(orient="records")
        except (OSError, questdb.QuestDBError) as error:
            raise HotStoreUnavailableError("QuestDB read failed") from error

    @staticmethod
    def _columns() -> str:
        return (
            "capture_id, asset, provider, source_id, channel, message_type, event_subtype, "
            "sid, seq, provider_timestamp, received_timestamp, schema_version, payload"
        )

    @staticmethod
    def _capture_fact(row: dict[str, Any]) -> CaptureFact:
        source_id = QuestDBHotStore._required_text(row, "source_id")
        message_type = QuestDBHotStore._required_text(row, "message_type")
        asset_value = row.get("asset")
        if not isinstance(asset_value, str):
            raise StoredCaptureFactIncompatibleError(
                "stored capture row has a non-canonical asset"
            )
        try:
            asset = AssetId(asset_value)
        except (TypeError, ValueError) as error:
            raise StoredCaptureFactIncompatibleError(
                "stored capture row has a non-canonical asset"
            ) from error
        received_timestamp = QuestDBHotStore._timestamp_ns(row["received_timestamp"])
        if received_timestamp is None:
            raise TypeError("QuestDB returned a null received timestamp")
        return CaptureFact(
            capture_id=row["capture_id"],
            asset=asset,
            provider=row["provider"],
            source_id=source_id,
            channel=row["channel"],
            message_type=message_type,
            event_subtype=QuestDBHotStore._optional_text(row, "event_subtype"),
            sid=row["sid"],
            seq=row["seq"],
            provider_timestamp=QuestDBHotStore._timestamp_ns(row["provider_timestamp"]),
            received_timestamp=received_timestamp,
            schema_version=row["schema_version"],
            payload=row["payload"],
        )

    @staticmethod
    def _required_text(row: dict[str, Any], field_name: str) -> str:
        value = row.get(field_name)
        if not isinstance(value, str) or not value:
            raise StoredCaptureFactIncompatibleError(
                f"stored capture row lacks required {field_name}"
            )
        return value

    @staticmethod
    def _optional_text(row: dict[str, Any], field_name: str) -> str | None:
        value = row.get(field_name)
        if value is None or pd.isna(value):
            return None
        if not isinstance(value, str):
            raise StoredCaptureFactIncompatibleError(
                f"stored capture row has an invalid {field_name}"
            )
        return value

    @staticmethod
    def _timestamp_ns(value: Any) -> int | None:
        if value is None or pd.isna(value):
            return None
        timestamp_value = getattr(value, "value", value)
        if pd.isna(timestamp_value):
            return None
        if not isinstance(timestamp_value, int):
            raise TypeError("QuestDB returned a non-nanosecond timestamp")
        return timestamp_value
