"""ShellSage CLI — shellsage init | translate | stats | replay | mcp"""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.version_option(package_name="shellsage")
def main() -> None:
    """ShellSage — shell translation layer backed by local Qdrant."""


@main.command()
@click.option("--qdrant-url", default="http://localhost:6333", show_default=True)
def init(qdrant_url: str) -> None:
    """Initialise Qdrant collections and load seed translations."""
    from shellsage import embedder, store
    from shellsage.seed import SEED_TRANSLATIONS

    console.print("[bold cyan]ShellSage init[/bold cyan]")

    # 1. Ensure collections exist
    with console.status("Creating Qdrant collections…"):
        try:
            store.ensure_collections(url=qdrant_url)
        except Exception as exc:
            console.print(f"[red]✗ Qdrant unreachable at {qdrant_url}[/red]")
            console.print(f"  {exc}")
            console.print("\nStart Qdrant with:  docker compose up -d")
            sys.exit(1)
    console.print("  [green]✓[/green] Collections ready")

    # 2. Load seed translations
    with console.status(f"Embedding {len(SEED_TRANSLATIONS)} seed translations…"):
        bash_cmds = [s["bash"] for s in SEED_TRANSLATIONS]
        vectors = embedder.embed_batch(bash_cmds)
        for seed, vec in zip(SEED_TRANSLATIONS, vectors, strict=False):
            store.upsert_translation(
                bash_cmd=seed["bash"],
                translated_cmd=seed["ps"],
                shell="powershell",
                os_name="windows",
                project_type="unknown",
                confidence=0.95,
                embedding=vec,
                url=qdrant_url,
            )
    console.print(f"  [green]✓[/green] {len(SEED_TRANSLATIONS)} seed translations loaded")

    console.print("\n[bold green]Ready.[/bold green]  Add to Claude Code:")
    console.print("  [dim]claude mcp add shellsage -- shellsage mcp[/dim]")
    console.print("\nAdd hooks to [dim].claude/settings.json[/dim]:  shellsage hooks install")


@main.command()
@click.argument("command")
@click.option("--project-root", default=".", show_default=True)
@click.option("--qdrant-url", default="http://localhost:6333", show_default=True)
@click.option("--json-out", is_flag=True, default=False)
def translate(command: str, project_root: str, qdrant_url: str, json_out: bool) -> None:
    """Translate a single command and print the result."""
    from shellsage.models import ShellContext
    from shellsage.translator import translate as _translate

    ctx = ShellContext.detect(project_root=project_root)
    result = _translate(command, ctx, qdrant_url=qdrant_url)

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


@main.command()
@click.option("--qdrant-url", default="http://localhost:6333", show_default=True)
def stats(qdrant_url: str) -> None:
    """Show Qdrant collection counts and recent failure patterns."""
    from shellsage import store

    try:
        counts = store.get_collection_counts(url=qdrant_url)
    except Exception as exc:
        console.print(f"[red]Qdrant unreachable:[/red] {exc}")
        sys.exit(1)

    table = Table(title="ShellSage — Qdrant Collections", show_header=True)
    table.add_column("Collection", style="cyan")
    table.add_column("Documents", justify="right", style="green")
    for name, count in counts.items():
        table.add_row(name, str(count))
    console.print(table)


@main.command()
@click.option("--qdrant-url", default="http://localhost:6333", show_default=True)
@click.option("--limit", default=20, show_default=True)
def replay(qdrant_url: str, limit: int) -> None:
    """Show recent failure patterns stored in Qdrant."""
    from qdrant_client import QdrantClient

    from shellsage.store import FAILURES_COLLECTION

    try:
        client = QdrantClient(url=qdrant_url, timeout=5)
        points, _ = client.scroll(
            collection_name=FAILURES_COLLECTION,
            limit=limit,
            with_payload=True,
        )
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    if not points:
        console.print("[dim]No failures recorded yet.[/dim]")
        return

    table = Table(title=f"Recent Failures (last {limit})", show_header=True)
    table.add_column("Shell", style="yellow")
    table.add_column("OS", style="cyan")
    table.add_column("Command", style="white")
    table.add_column("Error (truncated)", style="red")

    for p in points:
        pay = p.payload or {}
        table.add_row(
            pay.get("shell", "?"),
            pay.get("os", "?"),
            (pay.get("command") or "")[:50],
            (pay.get("error_text") or "")[:60],
        )
    console.print(table)


@main.command()
def mcp() -> None:
    """Start the MCP server (used by Claude Code and GitHub Copilot)."""
    try:
        from shellsage.server import run
    except ImportError:
        console.print("[red]MCP extra not installed.[/red]")
        console.print("Run:  pip install 'shellsage[mcp]'")
        sys.exit(1)
    run()


@main.group()
def hooks() -> None:
    """Manage Claude Code hook scripts."""


@hooks.command("install")
@click.option("--hooks-dir", default=".claude", show_default=True)
def hooks_install(hooks_dir: str) -> None:
    """Write PreToolUse and PostToolUse hook scripts into .claude/hooks/."""
    import os
    import stat

    hooks_path = os.path.join(hooks_dir, "hooks")
    os.makedirs(hooks_path, exist_ok=True)

    pre = os.path.join(hooks_path, "pre_tool_use.py")
    post = os.path.join(hooks_path, "post_tool_use.py")

    _write_hook(pre, _PRE_TOOL_USE_SCRIPT)
    _write_hook(post, _POST_TOOL_USE_SCRIPT)

    for path in (pre, post):
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    console.print(f"[green]✓[/green] Hooks written to [cyan]{hooks_path}[/cyan]")
    console.print("\nAdd to [dim].claude/settings.json[/dim]:")
    console.print("""
  {
    "hooks": {
      "PreToolUse":  [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/pre_tool_use.py"}]}],
      "PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/post_tool_use.py"}]}]
    }
  }
""")


def _write_hook(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


_PRE_TOOL_USE_SCRIPT = '''\
#!/usr/bin/env python3
"""PreToolUse hook — translates bash commands before Claude Code executes them."""
import json, sys

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
        event["tool_input"]["command"] = result.translated
        print(json.dumps({"decision": "approve", "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": event["tool_input"],
        }}))
        sys.exit(0)
except Exception:
    pass  # never block the agent

sys.exit(0)
'''

_POST_TOOL_USE_SCRIPT = '''\
#!/usr/bin/env python3
"""PostToolUse hook — stores command outcomes back to Qdrant."""
import json, sys

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
    from shellsage.models import CommandOutcome, OS, Shell, ShellContext
    from shellsage.translator import store_outcome
    ctx = ShellContext.detect()
    outcome = CommandOutcome(
        original=command,
        translated=command,
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
