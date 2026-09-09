"""Opt-in, task-owned QuestDB integration for the TruthDecision history adapter."""

from __future__ import annotations

import ctypes
import os
import shutil
import socket
import subprocess
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen
from uuid import uuid4

import pytest
import questdb

if os.name != "nt":
    pytest.skip("QuestDB TruthDecision integration is Windows-only", allow_module_level=True)

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.data_truth import (
    DataTruth,
    EventIdentity,
    TruthDecision,
    TruthDecisionAppendInDoubtError,
    TruthDecisionCategory,
    TruthDecisionInvariantError,
)
from live15_quant_v2.data.data_truth.questdb_history import QuestDBTruthDecisionHistory
from live15_quant_v2.data.storage.capture import CaptureFact

_RUN_INTEGRATION = os.getenv("LIVE15_RUN_DATA_TRUTH_QUESTDB_INTEGRATION") == "1"
_QUESTDB_EXE = Path(r"D:\LIVE15_V2_RUNTIME\questdb\dist\10.0.1\bin\questdb.exe")
_CREATE_SUSPENDED = 0x00000004
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_SYNCHRONIZE = 0x00100000
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_WAIT_OBJECT_0 = 0x00000000
_WAIT_TIMEOUT = 0x00000102
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _RUN_INTEGRATION,
        reason="set LIVE15_RUN_DATA_TRUTH_QUESTDB_INTEGRATION=1 to run task-owned QuestDB",
    ),
]


def _ports() -> dict[str, int]:
    listeners = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(4)]
    try:
        for listener in listeners:
            listener.bind(("127.0.0.1", 0))
        return dict(zip(("http", "pg", "min_http", "ilp"), (listener.getsockname()[1] for listener in listeners), strict=True))
    finally:
        for listener in listeners:
            listener.close()


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.2)
        return connection.connect_ex(("127.0.0.1", port)) == 0


class _StartupInfo(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lp_reserved", wintypes.LPWSTR),
        ("lp_desktop", wintypes.LPWSTR),
        ("lp_title", wintypes.LPWSTR),
        ("dw_x", wintypes.DWORD),
        ("dw_y", wintypes.DWORD),
        ("dw_x_size", wintypes.DWORD),
        ("dw_y_size", wintypes.DWORD),
        ("dw_x_count_chars", wintypes.DWORD),
        ("dw_y_count_chars", wintypes.DWORD),
        ("dw_fill_attribute", wintypes.DWORD),
        ("dw_flags", wintypes.DWORD),
        ("w_show_window", wintypes.WORD),
        ("cb_reserved2", wintypes.WORD),
        ("lp_reserved2", ctypes.POINTER(ctypes.c_byte)),
        ("h_std_input", wintypes.HANDLE),
        ("h_std_output", wintypes.HANDLE),
        ("h_std_error", wintypes.HANDLE),
    ]


class _ProcessInformation(ctypes.Structure):
    _fields_ = [
        ("process_handle", wintypes.HANDLE),
        ("thread_handle", wintypes.HANDLE),
        ("process_id", wintypes.DWORD),
        ("thread_id", wintypes.DWORD),
    ]


class _JobObjectBasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("per_process_user_time_limit", ctypes.c_longlong),
        ("per_job_user_time_limit", ctypes.c_longlong),
        ("limit_flags", wintypes.DWORD),
        ("minimum_working_set_size", ctypes.c_size_t),
        ("maximum_working_set_size", ctypes.c_size_t),
        ("active_process_limit", wintypes.DWORD),
        ("affinity", ctypes.c_size_t),
        ("priority_class", wintypes.DWORD),
        ("scheduling_class", wintypes.DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("read_operation_count", ctypes.c_ulonglong),
        ("write_operation_count", ctypes.c_ulonglong),
        ("other_operation_count", ctypes.c_ulonglong),
        ("read_transfer_count", ctypes.c_ulonglong),
        ("write_transfer_count", ctypes.c_ulonglong),
        ("other_transfer_count", ctypes.c_ulonglong),
    ]


