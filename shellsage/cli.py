"""ShellSage CLI — shellsage setup | init | translate | stats | replay | mcp | start | stop | status | hooks"""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.table import Table

from shellsage.config import DB_PATH as _DEFAULT_DB
from shellsage.config import DEFAULT_SEED_LIMIT, SEED_CONFIDENCE, SERVER_HOST, SERVER_PORT

console = Console()


@click.group()
@click.version_option(package_name="shellsage")
def main() -> None:
    """ShellSage — shell translation layer with local SQLite memory."""


# ── setup wizard ──────────────────────────────────────────────────────────────


@main.command()
@click.option("--port", default=SERVER_PORT, show_default=True, envvar="SHELLSAGE_PORT")
@click.option("--host", default=SERVER_HOST, show_default=True, envvar="SHELLSAGE_HOST")
def setup(port: int, host: str) -> None:
    """Interactive one-command install wizard."""
    from shellsage.setup_wizard import run_wizard
    run_wizard(port=port, host=host)


# ── init (seed the DB) ────────────────────────────────────────────────────────


@main.command()
@click.option("--all", "load_all", is_flag=True, help="Load the complete seed corpus.")
@click.option(
    "--limit",
    type=click.IntRange(min=1),
    default=DEFAULT_SEED_LIMIT,
    show_default=True,
    envvar="SHELLSAGE_SEED_LIMIT",
)
@click.option("--db-path", default=_DEFAULT_DB, show_default=True, envvar="SHELLSAGE_DB_PATH")
def init(load_all: bool, limit: int, db_path: str) -> None:
    """Initialise the local database and load seed translations."""
    from shellsage import store
    from shellsage.seed import SEED_TRANSLATIONS, select_seed_translations

    seeds = select_seed_translations(None if load_all else limit)

    console.print("[bold cyan]ShellSage init[/bold cyan]")
    console.print(
        f"Loading [bold]{len(seeds)}[/bold] seed examples "
        f"([dim]{len(SEED_TRANSLATIONS)} available; use --all for full set[/dim])"
    )

    store.ensure_tables(db_path)
    loaded = 0
    for seed in seeds:
        store.upsert_translation(
            bash_cmd=seed["bash"],
            translated_cmd=seed["ps"],
            shell="powershell",
            os_name="windows",
            project_type="unknown",
            confidence=SEED_CONFIDENCE,
            db_path=db_path,
        )
        loaded += 1

    counts = store.get_stats(db_path)
    console.print(f"  [green]OK[/green] {loaded} translations loaded  "
                  f"(total in DB: {counts['translations']})")
    console.print(f"\n[bold green]Ready.[/bold green]  Run setup wizard:")
    console.print("  [dim]shellsage setup[/dim]")


# ── translate (single command test) ──────────────────────────────────────────


@main.command()
@click.argument("command")
@click.option("--project-root", default=".", show_default=True)
@click.option("--db-path", default=_DEFAULT_DB, show_default=True, envvar="SHELLSAGE_DB_PATH")
@click.option("--json-out", is_flag=True, default=False)
def translate(command: str, project_root: str, db_path: str, json_out: bool) -> None:
    """Translate a single command and print the result."""
    from shellsage.models import ShellContext
    from shellsage.translator import translate as _translate

    ctx = ShellContext.detect(project_root=project_root)
    result = _translate(command, ctx, db_path=db_path)

    if json_out:
        click.echo(
            json.dumps(
                {
                    "original": result.original,
                    "translated": result.translated,
                    "changed": result.was_changed,
                    "confidence": round(result.confidence, 3),
                    "source": result.source,
                }
            )
        )
        return

    if result.was_changed:
        console.print(f"[yellow]original  :[/yellow]  {result.original}")
        console.print(f"[green]translated:[/green]  {result.translated}")
        console.print(f"[dim]source: {result.source}  confidence: {result.confidence:.2f}[/dim]")
    else:
        console.print(f"[dim]no translation needed[/dim]  {result.translated}")


# ── stats ─────────────────────────────────────────────────────────────────────


