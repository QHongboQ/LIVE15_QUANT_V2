"""Opt-in, raw QuestDB 5.0.0 SF restart-isolation reproducer for Windows."""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.request import urlopen
from uuid import uuid4

import pytest
import questdb

_RUN = os.getenv("LIVE15_RUN_QUESTDB_SF_UPSTREAM_ISOLATION") == "1"
_EXE = Path(r"D:\LIVE15_V2_RUNTIME\questdb\dist\10.0.1\bin\questdb.exe")
_WAIT_SECONDS = 30

pytestmark = pytest.mark.skipif(not _RUN, reason="set opt-in isolation environment")


def _ports() -> dict[str, int]:
    sockets = [socket.socket() for _ in range(4)]
    try:
        for item in sockets:
            item.bind(("127.0.0.1", 0))
        return dict(
            zip(("http", "pg", "min", "ilp"), (s.getsockname()[1] for s in sockets))
        )
    finally:
        for item in sockets:
            item.close()


class _Server:
    def __init__(self, root: Path) -> None:
        self.root, self.ports = root, _ports()
        self.process: subprocess.Popen[bytes] | None = None
        self.server_pid: int | None = None

    @property
    def connection(self) -> str:
        return f"ws::addr=127.0.0.1:{self.ports['http']};"

    def start(self) -> None:
        config = self.root / "conf" / "server.conf"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            "\n".join(
                (
                    "config.validation.strict=true",
                    f"http.net.bind.to=127.0.0.1:{self.ports['http']}",
                    f"http.min.net.bind.to=127.0.0.1:{self.ports['min']}",
                    f"pg.net.bind.to=127.0.0.1:{self.ports['pg']}",
                    f"line.tcp.net.bind.to=127.0.0.1:{self.ports['ilp']}",
                )
            ),
            encoding="utf-8",
        )
        self.process = subprocess.Popen(
            [_EXE, "-d", str(self.root)],
            cwd=self.root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        deadline = time.monotonic() + _WAIT_SECONDS
        while time.monotonic() < deadline:
            try:
                with urlopen(f"http://127.0.0.1:{self.ports['min']}/status", timeout=1):
                    database = questdb.connect(self.connection)
                    database.close()
                    self.server_pid = _listening_pid(self.ports["http"])
                    assert self.server_pid is not None
                    return
            except (OSError, questdb.QuestDBError):
                time.sleep(0.1)
        raise AssertionError("task-owned QuestDB did not become healthy")

    def stop(self) -> None:
        if self.process is None:
            return
        self.process.send_signal(signal.CTRL_BREAK_EVENT)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and _port_open(self.ports["http"]):
            time.sleep(0.1)
        if _port_open(self.ports["http"]):
            assert self.server_pid is not None
            subprocess.run(
                ["taskkill", "/PID", str(self.server_pid), "/T", "/F"], check=True
            )
        self.process.wait(timeout=15)
        self.process = None
        self.server_pid = None


def _port_open(port: int) -> bool:
    with socket.socket() as connection:
        connection.settimeout(0.2)
        return connection.connect_ex(("127.0.0.1", port)) == 0


def _listening_pid(port: int) -> int | None:
    output = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"], check=True, capture_output=True, text=True
    ).stdout
    for line in output.splitlines():
        fields = line.split()
        if (
            len(fields) == 5
            and fields[1].endswith(f":{port}")
            and fields[3] == "LISTENING"
        ):
            return int(fields[4])
    return None


def _create_table(connection: str, table: str) -> None:
    db = questdb.connect(connection)
    try:
        db.execute(
            f"CREATE TABLE {table} (id VARCHAR, value VARCHAR, received_timestamp TIMESTAMP_NS) "
            "TIMESTAMP(received_timestamp) PARTITION BY DAY WAL "
            "DEDUP UPSERT KEYS(received_timestamp, id)"
        )
    finally:
        db.close()


def _count(connection: str, table: str, identifier: str) -> int:
    db = questdb.connect(connection)
    try:
        return int(
            db.query(f"SELECT count() AS n FROM {table} WHERE id = '{identifier}'")
            .to_pandas()
            .iloc[0]["n"]
        )
    finally:
        db.close()


def _wait_count(connection: str, table: str, identifier: str) -> bool:
    deadline = time.monotonic() + _WAIT_SECONDS
    while time.monotonic() < deadline:
        if _count(connection, table, identifier) == 1:
            return True
        time.sleep(0.1)
    return False