class _JobObjectExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("basic_limit_information", _JobObjectBasicLimitInformation),
        ("io_info", _IoCounters),
        ("process_memory_limit", ctypes.c_size_t),
        ("job_memory_limit", ctypes.c_size_t),
        ("peak_process_memory_used", ctypes.c_size_t),
        ("peak_job_memory_used", ctypes.c_size_t),
    ]


_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
_HANDLE = wintypes.HANDLE
_DWORD = wintypes.DWORD
_BOOL = wintypes.BOOL
_KERNEL32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
_KERNEL32.CreateJobObjectW.restype = _HANDLE
_KERNEL32.SetInformationJobObject.argtypes = [_HANDLE, ctypes.c_int, ctypes.c_void_p, _DWORD]
_KERNEL32.SetInformationJobObject.restype = _BOOL
_KERNEL32.CreateProcessW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    ctypes.c_void_p,
    ctypes.c_void_p,
    _BOOL,
    _DWORD,
    ctypes.c_void_p,
    wintypes.LPCWSTR,
    ctypes.POINTER(_StartupInfo),
    ctypes.POINTER(_ProcessInformation),
]
_KERNEL32.CreateProcessW.restype = _BOOL
_KERNEL32.AssignProcessToJobObject.argtypes = [_HANDLE, _HANDLE]
_KERNEL32.AssignProcessToJobObject.restype = _BOOL
_KERNEL32.ResumeThread.argtypes = [_HANDLE]
_KERNEL32.ResumeThread.restype = _DWORD
_KERNEL32.IsProcessInJob.argtypes = [_HANDLE, _HANDLE, ctypes.POINTER(_BOOL)]
_KERNEL32.IsProcessInJob.restype = _BOOL
_KERNEL32.OpenProcess.argtypes = [_DWORD, _BOOL, _DWORD]
_KERNEL32.OpenProcess.restype = _HANDLE
_KERNEL32.WaitForSingleObject.argtypes = [_HANDLE, _DWORD]
_KERNEL32.WaitForSingleObject.restype = _DWORD
_KERNEL32.CloseHandle.argtypes = [_HANDLE]
_KERNEL32.CloseHandle.restype = _BOOL


def _win_error(operation: str) -> RuntimeError:
    return RuntimeError(f"{operation} failed with Windows error {ctypes.get_last_error()}")


def _close_handle(handle: int) -> None:
    if not _KERNEL32.CloseHandle(handle):
        raise _win_error("CloseHandle")


def _wait_for_exit(handle: int, *, timeout_seconds: float) -> bool:
    result = _KERNEL32.WaitForSingleObject(handle, int(timeout_seconds * 1_000))
    if result == _WAIT_OBJECT_0:
        return True
    if result == _WAIT_TIMEOUT:
        return False
    raise _win_error("WaitForSingleObject")


@dataclass
class _LauncherHandles:
    process: int
    thread: int
    pid: int