@main.command()
@click.option("--db-path", default=_DEFAULT_DB, show_default=True, envvar="SHELLSAGE_DB_PATH")
def stats(db_path: str) -> None:
    """Show local database counts."""
    try:
        from shellsage import store
        counts = store.get_stats(db_path)
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    table = Table(title="ShellSage - Local Memory", show_header=True)
    table.add_column("Table", style="cyan")
    table.add_column("Rows", justify="right", style="green")
    for name, count in counts.items():
        table.add_row(name, str(count))
    console.print(table)
    console.print(f"[dim]DB: {db_path}[/dim]")


# ── replay ────────────────────────────────────────────────────────────────────


@main.command()
@click.option("--limit", default=20, show_default=True)
@click.option("--db-path", default=_DEFAULT_DB, show_default=True, envvar="SHELLSAGE_DB_PATH")
def replay(limit: int, db_path: str) -> None:
    """Show recent failure patterns stored in local memory."""
    try:
        from shellsage import store
        failures = store.get_recent_failures(limit=limit, db_path=db_path)
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    if not failures:
        console.print("[dim]No failures recorded yet.[/dim]")
        return

    table = Table(title=f"Recent Failures (last {limit})", show_header=True)
    table.add_column("Shell", style="yellow")
    table.add_column("OS", style="cyan")
    table.add_column("Command", style="white")
    table.add_column("Error (truncated)", style="red")
    table.add_column("When", style="dim")

    for f in failures:
        table.add_row(
            f.get("shell", "?"),
            f.get("os_name", "?"),
            (f.get("command") or "")[:50],
            (f.get("error_text") or "")[:60],
            (f.get("created_at") or "")[:16],
        )
    console.print(table)


# ── MCP server ────────────────────────────────────────────────────────────────


@main.command()
@click.option("--http", "transport", flag_value="http", default=False,
              help="Run as HTTP/SSE server instead of stdio.")
@click.option("--port", default=SERVER_PORT, show_default=True, envvar="SHELLSAGE_PORT")
@click.option("--host", default=SERVER_HOST, show_default=True, envvar="SHELLSAGE_HOST")
def mcp(transport: str, port: int, host: str) -> None:
    """Start the MCP server (stdio by default; use --http for background service)."""
    try:
        from shellsage.server import run
    except ImportError:
        console.print("[red]MCP extra not installed.[/red]")
        console.print("Run:  pip install 'shellsage[mcp]'")
        sys.exit(1)
    run(transport=transport or "stdio", port=port, host=host)


# ── daemon: start / stop / status ────────────────────────────────────────────


@main.command()
@click.option("--port", default=SERVER_PORT, show_default=True, envvar="SHELLSAGE_PORT")
@click.option("--host", default=SERVER_HOST, show_default=True, envvar="SHELLSAGE_HOST")
def start(port: int, host: str) -> None:
    """Start the MCP server as a background daemon."""
    from shellsage.daemon import start_daemon

    result = start_daemon(port=port, host=host)
    if result.get("started"):
        console.print(
            f"[green]>[/green] ShellSage daemon started  "
            f"(PID {result['pid']} | http://{host}:{port}/sse)"
        )
        console.print(
            f"\nRegister with Claude Code:\n"
            f"  [dim]claude mcp add --transport sse shellsage http://{host}:{port}/sse[/dim]"
        )
    elif result.get("reason") == "already_running":
        console.print(
            f"[yellow]![/yellow] Already running  (PID {result.get('pid')})"
        )
    else:
        console.print(f"[red]X[/red] Could not start daemon: {result}")
        sys.exit(1)


@main.command()
def stop() -> None:
    """Stop the background daemon."""
    from shellsage.daemon import stop_daemon

    result = stop_daemon()
    if result.get("stopped"):
        console.print(f"[green]>[/green] Daemon stopped  (was PID {result.get('pid')})")
    elif result.get("reason") == "not_running":
        console.print("[dim]Daemon is not running.[/dim]")
    else:
        console.print(f"[red]X[/red] Could not stop daemon: {result.get('reason')}")
        sys.exit(1)


