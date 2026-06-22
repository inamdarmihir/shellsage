"""Background daemon management — start/stop/status for the HTTP MCP server."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
from pathlib import Path


def _data_dir() -> Path:
    d = Path.home() / ".shellsage"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _state_path() -> Path:
    return _data_dir() / "shellsage.json"


def log_path() -> Path:
    return _data_dir() / "shellsage.log"


# kept for callers that still import pid_path directly
def pid_path() -> Path:
    return _data_dir() / "shellsage.pid"


def _read_state() -> dict | None:
    p = _state_path()
    if not p.exists():
        # migrate legacy PID file
        old = _data_dir() / "shellsage.pid"
        if old.exists():
            try:
                pid = int(old.read_text().strip())
                return {"pid": pid, "port": 7842, "host": "127.0.0.1"}
            except (ValueError, OSError):
                pass
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def _is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Return True if something is actively listening on host:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except OSError:
            return False


def _find_available_port(start: int, host: str = "127.0.0.1") -> int:
    """Return the first free TCP port at or after *start*."""
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found in range {start}–{start + 19}")


def get_status() -> dict:
    state = _read_state()
    if state is None:
        return {"running": False, "pid": None, "port": None, "host": None}
    host = state.get("host", "127.0.0.1")
    port = state.get("port", 7842)
    pid = state.get("pid")
    if _is_port_open(host, port):
        return {"running": True, "pid": pid, "port": port, "host": host}
    # Stale state — clear it
    _state_path().unlink(missing_ok=True)
    return {"running": False, "pid": None, "port": None, "host": None}


def start_daemon(port: int = 7842, host: str = "127.0.0.1") -> dict:
    """Launch the MCP server as a detached background process.

    If *port* is already in use by something else (not ShellSage), the daemon
    will be started on the next free port.
    """
    status = get_status()
    if status["running"]:
        if status["port"] == port and status.get("host", "127.0.0.1") == host:
            return {
                "started": False,
                "reason": "already_running",
                "pid": status["pid"],
                "port": status["port"],
                "host": status["host"],
            }
        # Running on a different port/host — stop the old daemon and start fresh.
        stop_daemon()

    actual_port = _find_available_port(port, host)

    cmd = [
        sys.executable, "-m", "shellsage",
        "mcp", "--http", "--port", str(actual_port), "--host", host,
    ]

    log = open(log_path(), "a")
    kwargs: dict = {
        "stdout": log,
        "stderr": log,
        "stdin": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(cmd, **kwargs)
    log.close()

    state = {"pid": proc.pid, "port": actual_port, "host": host}
    _state_path().write_text(json.dumps(state))

    return {"started": True, "pid": proc.pid, "port": actual_port, "host": host}


def stop_daemon() -> dict:
    """Terminate the background MCP server."""
    status = get_status()
    if not status["running"]:
        return {"stopped": False, "reason": "not_running"}

    pid = status["pid"]
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                check=False,
            )
        else:
            import os
            import signal
            os.kill(pid, signal.SIGTERM)
        _state_path().unlink(missing_ok=True)
        return {"stopped": True, "pid": pid}
    except Exception as exc:
        return {"stopped": False, "reason": str(exc)}