class _WindowsJob:
    def __init__(self) -> None:
        self._handle = _KERNEL32.CreateJobObjectW(None, None)
        if not self._handle:
            raise _win_error("CreateJobObjectW")
        limits = _JobObjectExtendedLimitInformation()
        limits.basic_limit_information.limit_flags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not _KERNEL32.SetInformationJobObject(
            self._handle,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            error = _win_error("SetInformationJobObject")
            _close_handle(self._handle)
            raise error

    def assign(self, process_handle: int) -> None:
        if not _KERNEL32.AssignProcessToJobObject(self._handle, process_handle):
            raise _win_error("AssignProcessToJobObject")

    def contains(self, process_handle: int) -> bool:
        answer = _BOOL()
        if not _KERNEL32.IsProcessInJob(process_handle, self._handle, ctypes.byref(answer)):
            raise _win_error("IsProcessInJob")
        return bool(answer.value)

    def close(self) -> None:
        _close_handle(self._handle)


def _create_suspended_process(command: list[str], cwd: Path) -> _LauncherHandles:
    command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
    startup_info = _StartupInfo()
    startup_info.cb = ctypes.sizeof(startup_info)
    process_info = _ProcessInformation()
    if not _KERNEL32.CreateProcessW(
        None,
        command_line,
        None,
        None,
        False,
        _CREATE_SUSPENDED | _CREATE_NEW_PROCESS_GROUP,
        None,
        str(cwd),
        ctypes.byref(startup_info),
        ctypes.byref(process_info),
    ):
        raise _win_error("CreateProcessW")
    return _LauncherHandles(
        process_info.process_handle,
        process_info.thread_handle,
        process_info.process_id,
    )


def _resume_thread(thread_handle: int) -> None:
    if _KERNEL32.ResumeThread(thread_handle) == 0xFFFFFFFF:
        raise _win_error("ResumeThread")


def _open_process(pid: int) -> int:
    handle = _KERNEL32.OpenProcess(
        _SYNCHRONIZE | _PROCESS_QUERY_LIMITED_INFORMATION, False, pid
    )
    if not handle:
        raise _win_error(f"OpenProcess({pid})")
    return handle


def _wait_until(predicate: Callable[[], bool], *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return predicate()


class _TaskQuestDB:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.ports = _ports()
        self.job: _WindowsJob | None = None
        self.launcher: _LauncherHandles | None = None
        self.database: questdb.QuestDB | None = None
        self.java_handle: int | None = None
        self.server_pid: int | None = None
        self.lifecycle: dict[str, bool] = {}

    @property
    def connection_string(self) -> str:
        return f"ws::addr=127.0.0.1:{self.ports['http']};"

    def start(self) -> None:
        config = self.root / "conf" / "server.conf"
        config.parent.mkdir(parents=True)
        config.write_text(
            "\n".join(
                (
                    "config.validation.strict=true", "http.enabled=true",
                    f"http.net.bind.to=127.0.0.1:{self.ports['http']}", "http.min.enabled=true",
                    f"http.min.net.bind.to=127.0.0.1:{self.ports['min_http']}", "pg.enabled=true",
                    f"pg.net.bind.to=127.0.0.1:{self.ports['pg']}", "line.tcp.enabled=true",
                    f"line.tcp.net.bind.to=127.0.0.1:{self.ports['ilp']}",
                )
            ),
            encoding="utf-8",
        )
        self.job = _WindowsJob()
        self.lifecycle["job_created"] = True
        self.lifecycle["kill_on_job_close"] = True
        self.launcher = _create_suspended_process([str(_QUESTDB_EXE), "-d", str(self.root)], self.root)
        try:
            self.job.assign(self.launcher.process)
            self.lifecycle["assigned_before_resume"] = True
            self.lifecycle["launcher_in_job"] = self.job.contains(self.launcher.process)
            if not self.lifecycle["launcher_in_job"]:
                raise RuntimeError("task-owned QuestDB launcher escaped its Job Object")
            _resume_thread(self.launcher.thread)
        except BaseException:
            self._close_job()
            self._close_launcher_handles()
            raise

        try:
            self._wait_until_ready()
        except BaseException:
            self._cleanup_contained_processes()
            raise

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                with urlopen(f"http://127.0.0.1:{self.ports['min_http']}/status", timeout=1) as response:
                    assert response.status == 200
                    assert b"Healthy" in response.read()
                self.database = questdb.connect(self.connection_string)
                output = subprocess.run(["netstat.exe", "-ano", "-p", "tcp"], check=True, capture_output=True, text=True).stdout
                listener = next(line for line in output.splitlines() if f":{self.ports['http']}" in line and "LISTENING" in line)
                self.server_pid = int(listener.split()[-1])
                self.java_handle = _open_process(self.server_pid)
                self.lifecycle["server_java_in_job"] = self.job.contains(self.java_handle)
                if not self.lifecycle["server_java_in_job"]:
                    raise RuntimeError("task-owned QuestDB Java listener escaped its Job Object")
                self.lifecycle["server_ready"] = True
                return
            except (OSError, questdb.QuestDBError, AssertionError, StopIteration):
                time.sleep(0.1)
        raise RuntimeError("task-owned QuestDB did not become ready")

    def stop(self) -> None:
        self._cleanup_contained_processes()

    def _cleanup_contained_processes(self) -> None:
        self._close_database()
        self._close_job()
        self.lifecycle["job_close_used"] = True
        try:
            self.lifecycle["launcher_exited"] = (
                self.launcher is None
                or _wait_for_exit(self.launcher.process, timeout_seconds=15)
            )
            self.lifecycle["java_exited"] = (
                self.java_handle is None
                or _wait_for_exit(self.java_handle, timeout_seconds=15)
            )
            self.lifecycle["all_four_ports_closed"] = _wait_until(
                lambda: not any(_port_open(port) for port in self.ports.values()),
                timeout_seconds=10,
            )
            if not all(
                self.lifecycle[key]
                for key in ("launcher_exited", "java_exited", "all_four_ports_closed")
            ):
                raise RuntimeError("task-owned QuestDB did not stop safely")
            if self.root.exists():
                shutil.rmtree(self.root)
            self.lifecycle["root_delete"] = not self.root.exists()
            if not self.lifecycle["root_delete"]:
                raise RuntimeError("task-owned QuestDB root remains after cleanup")
        finally:
            self._close_java_handle()
            self._close_launcher_handles()

    def _close_database(self) -> None:
        if self.database is not None:
            self.database.close()
            self.database = None

    def _close_job(self) -> None:
        if self.job is not None:
            self.job.close()
            self.job = None

    def _close_java_handle(self) -> None:
        if self.java_handle is not None:
            _close_handle(self.java_handle)
            self.java_handle = None

    def _close_launcher_handles(self) -> None:
        if self.launcher is not None:
            _close_handle(self.launcher.thread)
            _close_handle(self.launcher.process)
            self.launcher = None


@contextmanager
def _server(tmp_path: Path) -> Iterator[_TaskQuestDB]:
    server = _TaskQuestDB(tmp_path / f"questdb-{uuid4().hex}")
    try:
        server.start()
        yield server
    finally:
        server.stop()


def _assert_lifecycle(server: _TaskQuestDB) -> None:
    assert all(
        server.lifecycle[key]
        for key in (
            "job_created",
            "kill_on_job_close",
            "assigned_before_resume",
            "launcher_in_job",
            "server_java_in_job",
            "server_ready",
            "job_close_used",
            "launcher_exited",
            "java_exited",
            "all_four_ports_closed",
            "root_delete",
        )
    )


class _HotStore:
    max_batch_rows = 1

    def __init__(self, facts: dict[str, CaptureFact]) -> None:
        self._facts = facts

    def read_capture(self, capture_id: str) -> CaptureFact | None:
        return self._facts.get(capture_id)


def _fact(capture_id: str) -> CaptureFact:
    return CaptureFact(capture_id, AssetId.BTC, "kalshi", "KXBTC", "ticker", "ticker", None, 1, None, None, 2, "market-ingress/v1", "{}")


def _accepted(capture_id: str) -> TruthDecision:
    return TruthDecision(capture_id, TruthDecisionCategory.ACCEPTED, "data-truth/v1", (capture_id,), None, EventIdentity("kalshi", "KXBTC", "trade", "trade-1"))


def _adapter(server: _TaskQuestDB, table_name: str, hot_store: _HotStore) -> QuestDBTruthDecisionHistory:
    return QuestDBTruthDecisionHistory(server.connection_string, table_name=table_name, hot_store=hot_store, acknowledgement_timeout_millis=5_000)


def _table_name() -> str:
    return f"truth_history_{uuid4().hex}"


def _count(server: _TaskQuestDB, table_name: str) -> int:
    assert server.database is not None
    return int(server.database.query(f"SELECT count() AS row_count FROM {table_name}", []).to_pandas().to_dict(orient="records")[0]["row_count"])


def test_adapter_creates_verifies_and_cleans_up_task_table(tmp_path: Path) -> None:
    table = _table_name()
    with _server(tmp_path) as server:
        adapter = _adapter(server, table, _HotStore({}))
        assert adapter.find_subject_decision("data-truth/v1", "absent") is None
        assert server.database is not None
        metadata = server.database.query("SELECT table_name, walEnabled, dedup FROM tables()", []).to_pandas().to_dict(orient="records")
        assert [row for row in metadata if row["table_name"] == table] == [{"table_name": table, "walEnabled": True, "dedup": False}]
        server.database.execute(f"DROP TABLE {table}")
        adapter.close()
    _assert_lifecycle(server)


def test_append_lookup_and_data_truth_reconciliation_are_append_only(tmp_path: Path) -> None:
    with _server(tmp_path) as server:
        table = _table_name()
        adapter = _adapter(server, table, _HotStore({}))
        truth = DataTruth(adapter)
        fact = _fact("ticker-1")
        first = truth.decide(fact)
        assert adapter.find_subject_decision(first.policy_version, first.subject_capture_id) == first
        assert truth.decide(fact) == first
        assert _count(server, table) == 1
        second = truth.decide(_fact("ticker-2"))
        assert second.subject_capture_id == "ticker-2"
        assert _count(server, table) == 2
        adapter.close()
    _assert_lifecycle(server)


def test_metadata_conflicts_event_evidence_and_in_doubt_contract(tmp_path: Path) -> None:
    with _server(tmp_path) as server:
        table = _table_name()
        fact = _fact("accepted-1")
        adapter = _adapter(server, table, _HotStore({fact.capture_id: fact}))
        decision = _accepted(fact.capture_id)
        adapter.append(decision)
        assert adapter.find_accepted_event(decision.event_identity).accepted_fact == fact
        adapter.append(decision)
        with pytest.raises(TruthDecisionInvariantError):
            adapter.find_subject_decision(decision.policy_version, decision.subject_capture_id)
        adapter.close()

        class _InDoubtAfterCommit:
            def find_subject_decision(self, policy_version: str, capture_id: str):
                return adapter.find_subject_decision(policy_version, capture_id)

            def find_accepted_event(self, event_identity: EventIdentity):
                return adapter.find_accepted_event(event_identity)

            def append(self, value: TruthDecision) -> None:
                adapter.append(value)
                raise TruthDecisionAppendInDoubtError("test seam after committed append")

        reconciliation_table = _table_name()
        reconciliation = _adapter(server, reconciliation_table, _HotStore({}))
        history = _InDoubtAfterCommit()
        adapter = reconciliation
        result = DataTruth(history).decide(_fact("ticker-in-doubt"))
        assert result.subject_capture_id == "ticker-in-doubt"
        assert _count(server, reconciliation_table) == 1
        reconciliation.close()
    _assert_lifecycle(server)


def test_post_containment_startup_failure_cleans_task_owned_resources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    original_wait_until_ready = _TaskQuestDB._wait_until_ready

    def _fail_after_containment(server: _TaskQuestDB) -> None:
        original_wait_until_ready(server)
        raise RuntimeError("injected post-containment startup failure")

    monkeypatch.setattr(_TaskQuestDB, "_wait_until_ready", _fail_after_containment)
    server = _TaskQuestDB(tmp_path / f"questdb-{uuid4().hex}")

    with pytest.raises(RuntimeError, match="injected post-containment"):
        server.start()

    _assert_lifecycle(server)
    assert server.database is None
    assert server.job is None
    assert server.launcher is None
    assert server.java_handle is None
    assert not server.root.exists()
