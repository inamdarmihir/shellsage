"""ShellSage MCP server — exposes 4 tools to Claude Code and GitHub Copilot."""

from __future__ import annotations

import os

from shellsage.models import OS, CommandOutcome, Shell, ShellContext, Translation
from shellsage.translator import store_outcome, translate

try:
    from mcp.server.fastmcp import FastMCP  # type: ignore
except ImportError as e:
    raise ImportError("MCP support requires the 'mcp' extra: pip install 'shellsage[mcp]'") from e

mcp = FastMCP("shellsage")

_QDRANT_URL = os.environ.get("SHELLSAGE_QDRANT_URL", "http://localhost:6333")


@mcp.tool()
def translate_command(command: str, project_root: str = ".") -> dict:
    """
    Translate a shell command for the current OS/shell environment.

    Returns the (possibly rewritten) command and metadata.
    Call this from a PreToolUse hook before executing any bash command.
    """
    ctx = ShellContext.detect(project_root=project_root)
    result: Translation = translate(command, ctx, qdrant_url=_QDRANT_URL)
    return {
        "original": result.original,
        "translated": result.translated,
        "changed": result.was_changed,
        "confidence": round(result.confidence, 3),
        "source": result.source,
        "shell": ctx.shell.value,
        "os": ctx.os.value,
    }


@mcp.tool()
def store_command_result(
    original: str,
    translated: str,
    shell: str,
    os_name: str,
    project_type: str,
    exit_code: int,
    error_snippet: str = "",
) -> dict:
    """
    Persist the outcome of a command execution back to Qdrant.

    Call this from a PostToolUse hook after every bash command runs.
    Successes reinforce translation mappings; failures enrich failure patterns.
    """
    outcome = CommandOutcome(
        original=original,
        translated=translated,
        shell=Shell(shell),
        os=OS(os_name),
        project_type=project_type,
        exit_code=exit_code,
        error_snippet=error_snippet[:300],
    )
    stored = store_outcome(outcome, qdrant_url=_QDRANT_URL)
    return {"stored": stored, "succeeded": outcome.succeeded}


@mcp.tool()
def get_shell_context(project_root: str = ".") -> dict:
    """Return the detected shell/OS context for the current machine."""
    ctx = ShellContext.detect(project_root=project_root)
    return {
        "os": ctx.os.value,
        "shell": ctx.shell.value,
        "shell_version": ctx.shell_version,
        "project_type": ctx.project_type,
        "needs_translation": ctx.needs_translation,
    }


@mcp.tool()
def get_stats() -> dict:
    """Return collection sizes from local Qdrant — useful for health checks."""
    try:
        from shellsage import store

        counts = store.get_collection_counts(url=_QDRANT_URL)
        return {"status": "ok", "collections": counts}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def run() -> None:
    mcp.run()


if __name__ == "__main__":
    run()