def _inventory(sf_dir: Path) -> dict[str, Any]:
    slots = sorted(sf_dir.glob("*-ingest-*"))
    return {
        "slots": [slot.name for slot in slots],
        "files": [
            {"path": str(path.relative_to(sf_dir)), "size": path.stat().st_size}
            for slot in slots
            for path in sorted(slot.iterdir())
            if path.is_file()
        ],
        "failed": any((slot / ".failed").exists() for slot in slots),
    }


def _write_child(root: Path) -> None:
    (root / "child.py").write_text(
        """import argparse, json, os, sys, time
from pathlib import Path

root = Path(os.environ["QDB_ISOLATION_ROOT"]).resolve()

def emit(event, **fields):
    print(json.dumps({"event": event, **fields}), flush=True)

def marker(name, **fields):
    destination = root / f"{name}.json"
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(fields), encoding="utf-8")
    temporary.replace(destination)

def wait_for_exit():
    while sys.stdin.readline().strip() != "EXIT":
        time.sleep(.02)

parser = argparse.ArgumentParser()
parser.add_argument("--mode", required=True)
mode = parser.parse_args().mode
emit("started", pid=os.getpid(), python=sys.executable, cwd=os.getcwd())
marker("started", pid=os.getpid(), python=sys.executable, cwd=os.getcwd())
if mode == "start-only":
    raise SystemExit(0)

import questdb
version = getattr(questdb, "__version__", "5.0.0")
emit("questdb_imported", version=version)
marker("questdb_imported", version=version)
if mode == "import-only":
    raise SystemExit(0)
if mode == "long-lived":
    emit("waiting", pid=os.getpid())
    marker("waiting", pid=os.getpid())
    wait_for_exit()
    emit("exiting")
    raise SystemExit(0)

s = json.loads((root / "scenario.json").read_text(encoding="utf-8"))
db = questdb.connect(s["connection"], sf_dir=s["sf_dir"], sender_id=s["sender_id"], sf_durability="memory", auto_flush=False, drain_orphans=s.get("drain_orphans", False))
sender = db.sender()
emit("connected")
marker("connected")
if mode == "producer":
    sender.row(s["table"], columns={"id": s["primer_id"], "value": "primer"}, at=questdb.TimestampNanos(s["timestamp"] - 1))
    primer_fsn = sender.flush_and_get_fsn()
    if not sender.await_acked_fsn(primer_fsn, timeout_millis=500):
        raise RuntimeError("primer acknowledgement timed out")
    emit("ready", primer_fsn=primer_fsn)
    marker("ready", primer_fsn=primer_fsn)
    while not (root / "publish.json").exists() and not (root / "exit.json").exists():
        time.sleep(.02)
    if (root / "publish.json").exists():
        sender.row(s["table"], columns={"id": s["id"], "value": "pending"}, at=questdb.TimestampNanos(s["timestamp"]))
        marker("published", fsn=sender.flush_and_get_fsn())
        while not (root / "exit.json").exists():
            time.sleep(.02)
    sender.close(flush=False)
    db.close()
else:
    marker("opened")
    while not (root / "release.json").exists() and not (root / "exit.json").exists():
        time.sleep(.02)
    sender.close(flush=False)
    db.close()
""",
        encoding="utf-8",
    )


def _child(root: Path, mode: str) -> subprocess.Popen[str]:
    child_path = (root / "child.py").resolve()
    assert Path(sys.executable).is_file()
    assert child_path.is_file()
    environment = os.environ | {
        "PYTHONUNBUFFERED": "1",
        "QDB_ISOLATION_ROOT": str(root.resolve()),
        "PYTHONPATH": str(Path.cwd() / "src"),
    }
    return subprocess.Popen(
        [sys.executable, "-u", str(child_path), "--mode", mode],
        cwd=Path.cwd().resolve(),
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
        close_fds=True,
    )


