"""Tests for data models — no Qdrant or network required."""

from shellsage.models import (
    OS,
    CommandOutcome,
    Shell,
    ShellContext,
    Translation,
    _detect_project_type,
)

# ── Translation ───────────────────────────────────────────────────────────────


def test_translation_was_changed_true():
    t = Translation(
        original="ls -la",
        translated="Get-ChildItem -Force",
        shell=Shell.POWERSHELL,
        confidence=0.95,
        source="seed",
    )
    assert t.was_changed is True


def test_translation_was_changed_false():
    t = Translation(
        original="git status",
        translated="git status",
        shell=Shell.BASH,
        confidence=1.0,
        source="passthrough",
    )
    assert t.was_changed is False


def test_translation_whitespace_ignored():
    t = Translation(
        original="  ls  ",
        translated="  ls  ",
        shell=Shell.BASH,
        confidence=1.0,
        source="passthrough",
    )
    assert t.was_changed is False


# ── CommandOutcome ────────────────────────────────────────────────────────────


def test_outcome_succeeded():
    o = CommandOutcome(
        original="ls",
        translated="Get-ChildItem",
        shell=Shell.POWERSHELL,
        os=OS.WINDOWS,
        project_type="python",
        exit_code=0,
    )
    assert o.succeeded is True


def test_outcome_failed():
    o = CommandOutcome(
        original="ls -la",
        translated="ls -la",
        shell=Shell.POWERSHELL,
        os=OS.WINDOWS,
        project_type="unknown",
        exit_code=1,
        error_snippet="ls : The term 'ls' is not recognized",
    )
    assert o.succeeded is False


def test_outcome_default_error_snippet():
    o = CommandOutcome(
        original="pwd",
        translated="Get-Location",
        shell=Shell.POWERSHELL,
        os=OS.WINDOWS,
        project_type="node",
        exit_code=0,
    )
    assert o.error_snippet == ""


# ── ShellContext ──────────────────────────────────────────────────────────────


def test_needs_translation_powershell():
    ctx = ShellContext(
        os=OS.WINDOWS,
        shell=Shell.POWERSHELL,
        shell_version="7.4.0",
        project_type="python",
        project_root=".",
    )
    assert ctx.needs_translation is True


def test_needs_translation_bash():
    ctx = ShellContext(
        os=OS.LINUX,
        shell=Shell.BASH,
        shell_version="5.2.0",
        project_type="python",
        project_root=".",
    )
    assert ctx.needs_translation is False


def test_needs_translation_cmd():
    ctx = ShellContext(
        os=OS.WINDOWS,
        shell=Shell.CMD,
        shell_version="unknown",
        project_type="unknown",
        project_root=".",
    )
    assert ctx.needs_translation is True


def test_context_key_format():
    ctx = ShellContext(
        os=OS.WINDOWS,
        shell=Shell.POWERSHELL,
        shell_version="7.4.0",
        project_type="node",
        project_root=".",
    )
    key = ctx.context_key()
    assert "windows" in key
    assert "powershell" in key
    assert "node" in key


# ── project type detection ────────────────────────────────────────────────────


def test_detect_project_type_python(tmp_path):
    (tmp_path / "pyproject.toml").touch()
    assert _detect_project_type(str(tmp_path)) == "python"


def test_detect_project_type_node(tmp_path):
    (tmp_path / "package.json").touch()
    assert _detect_project_type(str(tmp_path)) == "node"


def test_detect_project_type_rust(tmp_path):
    (tmp_path / "Cargo.toml").touch()
    assert _detect_project_type(str(tmp_path)) == "rust"


def test_detect_project_type_go(tmp_path):
    (tmp_path / "go.mod").touch()
    assert _detect_project_type(str(tmp_path)) == "go"


def test_detect_project_type_unknown(tmp_path):
    assert _detect_project_type(str(tmp_path)) == "unknown"


# ── Shell enum ────────────────────────────────────────────────────────────────


def test_shell_enum_values():
    assert Shell.BASH.value == "bash"
    assert Shell.POWERSHELL.value == "powershell"
    assert Shell.ZSH.value == "zsh"
    assert Shell.CMD.value == "cmd"


def test_os_enum_values():
    assert OS.WINDOWS.value == "windows"
    assert OS.MACOS.value == "macos"
    assert OS.LINUX.value == "linux"
