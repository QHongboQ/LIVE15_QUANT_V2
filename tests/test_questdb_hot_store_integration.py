"""Bounded adapter integration coverage for an official local QuestDB instance."""

import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

import pytest
import questdb

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.hot_store import (
    BatchTooLargeError,
    CaptureRange,
    TimestampOrder,
)
from live15_quant_v2.data.storage.hot_store.questdb_adapter import (
    QuestDBHotStore,
    QuestDBHotStoreMigrationRequiredError,
)

CONNECTION_STRING = os.getenv("LIVE15_QUESTDB_CONNECTION_STRING")
pytestmark = pytest.mark.integration
BASE_NS = 1_700_000_000_000_000_000
TABLE_PREFIX = "hot_store_dedup_evolution_integration"


def table_name() -> str:
    return f"{TABLE_PREFIX}_{uuid4().hex}"


@contextmanager
def disposable_table() -> Iterator[str]:
    """Own one task-scoped table and remove it on every test exit path."""
    assert CONNECTION_STRING is not None
    name = table_name()
    try:
        yield name
    finally:
        with questdb.connect(CONNECTION_STRING) as database:
            database.execute(f"DROP TABLE IF EXISTS {name}")


def physical_row_count(
    hot_store: QuestDBHotStore,
    name: str,
    *,
    capture_ids: set[str] | None = None,
) -> int:
    database = hot_store._database
    assert database is not None
    rows = database.query(f"SELECT capture_id FROM {name}").to_pandas().to_dict(
        orient="records"
    )
    return sum(
        1
        for row in rows
        if capture_ids is None or row["capture_id"] in capture_ids
    )


def wait_for_physical_row_count(
    hot_store: QuestDBHotStore,
    name: str,
    expected_count: int,
    *,
    capture_ids: set[str] | None = None,
) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if physical_row_count(hot_store, name, capture_ids=capture_ids) == expected_count:
            return
        time.sleep(0.05)
    assert physical_row_count(hot_store, name, capture_ids=capture_ids) == expected_count


def create_existing_table(name: str, *, dedup: bool) -> None:
    assert CONNECTION_STRING is not None
    ddl = (
        f"CREATE TABLE {name} ("
        "capture_id VARCHAR, asset SYMBOL, provider SYMBOL, source_id VARCHAR, "
        "channel SYMBOL, message_type VARCHAR, event_subtype VARCHAR, "
        "sid LONG, seq LONG, provider_timestamp TIMESTAMP_NS, "
        "schema_version VARCHAR, payload VARCHAR, received_timestamp TIMESTAMP_NS"
        ") TIMESTAMP(received_timestamp) PARTITION BY DAY WAL"
    )
    if dedup:
        ddl += " DEDUP UPSERT KEYS(received_timestamp, capture_id)"
    with questdb.connect(CONNECTION_STRING) as database:
        database.execute(ddl)


def capture_fact(
    capture_id: str,
    asset: AssetId,
    channel: str,
    sid: int,
    seq: int | None,
    provider_timestamp: int | None,
    received_timestamp: int,
    payload: str,
    *,
    message_type: str | None = None,
    event_subtype: str | None = None,
) -> CaptureFact:
    return CaptureFact(
        capture_id=capture_id,
        asset=asset,
        provider="kalshi",
        source_id=f"{asset.value}-source",
        channel=channel,
        message_type=message_type or channel,
        event_subtype=event_subtype,
        sid=sid,
        seq=seq,
        provider_timestamp=provider_timestamp,
        received_timestamp=received_timestamp,
        schema_version="market-ingress/v1",
        payload=payload,
    )