def _wait_file(path: Path, process: subprocess.Popen[str]) -> dict[str, Any]:
    deadline = time.monotonic() + _WAIT_SECONDS
    while time.monotonic() < deadline:
        if path.exists():
            return json.loads(path.read_text())
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise AssertionError(
                f"child exited before {path.name}: exit={process.returncode}; "
                f"stdout={stdout!r}; stderr={stderr!r}"
            )
        time.sleep(0.02)
    markers = sorted(item.name for item in path.parent.glob("*.json"))
    if process.poll() is None:
        process.terminate()
    stdout, stderr = process.communicate(timeout=10)
    raise AssertionError(
        f"child timed out before {path.name}: pid={process.pid}; poll={process.returncode}; "
        f"markers={markers}; stdout={stdout!r}; stderr={stderr!r}"
    )


def _clear(root: Path) -> None:
    for name in (
        "ready.json",
        "started.json",
        "connected.json",
        "publish.json",
        "published.json",
        "exit.json",
        "opened.json",
        "release.json",
    ):
        (root / name).unlink(missing_ok=True)


def _restart_case(
    server: _Server, root: Path, name: str, graceful: bool, drain_orphans: bool = False
) -> dict[str, Any]:
    table, sf_dir, sender_id = (
        f"sf_iso_{uuid4().hex}",
        root / f"sf-{name}",
        f"sender-{uuid4().hex}",
    )
    identifier, timestamp = f"id-{name}-{uuid4().hex}", 1_700_000_000_000_000_000
    primer_id = f"primer-{name}-{uuid4().hex}"
    sf_dir.mkdir()
    _create_table(server.connection, table)
    _clear(root)
    (root / "scenario.json").write_text(
        json.dumps(
            {
                "mode": "producer",
                "connection": server.connection,
                "table": table,
                "sf_dir": str(sf_dir),
                "sender_id": sender_id,
                "id": identifier,
                "primer_id": primer_id,
                "timestamp": timestamp,
                "graceful": graceful,
            }
        )
    )
    producer = _child(root, "producer")
    _wait_file(root / "started.json", producer)
    _wait_file(root / "connected.json", producer)
    ready = _wait_file(root / "ready.json", producer)
    assert _wait_count(server.connection, table, primer_id)
    server.stop()
    assert not _port_open(server.ports["http"])
    (root / "publish.json").write_text("{}")
    published = _wait_file(root / "published.json", producer)
    assert published["fsn"] is not None
    before = _inventory(sf_dir)
    if graceful:
        (root / "exit.json").write_text("{}")
    else:
        producer.kill()
    producer_stdout, producer_stderr = producer.communicate(timeout=15)
    if graceful:
        assert producer.returncode == 0, (producer_stdout, producer_stderr)
    else:
        assert producer.returncode is not None
    after_exit = _inventory(sf_dir)
    server.start()
    _clear(root)
    (root / "scenario.json").write_text(
        json.dumps(
            {
                "mode": "recovery",
                "connection": server.connection,
                "sf_dir": str(sf_dir),
                "sender_id": sender_id,
                "drain_orphans": drain_orphans,
            }
        )
    )
    recovery = _child(root, "recovery")
    _wait_file(root / "opened.json", recovery)
    reopened = _inventory(sf_dir)
    counts: list[int] = []
    deadline = time.monotonic() + _WAIT_SECONDS
    while time.monotonic() < deadline:
        if recovery.poll() is not None:
            stdout, stderr = recovery.communicate()
            raise AssertionError(
                f"recovery exited during observation: exit={recovery.returncode}; "
                f"stdout={stdout!r}; stderr={stderr!r}"
            )
        counts.append(_count(server.connection, table, identifier))
        time.sleep(0.25)
    (root / "release.json").write_text("{}")
    recovery_stdout, recovery_stderr = recovery.communicate(timeout=15)
    assert recovery.returncode == 0, (recovery_stdout, recovery_stderr)
    return {
        "ready": ready,
        "target_fsn": published["fsn"],
        "producer_exit_code": producer.returncode,
        "producer_stdout": producer_stdout,
        "producer_stderr": producer_stderr,
        "recovered": counts[-1] == 1 and 1 in counts,
        "final_row_count": counts[-1],
        "before": before,
        "after_exit": after_exit,
        "reopened": reopened,
        "same_dirty_slot_reopened": bool(
            set(before["slots"]) & set(reopened["slots"])
        ),
        "new_slot_created": bool(set(reopened["slots"]) - set(before["slots"])),
        "recovery_stdout": recovery_stdout,
        "recovery_stderr": recovery_stderr,
    }