@main.command()
def status() -> None:
    """Show daemon and database status."""
    from shellsage.daemon import get_status, log_path

    daemon_status = get_status()

    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()

    if daemon_status["running"]:
        table.add_row("Daemon", f"[green]running[/green]  (PID {daemon_status['pid']})")
        table.add_row("MCP endpoint", f"http://{SERVER_HOST}:{SERVER_PORT}/sse")
    else:
        table.add_row("Daemon", "[red]stopped[/red]")
        table.add_row("", "[dim]Run: shellsage start[/dim]")

    try:
        from shellsage import store
        counts = store.get_stats()
        table.add_row("Translations", str(counts["translations"]))
        table.add_row("Failures", str(counts["failures"]))
    except Exception:
        table.add_row("DB", "[dim]not initialised - run: shellsage init[/dim]")

    table.add_row("DB path", _DEFAULT_DB)
    table.add_row("Log", str(log_path()))

    console.print(table)


# ── hooks ─────────────────────────────────────────────────────────────────────


@main.group()
def hooks() -> None:
    """Manage Claude Code hook scripts."""


@hooks.command("install")
@click.option("--hooks-dir", default=".claude", show_default=True)
def hooks_install(hooks_dir: str) -> None:
    """Write PreToolUse and PostToolUse hook scripts into .claude/hooks/."""
    import stat
    from pathlib import Path

    hooks_path = Path(hooks_dir) / "hooks"
    hooks_path.mkdir(parents=True, exist_ok=True)

    pre = hooks_path / "pre_tool_use.py"
    post = hooks_path / "post_tool_use.py"

    pre.write_text(_PRE_TOOL_USE_SCRIPT)
    post.write_text(_POST_TOOL_USE_SCRIPT)

    for p in (pre, post):
        p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    console.print(f"[green]>[/green] Hooks written to [cyan]{hooks_path}[/cyan]")
    console.print("\nAdd to [dim].claude/settings.json[/dim]:")
    console.print("""\
  {
    "hooks": {
      "PreToolUse":  [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/pre_tool_use.py"}]}],
      "PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/post_tool_use.py"}]}]
    }
  }
""")


_PRE_TOOL_USE_SCRIPT = '''\
#!/usr/bin/env python3
"""PreToolUse hook — translates bash commands before Claude Code executes them."""
import json, os, sys, tempfile

event = json.load(sys.stdin)
if event.get("tool_name") != "Bash":
    sys.exit(0)

command = event.get("tool_input", {}).get("command", "")
if not command:
    sys.exit(0)

try:
    from shellsage.models import ShellContext
    from shellsage.translator import translate

    ctx = ShellContext.detect()
    result = translate(command, ctx)
    if result.was_changed:
        cache_path = os.path.join(tempfile.gettempdir(), "shellsage_pending.json")
        try:
            with open(cache_path, "w") as fh:
                json.dump({"original": result.original, "translated": result.translated}, fh)
        except Exception:
            pass

        event["tool_input"]["command"] = result.translated
        print(json.dumps({
            "decision": "approve",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": event["tool_input"],
            },
        }))
        sys.exit(0)
except Exception:
    pass  # never block the agent

sys.exit(0)
'''

_POST_TOOL_USE_SCRIPT = '''\
#!/usr/bin/env python3
"""PostToolUse hook — stores command outcomes back to local memory."""
import json, os, sys, tempfile

event = json.load(sys.stdin)
if event.get("tool_name") != "Bash":
    sys.exit(0)

tool_input  = event.get("tool_input", {})
tool_output = event.get("tool_response", {})
command     = tool_input.get("command", "")
exit_code   = tool_output.get("exit_code", 0)
stderr      = tool_output.get("stderr", "")

if not command:
    sys.exit(0)

try:
    from shellsage.models import CommandOutcome, ShellContext
    from shellsage.translator import store_outcome

    ctx = ShellContext.detect()

    original   = command
    translated = command
    cache_path = os.path.join(tempfile.gettempdir(), "shellsage_pending.json")
    try:
        with open(cache_path) as fh:
            cached = json.load(fh)
        original   = cached.get("original", command)
        translated = cached.get("translated", command)
        os.remove(cache_path)
    except Exception:
        pass

    outcome = CommandOutcome(
        original=original,
        translated=translated,
        shell=ctx.shell,
        os=ctx.os,
        project_type=ctx.project_type,
        exit_code=int(exit_code),
        error_snippet=str(stderr)[:300],
    )
    store_outcome(outcome)
except Exception:
    pass

sys.exit(0)
'''
