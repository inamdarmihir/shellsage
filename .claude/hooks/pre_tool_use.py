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
