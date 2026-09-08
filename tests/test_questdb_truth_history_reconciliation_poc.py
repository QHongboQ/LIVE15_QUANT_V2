"""Opt-in disposable QuestDB TruthDecision-history reconciliation POC."""

from __future__ import annotations

import json
import math
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.request import urlopen
from uuid import uuid4

import pytest
import questdb

from live15_quant_v2.data.data_truth.models import (
    EventIdentity,
    TradeNotAcceptedReason,
    TruthDecision,
    TruthDecisionCategory,
)

_RUN_POC = os.getenv("LIVE15_RUN_DATA_TRUTH_QUESTDB_POC") == "1"
_QUESTDB_EXE = Path(r"D:\LIVE15_V2_RUNTIME\questdb\dist\10.0.1\bin\questdb.exe")
_POLL_SECONDS = 30
_PHYSICAL_TIMESTAMP_NS = 1_800_000_000_000_000_000

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _RUN_POC,
        reason="set LIVE15_RUN_DATA_TRUTH_QUESTDB_POC=1 to run the local POC",
    ),
]


class _LookupState(StrEnum):
    ABSENT = "absent"
    EXACT = "exact"
    CONFLICTING = "conflicting"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class _Lookup:
    state: _LookupState
    decision: TruthDecision | None = None


class _ConflictingAuthorityError(RuntimeError):
    """Raised only by this test-local harness for non-exact stored authority."""


def _free_ports() -> dict[str, int]:
    sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(4)]
    try:
        for listener in sockets:
            listener.bind(("127.0.0.1", 0))
        return dict(
            zip(
                ("http", "pg", "min_http", "ilp"),
                (listener.getsockname()[1] for listener in sockets),
                strict=True,
            )
        )
    finally:
        for listener in sockets:
            listener.close()


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.2)
        return connection.connect_ex(("127.0.0.1", port)) == 0