def facts() -> list[CaptureFact]:
    return [
        capture_fact(
            "btc-orderbook-snapshot",
            AssetId.BTC,
            "orderbook",
            1,
            10,
            BASE_NS + 10,
            BASE_NS + 100,
            '{"type":"snapshot","yes":[["0.42",12]],"no":[["0.58",8]]}',
            message_type="orderbook_snapshot",
        ),
        capture_fact(
            "btc-orderbook-delta",
            AssetId.BTC,
            "orderbook",
            1,
            11,
            BASE_NS + 11,
            BASE_NS + 110,
            '{"type":"delta","side":"yes","price":"0.42","delta":3}',
            message_type="orderbook_delta",
        ),
        capture_fact(
            "eth-ticker", AssetId.ETH, "ticker", 2, None, BASE_NS + 20, BASE_NS + 200, '{"price":"100"}'
        ),
        capture_fact(
            "gold-pyth", AssetId.GOLD, "pyth_value", 3, None, BASE_NS + 30, BASE_NS + 300, '{"value":"2000"}'
        ),
        capture_fact(
            "silver-pyth", AssetId.SILVER, "pyth_value", 4, None, BASE_NS + 40, BASE_NS + 400, '{"value":"25"}'
        ),
        capture_fact(
            "xrp-trade", AssetId.XRP, "trade", 5, None, BASE_NS + 50, BASE_NS + 500, '{"trade":true}'
        ),
        capture_fact(
            "sol-lifecycle",
            AssetId.SOL,
            "lifecycle",
            6,
            None,
            None,
            BASE_NS + 600,
            '{"status":"open"}',
            message_type="market_lifecycle_v2",
            event_subtype="open",
        ),
        capture_fact(
            "hype-cf", AssetId.HYPE, "cf_reference", 7, None, BASE_NS + 70, BASE_NS + 700, '{"value":"1"}'
        ),
        capture_fact(
            "doge-cf", AssetId.DOGE, "cf_reference", 8, None, BASE_NS + 80, BASE_NS + 800, '{"value":"2"}'
        ),
        capture_fact(
            "bnb-cf", AssetId.BNB, "cf_reference", 9, None, BASE_NS + 90, BASE_NS + 900, '{"value":"3"}'
        ),
        capture_fact(
            "duplicate-a", AssetId.BTC, "trade", 10, None, BASE_NS + 100, BASE_NS + 1_000, '{"same":true}'
        ),
        capture_fact(
            "duplicate-b", AssetId.BTC, "trade", 10, None, BASE_NS + 100, BASE_NS + 1_100, '{"same":true}'
        ),
        capture_fact(
            "o3-100", AssetId.ETH, "ticker", 11, None, BASE_NS + 100, BASE_NS + 2_000, '{"o3":true}'
        ),
        capture_fact(
            "o3-105", AssetId.ETH, "ticker", 11, None, BASE_NS + 105, BASE_NS + 2_100, '{"o3":true}'
        ),
        capture_fact(
            "o3-102", AssetId.ETH, "ticker", 11, None, BASE_NS + 102, BASE_NS + 2_200, '{"o3":true}'
        ),
        capture_fact(
            "o3-103", AssetId.ETH, "ticker", 11, None, BASE_NS + 103, BASE_NS + 2_300, '{"o3":true}'
        ),
    ]


@pytest.mark.skipif(CONNECTION_STRING is None, reason="requires a local QuestDB connection")
def test_questdb_adapter_preserves_live15_capture_facts() -> None:
    assert CONNECTION_STRING is not None
    with disposable_table() as name:
        hot_store = QuestDBHotStore(CONNECTION_STRING, table_name=name)
        try:
            expected = facts()
            expected_by_capture_id = {fact.capture_id: fact for fact in expected}
            assert hot_store.append_batch(expected).appended_count == len(expected)

            deadline = time.monotonic() + 15
            actual: list[CaptureFact] = []
            while time.monotonic() < deadline:
                actual = hot_store.read_range(CaptureRange(BASE_NS, BASE_NS + 10_000))
                if len(actual) == len(expected):
                    break
                time.sleep(0.05)
            assert actual == expected
            assert hot_store.read_capture("duplicate-a") == expected_by_capture_id["duplicate-a"]
            assert hot_store.read_capture("duplicate-b") == expected_by_capture_id["duplicate-b"]
            assert [
                fact.capture_id
                for fact in hot_store.read_range(
                    CaptureRange(BASE_NS, BASE_NS + 10_000, order_by=TimestampOrder.PROVIDER)
                )
                if fact.capture_id.startswith("o3-")
            ] == ["o3-100", "o3-102", "o3-103", "o3-105"]
            assert [
                fact.capture_id
                for fact in hot_store.read_range(
                    CaptureRange(BASE_NS, BASE_NS + 10_000, asset=AssetId.BTC, channel="orderbook")
                )
            ] == ["btc-orderbook-snapshot", "btc-orderbook-delta"]
            with pytest.raises(BatchTooLargeError):
                hot_store.append_batch([expected[0]] * (hot_store.max_batch_rows + 1))
        finally:
            hot_store.close()


