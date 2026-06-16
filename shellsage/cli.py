"""ShellSage CLI — shellsage init | translate | stats | replay | mcp | hooks"""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from shellsage.config import DEFAULT_SEED_LIMIT, SEED_CONFIDENCE
from shellsage.config import QDRANT_URL as _DEFAULT_URL

console = Console()


@click.group()
@click.version_option(package_name="shellsage")
def main() -> None:
    """ShellSage — shell translation layer backed by local Qdrant."""


@main.command()
@click.option(
    "--qdrant-url", default=_DEFAULT_URL, show_default=True, envvar="SHELLSAGE_QDRANT_URL"
)
@click.option(
    "--limit",
    type=click.IntRange(min=1),
    default=DEFAULT_SEED_LIMIT,
    show_default=True,
    envvar="SHELLSAGE_SEED_LIMIT",
    help="Maximum number of curated seed examples to load.",
)
@click.option("--all", "load_all", is_flag=True, help="Load the complete seed corpus.")
@click.option(
    "--batch-size",
    type=click.IntRange(min=1),
    default=16,
    show_default=True,
    help="Embedding batch size.",
)
def init(qdrant_url: str, limit: int, load_all: bool, batch_size: int) -> None:
    """Initialise Qdrant collections and load a bounded seed set."""
    try:
        from shellsage import embedder, store
    except (ImportError, ModuleNotFoundError) as exc:
        console.print("[red]Vector dependencies are not installed.[/red]")
        console.print("Install them with:  [dim]pip install 'shellsage[vector]'[/dim]")
        console.print(f"[dim]{exc}[/dim]")
        sys.exit(1)

    from shellsage.seed import SEED_TRANSLATIONS, select_seed_translations

    seeds = select_seed_translations(None if load_all else limit)

    console.print("[bold cyan]ShellSage init[/bold cyan]")
    console.print(
        f"Loading [bold]{len(seeds)}[/bold] seed examples "
        f"([dim]{len(SEED_TRANSLATIONS)} available; use --all for the full set[/dim])"
    )

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )

    with progress:
        collections_task = progress.add_task("Preparing Qdrant collections", total=1)
        try:
            store.ensure_collections(url=qdrant_url)
        except Exception as exc:
            console.print(f"[red]✗ Qdrant unreachable at {qdrant_url}[/red]")
            console.print(f"  {exc}")
            console.print("\nStart Qdrant with:  docker compose up -d")
            sys.exit(1)
        progress.advance(collections_task)

        embed_task = progress.add_task("Embedding seed examples", total=len(seeds))
        vectors: list[list[float]] = []
        for start in range(0, len(seeds), batch_size):
            batch = seeds[start : start + batch_size]
            vectors.extend(embedder.embed_batch([s["bash"] for s in batch]))
            progress.advance(embed_task, len(batch))

        upsert_task = progress.add_task("Writing seed examples", total=len(seeds))
        loaded = 0
        failed = 0
        for seed, vec in zip(seeds, vectors, strict=False):
            try:
                store.upsert_translation(
                    bash_cmd=seed["bash"],
                    translated_cmd=seed["ps"],
                    shell="powershell",
                    os_name="windows",
                    project_type="unknown",
                    confidence=SEED_CONFIDENCE,
                    embedding=vec,
                    url=qdrant_url,
                )
                loaded += 1
            except Exception:
                failed += 1
            finally:
                progress.advance(upsert_task)

    console.print(f"  [green]✓[/green] {loaded}/{len(seeds)} seed translations loaded")
    if failed:
        console.print(f"  [yellow]![/yellow] {failed} seed translations failed to load")

    console.print("\n[bold green]Ready.[/bold green]  Register with Claude Code:")
    console.print("  [dim]claude mcp add shellsage -- shellsage mcp[/dim]")
    console.print("\nInstall hooks:  shellsage hooks install")


@main.command()
@click.argument("command")
@click.option("--project-root", default=".", show_default=True)
@click.option(
    "--qdrant-url", default=_DEFAULT_URL, show_default=True, envvar="SHELLSAGE_QDRANT_URL"
)
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
@click.option(
    "--qdrant-url", default=_DEFAULT_URL, show_default=True, envvar="SHELLSAGE_QDRANT_URL"
)
def stats(qdrant_url: str) -> None:
    """Show Qdrant collection counts."""
    try:
        from shellsage import store

        counts = store.get_collection_counts(url=qdrant_url)
    except (ImportError, ModuleNotFoundError):
        console.print("[red]Vector dependencies are not installed.[/red]")
        console.print("Install them with:  [dim]pip install 'shellsage[vector]'[/dim]")
        sys.exit(1)
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
@click.option(
    "--qdrant-url", default=_DEFAULT_URL, show_default=True, envvar="SHELLSAGE_QDRANT_URL"
)
@click.option("--limit", default=20, show_default=True)
def replay(qdrant_url: str, limit: int) -> None:
    """Show recent failure patterns stored in Qdrant."""
    try:
        from qdrant_client import QdrantClient

        from shellsage.store import FAILURES_COLLECTION

        client = QdrantClient(url=qdrant_url, timeout=5)
        points, _ = client.scroll(
            collection_name=FAILURES_COLLECTION,
            limit=limit,
            with_payload=True,
        )
    except (ImportError, ModuleNotFoundError):
        console.print("[red]Vector dependencies are not installed.[/red]")
        console.print("Install them with:  [dim]pip install 'shellsage[vector]'[/dim]")
        sys.exit(1)
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
import json
import os
import sys
import tempfile

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
"""PostToolUse hook — stores command outcomes back to Qdrant."""
import json
import os
import sys
import tempfile

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
