"""QuestDB implementation of the provider-neutral Hot Store seam."""

import re
from collections.abc import Sequence
from typing import Any

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


class StoredCaptureFactIncompatibleError(RuntimeError):
    """Raised when a stored row cannot satisfy the shared CaptureFact contract."""


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
                            "asset": fact.asset,
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
                self._database.execute(
                    f"CREATE TABLE IF NOT EXISTS {self._table_name} ("
                    "capture_id VARCHAR, asset SYMBOL, provider SYMBOL, source_id VARCHAR, "
                    "channel SYMBOL, message_type VARCHAR, event_subtype VARCHAR, "
                    "sid LONG, seq LONG, provider_timestamp TIMESTAMP_NS, "
                    "schema_version VARCHAR, payload VARCHAR, received_timestamp TIMESTAMP_NS"
                    ") TIMESTAMP(received_timestamp) PARTITION BY DAY WAL"
                )
                self._database.execute(
                    f"ALTER TABLE {self._table_name} ADD COLUMN IF NOT EXISTS "
                    "source_id VARCHAR, message_type VARCHAR, event_subtype VARCHAR"
                )
            except (OSError, questdb.QuestDBError) as error:
                raise HotStoreUnavailableError("QuestDB schema is unavailable") from error
            self._schema_ready = True
        return self._database

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
            event_subtype=row["event_subtype"],
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
    def _timestamp_ns(value: Any) -> int | None:
        if value is None or pd.isna(value):
            return None
        timestamp_value = getattr(value, "value", value)
        if pd.isna(timestamp_value):
            return None
        if not isinstance(timestamp_value, int):
            raise TypeError("QuestDB returned a non-nanosecond timestamp")
        return timestamp_value