@pytest.mark.skipif(CONNECTION_STRING is None, reason="requires a local QuestDB connection")
def test_questdb_native_dedup_preserves_transport_identity() -> None:
    assert CONNECTION_STRING is not None
    with disposable_table() as replay_table:
        replay_fact = capture_fact(
            "exact-replay",
            AssetId.BTC,
            "trade",
            99,
            None,
            BASE_NS + 1,
            BASE_NS + 5_000,
            '{"same":true}',
        )
        hot_store = QuestDBHotStore(CONNECTION_STRING, table_name=replay_table)
        try:
            hot_store.append_batch([replay_fact])
            hot_store.append_batch([replay_fact])
            wait_for_physical_row_count(hot_store, replay_table, 1)

            first = capture_fact(
                "distinct-a",
                AssetId.BTC,
                "trade",
                100,
                None,
                BASE_NS + 2,
                BASE_NS + 5_100,
                '{"same":true}',
            )
            second = CaptureFact(
                capture_id="distinct-b",
                asset=first.asset,
                provider=first.provider,
                source_id=first.source_id,
                channel=first.channel,
                message_type=first.message_type,
                event_subtype=first.event_subtype,
                sid=first.sid,
                seq=first.seq,
                provider_timestamp=first.provider_timestamp,
                received_timestamp=first.received_timestamp,
                schema_version=first.schema_version,
                payload=first.payload,
            )
            hot_store.append_batch([first, second])
            wait_for_physical_row_count(
                hot_store,
                replay_table,
                2,
                capture_ids={"distinct-a", "distinct-b"},
            )
        finally:
            hot_store.close()


@pytest.mark.skipif(CONNECTION_STRING is None, reason="requires a local QuestDB connection")
def test_existing_correct_questdb_table_is_accepted() -> None:
    assert CONNECTION_STRING is not None
    with disposable_table() as correct_table:
        create_existing_table(correct_table, dedup=True)
        hot_store = QuestDBHotStore(CONNECTION_STRING, table_name=correct_table)
        try:
            assert hot_store.append_batch(
                [
                    capture_fact(
                        "existing-correct",
                        AssetId.ETH,
                        "ticker",
                        101,
                        None,
                        BASE_NS + 3,
                        BASE_NS + 5_200,
                        '{"same":true}',
                    )
                ]
            ).appended_count == 1
        finally:
            hot_store.close()


@pytest.mark.skipif(CONNECTION_STRING is None, reason="requires a local QuestDB connection")
def test_existing_non_dedup_questdb_table_fails_closed() -> None:
    assert CONNECTION_STRING is not None
    with disposable_table() as non_dedup_table:
        create_existing_table(non_dedup_table, dedup=False)
        hot_store = QuestDBHotStore(CONNECTION_STRING, table_name=non_dedup_table)
        try:
            with pytest.raises(QuestDBHotStoreMigrationRequiredError, match="DEDUP enabled"):
                hot_store.append_batch(
                    [
                        capture_fact(
                            "existing-non-dedup",
                            AssetId.ETH,
                            "ticker",
                            102,
                            None,
                            BASE_NS + 4,
                            BASE_NS + 5_300,
                            '{"same":true}',
                        )
                    ]
                )
            with questdb.connect(CONNECTION_STRING) as database:
                metadata = database.query(
                    "SELECT table_name, dedup FROM tables()"
                ).to_pandas().to_dict(orient="records")
            assert next(row for row in metadata if row["table_name"] == non_dedup_table)[
                "dedup"
            ] is False
        finally:
            hot_store.close()


@pytest.mark.skipif(CONNECTION_STRING is None, reason="requires a local QuestDB connection")
def test_disposable_questdb_table_is_removed_after_test_path_exception() -> None:
    assert CONNECTION_STRING is not None
    names: list[str] = []
    with pytest.raises(RuntimeError, match="expected test path"), disposable_table() as name:
        names.append(name)
        create_existing_table(name, dedup=True)
        raise RuntimeError("expected test path")
    assert len(names) == 1
