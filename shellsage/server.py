"""ShellSage MCP server — exposes 4 tools to Claude Code and GitHub Copilot."""

from __future__ import annotations

from shellsage.config import DB_PATH as _DEFAULT_DB
from shellsage.config import SERVER_HOST, SERVER_PORT
from shellsage.models import OS, CommandOutcome, Shell, ShellContext, Translation
from shellsage.translator import store_outcome, translate

try:
    from mcp.server.fastmcp import FastMCP  # type: ignore
except ImportError as e:
    raise ImportError(
        "MCP support requires the 'mcp' extra: pip install 'shellsage[mcp]'"
    ) from e

mcp = FastMCP("shellsage")


@mcp.tool()
def translate_command(command: str, project_root: str = ".") -> dict:
    """
    Translate a shell command for the current OS/shell environment.

    Returns the (possibly rewritten) command and metadata.
    Call this from a PreToolUse hook before executing any bash command.
    """
    ctx = ShellContext.detect(project_root=project_root)
    result: Translation = translate(command, ctx)
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
    Persist the outcome of a command execution back to local memory.

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
    stored = store_outcome(outcome)
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
    """Return collection sizes from local memory — useful for health checks."""
    try:
        from shellsage import store

        counts = store.get_stats()
        return {"status": "ok", "db": _DEFAULT_DB, "counts": counts}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def run(transport: str = "stdio", port: int = SERVER_PORT, host: str = SERVER_HOST) -> None:
    if transport == "http":
        _run_http(host, port)
    else:
        mcp.run()


def _run_http(host: str, port: int) -> None:
    try:
        import uvicorn  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError(
            "HTTP mode requires uvicorn: pip install 'shellsage[mcp]'"
        ) from None

    # FastMCP exposes an ASGI app; try the newer API first then fall back.
    try:
        app = mcp.streamable_http_app()  # type: ignore[attr-defined]
    except AttributeError:
        try:
            app = mcp.sse_app()  # type: ignore[attr-defined]
        except AttributeError:
            # Last resort: let FastMCP handle it via run() kwargs
            mcp.run(transport="sse")  # type: ignore[call-arg]
            return

    uvicorn.run(app, host=host, port=port, log_level="error")


if __name__ == "__main__":
    run()
