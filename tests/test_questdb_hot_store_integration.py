"""Bounded adapter integration coverage for an official local QuestDB instance."""

import os
import time

import pytest
import questdb

from live15_quant_v2.data.storage.hot_store import (
    BatchTooLargeError,
    CaptureFact,
    CaptureRange,
    QuestDBHotStore,
    TimestampOrder,
)

CONNECTION_STRING = os.getenv("LIVE15_QUESTDB_CONNECTION_STRING")
pytestmark = pytest.mark.integration
BASE_NS = 1_700_000_000_000_000_000
TABLE_NAME = "hot_store_adapter_integration"


def facts() -> list[CaptureFact]:
    return [
        CaptureFact("btc-orderbook", "BTC", "orderbook", "kalshi", 1, 10, BASE_NS + 10, BASE_NS + 100, "market-ingress/v1", '{"snapshot":true}'),
        CaptureFact("eth-ticker", "ETH", "ticker", "kalshi", 2, None, BASE_NS + 20, BASE_NS + 200, "market-ingress/v1", '{"price":"100"}'),
        CaptureFact("gold-pyth", "Gold", "pyth_value", "kalshi", 3, None, BASE_NS + 30, BASE_NS + 300, "market-ingress/v1", '{"value":"2000"}'),
        CaptureFact("silver-pyth", "Silver", "pyth_value", "kalshi", 4, None, BASE_NS + 40, BASE_NS + 400, "market-ingress/v1", '{"value":"25"}'),
        CaptureFact("xrp-trade", "XRP", "trade", "kalshi", 5, None, BASE_NS + 50, BASE_NS + 500, "market-ingress/v1", '{"trade":true}'),
        CaptureFact("sol-lifecycle", "SOL", "lifecycle", "kalshi", 6, None, BASE_NS + 60, BASE_NS + 600, "market-ingress/v1", '{"status":"open"}'),
        CaptureFact("hype-cf", "HYPE", "cf_reference", "kalshi", 7, None, BASE_NS + 70, BASE_NS + 700, "market-ingress/v1", '{"value":"1"}'),
        CaptureFact("doge-cf", "DOGE", "cf_reference", "kalshi", 8, None, BASE_NS + 80, BASE_NS + 800, "market-ingress/v1", '{"value":"2"}'),
        CaptureFact("bnb-cf", "BNB", "cf_reference", "kalshi", 9, None, BASE_NS + 90, BASE_NS + 900, "market-ingress/v1", '{"value":"3"}'),
        CaptureFact("duplicate-a", "BTC", "trade", "kalshi", 10, None, BASE_NS + 100, BASE_NS + 1_000, "market-ingress/v1", '{"same":true}'),
        CaptureFact("duplicate-b", "BTC", "trade", "kalshi", 10, None, BASE_NS + 100, BASE_NS + 1_100, "market-ingress/v1", '{"same":true}'),
        CaptureFact("o3-100", "ETH", "ticker", "kalshi", 11, None, BASE_NS + 100, BASE_NS + 2_000, "market-ingress/v1", '{"o3":true}'),
        CaptureFact("o3-105", "ETH", "ticker", "kalshi", 11, None, BASE_NS + 105, BASE_NS + 2_100, "market-ingress/v1", '{"o3":true}'),
        CaptureFact("o3-102", "ETH", "ticker", "kalshi", 11, None, BASE_NS + 102, BASE_NS + 2_200, "market-ingress/v1", '{"o3":true}'),
        CaptureFact("o3-103", "ETH", "ticker", "kalshi", 11, None, BASE_NS + 103, BASE_NS + 2_300, "market-ingress/v1", '{"o3":true}'),
    ]


@pytest.mark.skipif(CONNECTION_STRING is None, reason="requires a local QuestDB connection")
def test_questdb_adapter_preserves_live15_capture_facts() -> None:
    assert CONNECTION_STRING is not None
    with questdb.connect(CONNECTION_STRING) as database:
        database.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")

    hot_store = QuestDBHotStore(CONNECTION_STRING, table_name=TABLE_NAME)
    expected = facts()
    assert hot_store.append_batch(expected).appended_count == len(expected)

    deadline = time.monotonic() + 15
    actual: list[CaptureFact] = []
    while time.monotonic() < deadline:
        actual = hot_store.read_range(CaptureRange(BASE_NS, BASE_NS + 10_000))
        if len(actual) == len(expected):
            break
        time.sleep(0.05)
    assert actual == expected
    assert hot_store.read_capture("duplicate-a") == expected[9]
    assert hot_store.read_capture("duplicate-b") == expected[10]
    assert [fact.capture_id for fact in hot_store.read_range(CaptureRange(BASE_NS, BASE_NS + 10_000, order_by=TimestampOrder.PROVIDER)) if fact.capture_id.startswith("o3-")] == ["o3-100", "o3-102", "o3-103", "o3-105"]
    assert len(hot_store.read_range(CaptureRange(BASE_NS, BASE_NS + 10_000, asset="BTC", channel="orderbook"))) == 1
    with pytest.raises(BatchTooLargeError):
        hot_store.append_batch([expected[0]] * (hot_store.max_batch_rows + 1))
    hot_store.close()
