"""Shared data models for ShellSage.  No external dependencies."""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from enum import Enum


class Shell(str, Enum):
    BASH = "bash"
    POWERSHELL = "powershell"
    ZSH = "zsh"
    CMD = "cmd"
    UNKNOWN = "unknown"


class OS(str, Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


# Process-level cache: list-of-one so get_cached() can mutate it from a classmethod.
_ctx_cache: list[ShellContext | None] = [None]

@dataclass
class ShellContext:
    """Runtime environment snapshot captured once per session."""

    os: OS
    shell: Shell
    shell_version: str
    project_type: str  # "python" | "node" | "rust" | "go" | "dotnet" | "java" | "unknown"
    project_root: str

    @classmethod
    def detect(cls, project_root: str = ".") -> ShellContext:
        """Auto-detect the current runtime environment."""
        os_name = _detect_os()
        shell, shell_version = _detect_shell()
        project_type = _detect_project_type(project_root)
        return cls(
            os=os_name,
            shell=shell,
            shell_version=shell_version,
            project_type=project_type,
            project_root=project_root,
        )

    @classmethod
    def get_cached(cls, project_root: str = ".") -> "ShellContext":
        """Return a process-level cached context (avoids repeated subprocess spawns).

        Callers on hot paths (proxy, hooks) should prefer this over detect().
        Use detect() directly only when a fresh snapshot is required.
        """
        if _ctx_cache[0] is None:
            _ctx_cache[0] = cls.detect(project_root)
        return _ctx_cache[0]

    @property
    def needs_translation(self) -> bool:
        """True when the shell is PowerShell or CMD — bash syntax will fail."""
        return self.shell in (Shell.POWERSHELL, Shell.CMD)

    def context_key(self) -> str:
        """Stable string key for store lookups."""
        return f"{self.os.value}:{self.shell.value}:{self.project_type}"


@dataclass
class Translation:
    """A resolved bash → target-shell mapping."""

    original: str
    translated: str
    shell: Shell
    confidence: float
    source: str  # "qdrant" | "rules" | "passthrough"

    @property
    def was_changed(self) -> bool:
        return self.original.strip() != self.translated.strip()


@dataclass
class CommandOutcome:
    """Result of running a translated command, persisted to local SQLite memory."""

    original: str
    translated: str
    shell: Shell
    os: OS
    project_type: str
    exit_code: int
    error_snippet: str = ""  # first 300 chars of stderr if failed

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


# ── private helpers ───────────────────────────────────────────────────────────


def _detect_os() -> OS:
    system = platform.system().lower()
    if system == "windows":
        return OS.WINDOWS
    if system == "darwin":
        return OS.MACOS
    if system == "linux":
        return OS.LINUX
    return OS.UNKNOWN


def _detect_shell() -> tuple[Shell, str]:
    """Return (Shell enum, version string)."""
    import os

    shell_env = os.environ.get("SHELL", "")
    if "zsh" in shell_env:
        return Shell.ZSH, _run_version("zsh --version")
    if "bash" in shell_env:
        return Shell.BASH, _run_version("bash --version")

    # Windows: prefer pwsh (7+) over powershell.exe (5.1)
    if platform.system().lower() == "windows":
        if _cmd_exists("pwsh"):
            return Shell.POWERSHELL, _run_version(
                "pwsh -NoProfile -Command $PSVersionTable.PSVersion.ToString()"
            )
        if _cmd_exists("powershell"):
            return Shell.POWERSHELL, _run_version(
                "powershell -NoProfile -Command $PSVersionTable.PSVersion.ToString()"
            )
        return Shell.POWERSHELL, "unknown"  # Windows always has PowerShell

    return Shell.BASH, _run_version("bash --version")


def _detect_project_type(root: str) -> str:
    import os

    markers: list[tuple[str, str]] = [
        ("package.json", "node"),
        ("pyproject.toml", "python"),
        ("setup.py", "python"),
        ("setup.cfg", "python"),
        ("Cargo.toml", "rust"),
        ("go.mod", "go"),
        ("pom.xml", "java"),
        ("build.gradle", "java"),
        ("*.csproj", "dotnet"),
        ("*.sln", "dotnet"),
    ]
    try:
        entries = os.listdir(root)
    except OSError:
        return "unknown"

    for marker, ptype in markers:
        if "*" in marker:
            ext = marker.replace("*", "")
            if any(f.endswith(ext) for f in entries if os.path.isfile(os.path.join(root, f))):
                return ptype
        elif marker in entries:
            return ptype
    return "unknown"


def _run_version(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
        return result.stdout.strip().split("\n")[0][:80]
    except Exception:
        return "unknown"


def _cmd_exists(cmd: str) -> bool:
    try:
        subprocess.run([cmd, "--version"], capture_output=True, timeout=2)
        return True
    except Exception:
        return False
