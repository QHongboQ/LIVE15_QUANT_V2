from collections.abc import Sequence
from dataclasses import replace
from typing import Any, Self

import pytest

from live15_quant_v2.data.storage.hot_store import (
    BatchTooLargeError,
    CaptureFact,
    CaptureRange,
    HotStoreUnavailableError,
    HotStoreWriteRejectedError,
    TimestampOrder,
    questdb_adapter,
)
from live15_quant_v2.data.storage.hot_store.questdb_adapter import QuestDBHotStore

BASE_NS = 1_700_000_000_000_000_000
LIVE15_ASSETS = ("BTC", "ETH", "Gold", "Silver", "XRP", "SOL", "HYPE", "DOGE", "BNB")


class FakeFrame:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def to_dict(self, *, orient: str) -> list[dict[str, Any]]:
        assert orient == "records"
        return self._rows


class FakeQueryResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def to_pandas(self) -> FakeFrame:
        return FakeFrame(self._rows)


class FakeSender:
    def __init__(self, database: "FakeDatabase") -> None:
        self._database = database
        self._pending: list[dict[str, Any]] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def row(self, _: str, *, columns: dict[str, Any], at: Any) -> None:
        self._pending.append(
            {
                **columns,
                "provider_timestamp": columns["provider_timestamp"].value,
                "received_timestamp": at.value,
            }
        )

    def flush_and_get_fsn(self) -> int:
        return 7

    def await_acked_fsn(self, _: int, *, timeout_millis: int) -> bool:
        assert timeout_millis == 15_000
        if self._database.acknowledged:
            self._database.rows.extend(self._pending)
        return self._database.acknowledged


class FakeDatabase:
    def __init__(self, *, acknowledged: bool = True) -> None:
        self.acknowledged = acknowledged
        self.rows: list[dict[str, Any]] = []
        self.executed: list[str] = []
        self.closed = False

    def close(self) -> None:
        self.closed = True

    def execute(self, sql: str) -> None:
        self.executed.append(sql)

    def sender(self) -> FakeSender:
        return FakeSender(self)

    def query(self, sql: str, binds: Sequence[Any]) -> FakeQueryResult:
        selected = list(self.rows)
        if "capture_id = $1" in sql:
            selected = [row for row in selected if row["capture_id"] == binds[0]]
        else:
            selected = [
                row
                for row in selected
                if binds[0] <= row["received_timestamp"] <= binds[1]
            ]
            if "asset = $3" in sql:
                selected = [row for row in selected if row["asset"] == binds[2]]
            if "channel = $3" in sql:
                selected = [row for row in selected if row["channel"] == binds[2]]
            if "channel = $4" in sql:
                selected = [row for row in selected if row["channel"] == binds[3]]
        order_column = "provider_timestamp" if "ORDER BY provider_timestamp" in sql else "received_timestamp"
        return FakeQueryResult(sorted(selected, key=lambda row: row[order_column]))


def fact(
    capture_id: str,
    *,
    asset: str = "BTC",
    channel: str = "orderbook",
    provider: str = "kalshi",
    sid: int = 1,
    seq: int | None = 1,
    provider_offset: int = 0,
    received_offset: int = 0,
    payload: str = '{"raw":true}',
) -> CaptureFact:
    return CaptureFact(
        capture_id=capture_id,
        asset=asset,
        channel=channel,
        provider=provider,
        sid=sid,
        seq=seq,
        provider_timestamp=BASE_NS + provider_offset,
        received_timestamp=BASE_NS + received_offset,
        schema_version="market-ingress/v1",
        payload=payload,
    )


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch) -> FakeDatabase:
    fake = FakeDatabase()
    monkeypatch.setattr(questdb_adapter.questdb, "connect", lambda _: fake)
    return fake


def store() -> QuestDBHotStore:
    return QuestDBHotStore("ws::addr=hot-store.test:9000;", table_name="hot_store_test")


def test_round_trip_preserves_every_raw_field(database: FakeDatabase) -> None:
    expected = fact(
        "capture-1",
        asset="Gold",
        channel="pyth_value",
        provider="kalshi",
        sid=41,
        seq=None,
        provider_offset=71,
        received_offset=99,
        payload='{"value":"123.456","raw":"exact"}',
    )

    hot_store = store()
    receipt = hot_store.append_batch([expected])

    assert receipt.appended_count == 1
    assert hot_store.read_capture("capture-1") == expected
    assert "DEDUP" not in database.executed[0]


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            '{"book":{"yes":[["0.42",12]],"no":[["0.58",8]]},"meta":{"depth":1}}',
            id="nested-json",
        ),
        pytest.param('{"symbol":"金","note":"café ☕","currency":"€"}', id="unicode"),
        pytest.param(
            r'{"line":"first\nsecond","quote":"\"exact\"","path":"C:\\data"}',
            id="escaped-characters",
        ),
        pytest.param("{}", id="empty-structured-payload"),
        pytest.param(
            '{"market":{"ticker":"BTC-USD","status":"open"},"levels":['
            '{"side":"yes","price":"0.4200","quantity":12345},'
            '{"side":"no","price":"0.5800","quantity":67890},'
            '{"side":"yes","price":"0.4100","quantity":11111}],'
            '"metadata":{"provider":"kalshi","sequence":987654321,'
            '"received_by":"live15","flags":["raw","unmodified","audit"]}}',
            id="representative-longer-payload",
        ),
    ],
)
def test_payload_text_round_trips_exactly(database: FakeDatabase, payload: str) -> None:
    """Hot Store preserves opaque payload text without inspecting its JSON structure."""
    expected = fact("payload-round-trip", payload=payload)
    hot_store = store()

    hot_store.append_batch([expected])

    assert hot_store.read_capture(expected.capture_id) == expected


