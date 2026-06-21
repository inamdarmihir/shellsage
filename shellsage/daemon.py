"""Background daemon management — start/stop/status for the HTTP MCP server."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _data_dir() -> Path:
    d = Path.home() / ".shellsage"
    d.mkdir(parents=True, exist_ok=True)
    return d


def pid_path() -> Path:
    return _data_dir() / "shellsage.pid"


def log_path() -> Path:
    return _data_dir() / "shellsage.log"


def _read_pid() -> int | None:
    p = pid_path()
    if not p.exists():
        return None
    try:
        return int(p.read_text().strip())
    except (ValueError, OSError):
        return None


def _is_running(pid: int) -> bool:
    try:
        if sys.platform == "win32":
            import ctypes
            PROCESS_QUERY_INFORMATION = 0x0400
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
            if not handle:
                return False
            # Check if process has exited
            import ctypes.wintypes
            exit_code = ctypes.wintypes.DWORD()
            ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(handle)
            return exit_code.value == 259  # STILL_ACTIVE
        else:
            import os
            os.kill(pid, 0)
            return True
    except (OSError, ProcessLookupError, AttributeError):
        return False


def get_status() -> dict:
    pid = _read_pid()
    if pid is None:
        return {"running": False, "pid": None}
    if _is_running(pid):
        return {"running": True, "pid": pid}
    # Stale PID file
    pid_path().unlink(missing_ok=True)
    return {"running": False, "pid": None}


def start_daemon(port: int = 7842, host: str = "127.0.0.1") -> dict:
    """Launch the MCP server as a detached background process."""
    status = get_status()
    if status["running"]:
        return {"started": False, "reason": "already_running", "pid": status["pid"]}

    cmd = [sys.executable, "-m", "shellsage", "mcp", "--http", "--port", str(port), "--host", host]

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

    pid_path().write_text(str(proc.pid))
    return {"started": True, "pid": proc.pid, "port": port, "host": host}


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
        pid_path().unlink(missing_ok=True)
        return {"stopped": True, "pid": pid}
    except Exception as exc:
        return {"stopped": False, "reason": str(exc)}
