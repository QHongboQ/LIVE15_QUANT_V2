from dataclasses import dataclass
from typing import Any

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.durable_persistence import (
    PersistenceStatus,
)
from live15_quant_v2.data.storage.durable_persistence.questdb_sf import (
    QuestDBSFDurablePersistence,
)


class FakeSender:
    def __init__(
        self,
        *,
        acknowledged: bool = True,
        row_error: BaseException | None = None,
        flush_error: BaseException | None = None,
        await_error: BaseException | None = None,
        errors: list["FakeSenderError"] | None = None,
        dropped_values: list[int] | None = None,
    ) -> None:
        self.row_calls: list[dict[str, Any]] = []
        self.closed = False
        self.acknowledged = acknowledged
        self.row_error = row_error
        self.flush_error = flush_error
        self.await_error = await_error
        self.errors = list(errors or [])
        self.dropped_values = iter(dropped_values or [0])
        self.last_dropped = 0

    def row(
        self,
        table_name: str,
        *,
        symbols: dict[str, str],
        columns: dict[str, Any],
        at: Any,
    ) -> None:
        if self.row_error is not None:
            raise self.row_error
        self.row_calls.append(
            {
                "table_name": table_name,
                "symbols": symbols,
                "columns": columns,
                "at": at,
            }
        )

    def flush_and_get_fsn(self) -> int:
        if self.flush_error is not None:
            raise self.flush_error
        return 42

    def await_acked_fsn(self, fsn: int, timeout_millis: int) -> bool:
        assert fsn == 42
        assert timeout_millis == 500
        if self.await_error is not None:
            raise self.await_error
        return self.acknowledged

    def poll_error(self) -> "FakeSenderError | None":
        return self.errors.pop(0) if self.errors else None

    def error_events_dropped(self) -> int:
        try:
            self.last_dropped = next(self.dropped_values)
        except StopIteration:
            pass
        return self.last_dropped

    def close(self, *, flush: bool) -> None:
        assert flush is False
        self.closed = True


class FakeDatabase:
    def __init__(self, sender: FakeSender, *, dropped_values: list[int] | None = None) -> None:
        self._sender = sender
        self._dropped_values = iter(dropped_values or [0])
        self._last_dropped = 0
        self.closed = False

    @property
    def error_events_dropped(self) -> int:
        try:
            self._last_dropped = next(self._dropped_values)
        except StopIteration:
            pass
        return self._last_dropped

    def sender(self) -> FakeSender:
        return self._sender

    def close(self) -> None:
        self.closed = True


@dataclass(frozen=True)
class FakeSenderError:
    from_fsn: int
    to_fsn: int
    applied_policy: str = "terminal"
    message_sequence: int | None = 1


def capture_fact() -> CaptureFact:
    return CaptureFact(
        capture_id="capture-1",
        asset=AssetId.BTC,
        provider="kalshi",
        source_id="KXBTC15M-TICKER",
        channel="ticker",
        message_type="ticker",
        event_subtype=None,
        sid=123,
        seq=456,
        provider_timestamp=1_700_000_000_000_000_001,
        received_timestamp=1_700_000_000_000_000_002,
        schema_version="market-ingress/v1",
        payload='{"price": "100"}',
    )


def persistence_for(
    monkeypatch, sender: FakeSender, *, database_dropped_values: list[int] | None = None
) -> QuestDBSFDurablePersistence:
    from live15_quant_v2.data.storage.durable_persistence import questdb_sf

    database = FakeDatabase(sender, dropped_values=database_dropped_values)
    monkeypatch.setattr(questdb_sf.questdb, "connect", lambda *_args, **_kwargs: database)
    return QuestDBSFDurablePersistence(
        connection_string="ws::addr=localhost:9000;",
        table_name="durable_persistence_test",
        sf_dir="D:/task-owned/sf",
        sender_id="live15-test-sender",
        acknowledgement_timeout_millis=500,
    )


