"""Opt-in disposable POC for Replay As-Of snapshot-membership pagination."""
# mypy: disable-error-code=import-untyped

from __future__ import annotations

import ctypes
import hashlib
import json
import math
import os
import shutil
import socket
import subprocess
import time
from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from ctypes import wintypes
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal
from urllib.request import urlopen
from uuid import uuid4

import pytest
import questdb

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.data_truth.models import (
    EventIdentity,
    TradeNotAcceptedReason,
    TruthDecision,
    TruthDecisionCategory,
)
from live15_quant_v2.data.storage.capture import CaptureFact

if os.name != "nt":
    pytest.skip("Replay As-Of snapshot POC is Windows-only", allow_module_level=True)


_RUN_POC = os.getenv("LIVE15_RUN_REPLAY_AS_OF_SNAPSHOT_POC") == "1"
_QUESTDB_EXE = Path(r"D:\LIVE15_V2_RUNTIME\questdb\dist\10.0.1\bin\questdb.exe")
_CREATE_SUSPENDED = 0x00000004
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_SYNCHRONIZE = 0x00100000
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_WAIT_OBJECT_0 = 0x00000000
_WAIT_TIMEOUT = 0x00000102
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_POLICY = "data-truth/v1"
_CUTOFF = 900

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _RUN_POC,
        reason="set LIVE15_RUN_REPLAY_AS_OF_SNAPSHOT_POC=1 to run the local POC",
    ),
]


class _SnapshotMismatch(RuntimeError):
    """A bound source membership no longer matches the current source read."""


class _SourceUnavailable(RuntimeError):
    """A source invariant prevents an exact, authoritative membership read."""


class _UnsupportedEventTime(RuntimeError):
    """EVENT_TIME selection has a qualified candidate without provider time."""