def _wait_marker(
    root: Path, name: str, process: subprocess.Popen[str], timeout: float = 10
) -> dict[str, Any]:
    path = root / f"{name}.json"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise AssertionError(
                f"child exited before {name}: exit={process.returncode}; "
                f"stdout={stdout!r}; stderr={stderr!r}"
            )
        time.sleep(0.02)
    marker_inventory = sorted(item.name for item in root.glob("*.json"))
    if process.poll() is None:
        process.terminate()
    stdout, stderr = process.communicate(timeout=10)
    raise AssertionError(
        f"child timed out before {name}: pid={process.pid}; poll={process.returncode}; "
        f"markers={marker_inventory}; stdout={stdout!r}; stderr={stderr!r}"
    )


def _child_events(stdout: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def _pure_python_smoke(root: Path) -> tuple[int, str, str]:
    marker = root / "pure-python.json"
    code = (
        "import json, os\n"
        "from pathlib import Path\n"
        "root = Path(os.environ['QDB_ISOLATION_ROOT']).resolve()\n"
        "payload = {'event': 'python_spawn_ok', 'pid': os.getpid()}\n"
        "temporary = root / 'pure-python.tmp'\n"
        "temporary.write_text(json.dumps(payload), encoding='utf-8')\n"
        "temporary.replace(root / 'pure-python.json')\n"
        "print(json.dumps(payload), flush=True)\n"
    )
    process = subprocess.Popen(
        [sys.executable, "-u", "-c", code],
        cwd=Path.cwd().resolve(),
        env=os.environ | {"PYTHONUNBUFFERED": "1", "QDB_ISOLATION_ROOT": str(root)},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
        close_fds=True,
    )
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 0, (process.returncode, stdout, stderr)
    assert marker.is_file(), (stdout, stderr)
    assert _child_events(stdout) == [json.loads(marker.read_text(encoding="utf-8"))]
    return process.returncode, stdout, stderr


def test_raw_questdb_500_windows_subprocess_spawn_diagnostic(tmp_path: Path) -> None:
    """Prove raw child lifecycle before exercising any SF restart behavior."""
    assert _EXE.is_file()
    ipc_root = (tmp_path / f"qdb-sf-ipc-{uuid4().hex}").resolve()
    server_root = (tmp_path / f"qdb-sf-server-{uuid4().hex}").resolve()
    ipc_root.mkdir()
    server: _Server | None = None
    child: subprocess.Popen[str] | None = None
    try:
        _pure_python_smoke(ipc_root)
        _write_child(ipc_root)
        assert Path(sys.executable).is_file()
        assert (ipc_root / "child.py").is_file()

        child = _child(ipc_root, "start-only")
        _wait_marker(ipc_root, "started", child)
        stdout, stderr = child.communicate(timeout=10)
        assert child.returncode == 0, (stdout, stderr)
        assert [event["event"] for event in _child_events(stdout)] == ["started"]

        (ipc_root / "started.json").unlink()
        child = _child(ipc_root, "import-only")
        _wait_marker(ipc_root, "started", child)
        imported = _wait_marker(ipc_root, "questdb_imported", child)
        stdout, stderr = child.communicate(timeout=10)
        assert child.returncode == 0, (stdout, stderr)
        assert imported["version"] == "5.0.0"
        assert [event["event"] for event in _child_events(stdout)] == [
            "started",
            "questdb_imported",
        ]

        for name in ("started.json", "questdb_imported.json"):
            (ipc_root / name).unlink()
        child = _child(ipc_root, "long-lived")
        _wait_marker(ipc_root, "started", child)
        _wait_marker(ipc_root, "questdb_imported", child)
        _wait_marker(ipc_root, "waiting", child)
        long_lived_pid = child.pid
        assert child.poll() is None
        stdout, stderr = child.communicate("EXIT\n", timeout=10)
        assert child.returncode == 0, (stdout, stderr)
        assert long_lived_pid > 0
        assert [event["event"] for event in _child_events(stdout)] == [
            "started",
            "questdb_imported",
            "waiting",
            "exiting",
        ]

        for marker in ipc_root.glob("*.json"):
            marker.unlink()
        server = _Server(server_root)
        server.start()
        table = f"sf_spawn_diagnostic_{uuid4().hex}"
        primer_id = f"primer-{uuid4().hex}"
        timestamp = 1_700_000_000_000_000_000
        sf_dir = (ipc_root / f"sf-{uuid4().hex}").resolve()
        sf_dir.mkdir()
        _create_table(server.connection, table)
        (ipc_root / "scenario.json").write_text(
            json.dumps(
                {
                    "connection": server.connection,
                    "sf_dir": str(sf_dir),
                    "sender_id": f"sender-{uuid4().hex}",
                    "table": table,
                    "primer_id": primer_id,
                    "timestamp": timestamp,
                }
            ),
            encoding="utf-8",
        )
        child = _child(ipc_root, "producer")
        _wait_marker(ipc_root, "started", child)
        _wait_marker(ipc_root, "questdb_imported", child)
        _wait_marker(ipc_root, "connected", child)
        ready = _wait_marker(ipc_root, "ready", child, timeout=_WAIT_SECONDS)
        assert ready["primer_fsn"] is not None
        assert _wait_count(server.connection, table, primer_id)
        (ipc_root / "exit.json").write_text("{}", encoding="utf-8")
        stdout, stderr = child.communicate(timeout=15)
        assert child.returncode == 0, (stdout, stderr)
        assert [event["event"] for event in _child_events(stdout)] == [
            "started",
            "questdb_imported",
            "connected",
            "ready",
        ]
        child = None
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            child.communicate(timeout=10)
        if server is not None:
            server.stop()
        shutil.rmtree(ipc_root, ignore_errors=True)
        shutil.rmtree(server_root, ignore_errors=True)


def test_raw_questdb_500_sf_process_restart_isolation(tmp_path: Path) -> None:
    assert _EXE.exists()
    root = (tmp_path / f"qdb-sf-ipc-{uuid4().hex}").resolve()
    server_root = (tmp_path / f"qdb-sf-server-{uuid4().hex}").resolve()
    root.mkdir()
    _write_child(root)
    server = None
    try:
        server = _Server(server_root)
        server.start()
        healthy_table, healthy_id = f"sf_iso_{uuid4().hex}", f"healthy-{uuid4().hex}"
        _create_table(server.connection, healthy_table)
        db = questdb.connect(
            server.connection,
            sf_dir=root / "healthy-sf",
            sender_id=f"healthy-{uuid4().hex}",
            sf_durability="memory",
            auto_flush=False,
        )
        sender = db.sender()
        sender.row(
            healthy_table,
            columns={"id": healthy_id, "value": "healthy"},
            at=questdb.TimestampNanos(1_700_000_000_000_000_000),
        )
        fsn = sender.flush_and_get_fsn()
        healthy = sender.await_acked_fsn(fsn, timeout_millis=500) and _wait_count(
            server.connection, healthy_table, healthy_id
        )
        sender.close(flush=False)
        db.close()
        same_table, same_id = f"sf_iso_{uuid4().hex}", f"same-{uuid4().hex}"
        _create_table(server.connection, same_table)
        same_db = questdb.connect(
            server.connection,
            sf_dir=root / "same-sf",
            sender_id=f"same-{uuid4().hex}",
            sf_durability="memory",
            auto_flush=False,
        )
        same_sender = same_db.sender()
        server.stop()
        assert not _port_open(server.ports["http"])
        same_sender.row(
            same_table,
            columns={"id": same_id, "value": "same-process"},
            at=questdb.TimestampNanos(1_700_000_000_000_000_000),
        )
        same_fsn = same_sender.flush_and_get_fsn()
        server.start()
        same = same_fsn is not None and _wait_count(
            server.connection, same_table, same_id
        )
        same_sender.close(flush=False)
        same_db.close()
        graceful = _restart_case(server, root, "graceful", True)
        crash = _restart_case(server, root, "crash", False)
        orphan: dict[str, Any] | None = None
        if not graceful["recovered"] or not crash["recovered"]:
            orphan = _restart_case(server, root, "orphan", True, drain_orphans=True)
        evidence = {
            "healthy": healthy,
            "same_process": same,
            "graceful": graceful,
            "crash": crash,
            "orphan": None if orphan is None else orphan["recovered"],
        }
        print(json.dumps(evidence, sort_keys=True))
        assert healthy and same and graceful["recovered"] and crash["recovered"], (
            json.dumps(evidence, sort_keys=True)
        )
    finally:
        if server is not None:
            server.stop()
        if root.exists():
            shutil.rmtree(root)
        if server_root.exists():
            shutil.rmtree(server_root)
