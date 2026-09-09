"""Opt-in disposable QuestDB acceptance for Replay availability support."""

import os
from uuid import uuid4

import pytest
from test_questdb_truth_history_integration import _assert_lifecycle, _server

from live15_quant_v2.data.replay_as_of.availability import (
    SUPPORTED_PROOF_SCHEMA_VERSION,
    AvailabilityKind,
    AvailabilityRecord,
    AvailabilitySupportError,
    AvailabilitySupportErrorCode,
)
from live15_quant_v2.data.replay_as_of.questdb_availability import (
    QuestDBAvailabilityStore,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("LIVE15_RUN_REPLAY_AVAILABILITY_QUESTDB_INTEGRATION") != "1",
    reason="set LIVE15_RUN_REPLAY_AVAILABILITY_QUESTDB_INTEGRATION=1 for task-owned QuestDB",
)


def _record(kind: AvailabilityKind, capture_id: str, policy: str | None, at: int) -> AvailabilityRecord:
    return AvailabilityRecord(kind, capture_id, policy, at, SUPPORTED_PROOF_SCHEMA_VERSION, "source/v1")


def test_disposable_append_find_floor_and_reopen_are_append_only(tmp_path) -> None:
    table = f"replay_availability_{uuid4().hex}"
    with _server(tmp_path) as server:
        adapter = QuestDBAvailabilityStore(server.connection_string, table_name=table, acknowledgement_timeout_millis=5_000)
        evidence = _record(AvailabilityKind.EVIDENCE, "capture-1", None, 11)
        authority = _record(AvailabilityKind.AUTHORITY, "capture-1", "data-truth/v1", 17)
        assert adapter.append(evidence) == evidence
        assert adapter.append(authority) == authority
        assert adapter.find(evidence.key) == evidence
        assert adapter.find(authority.key) == authority
        assert adapter.read_committed_floor() == 17
        assert adapter.append(evidence) == evidence
        with pytest.raises(AvailabilitySupportError) as error:
            adapter.append(_record(AvailabilityKind.EVIDENCE, "capture-1", None, 19))
        assert error.value.code is AvailabilitySupportErrorCode.INVARIANT_CONFLICT
        adapter.close()
        reopened = QuestDBAvailabilityStore(server.connection_string, table_name=table, acknowledgement_timeout_millis=5_000)
        assert reopened.find(authority.key) == authority
        assert reopened.read_committed_floor() == 17
        reopened.close()
    _assert_lifecycle(server)
