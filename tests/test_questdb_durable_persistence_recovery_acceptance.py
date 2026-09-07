"""Opt-in recovery acceptance for the merged QuestDB SF persistence seam."""

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

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.durable_persistence import PersistenceStatus
from live15_quant_v2.data.storage.durable_persistence.questdb_sf import (
    QuestDBSFDurablePersistence,
)

_RUN_ACCEPTANCE = os.getenv("LIVE15_RUN_DURABLE_PERSISTENCE_RECOVERY_ACCEPTANCE") == "1"
_QUESTDB_EXE = Path(r"D:\LIVE15_V2_RUNTIME\questdb\dist\10.0.1\bin\questdb.exe")
_POLL_SECONDS = 30

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _RUN_ACCEPTANCE,
        reason="set LIVE15_RUN_DURABLE_PERSISTENCE_RECOVERY_ACCEPTANCE=1 to run",
    ),
]


def _free_ports() -> dict[str, int]:
    sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(4)]
    try:
        for listener in sockets:
            listener.bind(("127.0.0.1", 0))
        return dict(
            zip(
                ("http", "pg", "min_http", "ilp"), (s.getsockname()[1] for s in sockets)
            )
        )
    finally:
        for listener in sockets:
            listener.close()


class _TaskQuestDB:
    """One task-owned foreground server, never the canonical service."""

    def __init__(self, root: Path, ports: dict[str, int]) -> None:
        self.root = root
        self.ports = ports
        self.process: subprocess.Popen[bytes] | None = None
        self._server_pid: int | None = None
        self._log_file: Any | None = None
        self._log_path: Path | None = None
        self.start_count = 0
        self.stop_count = 0

    @property
    def connection_string(self) -> str:
        return f"ws::addr=127.0.0.1:{self.ports['http']};"

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
        self._log_path = self.root / f"questdb-{self.start_count}.log"
        self._log_file = self._log_path.open("wb")
        self.process = subprocess.Popen(
            [_QUESTDB_EXE, "-d", str(self.root)],
            cwd=self.root,
            stdout=self._log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        self.start_count += 1
        self.wait_ready()

    def wait_ready(self) -> None:
        assert self.process is not None
        deadline = time.monotonic() + _POLL_SECONDS
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self._log_file.close()
                self._log_file = None
                output = self._log_path.read_text(encoding="utf-8", errors="replace")
                raise AssertionError(
                    f"task-owned QuestDB exited before becoming available: {output}"
                )
            try:
                with urlopen(
                    f"http://127.0.0.1:{self.ports['min_http']}/status", timeout=1
                ) as response:
                    assert response.status == 200
                    assert b"Healthy" in response.read()
                database = questdb.connect(self.connection_string)
                database.close()
                self._server_pid = _listening_process_id(self.ports["http"])
                assert self._server_pid is not None
                assert (self.root / "conf" / "server.conf").exists()
                return
            except (OSError, questdb.QuestDBError, AssertionError):
                time.sleep(0.1)
        raise AssertionError("task-owned QuestDB did not become available")

    def stop(self) -> None:
        if self.process is None:
            return
        try:
            self.process.send_signal(signal.CTRL_BREAK_EVENT)
        except OSError:
            pass
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and _port_open(self.ports["http"]):
            time.sleep(0.1)
        if _port_open(self.ports["http"]):
            if self._server_pid is None:
                self._server_pid = _listening_process_id(self.ports["http"])
            assert self._server_pid is not None
            subprocess.run(
                ["taskkill.exe", "/PID", str(self._server_pid), "/T", "/F"],
                check=True,
                capture_output=True,
            )
        if self.process.poll() is None:
            subprocess.run(
                ["taskkill.exe", "/PID", str(self.process.pid), "/T", "/F"],
                check=True,
                capture_output=True,
            )
        try:
            self.process.wait(timeout=15)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("task-owned QuestDB launcher did not exit") from error
        self.process = None
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None
        self.stop_count += 1
        assert not _port_open(self.ports["http"])
        self._server_pid = None


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


def _fact(label: str) -> CaptureFact:
    return CaptureFact(
        capture_id=f"acceptance-{label}-{uuid4().hex}",
        asset=AssetId.BTC,
        provider="kalshi",
        source_id="KXBTC15M-TICKER",
        channel="ticker",
        message_type="ticker",
        event_subtype=None,
        sid=123,
        seq=456,
        provider_timestamp=1_700_000_000_000_000_001,
        received_timestamp=1_700_000_000_000_000_002 + int(label != "primer"),
        schema_version="market-ingress/v1",
        payload=json.dumps({"scenario": label, "price": "100"}, ensure_ascii=False),
    )


def _create_table(connection_string: str, table_name: str) -> None:
    database = questdb.connect(connection_string)
    try:
        database.execute(
            f"CREATE TABLE {table_name} ("
            "capture_id VARCHAR, asset SYMBOL, provider SYMBOL, source_id VARCHAR, "
            "channel SYMBOL, message_type VARCHAR, event_subtype VARCHAR, "
            "sid LONG, seq LONG, provider_timestamp TIMESTAMP_NS, "
            "schema_version VARCHAR, payload VARCHAR, received_timestamp TIMESTAMP_NS"
            ") TIMESTAMP(received_timestamp) PARTITION BY DAY WAL "
            "DEDUP UPSERT KEYS(received_timestamp, capture_id)"
        )
    finally:
        database.close()


def _row(
    connection_string: str, table_name: str, fact: CaptureFact
) -> dict[str, object] | None:
    database = questdb.connect(connection_string)
    try:
        rows = (
            database.query(
                f"SELECT capture_id, received_timestamp, payload FROM {table_name} "
                f"WHERE capture_id = '{fact.capture_id}'"
            )
            .to_pandas()
            .to_dict(orient="records")
        )
        return rows[0] if rows else None
    finally:
        database.close()


def _wait_for_exact_row(
    connection_string: str, table_name: str, fact: CaptureFact
) -> dict[str, object]:
    deadline = time.monotonic() + _POLL_SECONDS
    while time.monotonic() < deadline:
        try:
            row = _row(connection_string, table_name, fact)
        except (OSError, questdb.QuestDBError):
            row = None
        if row is not None:
            return row
        time.sleep(0.1)
    database = questdb.connect(connection_string)
    try:
        observed = (
            database.query(
                f"SELECT capture_id, received_timestamp, payload FROM {table_name}"
            )
            .to_pandas()
            .to_dict(orient="records")
        )
    finally:
        database.close()
    raise AssertionError(
        f"SF did not recover {fact.capture_id}; observed physical rows={observed!r}"
    )


def _assert_exact_single_row(
    connection_string: str, table_name: str, fact: CaptureFact
) -> None:
    row = _wait_for_exact_row(connection_string, table_name, fact)
    assert row["capture_id"] == fact.capture_id
    assert row["received_timestamp"].value == fact.received_timestamp
    assert row["payload"] == fact.payload
    database = questdb.connect(connection_string)
    try:
        count = (
            database.query(
                f"SELECT count() AS row_count FROM {table_name} "
                f"WHERE capture_id = '{fact.capture_id}'"
            )
            .to_pandas()
            .to_dict(orient="records")[0]["row_count"]
        )
    finally:
        database.close()
    assert count == 1


def _wait_for_file(path: Path) -> dict[str, Any]:
    deadline = time.monotonic() + _POLL_SECONDS
    while time.monotonic() < deadline:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        time.sleep(0.05)
    raise AssertionError(f"child did not create coordination file {path.name}")


def _sf_inventory(sf_dir: Path) -> list[dict[str, int | str]]:
    """Record slot names and sizes only; never inspect persisted payloads."""
    if not sf_dir.exists():
        return []
    return [
        {
            "path": str(path.relative_to(sf_dir)),
            "size": path.stat().st_size,
        }
        for path in sorted(sf_dir.rglob("*"))
        if path.is_file()
    ]


def _clear_child_coordination(root: Path) -> None:
    for name in (
        "ready.json",
        "publish.json",
        "published.json",
        "exit.json",
        "resumed.json",
        "resume-exit.json",
    ):
        (root / name).unlink(missing_ok=True)


def _write_child_program(path: Path) -> None:
    path.write_text(
        """import json
import os
import time
from pathlib import Path

import questdb

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.durable_persistence.questdb_sf import QuestDBSFDurablePersistence

root = Path(os.environ["LIVE15_ACCEPTANCE_CHILD_ROOT"])
scenario = json.loads((root / "scenario.json").read_text(encoding="utf-8"))
mode = scenario["mode"]

def fact(value):
    return CaptureFact(asset=AssetId.BTC, provider="kalshi", source_id="KXBTC15M-TICKER", channel="ticker", message_type="ticker", event_subtype=None, sid=123, seq=456, provider_timestamp=1_700_000_000_000_000_001, schema_version="market-ingress/v1", **value)

def raw_persist(database, value):
    capture_fact = fact(value)
    sender = database.sender()
    try:
        sender.row(scenario["table_name"], symbols={"asset": capture_fact.asset.value, "provider": capture_fact.provider, "channel": capture_fact.channel}, columns={"capture_id": capture_fact.capture_id, "source_id": capture_fact.source_id, "message_type": capture_fact.message_type, "event_subtype": capture_fact.event_subtype, "sid": capture_fact.sid, "seq": capture_fact.seq, "provider_timestamp": questdb.TimestampNanos(capture_fact.provider_timestamp), "schema_version": capture_fact.schema_version, "payload": capture_fact.payload}, at=questdb.TimestampNanos(capture_fact.received_timestamp))
        fsn = sender.flush_and_get_fsn()
        try:
            return "acknowledged_ok" if sender.await_acked_fsn(fsn, timeout_millis=500) else "persisted_pending"
        except (OSError, questdb.QuestDBError):
            return "persisted_pending"
    finally:
        sender.close(flush=False)

if mode in {"publish_after_primer", "raw_publish_after_primer"}:
    persistence = None
    database = None
    if mode == "publish_after_primer":
        persistence = QuestDBSFDurablePersistence(connection_string=scenario["connection_string"], table_name=scenario["table_name"], sf_dir=scenario["sf_dir"], sender_id=scenario["sender_id"], acknowledgement_timeout_millis=500)
        publish = lambda value: persistence.persist(fact(value)).status.value
    else:
        database = questdb.connect(scenario["connection_string"], sf_dir=scenario["sf_dir"], sender_id=scenario["sender_id"], sf_durability="memory", auto_flush=False)
        publish = lambda value: raw_persist(database, value)
    try:
        (root / "ready.json").write_text(json.dumps({"status": publish(scenario["primer_fact"])}), encoding="utf-8")
        while not (root / "publish.json").exists():
            time.sleep(0.02)
        (root / "published.json").write_text(json.dumps({"status": publish(scenario["pending_fact"])}), encoding="utf-8")
        while not (root / "exit.json").exists():
            time.sleep(0.02)
    finally:
        if persistence is not None:
            persistence.close()
        if database is not None:
            database.close()
elif mode in {"resume", "raw_resume"}:
    database = questdb.connect(scenario["connection_string"], sf_dir=scenario["sf_dir"], sender_id=scenario["sender_id"], sf_durability="memory", auto_flush=False, drain_orphans=scenario.get("drain_orphans", False))
    sender = None
    try:
        sender = database.sender()
        (root / "resumed.json").write_text("{}", encoding="utf-8")
        while not (root / "resume-exit.json").exists():
            time.sleep(0.02)
    finally:
        if sender is not None:
            sender.close(flush=False)
        database.close()
""",
        encoding="utf-8",
    )


def _child_process(root: Path) -> subprocess.Popen[bytes]:
    environment = os.environ.copy()
    environment["LIVE15_ACCEPTANCE_CHILD_ROOT"] = str(root)
    environment["PYTHONPATH"] = str(Path.cwd() / "src")
    return subprocess.Popen(
        [sys.executable, str(root / "child.py")],
        cwd=Path.cwd(),
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=(root / "child.stderr.log").open("wb"),
    )


def _fact_data(fact: CaptureFact) -> dict[str, object]:
    return {
        "capture_id": fact.capture_id,
        "received_timestamp": fact.received_timestamp,
        "payload": fact.payload,
    }


def _write_production_child(path: Path) -> None:
    """Write a raw subprocess that exercises only the public adapter seam."""
    path.write_text(
        """import json
import os
import time
from pathlib import Path

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.durable_persistence.questdb_sf import QuestDBSFDurablePersistence

root = Path(os.environ["LIVE15_ACCEPTANCE_CHILD_ROOT"]).resolve()
scenario = json.loads((root / "scenario.json").read_text(encoding="utf-8"))

def marker(name, **payload):
    destination = root / f"{name}.json"
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    temporary.replace(destination)

def fact(value):
    return CaptureFact(asset=AssetId.BTC, provider="kalshi", source_id="KXBTC15M-TICKER", channel="ticker", message_type="ticker", event_subtype=None, sid=123, seq=456, provider_timestamp=1_700_000_000_000_000_001, schema_version="market-ingress/v1", **value)

def persistence():
    return QuestDBSFDurablePersistence(connection_string=scenario["connection_string"], table_name=scenario["table_name"], sf_dir=scenario["sf_dir"], sender_id=scenario["sender_id"], acknowledgement_timeout_millis=500)

if scenario["mode"] == "producer":
    adapter = persistence()
    marker("ready", status=adapter.persist(fact(scenario["primer_fact"])).status.value)
    while not (root / "publish.json").exists():
        time.sleep(.02)
    marker("published", status=adapter.persist(fact(scenario["pending_fact"])).status.value)
    while not (root / "exit.json").exists():
        time.sleep(.02)
    adapter.close()
elif scenario["mode"] == "recovery":
    adapter = persistence()
    marker("recovery", status=adapter.persist(fact(scenario["trigger_fact"])).status.value)
    while not (root / "exit.json").exists():
        time.sleep(.02)
    adapter.close()
else:
    raise RuntimeError(f"unsupported mode: {scenario['mode']}")
""",
        encoding="utf-8",
    )


def _production_child(root: Path) -> subprocess.Popen[str]:
    child_path = (root / "production_child.py").resolve()
    assert child_path.is_file()
    environment = os.environ | {
        "LIVE15_ACCEPTANCE_CHILD_ROOT": str(root.resolve()),
        "PYTHONPATH": str((Path.cwd() / "src").resolve()),
        "PYTHONUNBUFFERED": "1",
    }
    return subprocess.Popen(
        [sys.executable, "-u", str(child_path)],
        cwd=Path.cwd().resolve(),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )


def _wait_for_child_marker(
    root: Path, name: str, child: subprocess.Popen[str]
) -> dict[str, Any]:
    path = root / f"{name}.json"
    deadline = time.monotonic() + _POLL_SECONDS
    while time.monotonic() < deadline:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        if child.poll() is not None:
            stdout, stderr = child.communicate()
            raise AssertionError(
                f"child exited before {name}: exit={child.returncode}; "
                f"stdout={stdout!r}; stderr={stderr!r}"
            )
        time.sleep(0.02)
    if child.poll() is None:
        child.terminate()
    stdout, stderr = child.communicate(timeout=15)
    raise AssertionError(
        f"child timed out before {name}: exit={child.returncode}; "
        f"stdout={stdout!r}; stderr={stderr!r}"
    )


def _clear_production_child_coordination(root: Path) -> None:
    for name in ("ready.json", "publish.json", "published.json", "recovery.json", "exit.json"):
        (root / name).unlink(missing_ok=True)


def _has_dirty_sfa(sf_dir: Path) -> bool:
    return any(path.stat().st_size > 0 for path in sf_dir.rglob("*.sfa"))


def _production_restart_case(
    server: _TaskQuestDB, ipc_root: Path, name: str, graceful: bool
) -> dict[str, object]:
    table_name = f"p_{name[0]}_{uuid4().hex}"
    sf_dir = (ipc_root / f"s-{name[0]}-{uuid4().hex}").resolve()
    sender_id = f"p-{name[0]}-{uuid4().hex}"
    primer = _fact(f"{name}-primer")
    pending = _fact(f"{name}-pending")
    trigger = _fact(f"{name}-trigger")
    sf_dir.mkdir()
    _create_table(server.connection_string, table_name)
    _clear_production_child_coordination(ipc_root)
    (ipc_root / "scenario.json").write_text(
        json.dumps(
            {
                "mode": "producer",
                "connection_string": server.connection_string,
                "table_name": table_name,
                "sf_dir": str(sf_dir),
                "sender_id": sender_id,
                "primer_fact": _fact_data(primer),
                "pending_fact": _fact_data(pending),
            }
        ),
        encoding="utf-8",
    )
    child = _production_child(ipc_root)
    try:
        assert _wait_for_child_marker(ipc_root, "ready", child)["status"] == "acknowledged_ok"
        _assert_exact_single_row(server.connection_string, table_name, primer)
        server.stop()
        assert not _port_open(server.ports["http"])
        (ipc_root / "publish.json").write_text("{}", encoding="utf-8")
        published = _wait_for_child_marker(ipc_root, "published", child)
        assert published["status"] == "persisted_pending"
        dirty_before = _has_dirty_sfa(sf_dir)
        assert dirty_before
        if graceful:
            (ipc_root / "exit.json").write_text("{}", encoding="utf-8")
            stdout, stderr = child.communicate(timeout=15)
            assert child.returncode == 0, (stdout, stderr)
        else:
            child.kill()
            stdout, stderr = child.communicate(timeout=15)
            assert child.returncode is not None
        child = None
        dirty_after = _has_dirty_sfa(sf_dir)
        assert dirty_after
        server.start()
        _clear_production_child_coordination(ipc_root)
        (ipc_root / "scenario.json").write_text(
            json.dumps(
                {
                    "mode": "recovery",
                    "connection_string": server.connection_string,
                    "table_name": table_name,
                    "sf_dir": str(sf_dir),
                    "sender_id": sender_id,
                    "trigger_fact": _fact_data(trigger),
                }
            ),
            encoding="utf-8",
        )
        recovery = _production_child(ipc_root)
        try:
            assert _wait_for_child_marker(ipc_root, "recovery", recovery)["status"] == "acknowledged_ok"
            _assert_exact_single_row(server.connection_string, table_name, pending)
            _assert_exact_single_row(server.connection_string, table_name, trigger)
            (ipc_root / "exit.json").write_text("{}", encoding="utf-8")
            recovery_stdout, recovery_stderr = recovery.communicate(timeout=15)
            assert recovery.returncode == 0, (recovery_stdout, recovery_stderr)
        finally:
            if recovery.poll() is None:
                recovery.terminate()
                recovery.communicate(timeout=15)
        return {
            "pending": pending,
            "trigger": trigger,
            "target_status": published["status"],
            "producer_exit_code": child.returncode if child is not None else 0 if graceful else 1,
            "dirty_before": dirty_before,
            "dirty_after": dirty_after,
        }
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            child.communicate(timeout=15)


def test_questdb_sf_final_production_adapter_failure_mode_acceptance(
    tmp_path: Path,
) -> None:
    """The real adapter preserves pending facts across server and process outages."""
    assert _QUESTDB_EXE.is_file()
    task_root = (tmp_path / "q").resolve()
    server_root = task_root / "server"
    ipc_root = task_root / "ipc"
    ipc_root.mkdir(parents=True)
    server = _TaskQuestDB(server_root, _free_ports())
    direct: QuestDBSFDurablePersistence | None = None
    try:
        server.write_config()
        server.start()
        _write_production_child(ipc_root / "production_child.py")

        healthy_table = f"p_h_{uuid4().hex}"
        healthy_fact = _fact("healthy")
        healthy_sf = ipc_root / f"s-h-{uuid4().hex}"
        healthy_sf.mkdir()
        _create_table(server.connection_string, healthy_table)
        direct = QuestDBSFDurablePersistence(
            connection_string=server.connection_string,
            table_name=healthy_table,
            sf_dir=healthy_sf,
            sender_id=f"p-h-{uuid4().hex}",
            acknowledgement_timeout_millis=500,
        )
        assert direct.persist(healthy_fact).status is PersistenceStatus.ACKNOWLEDGED_OK
        _assert_exact_single_row(server.connection_string, healthy_table, healthy_fact)
        direct.close()
        direct = None

        outage_table = f"p_o_{uuid4().hex}"
        outage_fact = _fact("outage")
        outage_sf = ipc_root / f"s-o-{uuid4().hex}"
        outage_sf.mkdir()
        _create_table(server.connection_string, outage_table)
        direct = QuestDBSFDurablePersistence(
            connection_string=server.connection_string,
            table_name=outage_table,
            sf_dir=outage_sf,
            sender_id=f"p-o-{uuid4().hex}",
            acknowledgement_timeout_millis=500,
        )
        assert direct.persist(_fact("outage-primer")).status is PersistenceStatus.ACKNOWLEDGED_OK
        server.stop()
        assert direct.persist(outage_fact).status is PersistenceStatus.PERSISTED_PENDING
        server.start()
        _assert_exact_single_row(server.connection_string, outage_table, outage_fact)
        direct.close()
        direct = None

        graceful = _production_restart_case(server, ipc_root, "graceful", True)
        crash = _production_restart_case(server, ipc_root, "crash", False)
        print(json.dumps({"graceful": graceful, "crash": crash}, default=str, sort_keys=True))
    finally:
        if direct is not None:
            direct.close()
        server.stop()
        shutil.rmtree(task_root, ignore_errors=True)
        assert not task_root.exists()


def test_task_owned_questdb_foreground_launcher_requires_no_service(
    tmp_path: Path,
) -> None:
    """The official executable starts an isolated foreground 10.0.1 server non-admin."""
    assert _QUESTDB_EXE.exists()
    assert "10.0.1" in str(_QUESTDB_EXE)
    task_root = tmp_path / f"durable-persistence-launcher-{uuid4().hex}"
    server = _TaskQuestDB(task_root, _free_ports())
    try:
        server.write_config()
        server.start()
        assert server.process is not None
        assert server.process.pid > 0
        assert _port_open(server.ports["http"])
    finally:
        server.stop()
        if task_root.exists():
            shutil.rmtree(task_root)
        assert not task_root.exists()


def test_questdb_sf_recovers_server_and_live15_process_outages(tmp_path: Path) -> None:
    """QuestDB SF alone recovers one once-published fact across each outage seam."""
    assert _QUESTDB_EXE.exists()
    task_root = tmp_path / f"durable-persistence-recovery-{uuid4().hex}"
    ports = _free_ports()
    server = _TaskQuestDB(task_root, ports)
    table_name = f"durable_persistence_recovery_{uuid4().hex}"
    sf_dir = task_root / "sf"
    sender_id = f"live15-recovery-{uuid4().hex}"
    raw_sf_dir = task_root / "raw-sf"
    raw_sender_id = f"raw-recovery-{uuid4().hex}"
    child: subprocess.Popen[bytes] | None = None
    direct_persistence: QuestDBSFDurablePersistence | None = None
    try:
        server.write_config()
        sf_dir.mkdir(parents=True)
        server.start()
        _create_table(server.connection_string, table_name)

        direct_persistence = QuestDBSFDurablePersistence(
            connection_string=server.connection_string,
            table_name=table_name,
            sf_dir=sf_dir,
            sender_id=sender_id,
            acknowledgement_timeout_millis=500,
        )
        primer_fact = _fact("primer")
        assert (
            direct_persistence.persist(primer_fact).status
            is PersistenceStatus.ACKNOWLEDGED_OK
        )
        _assert_exact_single_row(server.connection_string, table_name, primer_fact)

        outage_fact = _fact("outage")
        server.stop()
        assert not _port_open(ports["http"])
        assert (
            direct_persistence.persist(outage_fact).status
            is PersistenceStatus.PERSISTED_PENDING
        )
        server.start()
        _assert_exact_single_row(server.connection_string, table_name, outage_fact)
        direct_persistence.close()
        direct_persistence = None

        process_primer = _fact("process-primer")
        process_restart_fact = _fact("process-restart")
        _write_child_program(task_root / "child.py")
        _clear_child_coordination(task_root)
        (task_root / "scenario.json").write_text(
            json.dumps(
                {
                    "mode": "publish_after_primer",
                    "connection_string": server.connection_string,
                    "table_name": table_name,
                    "sf_dir": str(sf_dir),
                    "sender_id": sender_id,
                    "primer_fact": _fact_data(process_primer),
                    "pending_fact": _fact_data(process_restart_fact),
                }
            ),
            encoding="utf-8",
        )
        child = _child_process(task_root)
        assert _wait_for_file(task_root / "ready.json")["status"] == "acknowledged_ok"
        server.stop()
        (task_root / "publish.json").write_text("{}", encoding="utf-8")
        assert (
            _wait_for_file(task_root / "published.json")["status"]
            == "persisted_pending"
        )
        adapter_slots_after_publish = _sf_inventory(sf_dir)
        (task_root / "exit.json").write_text("{}", encoding="utf-8")
        assert child.wait(timeout=15) == 0
        child = None
        adapter_slots_after_exit = _sf_inventory(sf_dir)

        server.start()
        _clear_child_coordination(task_root)
        (task_root / "scenario.json").write_text(
            json.dumps(
                {
                    "mode": "resume",
                    "connection_string": server.connection_string,
                    "sf_dir": str(sf_dir),
                    "sender_id": sender_id,
                }
            ),
            encoding="utf-8",
        )
        child = _child_process(task_root)
        _wait_for_file(task_root / "resumed.json")
        try:
            _assert_exact_single_row(
                server.connection_string, table_name, process_restart_fact
            )
            adapter_recovered = True
        except AssertionError:
            adapter_recovered = False
        adapter_slots_after_resume = _sf_inventory(sf_dir)
        (task_root / "resume-exit.json").write_text("{}", encoding="utf-8")
        assert child.wait(timeout=15) == 0
        child = None

        raw_sf_dir.mkdir()
        raw_primer = _fact("raw-process-primer")
        raw_restart_fact = _fact("raw-process-restart")
        _clear_child_coordination(task_root)
        (task_root / "scenario.json").write_text(
            json.dumps(
                {
                    "mode": "raw_publish_after_primer",
                    "connection_string": server.connection_string,
                    "table_name": table_name,
                    "sf_dir": str(raw_sf_dir),
                    "sender_id": raw_sender_id,
                    "primer_fact": _fact_data(raw_primer),
                    "pending_fact": _fact_data(raw_restart_fact),
                }
            ),
            encoding="utf-8",
        )
        child = _child_process(task_root)
        assert _wait_for_file(task_root / "ready.json")["status"] == "acknowledged_ok"
        server.stop()
        (task_root / "publish.json").write_text("{}", encoding="utf-8")
        assert (
            _wait_for_file(task_root / "published.json")["status"]
            == "persisted_pending"
        )
        raw_slots_after_publish = _sf_inventory(raw_sf_dir)
        (task_root / "exit.json").write_text("{}", encoding="utf-8")
        assert child.wait(timeout=15) == 0
        child = None
        raw_slots_after_exit = _sf_inventory(raw_sf_dir)

        server.start()
        _clear_child_coordination(task_root)
        (task_root / "scenario.json").write_text(
            json.dumps(
                {
                    "mode": "raw_resume",
                    "connection_string": server.connection_string,
                    "sf_dir": str(raw_sf_dir),
                    "sender_id": raw_sender_id,
                }
            ),
            encoding="utf-8",
        )
        child = _child_process(task_root)
        _wait_for_file(task_root / "resumed.json")
        try:
            _assert_exact_single_row(
                server.connection_string, table_name, raw_restart_fact
            )
            raw_recovered = True
        except AssertionError:
            raw_recovered = False
        raw_slots_after_resume = _sf_inventory(raw_sf_dir)
        (task_root / "resume-exit.json").write_text("{}", encoding="utf-8")
        assert child.wait(timeout=15) == 0
        child = None

        _clear_child_coordination(task_root)
        (task_root / "scenario.json").write_text(
            json.dumps(
                {
                    "mode": "raw_resume",
                    "connection_string": server.connection_string,
                    "sf_dir": str(raw_sf_dir),
                    "sender_id": raw_sender_id,
                    "drain_orphans": True,
                }
            ),
            encoding="utf-8",
        )
        child = _child_process(task_root)
        _wait_for_file(task_root / "resumed.json")
        try:
            _assert_exact_single_row(
                server.connection_string, table_name, raw_restart_fact
            )
            raw_orphan_recovered = True
        except AssertionError:
            raw_orphan_recovered = False
        raw_slots_after_orphan_resume = _sf_inventory(raw_sf_dir)
        forensic_evidence = {
            "adapter_recovered": adapter_recovered,
            "adapter_slots_after_publish": adapter_slots_after_publish,
            "adapter_slots_after_exit": adapter_slots_after_exit,
            "adapter_slots_after_resume": adapter_slots_after_resume,
            "raw_recovered": raw_recovered,
            "raw_orphan_recovered": raw_orphan_recovered,
            "raw_slots_after_publish": raw_slots_after_publish,
            "raw_slots_after_exit": raw_slots_after_exit,
            "raw_slots_after_resume": raw_slots_after_resume,
            "raw_slots_after_orphan_resume": raw_slots_after_orphan_resume,
        }
        (task_root / "resume-exit.json").write_text("{}", encoding="utf-8")
        assert child.wait(timeout=15) == 0
        child = None
        assert all((adapter_recovered, raw_recovered, raw_orphan_recovered)), (
            json.dumps(forensic_evidence, sort_keys=True)
        )
        # Initial launch plus one intentional restart for each outage seam.
        assert server.start_count == 4
        assert server.stop_count == 3
    finally:
        if direct_persistence is not None:
            direct_persistence.close()
        if child is not None and child.poll() is None:
            child.terminate()
            child.wait(timeout=15)
        server.stop()
        if task_root.exists():
            shutil.rmtree(task_root)
        assert not task_root.exists()
