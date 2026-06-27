#!/usr/bin/env python3
"""PostToolUse hook — stores command outcomes back to local memory."""
import hashlib, json, os, sys, tempfile

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

    ctx = ShellContext.get_cached()

    original   = command
    translated = command
    cmd_hash   = hashlib.md5(command.encode()).hexdigest()[:12]
    cache_path = os.path.join(tempfile.gettempdir(), f"shellsage_{cmd_hash}.json")
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
