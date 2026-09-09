"""Opt-in, task-owned QuestDB acceptance for Recorder Composition."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from kalshi.ws.models.cfbenchmarks import CFBenchmarksValueMessage
from test_questdb_truth_history_integration import (
    _assert_lifecycle,
    _server,
    _TaskQuestDB,
)

from live15_quant_v2.data.data_truth import DataTruth
from live15_quant_v2.data.data_truth.questdb_history import QuestDBTruthDecisionHistory
from live15_quant_v2.data.recorder_composition import RecorderComposition
from live15_quant_v2.data.replay_as_of import (
    AsOfRequest,
    ReplayAsOf,
    ReplayOrdering,
    SelectionAxis,
    SelectionWindow,
)
from live15_quant_v2.data.replay_as_of.availability import AvailabilityWriter
from live15_quant_v2.data.replay_as_of.questdb_availability import (
    QuestDBAvailabilityStore,
)
from live15_quant_v2.data.replay_as_of.questdb_source import QuestDBReplaySource
from live15_quant_v2.data.storage.capture_boundary import CaptureBoundary
from live15_quant_v2.data.storage.durable_persistence import PersistenceStatus
from live15_quant_v2.data.storage.durable_persistence.questdb_sf import (
    QuestDBSFDurablePersistence,
)
from live15_quant_v2.data.storage.hot_store.questdb_adapter import QuestDBHotStore

_RUN_END_TO_END = os.getenv("LIVE15_RUN_REPLAY_RECORDER_QUESTDB_END_TO_END") == "1"
_EVIDENCE_AUTHORITY = "recorder-evidence-authority/v1"
_TRUTH_AUTHORITY = "recorder-truth-authority/v1"
_AVAILABILITY_AUTHORITY = "recorder-availability-store/v1"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _RUN_END_TO_END,
        reason=(
            "set LIVE15_RUN_REPLAY_RECORDER_QUESTDB_END_TO_END=1 "
            "for task-owned QuestDB"
        ),
    ),
]


def _reference_message() -> CFBenchmarksValueMessage:
    return CFBenchmarksValueMessage.model_validate(
        {
            "type": "cfbenchmarks_value",
            "sid": 9,
            "seq": None,
            "msg": {
                "index_id": "BRTI",
                "received_at": 111,
                "data": '{"rate":"100.00000000"}',
                "avg_60s_data": {
                    "value": "100.00000000",
                    "window_size": 1,
                    "window_start_ts_ms": 1,
                    "window_end_ts_exclusive": 2,
                },
            },
        }
    )


def _count(server: _TaskQuestDB, table: str, capture_id: str) -> int:
    database = server.database
    assert database is not None
    rows = database.query(
        f"SELECT count() AS row_count FROM {table} WHERE capture_id = $1",
        [capture_id],
    ).to_pandas().to_dict(orient="records")
    return int(rows[0]["row_count"])


def _wait_for_task_table_visibility(server: _TaskQuestDB, table: str) -> None:
    database = server.database
    assert database is not None
    rows = database.query(
        f"SELECT wait_wal_table('{table}')", []
    ).to_pandas().to_dict(orient="records")
    assert len(rows) == 1
    assert next(iter(rows[0].values())) is True


def test_recorder_composition_publishes_one_replayable_proven_pair_and_recovers(
    tmp_path: Path,
) -> None:
    evidence_table = f"recorder_evidence_{uuid4().hex}"
    truth_table = f"recorder_truth_{uuid4().hex}"
    availability_table = f"recorder_availability_{uuid4().hex}"
    sf_dir = tmp_path / f"recorder-sf-{uuid4().hex}"

    with _server(tmp_path) as server:
        hot_store = QuestDBHotStore(server.connection_string, table_name=evidence_table)
        assert hot_store.read_capture("schema-primer") is None
        persistence = QuestDBSFDurablePersistence(
            connection_string=server.connection_string,
            table_name=evidence_table,
            sf_dir=sf_dir,
            sender_id=f"recorder-{uuid4().hex}",
            acknowledgement_timeout_millis=5_000,
        )
        history = QuestDBTruthDecisionHistory(
            server.connection_string,
            table_name=truth_table,
            hot_store=hot_store,
            acknowledgement_timeout_millis=5_000,
        )
        availability_store = QuestDBAvailabilityStore(
            server.connection_string,
            table_name=availability_table,
            acknowledgement_timeout_millis=5_000,
        )
        monotonic_ticks = iter((0, 1, 2, 3, 4))
        composition = RecorderComposition(
            capture_boundary=CaptureBoundary(
                clock_ns=lambda: 100,
                capture_id_factory=lambda: f"capture-{uuid4().hex}",
            ),
            durable_persistence=persistence,
            hot_store=hot_store,
            availability_writer=AvailabilityWriter(
                availability_store,
                wall_time_ns=lambda: 1_000,
                monotonic_ns=lambda: next(monotonic_ticks),
            ),
            data_truth=DataTruth(history),
            evidence_authority_identity=_EVIDENCE_AUTHORITY,
            truth_decision_authority_identity=_TRUTH_AUTHORITY,
        )

        recorded = composition.record_reference(_reference_message())

        assert recorded.persistence_result is not None
        assert recorded.persistence_result.status is PersistenceStatus.ACKNOWLEDGED_OK
        assert recorded.evidence_proven is False
        assert recorded.evidence_availability is None
        assert recorded.truth_decision is None
        assert recorded.authority_availability is None
        _wait_for_task_table_visibility(server, evidence_table)

        recovered = composition.recover_fact(recorded.capture_fact)

        assert recovered.persistence_result is None
        assert recovered.capture_fact == recorded.capture_fact
        assert recovered.evidence_proven is True
        assert recovered.evidence_availability is not None
        assert recovered.truth_decision is not None
        assert recovered.authority_availability is not None
        assert recovered.evidence_availability.available_at_ns < (
            recovered.authority_availability.available_at_ns
        )
        assert _count(server, evidence_table, recorded.capture_fact.capture_id) == 1
        assert _count(server, availability_table, recorded.capture_fact.capture_id) == 2

        source = QuestDBReplaySource(
            server.connection_string,
            evidence_table=evidence_table,
            truth_decision_table=truth_table,
            availability_table=availability_table,
            evidence_authority_identity=_EVIDENCE_AUTHORITY,
            truth_decision_authority_identity=_TRUTH_AUTHORITY,
            availability_authority_identity=_AVAILABILITY_AUTHORITY,
        )
        view = ReplayAsOf(source, max_page_size=10).read(
            AsOfRequest(
                2_000,
                "data-truth/v1",
                SelectionWindow(SelectionAxis.ARRIVAL_TIME, 0, 200),
                ReplayOrdering.ARRIVAL,
                None,
                None,
                10,
                None,
            )
        )
        assert [record.capture_fact.capture_id for record in view.records] == [
            recorded.capture_fact.capture_id
        ]
        assert len(view.records) == 1

        source.close()
        availability_store.close()
        history.close()
        persistence.close()
        hot_store.close()
        shutil.rmtree(sf_dir)
    _assert_lifecycle(server)
    assert not sf_dir.exists()
