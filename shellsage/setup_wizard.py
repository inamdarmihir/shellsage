"""Interactive setup wizard  -  guides the user through a one-command install."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table

console = Console()


# ── IDE detection ─────────────────────────────────────────────────────────────

def _detect_ides() -> list[dict]:
    """Return a list of supported IDEs/agents found on this machine."""
    found = []

    if shutil.which("claude"):
        found.append({"name": "Claude Code", "key": "claude_code", "how": "claude CLI"})

    cursor_home = Path.home() / ".cursor"
    if shutil.which("cursor") or cursor_home.exists():
        found.append({"name": "Cursor", "key": "cursor", "how": "~/.cursor/mcp.json"})

    windsurf_home = Path.home() / ".codeium" / "windsurf"
    if shutil.which("windsurf") or windsurf_home.exists():
        found.append({"name": "Windsurf", "key": "windsurf", "how": "~/.codeium/windsurf/mcp_config.json"})

    return found


def _register_ide(key: str, mcp_url: str) -> tuple[bool, str]:
    """Register the MCP server with the given IDE. Returns (success, message)."""
    if key == "claude_code":
        return _register_claude_code(mcp_url)
    if key == "cursor":
        return _register_cursor(mcp_url)
    if key == "windsurf":
        return _register_windsurf(mcp_url)
    return False, f"Unknown IDE key: {key}"


def _register_claude_code(mcp_url: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["claude", "mcp", "add", "--transport", "sse", "shellsage", mcp_url],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return True, "MCP server registered"
        msg = (result.stderr or result.stdout).strip()
        return False, msg or "claude mcp add failed"
    except FileNotFoundError:
        return False, "claude CLI not found"
    except subprocess.TimeoutExpired:
        return False, "claude CLI timed out"


def _register_cursor(mcp_url: str) -> tuple[bool, str]:
    config_path = Path.home() / ".cursor" / "mcp.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing: dict = json.loads(config_path.read_text()) if config_path.exists() else {}
        existing.setdefault("mcpServers", {})["shellsage"] = {"url": mcp_url}
        config_path.write_text(json.dumps(existing, indent=2))
        return True, f"Written to {config_path}"
    except Exception as exc:
        return False, str(exc)


def _register_windsurf(mcp_url: str) -> tuple[bool, str]:
    config_path = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing: dict = json.loads(config_path.read_text()) if config_path.exists() else {}
        existing.setdefault("mcpServers", {})["shellsage"] = {"serverUrl": mcp_url}
        config_path.write_text(json.dumps(existing, indent=2))
        return True, f"Written to {config_path}"
    except Exception as exc:
        return False, str(exc)


def _proxy_launch_command(host: str, port: int) -> str:
    """Return the shell command to launch Claude Code through the ShellSage proxy."""
    base_url = f"http://{host}:{port}"
    if sys.platform == "win32":
        return f'$env:ANTHROPIC_BASE_URL="{base_url}"; claude'
    return f"ANTHROPIC_BASE_URL={base_url} claude"


def run_wizard(port: int = 7842, host: str = "127.0.0.1") -> None:
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]ShellSage[/bold cyan]  [dim]setup wizard[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    steps_passed = 0
    steps_total = 5

    # ── Step 1: Detect environment ────────────────────────────────────────────
    _step(1, steps_total, "Detecting environment")
    try:
        from shellsage.models import ShellContext
        ctx = ShellContext.detect()
        _ok(f"{ctx.os.value.title()}  /  {ctx.shell.value}  /  {ctx.project_type} project")
        steps_passed += 1
    except Exception as exc:
        _fail(str(exc))

    # ── Step 2: Initialize local database ────────────────────────────────────
    _step(2, steps_total, "Initialising local database & loading seed translations")
    try:
        from shellsage import store
        from shellsage.config import DB_PATH, SEED_CONFIDENCE
        from shellsage.seed import SEED_TRANSLATIONS

        store.ensure_tables()
        loaded = 0
        for seed in SEED_TRANSLATIONS:
            store.upsert_translation(
                bash_cmd=seed["bash"],
                translated_cmd=seed["ps"],
                shell="powershell",
                os_name="windows",
                project_type="unknown",
                confidence=SEED_CONFIDENCE,
            )
            loaded += 1

        _ok(f"{loaded} seed pairs loaded  |  DB: [dim]{DB_PATH}[/dim]")
        steps_passed += 1
    except Exception as exc:
        _fail(str(exc))

    # ── Step 3: Start background server ──────────────────────────────────────
    _step(3, steps_total, f"Starting background MCP + proxy server (preferred port {port})")
    server_started = False
    actual_port = port
    server_pid = None
    try:
        from shellsage.daemon import start_daemon
        result = start_daemon(port=port, host=host)
        if result.get("started"):
            server_pid = result["pid"]
            actual_port = result["port"]
            if actual_port != port:
                _warn(f"Port {port} was in use — started on port {actual_port} instead")
            time.sleep(2)  # allow uvicorn to bind
            _ok(f"PID {server_pid}  |  http://{host}:{actual_port}/sse")
            server_started = True
            steps_passed += 1
        elif result.get("reason") == "already_running":
            server_pid = result.get("pid")
            actual_port = result.get("port", port)
            _ok(f"Already running  (PID {server_pid} | port {actual_port})")
            server_started = True
            steps_passed += 1
        else:
            _warn("Could not start server  -  MCP extra may not be installed.")
            console.print(f"    Run:  [dim]pip install 'shellsage[mcp]'[/dim]")
    except Exception as exc:
        _fail(str(exc))

    # ── Step 4: Detect IDEs and register MCP server ──────────────────────────
    mcp_url = f"http://{host}:{actual_port}/sse"
    _step(4, steps_total, "Detecting IDE / agent tools")
    ides = _detect_ides()
    selected_ides: list[dict] = []

    if not ides:
        _warn("No supported IDE detected (Claude Code, Cursor, Windsurf)")
        console.print(f"    Add manually  →  MCP URL: [dim]{mcp_url}[/dim]")
    elif len(ides) == 1:
        _ok(f"Found: [bold]{ides[0]['name']}[/bold]  ({ides[0]['how']})")
        selected_ides = ides
    else:
        _ok("Found multiple IDEs:")
        for idx, ide in enumerate(ides, 1):
            console.print(f"    [[bold]{idx}[/bold]] {ide['name']}  [dim]({ide['how']})[/dim]")
        console.print("    [[bold]a[/bold]] All")
        choice = Prompt.ask("    Configure which", default="a")
        if choice.strip().lower() == "a":
            selected_ides = ides
        else:
            try:
                selected_ides = [ides[int(choice.strip()) - 1]]
            except (ValueError, IndexError):
                _warn(f"Invalid choice '{choice}'  -  defaulting to all")
                selected_ides = ides

    has_claude_code = False
    if server_started and selected_ides:
        for ide in selected_ides:
            ok, msg = _register_ide(ide["key"], mcp_url)
            if ok:
                _ok(f"{ide['name']}: {msg}")
                if ide["key"] == "claude_code":
                    has_claude_code = True
            else:
                _warn(f"{ide['name']}: {msg}")
                if ide["key"] == "claude_code":
                    console.print(
                        f"    [dim]claude mcp add --transport sse shellsage {mcp_url}[/dim]"
                    )
                else:
                    console.print(f"    MCP URL: [dim]{mcp_url}[/dim]")
        steps_passed += 1
    elif not server_started:
        _skip("Skipped  -  server not running")

    # ── Step 5: Install hooks (Claude Code only) ──────────────────────────────
    _step(5, steps_total, "Install Claude Code hooks (auto-translate Bash commands)?")
    if not has_claude_code:
        _skip("Skipped  -  Claude Code not selected")
        steps_passed += 1  # not a user failure; count it
    elif Confirm.ask("    Install hooks", default=True):
        try:
            _install_hooks()
            _ok("Hooks installed in .claude/hooks/")
            steps_passed += 1
        except Exception as exc:
            _fail(str(exc))
    else:
        _skip("Skipped")

    # ── Summary ───────────────────────────────────────────────────────────────
    console.print()
    console.print(Rule(style="cyan"))
    console.print()

    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()

    try:
        from shellsage import store as _store
        db_counts = _store.get_stats()
        table.add_row("Translations", str(db_counts["translations"]))
        table.add_row("Failures logged", str(db_counts["failures"]))
    except Exception:
        pass

    if server_started:
        table.add_row("MCP endpoint", f"http://{host}:{actual_port}/sse  (PID {server_pid})")
        table.add_row("Proxy endpoint", f"http://{host}:{actual_port}/v1/messages")
    table.add_row("Logs", str(Path.home() / ".shellsage" / "shellsage.log"))

    if steps_passed == steps_total:
        console.print(
            Panel(table, title="[bold green]Setup complete[/bold green]", border_style="green")
        )
    else:
        console.print(
            Panel(
                table,
                title=f"[bold yellow]Partial setup ({steps_passed}/{steps_total} steps)[/bold yellow]",
                border_style="yellow",
            )
        )
        console.print()
        console.print("  Fix the warnings above, then run [dim]shellsage setup[/dim] again.")

    # ── Usage instructions ────────────────────────────────────────────────────
    if server_started:
        console.print()
        console.print(Rule("How to use ShellSage", style="dim"))
        console.print()

        console.print("  [bold]Option A — MCP tools[/bold]  (hooks translate commands automatically)")
        console.print(f"    [dim]Open Claude Code — ShellSage translates every Bash command it runs.[/dim]")
        console.print()

        proxy_cmd = _proxy_launch_command(host, actual_port)
        console.print("  [bold]Option B — Anthropic API proxy[/bold]  (intercepts requests before the LLM responds)")
        console.print(f"    ShellSage sits between Claude Code and the Anthropic API.")
        console.print(f"    Every bash command in the model's response is translated on the fly.")
        console.print()
        console.print(f"    Launch Claude Code with:")
        console.print(f"      [bold cyan]{proxy_cmd}[/bold cyan]")
        console.print()
        console.print(f"    [dim]ShellSage forwards all other requests to api.anthropic.com unchanged.[/dim]")

    console.print()


# ── helpers ───────────────────────────────────────────────────────────────────

def _step(n: int, total: int, msg: str) -> None:
    console.print(f"[bold cyan]Step {n}/{total}[/bold cyan]  {msg}...")

def _ok(msg: str) -> None:
    console.print(f"  [green]>[/green]  {msg}")

def _warn(msg: str) -> None:
    console.print(f"  [yellow]![/yellow]  {msg}")

def _fail(msg: str) -> None:
    console.print(f"  [red]X[/red]  {msg}")

def _skip(msg: str) -> None:
    console.print(f"  [dim]-  {msg}[/dim]")


def _install_hooks() -> None:
    import stat

    hooks_path = Path(".claude") / "hooks"
    hooks_path.mkdir(parents=True, exist_ok=True)

    pre = hooks_path / "pre_tool_use.py"
    post = hooks_path / "post_tool_use.py"

    pre.write_text(_PRE_HOOK)
    post.write_text(_POST_HOOK)

    for p in (pre, post):
        p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    settings = Path(".claude") / "settings.json"
    _ensure_hook_settings(settings)


def _ensure_hook_settings(settings_path: Path) -> None:
    import json

    hook_config = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/pre_tool_use.py"}]}
            ],
            "PostToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/post_tool_use.py"}]}
            ],
        }
    }

    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text())
            if "hooks" not in existing:
                existing["hooks"] = hook_config["hooks"]
                settings_path.write_text(json.dumps(existing, indent=2))
        except (json.JSONDecodeError, OSError):
            pass
    else:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(hook_config, indent=2))


_PRE_HOOK = '''\
#!/usr/bin/env python3
"""PreToolUse hook  -  translates bash commands before Claude Code executes them."""
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

_POST_HOOK = '''\
#!/usr/bin/env python3
"""PostToolUse hook  -  stores command outcomes back to local memory."""
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
