"""Tests for translator.py — Qdrant and embedder are mocked."""

from unittest.mock import patch

from shellsage.models import OS, CommandOutcome, Shell, ShellContext
from shellsage.translator import store_outcome, translate


def _ps_ctx() -> ShellContext:
    return ShellContext(
        os=OS.WINDOWS,
        shell=Shell.POWERSHELL,
        shell_version="7.4.0",
        project_type="python",
        project_root=".",
    )


def _bash_ctx() -> ShellContext:
    return ShellContext(
        os=OS.LINUX,
        shell=Shell.BASH,
        shell_version="5.2.0",
        project_type="python",
        project_root=".",
    )


# ── passthrough on bash ───────────────────────────────────────────────────────


def test_translate_passthrough_on_bash():
    ctx = _bash_ctx()
    result = translate("ls -la", ctx)
    assert result.source == "passthrough"
    assert result.translated == "ls -la"
    assert result.confidence == 1.0


# ── Qdrant hit ────────────────────────────────────────────────────────────────


@patch("shellsage.translator._query_qdrant")
def test_translate_qdrant_hit(mock_query):
    mock_query.return_value = [
        {
            "score": 0.95,
            "bash_cmd": "custom-find-latest",
            "translated_cmd": "Get-ChildItem | Sort-Object LastWriteTime -Descending | Select-Object -First 1",
            "shell": "powershell",
            "os": "windows",
            "project_type": "python",
            "confidence": 0.95,
            "hits": 3,
        }
    ]
    ctx = _ps_ctx()
    result = translate("custom-find-latest", ctx)
    assert result.source == "qdrant"
    assert result.translated.startswith("Get-ChildItem")
    assert result.confidence == 0.95


# ── Qdrant miss → rule fallback ───────────────────────────────────────────────


@patch("shellsage.translator._query_qdrant")
def test_translate_qdrant_miss_falls_to_rules(mock_query):
    mock_query.return_value = []  # no hits
    ctx = _ps_ctx()
    result = translate("ls -la", ctx)
    assert result.source == "rules"
    assert "Get-ChildItem" in result.translated
    mock_query.assert_not_called()


# ── Qdrant unavailable → rule fallback ───────────────────────────────────────


@patch("shellsage.translator._query_qdrant", side_effect=ConnectionError("down"))
def test_translate_qdrant_unavailable_falls_to_rules(mock_query):
    ctx = _ps_ctx()
    result = translate("ls -la", ctx)
    # Should still succeed via rules — never raise
    assert result.translated is not None
    assert result.source in ("rules", "passthrough")


# ── unknown command passthrough ───────────────────────────────────────────────


@patch("shellsage.translator._query_qdrant")
def test_translate_unknown_command(mock_query):
    mock_query.return_value = []
    ctx = _ps_ctx()
    result = translate("some-exotic-tool --flag", ctx)
    assert result.source == "passthrough"
    assert result.translated == "some-exotic-tool --flag"


@patch("shellsage.translator._query_qdrant", side_effect=ModuleNotFoundError("qdrant_client"))
def test_translate_without_vector_dependencies_still_works(mock_query):
    ctx = _ps_ctx()
    result = translate("some-exotic-tool --flag", ctx)
    assert result.source == "passthrough"
    assert result.translated == "some-exotic-tool --flag"


# ── store_outcome success ─────────────────────────────────────────────────────


@patch("shellsage.translator._store_to_qdrant")
def test_store_outcome_success(mock_store):
    outcome = CommandOutcome(
        original="ls -la",
        translated="Get-ChildItem -Force",
        shell=Shell.POWERSHELL,
        os=OS.WINDOWS,
        project_type="python",
        exit_code=0,
    )
    assert store_outcome(outcome) is True
    mock_store.assert_called_once_with(outcome, "http://localhost:6333")


# ── store_outcome failure ─────────────────────────────────────────────────────


@patch("shellsage.translator._store_to_qdrant")
def test_store_outcome_failure(mock_store):
    outcome = CommandOutcome(
        original="ls -la",
        translated="ls -la",
        shell=Shell.POWERSHELL,
        os=OS.WINDOWS,
        project_type="python",
        exit_code=1,
        error_snippet="term 'ls' not recognized",
    )
    assert store_outcome(outcome) is True
    mock_store.assert_called_once_with(outcome, "http://localhost:6333")


# ── store_outcome never raises ────────────────────────────────────────────────


@patch("shellsage.translator._store_to_qdrant", side_effect=Exception("boom"))
def test_store_outcome_swallows_errors(mock_store):
    outcome = CommandOutcome(
        original="ls",
        translated="Get-ChildItem",
        shell=Shell.POWERSHELL,
        os=OS.WINDOWS,
        project_type="unknown",
        exit_code=0,
    )
    # Must not raise — storage failures are non-fatal
    assert store_outcome(outcome) is False