def test_duplicate_raw_facts_remain_individually_retrievable(database: FakeDatabase) -> None:
    hot_store = store()
    first = fact("capture-a", channel="trade", seq=None, payload='{"price":"100"}')
    second = replace(first, capture_id="capture-b")

    hot_store.append_batch([first, second])

    assert hot_store.read_capture(first.capture_id) == first
    assert hot_store.read_capture(second.capture_id) == second
    assert len(database.rows) == 2


def test_null_sequence_and_received_timestamp_are_preserved(
    database: FakeDatabase,
) -> None:
    hot_store = store()
    expected = fact("capture-null-seq", seq=None, received_offset=321)

    hot_store.append_batch([expected])

    assert hot_store.read_capture(expected.capture_id) == expected


def test_out_of_order_provider_times_are_physical_facts(database: FakeDatabase) -> None:
    hot_store = store()
    facts = [
        fact(f"capture-{offset}", provider_offset=offset, received_offset=index)
        for index, offset in enumerate((100, 105, 102, 103))
    ]
    hot_store.append_batch(facts)

    result = hot_store.read_range(
        CaptureRange(
            BASE_NS,
            BASE_NS + 1_000,
            order_by=TimestampOrder.PROVIDER,
        )
    )

    assert [item.provider_timestamp - BASE_NS for item in result] == [100, 102, 103, 105]
    assert {item.received_timestamp for item in result} == {
        BASE_NS,
        BASE_NS + 1,
        BASE_NS + 2,
        BASE_NS + 3,
    }


def test_all_nine_assets_and_representative_channels_round_trip(
    database: FakeDatabase,
) -> None:
    channels = (
        "orderbook",
        "ticker",
        "pyth_value",
        "pyth_value",
        "trade",
        "lifecycle",
        "cf_reference",
        "cf_reference",
        "cf_reference",
    )
    facts = [
        fact(
            f"capture-{asset.lower()}",
            asset=asset,
            channel=channel,
            provider="kalshi",
            sid=index + 1,
            seq=None if channel != "orderbook" else 1,
            received_offset=index,
        )
        for index, (asset, channel) in enumerate(zip(LIVE15_ASSETS, channels, strict=True))
    ]
    hot_store = store()

    hot_store.append_batch(facts)

    assert {hot_store.read_capture(item.capture_id) for item in facts} == set(facts)


def test_capture_and_filtered_range_reads(database: FakeDatabase) -> None:
    hot_store = store()
    facts = [
        fact("btc-orderbook", asset="BTC", channel="orderbook", received_offset=10),
        fact("btc-ticker", asset="BTC", channel="ticker", received_offset=20),
        fact("eth-orderbook", asset="ETH", channel="orderbook", received_offset=30),
    ]
    hot_store.append_batch(facts)

    assert hot_store.read_capture("missing") is None
    assert hot_store.read_range(CaptureRange(BASE_NS, BASE_NS + 100, asset="BTC")) == facts[:2]
    assert hot_store.read_range(CaptureRange(BASE_NS, BASE_NS + 100, channel="orderbook")) == [facts[0], facts[2]]
    assert hot_store.read_range(CaptureRange(BASE_NS, BASE_NS + 100, asset="BTC", channel="orderbook")) == [facts[0]]


def test_batch_limit_is_explicit_and_does_not_split(database: FakeDatabase) -> None:
    hot_store = store()
    too_many = [fact(f"capture-{index}") for index in range(hot_store.max_batch_rows + 1)]

    with pytest.raises(BatchTooLargeError, match="limited to 500"):
        hot_store.append_batch(too_many)

    assert database.rows == []


def test_unavailable_database_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(_: str) -> None:
        raise OSError("offline")

    monkeypatch.setattr(questdb_adapter.questdb, "connect", unavailable)

    with pytest.raises(HotStoreUnavailableError, match="unavailable"):
        store().read_capture("capture-1")


def test_unacknowledged_write_is_not_reported_as_persisted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = FakeDatabase(acknowledged=False)
    monkeypatch.setattr(questdb_adapter.questdb, "connect", lambda _: database)

    with pytest.raises(HotStoreWriteRejectedError, match="did not acknowledge"):
        store().append_batch([fact("rejected")])

    assert database.rows == []
