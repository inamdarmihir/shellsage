"""
Built-in rule-based bash→PowerShell translations.

These run with zero Qdrant dependency — they are the cold-start seed.
Rules are ordered from most-specific to least-specific.
"""

from __future__ import annotations

import re

from shellsage.models import Shell

# Each entry: (bash_pattern_regex, powershell_replacement_or_callable)
# Callable receives the re.Match and returns the replacement string.
_RULES: list[tuple[re.Pattern, object]] = []


def _rule(pattern: str, replacement: object) -> None:
    _RULES.append((re.compile(pattern, re.IGNORECASE), replacement))


# ── shebang / heredoc guards (must come first) ───────────────────────────────
_rule(r"^#!/", "# ShellSage: shebang line not valid in PowerShell — use a .ps1 file")
_rule(
    r"<<\s*'?EOF'?",
    "# ShellSage: heredoc not supported in PowerShell — use @'...'@ here-string syntax",
)

# ── file listing ──────────────────────────────────────────────────────────────
_rule(r"^ls\s+-la?\s*$", "Get-ChildItem -Force")
_rule(r"^ls\s+-la\s+([^|]+)$", lambda m: f"Get-ChildItem -Force '{m.group(1)}'")
_rule(r"^ls\s+([^|]+)$", lambda m: f"Get-ChildItem '{m.group(1)}'")
_rule(r"^ls\s*$", "Get-ChildItem")

# ── grep ──────────────────────────────────────────────────────────────────────
_rule(
    r"^grep\s+-r\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Get-ChildItem -Recurse '{m.group(2)}' | Select-String -Pattern '{m.group(1)}'",
)
_rule(
    r"^grep\s+-rn\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Get-ChildItem -Recurse '{m.group(2)}' | Select-String -Pattern '{m.group(1)}'",
)
_rule(
    r"^grep\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1)}' -Path '{m.group(2)}'",
)
_rule(
    r"\|\s*grep\s+['\"]?(.+?)['\"]?\s*$",
    lambda m: f"| Where-Object {{ $_ -match '{m.group(1)}' }}",
)

# ── find ──────────────────────────────────────────────────────────────────────
_rule(
    r"^find\s+\.\s+-type\s+f\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Recurse -File -Filter '{m.group(1)}'",
)
_rule(
    r"^find\s+\.\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Recurse -Filter '{m.group(1)}'",
)
_rule(
    r"^find\s+(\S+)\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Path '{m.group(1)}' -Recurse -Filter '{m.group(2)}'",
)

# ── cat ───────────────────────────────────────────────────────────────────────
_rule(r"^cat\s+([^|]+)$", lambda m: f"Get-Content '{m.group(1)}'")

# ── mkdir ─────────────────────────────────────────────────────────────────────
_rule(r"^mkdir\s+-p\s+([^|]+)$", lambda m: f"New-Item -ItemType Directory -Force -Path '{m.group(1)}'")
_rule(r"^mkdir\s+([^|]+)$", lambda m: f"New-Item -ItemType Directory -Path '{m.group(1)}'")

# ── rm ────────────────────────────────────────────────────────────────────────
_rule(r"^rm\s+-rf\s+([^|]+)$", lambda m: f"Remove-Item -Recurse -Force '{m.group(1)}'")
_rule(r"^rm\s+-r\s+([^|]+)$", lambda m: f"Remove-Item -Recurse '{m.group(1)}'")
_rule(r"^rm\s+-f\s+([^|]+)$", lambda m: f"Remove-Item -Force '{m.group(1)}'")
_rule(r"^rm\s+([^|]+)$", lambda m: f"Remove-Item '{m.group(1)}'")

# ── cp / mv ───────────────────────────────────────────────────────────────────
_rule(r"^cp\s+-r\s+(\S+)\s+(\S+)$", lambda m: f"Copy-Item -Recurse '{m.group(1)}' '{m.group(2)}'")
_rule(r"^cp\s+(\S+)\s+(\S+)$", lambda m: f"Copy-Item '{m.group(1)}' '{m.group(2)}'")
_rule(r"^mv\s+(\S+)\s+(\S+)$", lambda m: f"Move-Item '{m.group(1)}' '{m.group(2)}'")

# ── echo / export / env ───────────────────────────────────────────────────────
_rule(r"^echo\s+([^|]+)$", lambda m: f"Write-Output '{m.group(1)}'")
_rule(
    r"^export\s+(\w+)=([^|]+)$",
    lambda m: f"$env:{m.group(1)} = '{m.group(2)}'",
)
_rule(r"^env\s*$", "Get-ChildItem Env:")
_rule(r"^printenv\s+(\w+)$", lambda m: f"$env:{m.group(1)}")

# ── process / service ─────────────────────────────────────────────────────────
_rule(r"^ps\s+aux\s*$", "Get-Process")
_rule(r"^ps\s+aux\s*\|", "Get-Process |")
_rule(r"^kill\s+-9\s+(\d+)$", lambda m: f"Stop-Process -Id {m.group(1)} -Force")
_rule(r"^kill\s+(\d+)$", lambda m: f"Stop-Process -Id {m.group(1)}")

# ── networking ────────────────────────────────────────────────────────────────
_rule(r"^curl\s+-s\s+([^|]+)$", lambda m: f"Invoke-RestMethod '{m.group(1)}'")
_rule(r"^curl\s+([^|]+)$", lambda m: f"Invoke-WebRequest -Uri '{m.group(1)}'")
_rule(r"^wget\s+([^|]+)$", lambda m: f"Invoke-WebRequest -Uri '{m.group(1)}' -OutFile './download'")

# ── text processing ───────────────────────────────────────────────────────────
_rule(r"^wc\s+-l\s+([^|]+)$", lambda m: f"(Get-Content '{m.group(1)}').Count")
_rule(r"\|\s*wc\s+-l\s*$", "| Measure-Object -Line")
_rule(
    r"^head\s+-n\s+(\d+)\s+([^|]+)$", lambda m: f"Get-Content '{m.group(2)}' -TotalCount {m.group(1)}"
)
_rule(r"^tail\s+-n\s+(\d+)\s+([^|]+)$", lambda m: f"Get-Content '{m.group(2)}' -Tail {m.group(1)}")
_rule(r"^tail\s+-f\s+([^|]+)$", lambda m: f"Get-Content -Wait '{m.group(1)}'")
_rule(r"\|\s*sort\s+-u\s*$", "| Sort-Object -Unique")
_rule(r"\|\s*sort\s*$", "| Sort-Object")
_rule(r"\|\s*uniq\s*$", "| Select-Object -Unique")

# ── path separators (forward → back on Windows) ───────────────────────────────
# Applied only when entire command is a path-like invocation
_rule(r"^(\./|/)([^\s]+)$", lambda m: m.group(0).replace("/", "\\"))


def apply(command: str, shell: Shell) -> str:
    """
    Apply the first matching rule to *command*.

    Returns the translated string, or the original if no rule matched.
    Only translates for PowerShell/CMD targets.
    """
    if shell not in (Shell.POWERSHELL, Shell.CMD):
        return command

    cmd = command.strip()
    for pattern, replacement in _RULES:
        m = pattern.search(cmd)
        if m:
            if callable(replacement):
                res = replacement(m)
                if res.startswith("|") or m.group(0) != cmd:
                    return pattern.sub(replacement, cmd)
                return res
            # String replacement: use re.sub for inline pipe rewrites
            if replacement.startswith("|") or m.group(0) != cmd:
                return pattern.sub(replacement, cmd)
            return str(replacement)

    return command
