"""Bounded live acceptance for the QuestDB SF Durable Persistence seam."""

import os
import shutil
import time
from uuid import uuid4

import pytest
import questdb

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.durable_persistence import PersistenceStatus
from live15_quant_v2.data.storage.durable_persistence.questdb_sf import (
    QuestDBSFDurablePersistence,
)

CONNECTION_STRING = os.getenv("LIVE15_QUESTDB_CONNECTION_STRING")
pytestmark = pytest.mark.integration


def _table_name() -> str:
    return f"durable_persistence_sf_integration_{uuid4().hex}"


def _table_exists(database: questdb.QuestDB, table_name: str) -> bool:
    rows = database.query(
        f"SELECT table_name FROM tables() WHERE table_name = '{table_name}'"
    ).to_pandas().to_dict(orient="records")
    return bool(rows)


def _wait_for_row(database: questdb.QuestDB, table_name: str, capture_id: str) -> dict[str, object]:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        rows = database.query(
            f"SELECT capture_id, received_timestamp, payload FROM {table_name} "
            f"WHERE capture_id = '{capture_id}'"
        ).to_pandas().to_dict(orient="records")
        if rows:
            return rows[0]
        time.sleep(0.05)
    raise AssertionError("SF-published capture fact did not appear in its task-owned table")


@pytest.mark.skipif(CONNECTION_STRING is None, reason="LIVE15 QuestDB is not configured")
def test_questdb_sf_persists_one_fact_and_cleans_task_resources(tmp_path) -> None:
    assert CONNECTION_STRING is not None
    table_name = _table_name()
    sf_dir = tmp_path / "sf"
    sf_dir.mkdir()
    control_database = questdb.connect(CONNECTION_STRING)
    persistence = QuestDBSFDurablePersistence(
        connection_string=CONNECTION_STRING,
        table_name=table_name,
        sf_dir=sf_dir,
        sender_id=f"live15-durable-persistence-{uuid4().hex}",
        acknowledgement_timeout_millis=15_000,
    )
    try:
        control_database.execute(
            f"CREATE TABLE {table_name} ("
            "capture_id VARCHAR, asset SYMBOL, provider SYMBOL, source_id VARCHAR, "
            "channel SYMBOL, message_type VARCHAR, event_subtype VARCHAR, "
            "sid LONG, seq LONG, provider_timestamp TIMESTAMP_NS, "
            "schema_version VARCHAR, payload VARCHAR, received_timestamp TIMESTAMP_NS"
            ") TIMESTAMP(received_timestamp) PARTITION BY DAY WAL "
            "DEDUP UPSERT KEYS(received_timestamp, capture_id)"
        )
        fact = CaptureFact(
            capture_id=f"capture-{uuid4().hex}",
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
            payload='{"price":"100"}',
        )

        result = persistence.persist(fact)

        assert result.status is PersistenceStatus.ACKNOWLEDGED_OK
        row = _wait_for_row(control_database, table_name, fact.capture_id)
        assert row["capture_id"] == fact.capture_id
        assert row["received_timestamp"].value == fact.received_timestamp
        assert row["payload"] == fact.payload
    finally:
        persistence.close()
        control_database.execute(f"DROP TABLE IF EXISTS {table_name}")
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and _table_exists(control_database, table_name):
            time.sleep(0.05)
        assert not _table_exists(control_database, table_name)
        control_database.close()
        shutil.rmtree(sf_dir)
        assert not sf_dir.exists()
