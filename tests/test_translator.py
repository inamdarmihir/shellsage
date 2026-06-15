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


@patch("shellsage.translator.store.query_translation")
@patch("shellsage.translator.embedder.embed")
def test_translate_qdrant_hit(mock_embed, mock_query):
    mock_embed.return_value = [0.1] * 384
    mock_query.return_value = [
        {
            "score": 0.95,
            "bash_cmd": "ls -la",
            "translated_cmd": "Get-ChildItem -Force",
            "shell": "powershell",
            "os": "windows",
            "project_type": "python",
            "confidence": 0.95,
            "hits": 3,
        }
    ]
    ctx = _ps_ctx()
    result = translate("ls -la", ctx)
    assert result.source == "qdrant"
    assert result.translated == "Get-ChildItem -Force"
    assert result.confidence == 0.95


# ── Qdrant miss → rule fallback ───────────────────────────────────────────────


@patch("shellsage.translator.store.query_translation")
@patch("shellsage.translator.embedder.embed")
def test_translate_qdrant_miss_falls_to_rules(mock_embed, mock_query):
    mock_embed.return_value = [0.1] * 384
    mock_query.return_value = []  # no hits
    ctx = _ps_ctx()
    result = translate("ls -la", ctx)
    assert result.source == "rules"
    assert "Get-ChildItem" in result.translated


# ── Qdrant unavailable → rule fallback ───────────────────────────────────────


@patch("shellsage.translator.store.query_translation", side_effect=ConnectionError("down"))
@patch("shellsage.translator.embedder.embed")
def test_translate_qdrant_unavailable_falls_to_rules(mock_embed, mock_query):
    mock_embed.return_value = [0.1] * 384
    ctx = _ps_ctx()
    result = translate("ls -la", ctx)
    # Should still succeed via rules — never raise
    assert result.translated is not None
    assert result.source in ("rules", "passthrough")


# ── unknown command passthrough ───────────────────────────────────────────────


@patch("shellsage.translator.store.query_translation")
@patch("shellsage.translator.embedder.embed")
def test_translate_unknown_command(mock_embed, mock_query):
    mock_embed.return_value = [0.1] * 384
    mock_query.return_value = []
    ctx = _ps_ctx()
    result = translate("some-exotic-tool --flag", ctx)
    assert result.source == "passthrough"
    assert result.translated == "some-exotic-tool --flag"


# ── store_outcome success ─────────────────────────────────────────────────────


@patch("shellsage.translator.store.upsert_translation")
@patch("shellsage.translator.embedder.embed")
def test_store_outcome_success(mock_embed, mock_upsert):
    mock_embed.return_value = [0.1] * 384
    outcome = CommandOutcome(
        original="ls -la",
        translated="Get-ChildItem -Force",
        shell=Shell.POWERSHELL,
        os=OS.WINDOWS,
        project_type="python",
        exit_code=0,
    )
    store_outcome(outcome)
    mock_upsert.assert_called_once()
    call_kwargs = mock_upsert.call_args.kwargs
    assert call_kwargs["bash_cmd"] == "ls -la"
    assert call_kwargs["translated_cmd"] == "Get-ChildItem -Force"
    assert call_kwargs["confidence"] == 0.99


# ── store_outcome failure ─────────────────────────────────────────────────────


@patch("shellsage.translator.store.upsert_failure")
@patch("shellsage.translator.embedder.embed")
def test_store_outcome_failure(mock_embed, mock_upsert_failure):
    mock_embed.return_value = [0.1] * 384
    outcome = CommandOutcome(
        original="ls -la",
        translated="ls -la",
        shell=Shell.POWERSHELL,
        os=OS.WINDOWS,
        project_type="python",
        exit_code=1,
        error_snippet="term 'ls' not recognized",
    )
    store_outcome(outcome)
    mock_upsert_failure.assert_called_once()


# ── store_outcome never raises ────────────────────────────────────────────────


@patch("shellsage.translator.store.upsert_translation", side_effect=Exception("boom"))
@patch("shellsage.translator.embedder.embed")
def test_store_outcome_swallows_errors(mock_embed, mock_upsert):
    mock_embed.return_value = [0.1] * 384
    outcome = CommandOutcome(
        original="ls",
        translated="Get-ChildItem",
        shell=Shell.POWERSHELL,
        os=OS.WINDOWS,
        project_type="unknown",
        exit_code=0,
    )
    # Must not raise — storage failures are non-fatal
    store_outcome(outcome)