def _ports() -> dict[str, int]:
    listeners = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(4)]
    try:
        for listener in listeners:
            listener.bind(("127.0.0.1", 0))
        return dict(
            zip(
                ("http", "pg", "min_http", "ilp"),
                (listener.getsockname()[1] for listener in listeners),
                strict=True,
            )
        )
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
    """Anonymous Job Object which terminates its contained tree when closed."""

    def __init__(self) -> None:
        self.handle = _KERNEL32.CreateJobObjectW(None, None)
        if not self.handle:
            raise _win_error("CreateJobObjectW")
        limits = _JobObjectExtendedLimitInformation()
        limits.basic_limit_information.limit_flags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not _KERNEL32.SetInformationJobObject(
            self.handle,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            error = _win_error("SetInformationJobObject")
            _close_handle(self.handle)
            raise error

    def assign(self, process_handle: int) -> None:
        if not _KERNEL32.AssignProcessToJobObject(self.handle, process_handle):
            raise _win_error("AssignProcessToJobObject")

    def contains(self, process_handle: int) -> bool:
        contained = _BOOL()
        if not _KERNEL32.IsProcessInJob(
            process_handle, self.handle, ctypes.byref(contained)
        ):
            raise _win_error("IsProcessInJob")
        return bool(contained.value)

    def close(self) -> None:
        _close_handle(self.handle)


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
    """A fresh task root and full process tree contained in one Job Object."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.ports = _ports()
        self.job: _WindowsJob | None = None
        self.launcher: _LauncherHandles | None = None
        self.database: Any | None = None
        self.java_handle: int | None = None
        self.lifecycle: dict[str, bool] = {}
        self.restart_exercised = False

    @property
    def connection_string(self) -> str:
        return f"ws::addr=127.0.0.1:{self.ports['http']};"

    def start(self) -> None:
        config = self.root / "conf" / "server.conf"
        config.parent.mkdir(parents=True, exist_ok=True)
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
        self.job = _WindowsJob()
        self.lifecycle["job_created"] = True
        self.lifecycle["kill_on_job_close"] = True
        self.launcher = _create_suspended_process(
            [str(_QUESTDB_EXE), "-d", str(self.root)], self.root
        )
        try:
            self.job.assign(self.launcher.process)
            self.lifecycle["assigned_before_resume"] = True
            assert self.job.contains(self.launcher.process)
            _resume_thread(self.launcher.thread)
            self._wait_until_ready()
        except BaseException:
            self._shutdown(remove_root=False)
            raise

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                with urlopen(
                    f"http://127.0.0.1:{self.ports['min_http']}/status", timeout=1
                ) as response:
                    assert response.status == 200
                    assert b"Healthy" in response.read()
                self.database = questdb.connect(self.connection_string)
                netstat = subprocess.run(
                    ["netstat.exe", "-ano", "-p", "tcp"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout
                listener = next(
                    line
                    for line in netstat.splitlines()
                    if f":{self.ports['http']}" in line and "LISTENING" in line
                )
                java_handle = _open_process(int(listener.split()[-1]))
                try:
                    assert self.job is not None
                    assert self.job.contains(java_handle)
                except BaseException:
                    _close_handle(java_handle)
                    raise
                self.java_handle = java_handle
                self.lifecycle["server_java_in_job"] = True
                self.lifecycle["server_ready"] = True
                return
            except (OSError, questdb.QuestDBError, AssertionError, StopIteration):
                time.sleep(0.1)
        raise RuntimeError("task-owned QuestDB did not become ready")

    def restart(self) -> None:
        self._shutdown(remove_root=False)
        assert self.root.exists()
        self.restart_exercised = True
        self.start()

    def stop(self) -> None:
        self._shutdown(remove_root=True)

    def _shutdown(self, *, remove_root: bool) -> None:
        if self.database is not None:
            self.database.close()
            self.database = None
        if self.job is not None:
            self.job.close()
            self.job = None
        self.lifecycle["job_close_used"] = True
        try:
            launcher_exited = self.launcher is None or _wait_for_exit(
                self.launcher.process, timeout_seconds=15
            )
            java_exited = self.java_handle is None or _wait_for_exit(
                self.java_handle, timeout_seconds=15
            )
            ports_closed = _wait_until(
                lambda: not any(_port_open(port) for port in self.ports.values()),
                timeout_seconds=10,
            )
            if not (launcher_exited and java_exited and ports_closed):
                raise RuntimeError("task-owned QuestDB did not stop safely")
            if remove_root:
                shutil.rmtree(self.root)
                self.lifecycle["root_delete"] = not self.root.exists()
                if not self.lifecycle["root_delete"]:
                    raise RuntimeError("task-owned QuestDB root remains after cleanup")
        finally:
            if self.java_handle is not None:
                _close_handle(self.java_handle)
                self.java_handle = None
            if self.launcher is not None:
                _close_handle(self.launcher.thread)
                _close_handle(self.launcher.process)
                self.launcher = None


@contextmanager
def _server(root: Path) -> Iterator[_TaskQuestDB]:
    server = _TaskQuestDB(root)
    try:
        server.start()
        yield server
    finally:
        server.stop()


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _rows(database: Any, statement: str) -> list[dict[str, object]]:
    return database.query(statement, []).to_pandas().to_dict(orient="records")


def _wait_wal(database: Any, table: str) -> None:
    _rows(database, f"SELECT wait_wal_table({_sql_text(table)})")


def _append(database: Any, table: str, columns: dict[str, object], at_ns: int) -> None:
    sender = database.sender()
    try:
        sender.row(table, columns=columns, at=questdb.TimestampNanos(at_ns))
        frame_sequence_number = sender.flush_and_get_fsn()
        assert frame_sequence_number is not None
        assert sender.await_acked_fsn(frame_sequence_number, timeout_millis=5_000)
        assert sender.poll_error() is None
    finally:
        sender.close(flush=False)
    _wait_wal(database, table)


def _ns(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    timestamp_value = getattr(value, "value", None)
    if isinstance(timestamp_value, int):
        if timestamp_value == -9_223_372_036_854_775_808:
            return None
        return timestamp_value
    raise TypeError(f"expected timestamp nanoseconds, got {type(value).__name__}")


def _optional_text(value: object) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if not isinstance(value, str):
        raise TypeError("expected optional text")
    return value


@dataclass(frozen=True)
class _Marker:
    kind: Literal["evidence", "authority"]
    policy_version: str | None
    capture_id: str
    available_at_ns: int


@dataclass(frozen=True)
class _Request:
    request_id: str
    selection_axis: Literal["arrival_time", "event_time"]
    ordering: Literal["arrival", "strict_event"]
    window_start_ns: int
    window_end_ns: int
    asset: AssetId
    channel: str | None
    authority_policy_version: str = _POLICY


@dataclass(frozen=True)
class _Cursor:
    request_id: str
    snapshot_id: str
    last_key: tuple[int | str, ...]


@dataclass(frozen=True)
class _Page:
    capture_ids: tuple[str, ...]
    cursor: _Cursor | None


class _SnapshotSource:
    """POC-only read model; it deliberately does not call DataTruth.decide()."""

    scheme_version = "replay-as-of-membership-poc/v1"
    ordering_version = "keyset-v1"

    def __init__(self, connection_string: str, tables: dict[str, str]) -> None:
        self.database = questdb.connect(connection_string)
        self.tables = tables

    def close(self) -> None:
        self.database.close()

    def _facts(self) -> dict[str, CaptureFact]:
        evidence = _rows(
            self.database,
            "SELECT capture_id, asset, provider, source_id, channel, message_type, "
            "event_subtype, sid, seq, provider_timestamp, received_timestamp, "
            f"schema_version, payload FROM {self.tables['evidence']}",
        )
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in evidence:
            capture_id = row.get("capture_id")
            if not isinstance(capture_id, str):
                raise _SourceUnavailable("malformed evidence capture ID")
            grouped[capture_id].append(row)
        facts: dict[str, CaptureFact] = {}
        for capture_id, rows_for_capture in grouped.items():
            if len(rows_for_capture) != 1:
                raise _SourceUnavailable("evidence capture ID is not exactly singular")
            row = rows_for_capture[0]
            required = (
                "asset",
                "provider",
                "source_id",
                "channel",
                "message_type",
                "sid",
                "schema_version",
                "payload",
            )
            if not all(isinstance(row.get(name), str) for name in required[:5]) or not all(
                isinstance(row.get(name), str) for name in required[6:]
            ):
                raise _SourceUnavailable("malformed required evidence field")
            try:
                received = _ns(row.get("received_timestamp"))
                provider = _ns(row.get("provider_timestamp"))
                sid = row.get("sid")
                sequence = row.get("seq")
                if received is None or not isinstance(sid, int):
                    raise TypeError("missing required evidence timestamp or sid")
                if sequence is not None and not isinstance(sequence, int):
                    raise TypeError("invalid evidence sequence")
                facts[capture_id] = CaptureFact(
                    capture_id,
                    AssetId(row["asset"]),
                    row["provider"],
                    row["source_id"],
                    row["channel"],
                    row["message_type"],
                    row.get("event_subtype") if isinstance(row.get("event_subtype"), str) else None,
                    sid,
                    sequence,
                    provider,
                    received,
                    row["schema_version"],
                    row["payload"],
                )
            except (TypeError, ValueError) as error:
                raise _SourceUnavailable("evidence does not decode as CaptureFact") from error
        return facts

    def _decisions(self) -> dict[tuple[str, str], TruthDecision]:
        records = _rows(
            self.database,
            "SELECT policy_version, subject_capture_id, category, "
            "contributing_capture_ids, reason, event_provider, event_source_id, "
            f"event_message_type, event_trade_id FROM {self.tables['truth']}",
        )
        grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
        for row in records:
            policy, subject = row.get("policy_version"), row.get("subject_capture_id")
            if not isinstance(policy, str) or not isinstance(subject, str):
                raise _SourceUnavailable("malformed TruthDecision authority key")
            grouped[(policy, subject)].append(row)
        decisions: dict[tuple[str, str], TruthDecision] = {}
        for key, key_rows in grouped.items():
            if len(key_rows) != 1:
                raise _SourceUnavailable("ambiguous physical TruthDecision authority")
            row = key_rows[0]
            references = row.get("contributing_capture_ids")
            category = row.get("category")
            if not isinstance(references, str) or not isinstance(category, str):
                raise _SourceUnavailable("malformed TruthDecision fields")
            try:
                contributing = json.loads(references)
                if not isinstance(contributing, list) or not all(
                    isinstance(value, str) for value in contributing
                ):
                    raise TypeError("invalid contributing IDs")
                reason = _optional_text(row.get("reason"))
                event_fields = tuple(
                    _optional_text(row.get(column))
                    for column in (
                        "event_provider",
                        "event_source_id",
                        "event_message_type",
                        "event_trade_id",
                    )
                )
                if all(value is None for value in event_fields):
                    event = None
                elif all(isinstance(value, str) for value in event_fields):
                    event = EventIdentity(*event_fields)
                else:
                    raise TypeError("partial TruthDecision event identity")
                decisions[key] = TruthDecision(
                    key[1],
                    TruthDecisionCategory(category),
                    key[0],
                    tuple(contributing),
                    None if reason is None else TradeNotAcceptedReason(reason),
                    event,
                )
            except (TypeError, ValueError, json.JSONDecodeError) as error:
                raise _SourceUnavailable("TruthDecision does not decode") from error
        return decisions

    def _markers(self) -> dict[tuple[str, str | None, str], _Marker]:
        records = _rows(
            self.database,
            "SELECT kind, policy_version, capture_id, available_at_ns "
            f"FROM {self.tables['availability']}",
        )
        grouped: dict[tuple[str, str | None, str], list[dict[str, object]]] = defaultdict(list)
        for row in records:
            kind, policy, capture_id = (
                row.get("kind"),
                row.get("policy_version"),
                row.get("capture_id"),
            )
            if not isinstance(capture_id, str):
                raise _SourceUnavailable("malformed availability marker")
            marker_key: tuple[str, str | None, str]
            if kind == "evidence":
                marker_key = ("evidence", None, capture_id)
            elif kind == "authority" and isinstance(policy, str):
                marker_key = ("authority", policy, capture_id)
            else:
                raise _SourceUnavailable("malformed availability marker")
            grouped[marker_key].append(row)
        result: dict[tuple[str, str | None, str], _Marker] = {}
        for key, marker_rows in grouped.items():
            if len(marker_rows) != 1:
                raise _SourceUnavailable("availability marker is not exactly singular")
            available = _ns(marker_rows[0].get("available_at_ns"))
            if available is None:
                raise _SourceUnavailable("marker lacks conservative proof time")
            result[key] = _Marker(key[0], key[1], key[2], available)  # type: ignore[arg-type]
        return result

    def membership(self, request: _Request, cutoff_ns: int) -> tuple[CaptureFact, ...]:
        facts = self._facts()
        decisions = self._decisions()
        markers = self._markers()
        qualified: list[CaptureFact] = []
        for capture_id, fact in facts.items():
            if fact.asset != request.asset or (
                request.channel is not None and fact.channel != request.channel
            ):
                continue
            decision = decisions.get((request.authority_policy_version, capture_id))
            evidence_marker = markers.get(("evidence", None, capture_id))
            authority_marker = markers.get(
                ("authority", request.authority_policy_version, capture_id)
            )
            if (
                decision is None
                or decision.subject_capture_id != capture_id
                or evidence_marker is None
                or authority_marker is None
                or evidence_marker.available_at_ns > cutoff_ns
                or authority_marker.available_at_ns > cutoff_ns
            ):
                continue
            # Evidence proof is the decoded immutable CaptureFact obtained by exact ID.
            if facts.get(capture_id) != fact:
                raise _SourceUnavailable("configured evidence read is not exact")
            qualified.append(fact)
        if request.selection_axis == "event_time" and any(
            fact.provider_timestamp is None for fact in qualified
        ):
            raise _UnsupportedEventTime("qualified evidence has null provider timestamp")
        selected = [
            fact
            for fact in qualified
            if request.window_start_ns
            <= self._selection_timestamp(request.selection_axis, fact)
            < request.window_end_ns
        ]
        if request.ordering == "strict_event" and any(
            fact.provider_timestamp is None for fact in selected
        ):
            raise _UnsupportedEventTime("selected evidence has null provider timestamp")
        return tuple(sorted(selected, key=lambda fact: self._key(request.ordering, fact)))

    def fingerprint(self, request: _Request, cutoff_ns: int) -> tuple[str, tuple[CaptureFact, ...]]:
        membership = self.membership(request, cutoff_ns)
        payload = {
            "asset": request.asset.value,
            "authority_policy_version": request.authority_policy_version,
            "availability_source_authority_identity": self.tables["availability"],
            "configured_channel": request.channel,
            "cutoff_ns": cutoff_ns,
            "evidence_source_authority_identity": self.tables["evidence"],
            "ordering_rule_version": self.ordering_version,
            "ordering": request.ordering,
            "scheme_version": self.scheme_version,
            "selection_axis": request.selection_axis,
            "selection_window_ns": [request.window_start_ns, request.window_end_ns],
            "sorted_eligible_semantic_membership_keys": [
                [request.authority_policy_version, fact.capture_id]
                for fact in sorted(
                    membership,
                    key=lambda fact: (request.authority_policy_version, fact.capture_id),
                )
            ],
            "truth_decision_source_authority_identity": self.tables["truth"],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest(), membership

    @staticmethod
    def _selection_timestamp(
        selection_axis: Literal["arrival_time", "event_time"], fact: CaptureFact
    ) -> int:
        if selection_axis == "arrival_time":
            return fact.received_timestamp
        assert fact.provider_timestamp is not None
        return fact.provider_timestamp

    @staticmethod
    def _key(
        ordering: Literal["arrival", "strict_event"], fact: CaptureFact
    ) -> tuple[int | str, ...]:
        if ordering == "arrival":
            return (fact.received_timestamp, fact.capture_id)
        assert fact.provider_timestamp is not None
        return (fact.provider_timestamp, fact.received_timestamp, fact.capture_id)

    def first_page(self, request: _Request, cutoff_ns: int, size: int) -> _Page:
        snapshot_id, membership = self.fingerprint(request, cutoff_ns)
        page = membership[:size]
        cursor = (
            _Cursor(request.request_id, snapshot_id, self._key(request.ordering, page[-1]))
            if page and len(page) < len(membership)
            else None
        )
        return _Page(tuple(fact.capture_id for fact in page), cursor)

    def next_page(
        self, request: _Request, cutoff_ns: int, cursor: _Cursor, size: int
    ) -> _Page:
        if cursor.request_id != request.request_id:
            raise _SnapshotMismatch("cursor request identity mismatch")
        snapshot_id, membership = self.fingerprint(request, cutoff_ns)
        if snapshot_id != cursor.snapshot_id:
            raise _SnapshotMismatch("SOURCE_SNAPSHOT_IDENTITY mismatch")
        page = tuple(
            fact for fact in membership if self._key(request.ordering, fact) > cursor.last_key
        )[:size]
        next_cursor = (
            _Cursor(request.request_id, snapshot_id, self._key(request.ordering, page[-1]))
            if page
            and self._key(request.ordering, page[-1])
            != self._key(request.ordering, membership[-1])
            else None
        )
        return _Page(tuple(fact.capture_id for fact in page), next_cursor)


def _create_tables(server: _TaskQuestDB) -> dict[str, str]:
    assert server.database is not None
    suffix = uuid4().hex
    tables = {
        "evidence": f"replay_poc_evidence_{suffix}",
        "truth": f"replay_poc_truth_{suffix}",
        "availability": f"replay_poc_availability_{suffix}",
    }
    server.database.execute(
        f"CREATE TABLE {tables['evidence']} (capture_id VARCHAR, asset VARCHAR, "
        "provider VARCHAR, source_id VARCHAR, channel VARCHAR, message_type VARCHAR, "
        "event_subtype VARCHAR, sid LONG, seq LONG, provider_timestamp TIMESTAMP_NS, "
        "received_timestamp TIMESTAMP_NS, schema_version VARCHAR, payload VARCHAR) "
        "TIMESTAMP(received_timestamp) PARTITION BY DAY WAL"
    )
    server.database.execute(
        f"CREATE TABLE {tables['truth']} (policy_version VARCHAR, "
        "subject_capture_id VARCHAR, category VARCHAR, contributing_capture_ids VARCHAR, "
        "reason VARCHAR, event_provider VARCHAR, event_source_id VARCHAR, event_message_type VARCHAR, "
        "event_trade_id VARCHAR, physical_written_at TIMESTAMP_NS) "
        "TIMESTAMP(physical_written_at) PARTITION BY DAY WAL"
    )
    server.database.execute(
        f"CREATE TABLE {tables['availability']} (kind VARCHAR, policy_version VARCHAR, "
        "capture_id VARCHAR, available_at_ns TIMESTAMP_NS, written_at_ns TIMESTAMP_NS) "
        "TIMESTAMP(written_at_ns) PARTITION BY DAY WAL"
    )
    return tables


def _fact(capture_id: str, *, received: int, provider: int | None, channel: str) -> CaptureFact:
    return CaptureFact(
        capture_id,
        AssetId.BTC,
        "kalshi",
        "KXBTC",
        channel,
        "trade",
        None,
        1,
        1,
        provider,
        received,
        "market-ingress/v1",
        json.dumps({"capture_id": capture_id}, separators=(",", ":")),
    )


def _decision(
    fact: CaptureFact, category: TruthDecisionCategory = TruthDecisionCategory.ACCEPTED
) -> TruthDecision:
    reason = (
        TradeNotAcceptedReason.INVALID_TRADE_EVIDENCE
        if category is TruthDecisionCategory.NOT_ACCEPTED
        else None
    )
    event = (
        None
        if category is TruthDecisionCategory.NOT_ACCEPTED
        else EventIdentity("kalshi", "KXBTC", "trade", f"trade-{fact.capture_id}")
    )
    return TruthDecision(
        fact.capture_id,
        category,
        _POLICY,
        (fact.capture_id,),
        reason,
        event,
    )


def _append_fact(server: _TaskQuestDB, table: str, fact: CaptureFact) -> None:
    assert server.database is not None
    columns: dict[str, object] = {
        "capture_id": fact.capture_id,
        "asset": fact.asset.value,
        "provider": fact.provider,
        "source_id": fact.source_id,
        "channel": fact.channel,
        "message_type": fact.message_type,
        "sid": fact.sid,
        "schema_version": fact.schema_version,
        "payload": fact.payload,
    }
    if fact.seq is not None:
        columns["seq"] = fact.seq
    if fact.provider_timestamp is not None:
        columns["provider_timestamp"] = questdb.TimestampNanos(fact.provider_timestamp)
    _append(server.database, table, columns, fact.received_timestamp)


def _append_decision(
    server: _TaskQuestDB, table: str, decision: TruthDecision, *, written_at: int
) -> None:
    assert server.database is not None
    event = decision.event_identity
    _append(
        server.database,
        table,
        {
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
        },
        written_at,
    )


def _append_marker(
    server: _TaskQuestDB,
    table: str,
    *,
    kind: Literal["evidence", "authority"],
    capture_id: str,
    available_at: int,
    written_at: int,
) -> None:
    assert server.database is not None
    _append(
        server.database,
        table,
        {
            "kind": kind,
            "policy_version": _POLICY if kind == "authority" else None,
            "capture_id": capture_id,
            "available_at_ns": questdb.TimestampNanos(available_at),
        },
        written_at,
    )


def _append_eligible(
    server: _TaskQuestDB,
    tables: dict[str, str],
    fact: CaptureFact,
    *,
    available_at: int,
    written_at: int,
    category: TruthDecisionCategory = TruthDecisionCategory.ACCEPTED,
) -> None:
    _append_fact(server, tables["evidence"], fact)
    _append_decision(
        server, tables["truth"], _decision(fact, category), written_at=written_at
    )
    _append_marker(
        server,
        tables["availability"],
        kind="evidence",
        capture_id=fact.capture_id,
        available_at=available_at,
        written_at=written_at,
    )
    _append_marker(
        server,
        tables["availability"],
        kind="authority",
        capture_id=fact.capture_id,
        available_at=available_at,
        written_at=written_at + 1,
    )


def _assert_no_task_residue(server: _TaskQuestDB) -> None:
    assert not server.root.exists()
    assert not any(_port_open(port) for port in server.ports.values())
    assert server.lifecycle["root_delete"]


def test_snapshot_membership_pagination_poc() -> None:
    """Prove normal stability and deterministic fail-closed membership drift."""
    root = Path.cwd() / f".pytest-replay-as-of-snapshot-poc-{uuid4().hex}"
    with _server(root) as server:
        tables = _create_tables(server)
        a = _fact("A", received=500, provider=50, channel="trade")
        b = _fact("B", received=500, provider=50, channel="trade")
        u = _fact("U", received=550, provider=60, channel="trade")
        null_event = _fact("N", received=1_500, provider=None, channel="arrival-null")
        _append_eligible(server, tables, a, available_at=100, written_at=101)
        _append_eligible(server, tables, b, available_at=100, written_at=103)
        _append_fact(server, tables["evidence"], u)
        _append_decision(server, tables["truth"], _decision(u), written_at=105)
        _append_eligible(server, tables, null_event, available_at=100, written_at=107)
        category_facts = (
            (_fact("CATEGORY_ACCEPTED", received=600, provider=61, channel="categories"), TruthDecisionCategory.ACCEPTED),
            (_fact("CATEGORY_DUPLICATE", received=601, provider=62, channel="categories"), TruthDecisionCategory.DUPLICATE),
            (_fact("CATEGORY_CONFLICT", received=602, provider=63, channel="categories"), TruthDecisionCategory.CONFLICT),
            (_fact("CATEGORY_NOT_ACCEPTED", received=603, provider=64, channel="categories"), TruthDecisionCategory.NOT_ACCEPTED),
        )
        for index, (fact, category) in enumerate(category_facts, start=1):
            _append_eligible(
                server,
                tables,
                fact,
                available_at=100,
                written_at=110 + index * 2,
                category=category,
            )

        request = _Request(
            "page-request-1", "arrival_time", "arrival", 400, 700, AssetId.BTC, "trade"
        )
        source = _SnapshotSource(server.connection_string, tables)
        try:
            categories_request = _Request(
                "all-categories", "arrival_time", "arrival", 400, 700, AssetId.BTC, "categories"
            )
            assert source.first_page(categories_request, _CUTOFF, size=10).capture_ids == (
                "CATEGORY_ACCEPTED",
                "CATEGORY_DUPLICATE",
                "CATEGORY_CONFLICT",
                "CATEGORY_NOT_ACCEPTED",
            )
            page1 = source.first_page(request, _CUTOFF, size=1)
            assert page1.capture_ids == ("A",)
            assert page1.cursor is not None
            assert source.fingerprint(request, _CUTOFF)[1] == (a, b)
            for changed_request in (
                replace(request, selection_axis="event_time"),
                replace(request, ordering="strict_event"),
                replace(request, window_end_ns=701),
                replace(request, channel="categories"),
                replace(request, authority_policy_version="data-truth/other"),
            ):
                with pytest.raises(_SnapshotMismatch):
                    source.next_page(changed_request, _CUTOFF, page1.cursor, size=1)

            c_new = _fact("C_NEW", received=510, provider=55, channel="trade")
            _append_eligible(server, tables, c_new, available_at=901, written_at=901)
            assert source.fingerprint(request, _CUTOFF)[0] == page1.cursor.snapshot_id

            _append_marker(
                server,
                tables["availability"],
                kind="evidence",
                capture_id="U",
                available_at=902,
                written_at=902,
            )
            _append_marker(
                server,
                tables["availability"],
                kind="authority",
                capture_id="U",
                available_at=902,
                written_at=903,
            )
            assert source.fingerprint(request, _CUTOFF)[0] == page1.cursor.snapshot_id
        finally:
            source.close()

        source = _SnapshotSource(server.connection_string, tables)
        try:
            page2 = source.next_page(request, _CUTOFF, page1.cursor, size=1)
            assert page2.capture_ids == ("B",)
            assert page2.cursor is None
        finally:
            source.close()

        server.restart()
        source = _SnapshotSource(server.connection_string, tables)
        try:
            assert source.fingerprint(request, _CUTOFF)[0] == page1.cursor.snapshot_id
            restart_page2 = source.next_page(request, _CUTOFF, page1.cursor, size=1)
            assert restart_page2 == page2

            event_arrival = _Request(
                "event-arrival", "event_time", "arrival", 40, 70, AssetId.BTC, "trade"
            )
            event_page = source.first_page(event_arrival, _CUTOFF, size=1)
            assert event_page.capture_ids == ("A",)
            assert event_page.cursor is not None
            assert source.next_page(event_arrival, _CUTOFF, event_page.cursor, size=1).capture_ids == ("B",)
            event_strict = _Request(
                "event-strict", "event_time", "strict_event", 40, 70, AssetId.BTC, "trade"
            )
            assert source.first_page(event_strict, _CUTOFF, size=10).capture_ids == ("A", "B")
            assert source.fingerprint(event_arrival, _CUTOFF)[0] != source.fingerprint(
                event_strict, _CUTOFF
            )[0]
            assert source.first_page(
                _Request(
                    "event-discriminator", "event_time", "arrival", 400, 700, AssetId.BTC, "trade"
                ),
                _CUTOFF,
                size=10,
            ).capture_ids == ()
            assert source.fingerprint(event_arrival, _CUTOFF)[0] != source.fingerprint(
                _Request(
                    "arrival-selection-binding",
                    "arrival_time",
                    "arrival",
                    40,
                    70,
                    AssetId.BTC,
                    "trade",
                ),
                _CUTOFF,
            )[0]

            arrival_strict_event = _Request(
                "arrival-strict-event", "arrival_time", "strict_event", 400, 700, AssetId.BTC, "trade"
            )
            strict_event_page = source.first_page(arrival_strict_event, _CUTOFF, size=1)
            assert strict_event_page.capture_ids == ("A",)
            assert strict_event_page.cursor is not None
            assert source.next_page(
                arrival_strict_event, _CUTOFF, strict_event_page.cursor, size=1
            ).capture_ids == ("B",)

            arrival_null = _Request(
                "arrival-null", "arrival_time", "arrival", 1_000, 2_000, AssetId.BTC, "arrival-null"
            )
            assert source.first_page(arrival_null, _CUTOFF, size=1).capture_ids == ("N",)
            event_null = _Request(
                "event-null", "event_time", "arrival", 1_000, 1_200, AssetId.BTC, "arrival-null"
            )
            with pytest.raises(_UnsupportedEventTime):
                source.first_page(event_null, _CUTOFF, size=1)
            strict_event_null = _Request(
                "strict-event-null", "arrival_time", "strict_event", 1_000, 2_000, AssetId.BTC, "arrival-null"
            )
            with pytest.raises(_UnsupportedEventTime):
                source.first_page(strict_event_null, _CUTOFF, size=1)

            # Explicit rollback adversary: a last-marker floor alone permits 200 <= C.
            last_marker, bind_wall_time, rolled_back_now = 100, 1_000, 200
            candidate = max(rolled_back_now, last_marker + 1)
            assert bind_wall_time > _CUTOFF
            assert candidate == 200 <= _CUTOFF
            rollback = _fact("ROLLBACK", received=520, provider=56, channel="trade")
            _append_eligible(server, tables, rollback, available_at=candidate, written_at=904)
            with pytest.raises(_SnapshotMismatch):
                source.next_page(request, _CUTOFF, page1.cursor, size=1)

            _append_decision(server, tables["truth"], _decision(b), written_at=905)
            with pytest.raises(_SourceUnavailable, match="ambiguous physical TruthDecision"):
                source.next_page(request, _CUTOFF, page1.cursor, size=1)

            print(
                "POC_RESULT=PASS_WITH_FAIL_CLOSED_DRIFT "
                "PAGE1_MEMBERSHIP=A,B "
                f"PAGE1_SNAPSHOT_ID={page1.cursor.snapshot_id} "
                "LAST_MARKER_FLOOR_ALONE_STABLE=NO "
                "CLOCK_POLICY_RESULT=MEMBERSHIP_FINGERPRINT_FAIL_CLOSED_SUFFICIENT"
            )
        finally:
            source.close()
    _assert_no_task_residue(server)