def _listening_process_id(port: int) -> int | None:
    output = subprocess.run(
        ["netstat.exe", "-ano", "-p", "tcp"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    suffix = f":{port}"
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 5 and fields[1].endswith(suffix) and fields[3] == "LISTENING":
            return int(fields[4])
    return None


class _TaskQuestDB:
    """One foreground 10.0.1 process under a test-owned temporary root."""

    def __init__(self, root: Path, ports: dict[str, int]) -> None:
        self.root = root
        self.ports = ports
        self.process: subprocess.Popen[bytes] | None = None
        self._server_pid: int | None = None
        self._database: Any | None = None
        self._log_file: Any | None = None

    @property
    def connection_string(self) -> str:
        return f"ws::addr=127.0.0.1:{self.ports['http']};"

    @property
    def database(self) -> Any:
        if self._database is None:
            raise RuntimeError("task-owned QuestDB control connection is not ready")
        return self._database

    def write_config(self) -> None:
        config = self.root / "conf" / "server.conf"
        config.parent.mkdir(parents=True)
        config.write_text(
            "\n".join(
                (
                    "config.validation.strict=true",
                    "http.enabled=true",
                    f"http.net.bind.to=127.0.0.1:{self.ports['http']}",
                    "http.min.enabled=true",
                    f"http.min.net.bind.to=127.0.0.1:{self.ports['min_http']}",
                    "pg.enabled=true",
                    f"pg.net.bind.to=127.0.0.1:{self.ports['pg']}",
                    "line.tcp.enabled=true",
                    f"line.tcp.net.bind.to=127.0.0.1:{self.ports['ilp']}",
                )
            ),
            encoding="utf-8",
        )

    def start(self) -> None:
        assert self.process is None
        log_path = self.root / "questdb.log"
        self._log_file = log_path.open("wb")
        self.process = subprocess.Popen(
            [_QUESTDB_EXE, "-d", str(self.root)],
            cwd=self.root,
            stdout=self._log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        deadline = time.monotonic() + _POLL_SECONDS
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise AssertionError("task-owned QuestDB exited before becoming ready")
            try:
                with urlopen(
                    f"http://127.0.0.1:{self.ports['min_http']}/status", timeout=1
                ) as response:
                    assert response.status == 200
                    assert b"Healthy" in response.read()
                self._database = questdb.connect(self.connection_string)
                self._server_pid = _listening_process_id(self.ports["http"])
                assert self._server_pid is not None
                return
            except (OSError, questdb.QuestDBError, AssertionError):
                time.sleep(0.1)
        raise AssertionError("task-owned QuestDB did not become available")

    def stop(self) -> None:
        if self.process is None:
            return
        if self._database is not None:
            self._database.close()
            self._database = None
        try:
            self.process.send_signal(signal.CTRL_BREAK_EVENT)
        except OSError:
            pass
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and _port_open(self.ports["http"]):
            time.sleep(0.1)
        if _port_open(self.ports["http"]):
            assert self._server_pid is not None
            subprocess.run(
                ["taskkill.exe", "/PID", str(self._server_pid), "/T", "/F"],
                check=True,
                capture_output=True,
            )
        try:
            self.process.wait(timeout=15)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("task-owned QuestDB launcher did not exit") from error
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None
        self.process = None
        assert not _port_open(self.ports["http"])


@contextmanager
def _owned_server(root: Path) -> Iterator[_TaskQuestDB]:
    server = _TaskQuestDB(root, _free_ports())
    try:
        server.write_config()
        server.start()
        yield server
    finally:
        server.stop()
        shutil.rmtree(root, ignore_errors=True)
        assert not root.exists()


@pytest.fixture(scope="module")
def server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[_TaskQuestDB]:
    root = tmp_path_factory.mktemp(f"truth-history-poc-{uuid4().hex}").resolve()
    with _owned_server(root) as owned:
        yield owned


def _table_name() -> str:
    return f"truth_history_poc_{uuid4().hex}"


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


@contextmanager
def _fresh_reader(server: _TaskQuestDB) -> Iterator[Any]:
    database = questdb.connect(server.connection_string)
    try:
        yield database
    finally:
        database.close()


def _table_exists(server: _TaskQuestDB, table_name: str) -> bool:
    rows = server.database.query(
        f"SELECT table_name FROM tables() WHERE table_name = {_sql_text(table_name)}"
    ).to_pandas().to_dict(orient="records")
    return bool(rows)


def _assert_table_absent(server: _TaskQuestDB, table_name: str) -> None:
    deadline = time.monotonic() + _POLL_SECONDS
    while time.monotonic() < deadline:
        if not _table_exists(server, table_name):
            return
        time.sleep(0.05)
    assert not _table_exists(server, table_name)


def _create_table(server: _TaskQuestDB, table_name: str) -> None:
    server.database.execute(
        f"CREATE TABLE {table_name} ("
        "policy_version VARCHAR, subject_capture_id VARCHAR, category VARCHAR, "
        "contributing_capture_ids VARCHAR, reason VARCHAR, event_provider VARCHAR, "
        "event_source_id VARCHAR, event_message_type VARCHAR, event_trade_id VARCHAR, "
        "physical_written_at TIMESTAMP_NS"
        ") TIMESTAMP(physical_written_at) PARTITION BY DAY WAL"
    )


@contextmanager
def _disposable_table(server: _TaskQuestDB) -> Iterator[str]:
    table_name = _table_name()
    _create_table(server, table_name)
    try:
        yield table_name
    finally:
        server.database.execute(f"DROP TABLE IF EXISTS {table_name}")
        _assert_table_absent(server, table_name)


def _decision(label: str, *, conflicting: bool = False) -> TruthDecision:
    subject_capture_id = f"subject-{label}"
    if conflicting:
        return TruthDecision(
            subject_capture_id=subject_capture_id,
            category=TruthDecisionCategory.NOT_ACCEPTED,
            policy_version="data-truth/v1",
            contributing_capture_ids=(subject_capture_id,),
            reason=TradeNotAcceptedReason.INVALID_TRADE_EVIDENCE,
            event_identity=None,
        )
    return TruthDecision(
        subject_capture_id=subject_capture_id,
        category=TruthDecisionCategory.ACCEPTED,
        policy_version="data-truth/v1",
        contributing_capture_ids=(subject_capture_id, f"evidence-{label}"),
        reason=None,
        event_identity=EventIdentity(
            provider="kalshi",
            source_id="KXBTC15M-TICKER",
            message_type="trade",
            trade_id=f"trade-{label}",
        ),
    )


def _fields(decision: TruthDecision) -> dict[str, str | None]:
    event = decision.event_identity
    return {
        "policy_version": decision.policy_version,
        "subject_capture_id": decision.subject_capture_id,
        "category": decision.category.value,
        "contributing_capture_ids": json.dumps(
            decision.contributing_capture_ids, separators=(",", ":")
        ),
        "reason": None if decision.reason is None else decision.reason.value,
        "event_provider": None if event is None else event.provider,
        "event_source_id": None if event is None else event.source_id,
        "event_message_type": None if event is None else event.message_type,
        "event_trade_id": None if event is None else event.trade_id,
    }


def _append_direct(server: _TaskQuestDB, table_name: str, decision: TruthDecision) -> int:
    sender = server.database.sender()
    try:
        dropped_before = sender.error_events_dropped()
        sender.row(
            table_name,
            columns=_fields(decision),
            at=questdb.TimestampNanos(_PHYSICAL_TIMESTAMP_NS),
        )
        frame_sequence_number = sender.flush_and_get_fsn()
        assert frame_sequence_number is not None
        assert sender.await_acked_fsn(frame_sequence_number, timeout_millis=5_000)
        assert sender.error_events_dropped() == dropped_before
        assert sender.poll_error() is None
        return frame_sequence_number
    finally:
        sender.close(flush=False)


def _rows_for_subject(
    database: Any, table_name: str, decision: TruthDecision
) -> list[dict[str, object]]:
    return database.query(
        f"SELECT policy_version, subject_capture_id, category, contributing_capture_ids, "
        f"reason, event_provider, event_source_id, event_message_type, event_trade_id "
        f"FROM {table_name} WHERE policy_version = {_sql_text(decision.policy_version)} "
        f"AND subject_capture_id = {_sql_text(decision.subject_capture_id)}"
    ).to_pandas().to_dict(orient="records")


def _optional_text(value: object) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if not isinstance(value, str):
        raise TypeError("stored optional text is not text")
    return value


def _decode(row: dict[str, object]) -> TruthDecision:
    policy_version = row.get("policy_version")
    subject_capture_id = row.get("subject_capture_id")
    category = row.get("category")
    contributing = row.get("contributing_capture_ids")
    if not all(isinstance(value, str) for value in (policy_version, subject_capture_id, category, contributing)):
        raise TypeError("stored required TruthDecision field is invalid")
    references = json.loads(contributing)
    if not isinstance(references, list) or not all(isinstance(value, str) for value in references):
        raise TypeError("stored contributing capture IDs are invalid")
    reason_text = _optional_text(row.get("reason"))
    event_values = tuple(
        _optional_text(row.get(column))
        for column in (
            "event_provider",
            "event_source_id",
            "event_message_type",
            "event_trade_id",
        )
    )
    if any(value is None for value in event_values) and any(value is not None for value in event_values):
        raise TypeError("stored EventIdentity is partial")
    event = None
    if all(value is not None for value in event_values):
        event = EventIdentity(*event_values)  # type: ignore[arg-type]
    return TruthDecision(
        subject_capture_id=subject_capture_id,
        category=TruthDecisionCategory(category),
        policy_version=policy_version,
        contributing_capture_ids=tuple(references),
        reason=None if reason_text is None else TradeNotAcceptedReason(reason_text),
        event_identity=event,
    )


def _lookup(database: Any, table_name: str, candidate: TruthDecision) -> _Lookup:
    rows = _rows_for_subject(database, table_name, candidate)
    if not rows:
        return _Lookup(_LookupState.ABSENT)
    if len(rows) != 1:
        return _Lookup(_LookupState.INVALID)
    try:
        stored = _decode(rows[0])
    except (TypeError, ValueError, json.JSONDecodeError):
        return _Lookup(_LookupState.INVALID)
    return _Lookup(_LookupState.EXACT, stored) if stored == candidate else _Lookup(
        _LookupState.CONFLICTING, stored
    )


def _lookup_fresh(
    server: _TaskQuestDB, table_name: str, candidate: TruthDecision
) -> _Lookup:
    with _fresh_reader(server) as database:
        return _lookup(database, table_name, candidate)


def _wait_for_exact(
    server: _TaskQuestDB, table_name: str, candidate: TruthDecision
) -> _Lookup:
    with _fresh_reader(server) as database:
        deadline = time.monotonic() + _POLL_SECONDS
        while time.monotonic() < deadline:
            result = _lookup(database, table_name, candidate)
            if result.state is _LookupState.EXACT:
                return result
            time.sleep(0.05)
        return _lookup(database, table_name, candidate)


def _wait_for_state(
    server: _TaskQuestDB,
    table_name: str,
    candidate: TruthDecision,
    expected: _LookupState,
) -> _Lookup:
    with _fresh_reader(server) as database:
        deadline = time.monotonic() + _POLL_SECONDS
        while time.monotonic() < deadline:
            result = _lookup(database, table_name, candidate)
            if result.state is expected:
                return result
            time.sleep(0.05)
        result = _lookup(database, table_name, candidate)
        assert result.state is expected
        return result


def _physical_count(server: _TaskQuestDB, table_name: str) -> int:
    with _fresh_reader(server) as database:
        return database.query(
            f"SELECT count() AS row_count FROM {table_name}"
        ).to_pandas().to_dict(orient="records")[0]["row_count"]


class _PocHistory:
    """Test-local subject-key persistence/reconciliation harness only."""

    def __init__(self, server: _TaskQuestDB, table_name: str) -> None:
        self._server = server
        self._table_name = table_name
        self.append_attempts = 0

    def persist(self, candidate: TruthDecision) -> str:
        existing = _lookup_fresh(self._server, self._table_name, candidate)
        if existing.state is _LookupState.EXACT:
            return "reconciled"
        if existing.state is not _LookupState.ABSENT:
            raise _ConflictingAuthorityError(existing.state.value)
        self.append_attempts += 1
        _append_direct(self._server, self._table_name, candidate)
        verified = _wait_for_exact(self._server, self._table_name, candidate)
        if verified.state is not _LookupState.EXACT:
            raise AssertionError("acknowledged append was not exactly visible")
        return "acknowledged_ok"

    def definite_prewrite_failure(self, candidate: TruthDecision) -> str:
        assert _lookup_fresh(
            self._server, self._table_name, candidate
        ).state is _LookupState.ABSENT
        return "definitely_rejected"

    def ambiguous_without_submission(self, candidate: TruthDecision) -> str:
        assert _lookup_fresh(
            self._server, self._table_name, candidate
        ).state is _LookupState.ABSENT
        self.append_attempts += 1
        return "in_doubt"

    def reconcile_ack_unavailable(self, candidate: TruthDecision) -> str:
        result = _lookup_fresh(self._server, self._table_name, candidate)
        if result.state is _LookupState.EXACT:
            return "reconciled"
        if result.state is _LookupState.ABSENT:
            return "in_doubt"
        raise _ConflictingAuthorityError(result.state.value)


def _write_child(path: Path) -> None:
    path.write_text(
        """import json
import os
import time
from pathlib import Path

import questdb

root = Path(os.environ[\"LIVE15_TRUTH_POC_CHILD_ROOT\"])
scenario = json.loads((root / \"scenario.json\").read_text(encoding=\"utf-8\"))
database = questdb.connect(scenario[\"connection_string\"])
sender = database.sender()
try:
    sender.row(
        scenario[\"table_name\"],
        columns=scenario[\"fields\"],
        at=questdb.TimestampNanos(scenario[\"physical_timestamp_ns\"]),
    )
    fsn = sender.flush_and_get_fsn()
    marker = root / \"frame_published.json\"
    temporary = marker.with_suffix(\".tmp\")
    temporary.write_text(json.dumps({\"fsn\": fsn}), encoding=\"utf-8\")
    temporary.replace(marker)
    while not (root / \"release.json\").exists():
        time.sleep(0.02)
finally:
    sender.close(flush=False)
    database.close()
""",
        encoding="utf-8",
    )


def _wait_for_marker(root: Path, child: subprocess.Popen[bytes]) -> dict[str, object]:
    marker = root / "frame_published.json"
    deadline = time.monotonic() + _POLL_SECONDS
    while time.monotonic() < deadline:
        if marker.is_file():
            return json.loads(marker.read_text(encoding="utf-8"))
        if child.poll() is not None:
            raise AssertionError("POC child exited before publishing its frame")
        time.sleep(0.02)
    raise AssertionError("POC child did not publish its frame")


def test_case_a_normal_append_ack_and_exact_lookup(server: _TaskQuestDB) -> None:
    with _disposable_table(server) as table_name:
        history = _PocHistory(server, table_name)
        candidate = _decision("ack")
        assert history.persist(candidate) == "acknowledged_ok"
        assert _lookup_fresh(server, table_name, candidate).state is _LookupState.EXACT
        assert history.append_attempts == 1
        assert _physical_count(server, table_name) == 1


def test_case_b_append_has_bounded_exact_visibility(server: _TaskQuestDB) -> None:
    with _disposable_table(server) as table_name:
        candidate = _decision("visibility")
        _append_direct(server, table_name, candidate)
        assert _wait_for_exact(server, table_name, candidate).state is _LookupState.EXACT
        assert _physical_count(server, table_name) == 1


def test_case_c_definite_prewrite_failure_is_absent(server: _TaskQuestDB) -> None:
    with _disposable_table(server) as table_name:
        history = _PocHistory(server, table_name)
        candidate = _decision("prewrite")
        assert history.definite_prewrite_failure(candidate) == "definitely_rejected"
        assert history.append_attempts == 0
        assert _lookup_fresh(server, table_name, candidate).state is _LookupState.ABSENT
        assert _physical_count(server, table_name) == 0


def test_case_d_real_committed_row_without_caller_ack_reconciles(
    server: _TaskQuestDB, tmp_path: Path
) -> None:
    with _disposable_table(server) as table_name:
        candidate = _decision("no-caller-ack")
        root = tmp_path / f"child-{uuid4().hex}"
        root.mkdir()
        _write_child(root / "child.py")
        (root / "scenario.json").write_text(
            json.dumps(
                {
                    "connection_string": server.connection_string,
                    "table_name": table_name,
                    "fields": _fields(candidate),
                    "physical_timestamp_ns": _PHYSICAL_TIMESTAMP_NS,
                }
            ),
            encoding="utf-8",
        )
        environment = os.environ | {"LIVE15_TRUTH_POC_CHILD_ROOT": str(root)}
        child = subprocess.Popen(
            [sys.executable, str(root / "child.py")],
            cwd=root,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            marker = _wait_for_marker(root, child)
            assert isinstance(marker.get("fsn"), int)
            assert _wait_for_exact(server, table_name, candidate).state is _LookupState.EXACT
            child.kill()
            child.wait(timeout=15)
            history = _PocHistory(server, table_name)
            assert history.reconcile_ack_unavailable(candidate) == "reconciled"
            assert _physical_count(server, table_name) == 1
            assert not (root / "acknowledged.json").exists()
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=15)
            shutil.rmtree(root, ignore_errors=True)
            assert not root.exists()


def test_case_e_ambiguous_absent_remains_in_doubt(server: _TaskQuestDB) -> None:
    with _disposable_table(server) as table_name:
        history = _PocHistory(server, table_name)
        candidate = _decision("ambiguous-absent")
        assert history.ambiguous_without_submission(candidate) == "in_doubt"
        assert history.append_attempts == 1
        assert history.reconcile_ack_unavailable(candidate) == "in_doubt"
        assert _lookup_fresh(server, table_name, candidate).state is _LookupState.ABSENT
        assert _physical_count(server, table_name) == 0


def test_case_f_conflicting_existing_subject_fails_closed(server: _TaskQuestDB) -> None:
    with _disposable_table(server) as table_name:
        candidate = _decision("conflict")
        _append_direct(server, table_name, _decision("conflict", conflicting=True))
        assert _wait_for_state(
            server, table_name, candidate, _LookupState.CONFLICTING
        ).state is _LookupState.CONFLICTING
        history = _PocHistory(server, table_name)
        with pytest.raises(_ConflictingAuthorityError):
            history.persist(candidate)
        assert history.append_attempts == 0
        assert _physical_count(server, table_name) == 1


def test_case_g_second_invocation_does_not_append_again(server: _TaskQuestDB) -> None:
    with _disposable_table(server) as table_name:
        history = _PocHistory(server, table_name)
        candidate = _decision("second")
        assert history.persist(candidate) == "acknowledged_ok"
        assert history.persist(candidate) == "reconciled"
        assert history.append_attempts == 1
        assert _physical_count(server, table_name) == 1


def test_case_h_distinct_subjects_remain_append_only(server: _TaskQuestDB) -> None:
    with _disposable_table(server) as table_name:
        history = _PocHistory(server, table_name)
        first = _decision("first")
        second = _decision("second-distinct")
        assert history.persist(first) == "acknowledged_ok"
        assert history.persist(second) == "acknowledged_ok"
        assert _lookup_fresh(server, table_name, first).state is _LookupState.EXACT
        assert _lookup_fresh(server, table_name, second).state is _LookupState.EXACT
        assert history.append_attempts == 2
        assert _physical_count(server, table_name) == 2


def test_case_i_metadata_has_no_dedup_or_upsert(server: _TaskQuestDB) -> None:
    with _disposable_table(server) as table_name:
        table_rows = server.database.query(
            f"SELECT dedup FROM tables() WHERE table_name = {_sql_text(table_name)}"
        ).to_pandas().to_dict(orient="records")
        columns = server.database.query(
            f"SELECT \"column\", upsertKey FROM table_columns('{table_name}')"
        ).to_pandas().to_dict(orient="records")
        assert table_rows == [{"dedup": False}]
        assert not any(row["upsertKey"] is True for row in columns)


def test_case_j_multiple_same_key_authority_fails_closed(server: _TaskQuestDB) -> None:
    with _disposable_table(server) as table_name:
        candidate = _decision("multiple")
        _append_direct(server, table_name, candidate)
        _append_direct(server, table_name, _decision("multiple", conflicting=True))
        assert _wait_for_state(
            server, table_name, candidate, _LookupState.INVALID
        ).state is _LookupState.INVALID
        history = _PocHistory(server, table_name)
        with pytest.raises(_ConflictingAuthorityError):
            history.persist(candidate)
        assert history.append_attempts == 0
        assert _physical_count(server, table_name) == 2


def test_case_k_cleanup_after_success(tmp_path: Path) -> None:
    root = tmp_path / f"success-{uuid4().hex}"
    table_name = ""
    with _owned_server(root) as owned:
        with _disposable_table(owned) as table_name:
            assert _PocHistory(owned, table_name).persist(_decision("cleanup-success")) == "acknowledged_ok"
        _assert_table_absent(owned, table_name)
    assert not root.exists()


def test_case_l_cleanup_after_intentional_exception(tmp_path: Path) -> None:
    root = tmp_path / f"exception-{uuid4().hex}"
    with (
        pytest.raises(RuntimeError, match="intentional POC cleanup path"),
        _owned_server(root) as owned,
        _disposable_table(owned) as table_name,
    ):
        assert _PocHistory(owned, table_name).persist(_decision("cleanup-exception")) == "acknowledged_ok"
        raise RuntimeError("intentional POC cleanup path")
    assert not root.exists()