def test_persist_acknowledges_exact_capture_fact(monkeypatch) -> None:
    from live15_quant_v2.data.storage.durable_persistence import questdb_sf

    sender = FakeSender()
    database = FakeDatabase(sender)
    connect_calls: list[tuple[str, dict[str, Any]]] = []

    def connect(connection_string: str, **kwargs: Any) -> FakeDatabase:
        connect_calls.append((connection_string, kwargs))
        return database

    monkeypatch.setattr(questdb_sf.questdb, "connect", connect)
    persistence = QuestDBSFDurablePersistence(
        connection_string="ws::addr=localhost:9000;",
        table_name="durable_persistence_test",
        sf_dir="D:/task-owned/sf",
        sender_id="live15-test-sender",
        acknowledgement_timeout_millis=500,
    )

    result = persistence.persist(capture_fact())

    assert result.status is PersistenceStatus.ACKNOWLEDGED_OK
    assert connect_calls == [
        (
            "ws::addr=localhost:9000;",
            {
                "sf_dir": "D:/task-owned/sf",
                "sender_id": "live15-test-sender",
                "sf_durability": "memory",
                "auto_flush": False,
            },
        )
    ]
    assert len(sender.row_calls) == 1
    row = sender.row_calls[0]
    assert row["table_name"] == "durable_persistence_test"
    assert row["symbols"] == {"asset": "BTC", "provider": "kalshi", "channel": "ticker"}
    columns = dict(row["columns"])
    provider_timestamp = columns.pop("provider_timestamp")
    assert columns == {
        "capture_id": "capture-1",
        "source_id": "KXBTC15M-TICKER",
        "message_type": "ticker",
        "event_subtype": None,
        "sid": 123,
        "seq": 456,
        "schema_version": "market-ingress/v1",
        "payload": '{"price": "100"}',
    }
    assert type(provider_timestamp) is questdb_sf.questdb.TimestampNanos
    assert provider_timestamp.value == 1_700_000_000_000_000_001
    assert type(row["at"]) is questdb_sf.questdb.TimestampNanos
    assert row["at"].value == 1_700_000_000_000_000_002
    assert sender.closed is True


def test_ack_timeout_is_pending_without_a_second_publish(monkeypatch) -> None:
    sender = FakeSender(acknowledged=False)
    persistence = persistence_for(monkeypatch, sender)

    result = persistence.persist(capture_fact())

    assert result.status is PersistenceStatus.PERSISTED_PENDING
    assert len(sender.row_calls) == 1


def test_definite_pre_publication_failure_is_not_persisted(monkeypatch) -> None:
    sender = FakeSender(row_error=OSError("buffer serialization failed"))
    persistence = persistence_for(monkeypatch, sender)

    result = persistence.persist(capture_fact())

    assert result.status is PersistenceStatus.LOCAL_PERSISTENCE_FAILED


def test_structured_rejection_covering_the_frame_is_definite(monkeypatch) -> None:
    sender = FakeSender(errors=[FakeSenderError(from_fsn=42, to_fsn=42)])
    persistence = persistence_for(monkeypatch, sender)

    result = persistence.persist(capture_fact())

    assert result.status is PersistenceStatus.DEFINITELY_REJECTED


def test_structured_rejection_for_another_frame_does_not_reject_current_fact(monkeypatch) -> None:
    sender = FakeSender(errors=[FakeSenderError(from_fsn=43, to_fsn=43)])
    persistence = persistence_for(monkeypatch, sender)

    result = persistence.persist(capture_fact())

    assert result.status is PersistenceStatus.ACKNOWLEDGED_OK


def test_diagnostic_loss_after_publication_fails_closed(monkeypatch) -> None:
    sender = FakeSender(dropped_values=[0, 1])
    persistence = persistence_for(monkeypatch, sender)

    result = persistence.persist(capture_fact())

    assert result.status is PersistenceStatus.IN_DOUBT


def test_database_diagnostic_loss_after_publication_fails_closed(monkeypatch) -> None:
    sender = FakeSender()
    persistence = persistence_for(monkeypatch, sender, database_dropped_values=[0, 1])

    result = persistence.persist(capture_fact())

    assert result.status is PersistenceStatus.IN_DOUBT


def test_ambiguous_publication_failure_is_in_doubt(monkeypatch) -> None:
    class InDoubtError(OSError):
        in_doubt = True

    sender = FakeSender(flush_error=InDoubtError("connection lost"))
    persistence = persistence_for(monkeypatch, sender)

    result = persistence.persist(capture_fact())

    assert result.status is PersistenceStatus.IN_DOUBT


def test_post_publication_observation_failure_does_not_reenqueue(monkeypatch) -> None:
    sender = FakeSender(await_error=OSError("observation connection lost"))
    persistence = persistence_for(monkeypatch, sender)

    result = persistence.persist(capture_fact())

    assert result.status is PersistenceStatus.IN_DOUBT
    assert len(sender.row_calls) == 1


def test_close_releases_the_upstream_database(monkeypatch) -> None:
    from live15_quant_v2.data.storage.durable_persistence import questdb_sf

    database = FakeDatabase(FakeSender())
    monkeypatch.setattr(questdb_sf.questdb, "connect", lambda *_args, **_kwargs: database)
    persistence = QuestDBSFDurablePersistence(
        connection_string="ws::addr=localhost:9000;",
        table_name="durable_persistence_test",
        sf_dir="D:/task-owned/sf",
        sender_id="live15-test-sender",
        acknowledgement_timeout_millis=500,
    )

    persistence.persist(capture_fact())
    persistence.close()

    assert database.closed is True
