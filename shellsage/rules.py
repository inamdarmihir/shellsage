"""
Built-in rule-based bash → PowerShell translations.

These run with zero external dependencies — they are the cold-start safety net.
Rules are ordered from most-specific to least-specific so the first match wins.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from shellsage.models import Shell

# Each entry: (compiled_pattern, powershell_replacement_or_callable, ref_url)
_Replacement = str | Callable[[re.Match[str]], str]
_RULES: list[tuple[re.Pattern[str], _Replacement, str]] = []


def _rule(pattern: str, replacement: _Replacement, ref: str = "") -> None:
    _RULES.append((re.compile(pattern, re.IGNORECASE), replacement, ref))


# ── shebang / heredoc guards (must come first) ───────────────────────────────
_rule(
    r"^#!/",
    "# ShellSage: shebang line not valid in PowerShell — use a .ps1 file",
    ref="https://learn.microsoft.com/en-us/powershell/scripting/overview",
)
_rule(
    r"<<\s*'?EOF'?",
    "# ShellSage: heredoc not supported in PowerShell — use @'...'@ here-string syntax",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules",
)

# ── compound pipe rules (must come first — beat component rules at matching) ──
_GCI = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-childitem"
_GC = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-content"
_SS = (
    "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/select-string"
)
_WO = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/where-object"
_RI = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/remove-item"
_CI = (
    "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/copy-item"
)
_MI = (
    "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/move-item"
)
_NI = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/new-item"
_SP = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/stop-process"
_GP = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-process"
_IRM = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/invoke-restmethod"
_IWR = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/invoke-webrequest"
_SL = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/set-location"
_GL = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-location"
_SO = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/sort-object"
_MO = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/measure-object"
_SEL = (
    "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/select-object"
)
_CA = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/compress-archive"
_EA = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/expand-archive"
_TC = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/test-connection"
_GD = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-date"
_GH = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-history"
_GCI_SS = _GCI  # combined GCI+SS pipes share the GCI ref

_rule(
    r"^cat\s+([^|]+?)\s*\|\s*head\s+-n\s+(\d+)\s*$",
    lambda m: f"Get-Content '{m.group(1).strip()}' -TotalCount {m.group(2)}",
    ref=_GC,
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*head\s*$",
    lambda m: f"Get-Content '{m.group(1).strip()}' -TotalCount 10",
    ref=_GC,
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*tail\s+-n\s+(\d+)\s*$",
    lambda m: f"Get-Content '{m.group(1).strip()}' -Tail {m.group(2)}",
    ref=_GC,
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*tail\s*$",
    lambda m: f"Get-Content '{m.group(1).strip()}' -Tail 10",
    ref=_GC,
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*wc\s+-l\s*$",
    lambda m: f"(Get-Content '{m.group(1).strip()}').Count",
    ref=_GC,
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*grep\s+-i\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Select-String -Pattern '{m.group(2).strip()}' -Path '{m.group(1).strip()}' -CaseSensitive:$false",
    ref=_SS,
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*grep\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Select-String -Pattern '{m.group(2).strip()}' -Path '{m.group(1).strip()}'",
    ref=_SS,
)
_rule(
    r"^ls\s*\|\s*grep\s+-i\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Get-ChildItem | Where-Object {{ $_.Name -imatch '{m.group(1).strip()}' }}",
    ref=_GCI,
)
_rule(
    r"^ls\s*\|\s*grep\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Get-ChildItem | Where-Object {{ $_.Name -match '{m.group(1).strip()}' }}",
    ref=_GCI,
)
_rule(
    r"^find\s+\.\s+-name\s+['\"]?([^'\"]+)['\"]?\s*\|\s*xargs\s+grep\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Get-ChildItem -Recurse -Filter '{m.group(1)}' | Select-String '{m.group(2).strip()}'",
    ref=_SS,
)
_rule(
    r"^find\s+\.\s+-type\s+f\s+\|\s*xargs\s+grep\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Get-ChildItem -Recurse -File | Select-String '{m.group(1).strip()}'",
    ref=_SS,
)

# ── file listing ──────────────────────────────────────────────────────────────
_rule(r"^ls\s+(-la?|-al)\s*$", "Get-ChildItem -Force", ref=_GCI)
_rule(
    r"^ls\s+(-la?|-al)\s+([^|]+)$",
    lambda m: f"Get-ChildItem -Force '{m.group(2).strip()}'",
    ref=_GCI,
)
_rule(r"^ls\s+-lh\s*$", "Get-ChildItem | Format-List Name, Length, LastWriteTime", ref=_GCI)
_rule(r"^ls\s+-R\s*$", "Get-ChildItem -Recurse", ref=_GCI)
_rule(r"^ls\s+([^|]+)$", lambda m: f"Get-ChildItem '{m.group(1).strip()}'", ref=_GCI)
_rule(r"^ls\s*$", "Get-ChildItem", ref=_GCI)

# ── grep (context lines + line numbers — must precede general grep rules) ────
_rule(
    r"^grep\s+-A\s+(\d+)\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(2).strip()}' -Path '{m.group(3).strip()}' -Context 0,{m.group(1)}",
    ref=_SS,
)
_rule(
    r"^grep\s+-B\s+(\d+)\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(2).strip()}' -Path '{m.group(3).strip()}' -Context {m.group(1)},0",
    ref=_SS,
)
_rule(
    r"^grep\s+-C\s+(\d+)\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(2).strip()}' -Path '{m.group(3).strip()}' -Context {m.group(1)},{m.group(1)}",
    ref=_SS,
)
_rule(
    r"^grep\s+-n\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}' | Select-Object LineNumber, Line",
    ref=_SS,
)
_rule(
    r"^grep\s+-rn\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Get-ChildItem -Recurse '{m.group(2).strip()}' | Select-String -Pattern '{m.group(1).strip()}' | Select-Object Path, LineNumber, Line",
    ref=_SS,
)

# ── grep ──────────────────────────────────────────────────────────────────────
_rule(
    r"^grep\s+-ri\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Get-ChildItem -Recurse '{m.group(2).strip()}' | Select-String -Pattern '{m.group(1).strip()}' -CaseSensitive:$false",
    ref=_SS,
)
_rule(
    r"^grep\s+-r[ni]*\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Get-ChildItem -Recurse '{m.group(2).strip()}' | Select-String -Pattern '{m.group(1).strip()}'",
    ref=_SS,
)
_rule(
    r"^grep\s+-i\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}' -CaseSensitive:$false",
    ref=_SS,
)
_rule(
    r"^grep\s+-v\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(2).strip()}' | Where-Object {{ $_ -notmatch '{m.group(1).strip()}' }}",
    ref=_SS,
)
_rule(
    r"^grep\s+-c\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"(Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}').Count",
    ref=_SS,
)
_rule(
    r"^grep\s+-l\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}' | Select-Object -ExpandProperty Path -Unique",
    ref=_SS,
)
_rule(
    r"^grep\s+-E\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}'",
    ref=_SS,
)
_rule(
    r"^grep\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}'",
    ref=_SS,
)
_rule(
    r"\|\s*grep\s+-i\s+['\"]?([^|]+?)['\"]?\s*(?=\||$)",
    lambda m: f"| Where-Object {{ $_ -imatch '{m.group(1).strip()}' }}",
    ref=_WO,
)
_rule(
    r"\|\s*grep\s+-v\s+['\"]?([^|]+?)['\"]?\s*(?=\||$)",
    lambda m: f"| Where-Object {{ $_ -notmatch '{m.group(1).strip()}' }}",
    ref=_WO,
)
_rule(
    r"\|\s*grep\s+['\"]?([^|]+?)['\"]?\s*(?=\||$)",
    lambda m: f"| Where-Object {{ $_ -match '{m.group(1).strip()}' }}",
    ref=_WO,
)

# ── find ──────────────────────────────────────────────────────────────────────
_rule(
    r"^find\s+\.\s+-type\s+f\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Recurse -File -Filter '{m.group(1)}'",
    ref=_GCI,
)
_rule(
    r"^find\s+\.\s+-type\s+d\s*$",
    "Get-ChildItem -Recurse -Directory",
    ref=_GCI,
)
_rule(
    r"^find\s+\.\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Recurse -Filter '{m.group(1)}'",
    ref=_GCI,
)
_rule(
    r"^find\s+(\S+)\s+-type\s+f\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Path '{m.group(1)}' -Recurse -File -Filter '{m.group(2)}'",
    ref=_GCI,
)
_rule(
    r"^find\s+(\S+)\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Path '{m.group(1)}' -Recurse -Filter '{m.group(2)}'",
    ref=_GCI,
)
_rule(
    r"^find\s+\.\s+-mtime\s+-(\d+)$",
    lambda m: f"Get-ChildItem -Recurse | Where-Object {{ $_.LastWriteTime -gt (Get-Date).AddDays(-{m.group(1)}) }}",
    ref=_GCI,
)
_rule(
    r"^find\s+\.\s+-size\s+\+(\d+)[Mm]$",
    lambda m: f"Get-ChildItem -Recurse | Where-Object {{ $_.Length -gt {m.group(1)}MB }}",
    ref=_GCI,
)
_rule(
    r"^find\s+\.\s+-size\s+\+(\d+)[Kk]$",
    lambda m: f"Get-ChildItem -Recurse | Where-Object {{ $_.Length -gt {m.group(1)}KB }}",
    ref=_GCI,
)
_rule(
    r"^find\s+\.\s+-empty$",
    "Get-ChildItem -Recurse | Where-Object { $_.Length -eq 0 }",
    ref=_GCI,
)

# ── cat ───────────────────────────────────────────────────────────────────────
_rule(
    r"^cat\s+-n\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | ForEach-Object -Begin {{$i=1}} -Process {{\"{{0,4}}: {{1}}\" -f $i++,$_}}",
    ref=_GC,
)
_rule(r"^cat\s+([^|]+)$", lambda m: f"Get-Content '{m.group(1).strip()}'", ref=_GC)

# ── mkdir ─────────────────────────────────────────────────────────────────────
_rule(
    r"^mkdir\s+-p\s+([^|]+)$",
    lambda m: f"New-Item -ItemType Directory -Force -Path '{m.group(1).strip()}'",
    ref=_NI,
)
_rule(
    r"^mkdir\s+([^|]+)$",
    lambda m: f"New-Item -ItemType Directory -Path '{m.group(1).strip()}'",
    ref=_NI,
)

# ── rm ────────────────────────────────────────────────────────────────────────
_rule(
    r"^rm\s+-rf\s+([^|]+)$",
    lambda m: f"Remove-Item -Recurse -Force '{m.group(1).strip()}'",
    ref=_RI,
)
_rule(
    r"^rm\s+-fr\s+([^|]+)$",
    lambda m: f"Remove-Item -Recurse -Force '{m.group(1).strip()}'",
    ref=_RI,
)
_rule(r"^rm\s+-r\s+([^|]+)$", lambda m: f"Remove-Item -Recurse '{m.group(1).strip()}'", ref=_RI)
_rule(r"^rm\s+-f\s+([^|]+)$", lambda m: f"Remove-Item -Force '{m.group(1).strip()}'", ref=_RI)
_rule(r"^rm\s+([^|]+)$", lambda m: f"Remove-Item '{m.group(1).strip()}'", ref=_RI)

# ── cp / mv ───────────────────────────────────────────────────────────────────
_rule(
    r"^cp\s+-r\s+(\S+)\s+(\S+)$",
    lambda m: f"Copy-Item -Recurse '{m.group(1)}' '{m.group(2)}'",
    ref=_CI,
)
_rule(r"^cp\s+(\S+)\s+(\S+)$", lambda m: f"Copy-Item '{m.group(1)}' '{m.group(2)}'", ref=_CI)
_rule(r"^mv\s+(\S+)\s+(\S+)$", lambda m: f"Move-Item '{m.group(1)}' '{m.group(2)}'", ref=_MI)

# ── touch / ln ────────────────────────────────────────────────────────────────
_rule(
    r"^touch\s+([^|]+)$",
    lambda m: f"New-Item -ItemType File -Force '{m.group(1).strip()}'",
    ref=_NI,
)
_rule(
    r"^ln\s+-s\s+(\S+)\s+(\S+)$",
    lambda m: f"New-Item -ItemType SymbolicLink -Name '{m.group(2)}' -Target '{m.group(1)}'",
    ref=_NI,
)
_rule(
    r"^ln\s+(\S+)\s+(\S+)$",
    lambda m: f"New-Item -ItemType HardLink -Name '{m.group(2)}' -Target '{m.group(1)}'",
    ref=_NI,
)

# ── echo / printf ─────────────────────────────────────────────────────────────
_WO_ENV = (
    "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/write-output"
)
_rule(
    r"^echo\s+\$(\w+)$",
    lambda m: f"$env:{m.group(1)}",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables",
)
_rule(
    r"^echo\s+(.+)\s*>>\s*(.+)$",
    lambda m: f"Add-Content '{m.group(2).strip()}' '{m.group(1).strip()}'",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/add-content",
)
_rule(
    r"^echo\s+(.+)\s*>\s*(.+)$",
    lambda m: f"Set-Content '{m.group(2).strip()}' '{m.group(1).strip()}'",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/set-content",
)
_rule(r"^echo\s+([^|]+)$", lambda m: f"Write-Output '{m.group(1).strip()}'", ref=_WO_ENV)
_rule(r"^printf\s+'([^']+)'$", lambda m: f"Write-Output '{m.group(1)}'", ref=_WO_ENV)

# ── export / env / unset ──────────────────────────────────────────────────────
_ENV_REF = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables"
_rule(
    r"^export\s+(\w+)=(.+)$",
    lambda m: f"$env:{m.group(1)} = '{m.group(2).strip()}'",
    ref=_ENV_REF,
)
_rule(r"^unset\s+(\w+)$", lambda m: f"Remove-Item Env:\\{m.group(1)}", ref=_ENV_REF)
_rule(r"^env\s*$", "Get-ChildItem Env:", ref=_ENV_REF)
_rule(r"^printenv\s+(\w+)$", lambda m: f"$env:{m.group(1)}", ref=_ENV_REF)
_rule(r"^printenv\s*$", "Get-ChildItem Env:", ref=_ENV_REF)

# ── process / service ─────────────────────────────────────────────────────────
_rule(r"^ps\s+(aux|ef|-ef|-a|-e)\s*$", "Get-Process", ref=_GP)
_rule(r"^ps\s+(aux|ef|-ef|-a|-e)\s*\|", "Get-Process |", ref=_GP)
_rule(r"^pgrep\s+(-l\s+)?(\S+)$", lambda m: f"Get-Process -Name '*{m.group(2)}*'", ref=_GP)
_rule(r"^pkill\s+(-9\s+)?(\S+)$", lambda m: f"Stop-Process -Name '{m.group(2)}' -Force", ref=_SP)
_rule(r"^kill\s+-9\s+(\d+)$", lambda m: f"Stop-Process -Id {m.group(1)} -Force", ref=_SP)
_rule(r"^kill\s+(-SIGTERM\s+)?(\d+)$", lambda m: f"Stop-Process -Id {m.group(2)}", ref=_SP)
_rule(r"^killall\s+(\S+)$", lambda m: f"Stop-Process -Name '{m.group(1)}' -Force", ref=_SP)
_rule(
    r"^sleep\s+(\d+)$",
    lambda m: f"Start-Sleep {m.group(1)}",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/start-sleep",
)
_rule(
    r"^sleep\s+(\d+\.\d+)$",
    lambda m: f"Start-Sleep -Milliseconds {int(float(m.group(1)) * 1000)}",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/start-sleep",
)

# ── networking ────────────────────────────────────────────────────────────────
_rule(
    r"^curl\s+-X\s+POST\s+([^\s]+)\s+-d\s+'([^']+)'",
    lambda m: f"Invoke-RestMethod -Method POST -Uri '{m.group(1)}' -Body '{m.group(2)}' -ContentType 'application/json'",
    ref=_IRM,
)
_rule(
    r"^curl\s+-X\s+POST\s+([^\s]+)\s+-d\s+\"([^\"]+)\"",
    lambda m: f"Invoke-RestMethod -Method POST -Uri '{m.group(1)}' -Body '{m.group(2)}' -ContentType 'application/json'",
    ref=_IRM,
)
_rule(
    r"^curl\s+-X\s+(PUT|DELETE|PATCH)\s+([^\s]+)$",
    lambda m: f"Invoke-RestMethod -Method {m.group(1)} -Uri '{m.group(2)}'",
    ref=_IRM,
)
_rule(
    r"^curl\s+-o\s+(\S+)\s+([^\s]+)$",
    lambda m: f"Invoke-WebRequest -Uri '{m.group(2)}' -OutFile '{m.group(1)}'",
    ref=_IWR,
)
_rule(r"^curl\s+-s\s+([^|]+)$", lambda m: f"Invoke-RestMethod '{m.group(1).strip()}'", ref=_IRM)
_rule(r"^curl\s+([^|]+)$", lambda m: f"Invoke-WebRequest -Uri '{m.group(1).strip()}'", ref=_IWR)
_rule(
    r"^wget\s+-O\s+(\S+)\s+([^\s]+)$",
    lambda m: f"Invoke-WebRequest -Uri '{m.group(2)}' -OutFile '{m.group(1)}'",
    ref=_IWR,
)
_rule(
    r"^wget\s+-q\s+([^|]+)$",
    lambda m: f"Invoke-WebRequest -Uri '{m.group(1).strip()}' -OutFile 'download'",
    ref=_IWR,
)
_rule(
    r"^wget\s+([^|]+)$",
    lambda m: f"Invoke-WebRequest -Uri '{m.group(1).strip()}' -OutFile './download'",
    ref=_IWR,
)
_rule(
    r"^ping\s+-c\s+(\d+)\s+(\S+)$",
    lambda m: f"Test-Connection -ComputerName '{m.group(2)}' -Count {m.group(1)}",
    ref=_TC,
)
_rule(r"^ping\s+(\S+)$", lambda m: f"Test-Connection -ComputerName '{m.group(1)}'", ref=_TC)
_rule(
    r"^nslookup\s+(\S+)$",
    lambda m: f"Resolve-DnsName '{m.group(1)}'",
    ref="https://learn.microsoft.com/en-us/powershell/module/dnsclient/resolve-dnsname",
)
_rule(
    r"^host\s+(\S+)$",
    lambda m: f"Resolve-DnsName '{m.group(1)}'",
    ref="https://learn.microsoft.com/en-us/powershell/module/dnsclient/resolve-dnsname",
)
_rule(
    r"^netstat\s+-[a-z]+$",
    "Get-NetTCPConnection",
    ref="https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-nettcpconnection",
)
_rule(
    r"^ss\s+-[a-z]+$",
    "Get-NetTCPConnection | Where-Object { $_.State -eq 'Listen' }",
    ref="https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-nettcpconnection",
)

# ── text processing ───────────────────────────────────────────────────────────
_rule(r"^wc\s+-l\s+([^|]+)$", lambda m: f"(Get-Content '{m.group(1).strip()}').Count", ref=_MO)
_rule(
    r"^wc\s+-w\s+([^|]+)$",
    lambda m: f"((Get-Content '{m.group(1).strip()}') -split '\\s+').Count",
    ref=_MO,
)
_rule(r"^wc\s+-c\s+([^|]+)$", lambda m: f"(Get-Item '{m.group(1).strip()}').Length", ref=_MO)
_rule(r"\|\s*wc\s+-l\s*$", "| Measure-Object -Line", ref=_MO)
_rule(r"\|\s*wc\s*$", "| Measure-Object -Line", ref=_MO)
_rule(
    r"^head\s+-n\s+(\d+)\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(2).strip()}' -TotalCount {m.group(1)}",
    ref=_GC,
)
_rule(r"^head\s+([^|]+)$", lambda m: f"Get-Content '{m.group(1).strip()}' -TotalCount 10", ref=_GC)
_rule(
    r"^tail\s+-n\s+(\d+)\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(2).strip()}' -Tail {m.group(1)}",
    ref=_GC,
)
_rule(r"^tail\s+-f\s+([^|]+)$", lambda m: f"Get-Content -Wait '{m.group(1).strip()}'", ref=_GC)
_rule(r"^tail\s+([^|]+)$", lambda m: f"Get-Content '{m.group(1).strip()}' -Tail 10", ref=_GC)
_rule(
    r"^sort\s+-u\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | Sort-Object -Unique",
    ref=_SO,
)
_rule(
    r"^sort\s+-r\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | Sort-Object -Descending",
    ref=_SO,
)
_rule(r"^sort\s+([^|]+)$", lambda m: f"Get-Content '{m.group(1).strip()}' | Sort-Object", ref=_SO)
_rule(r"\|\s*sort\s+-u\s*$", "| Sort-Object -Unique", ref=_SO)
_rule(r"\|\s*sort\s+-r\s*$", "| Sort-Object -Descending", ref=_SO)
_rule(r"\|\s*sort\s*$", "| Sort-Object", ref=_SO)
_rule(
    r"\|\s*uniq\s+-c\s*$",
    "| Group-Object | Select-Object Count, Name",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/group-object",
)
_rule(r"\|\s*uniq\s*$", "| Select-Object -Unique", ref=_SEL)
_rule(r"\|\s*head\s+-n\s+(\d+)\s*$", lambda m: f"| Select-Object -First {m.group(1)}", ref=_SEL)
_rule(r"\|\s*head\s*$", "| Select-Object -First 10", ref=_SEL)
_rule(r"\|\s*tail\s+-n\s+(\d+)\s*$", lambda m: f"| Select-Object -Last {m.group(1)}", ref=_SEL)
_rule(r"\|\s*tail\s*$", "| Select-Object -Last 10", ref=_SEL)
_rule(
    r"\|\s*tee\s+([^\s]+)\s*$",
    lambda m: f"| Tee-Object -FilePath '{m.group(1)}'",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/tee-object",
)

# ── sed ───────────────────────────────────────────────────────────────────────
_rule(
    r"^sed\s+-i\s+'s/([^/]+)/([^/]*)/(g?)'\s+([^|]+)$",
    lambda m: f"(Get-Content '{m.group(4).strip()}') -replace '{m.group(1)}','{m.group(2)}' | Set-Content '{m.group(4).strip()}'",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/set-content",
)
_rule(
    r"^sed\s+'s/([^/]+)/([^/]*)/(g?)'\s+([^|]+)$",
    lambda m: f"(Get-Content '{m.group(4).strip()}') -replace '{m.group(1)}','{m.group(2)}'",
    ref=_GC,
)
_rule(
    r"^sed\s+'/\^#/d'\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | Where-Object {{ $_ -notmatch '^#' }}",
    ref=_WO,
)
_rule(
    r"^sed\s+'/\^\$/d'\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | Where-Object {{ $_.Trim() -ne '' }}",
    ref=_WO,
)

# ── awk ───────────────────────────────────────────────────────────────────────
_FE = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/foreach-object"
_rule(
    r"^awk\s+'\{print \$1\}'\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | ForEach-Object {{ ($_ -split '\\s+')[0] }}",
    ref=_FE,
)
_rule(
    r"^awk\s+'\{print \$NF\}'\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | ForEach-Object {{ ($_ -split '\\s+')[-1] }}",
    ref=_FE,
)

# ── archive ───────────────────────────────────────────────────────────────────
_rule(
    r"^tar\s+-czf\s+(\S+)\s+(.+)$",
    lambda m: f"Compress-Archive -Path '{m.group(2).strip()}' -DestinationPath '{m.group(1)}'",
    ref=_CA,
)
_rule(
    r"^tar\s+-(x|xz|xzf|xf)\s+(\S+)$",
    lambda m: f"Expand-Archive -Path '{m.group(2)}' -DestinationPath '.'",
    ref=_EA,
)
_rule(
    r"^tar\s+-(x|xz|xzf|xf)\s+(\S+)\s+-C\s+(\S+)$",
    lambda m: f"Expand-Archive -Path '{m.group(2)}' -DestinationPath '{m.group(3)}'",
    ref=_EA,
)
_rule(
    r"^zip\s+(-r\s+)?(\S+)\s+(.+)$",
    lambda m: f"Compress-Archive -Path '{m.group(3).strip()}' -DestinationPath '{m.group(2)}'",
    ref=_CA,
)
_rule(
    r"^unzip\s+(\S+)\s+-d\s+(\S+)$",
    lambda m: f"Expand-Archive -Path '{m.group(1)}' -DestinationPath '{m.group(2)}'",
    ref=_EA,
)
_rule(
    r"^unzip\s+(\S+)$",
    lambda m: f"Expand-Archive -Path '{m.group(1)}' -DestinationPath '.'",
    ref=_EA,
)

# ── disk / system info ────────────────────────────────────────────────────────
_PSD = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-psdrive"
_CIM = "https://learn.microsoft.com/en-us/powershell/module/cimcmdlets/get-ciminstance"
_rule(r"^df\s+-[hH]\s*$", "Get-PSDrive -PSProvider FileSystem", ref=_PSD)
_rule(r"^df\s*$", "Get-PSDrive -PSProvider FileSystem", ref=_PSD)
_rule(
    r"^du\s+-sh\s+([^|]+)$",
    lambda m: f"(Get-ChildItem -Recurse '{m.group(1).strip()}' | Measure-Object -Property Length -Sum).Sum / 1MB",
    ref=_MO,
)
_rule(
    r"^du\s+-sh\s*\.$",
    "(Get-ChildItem -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB",
    ref=_MO,
)
_rule(
    r"^uname\s+-a$",
    "Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-computerinfo",
)
_rule(r"^uname\s+-r$", "(Get-CimInstance Win32_OperatingSystem).Version", ref=_CIM)
_rule(r"^uname\s+-m$", "$env:PROCESSOR_ARCHITECTURE", ref=_ENV_REF)
_rule(r"^uname\s*$", "(Get-CimInstance Win32_OperatingSystem).Caption", ref=_CIM)
_rule(r"^hostname\s*$", "$env:COMPUTERNAME", ref=_ENV_REF)
_rule(r"^whoami\s*$", "$env:USERNAME", ref=_ENV_REF)
_rule(r"^date\s*$", "Get-Date", ref=_GD)
_rule(r"^date\s+'\+%Y-%m-%d'$", "Get-Date -Format 'yyyy-MM-dd'", ref=_GD)
_rule(r"^date\s+'\+%H:%M:%S'$", "Get-Date -Format 'HH:mm:ss'", ref=_GD)
_rule(
    r"^uptime\s*$", "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime", ref=_CIM
)
_rule(
    r"^clear\s*$",
    "Clear-Host",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/clear-host",
)
_rule(r"^history\s*$", "Get-History", ref=_GH)

# ── permissions ───────────────────────────────────────────────────────────────
_EXEC_POL = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy"
_ICACLS = "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/icacls"
_rule(
    r"^chmod\s+\+x\s+(.+)$",
    lambda m: f"# chmod +x not needed in PowerShell — rename to '{m.group(1).strip().replace('.sh', '.ps1')}' or use Set-ExecutionPolicy",
    ref=_EXEC_POL,
)
_rule(
    r"^chmod\s+[0-7]{3}\s+(.+)$",
    "# chmod not available in PowerShell — use icacls for ACL management",
    ref=_ICACLS,
)
_rule(
    r"^chown\s+.+$",
    "# chown not available in PowerShell — use icacls: icacls <path> /setowner <user>",
    ref=_ICACLS,
)
_rule(
    r"^sudo\s+(.+)$",
    lambda m: f"# Run as Administrator, then: {m.group(1)}",
    ref="https://learn.microsoft.com/en-us/powershell/scripting/learn/ps101/01-getting-started",
)

# ── directory navigation ──────────────────────────────────────────────────────
_rule(r"^pwd\s*$", "Get-Location", ref=_GL)
_rule(r"^cd\s+~\s*$", "Set-Location $HOME", ref=_SL)
_rule(r"^cd\s+/\s*$", "Set-Location C:\\", ref=_SL)
_rule(r"^cd\s+\.\.\s*$", "Set-Location ..", ref=_SL)
_rule(r"^cd\s+([^|]+)$", lambda m: f"Set-Location '{m.group(1).strip()}'", ref=_SL)
_rule(
    r"^pushd\s+([^|]+)$",
    lambda m: f"Push-Location '{m.group(1).strip()}'",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/push-location",
)
_rule(
    r"^popd\s*$",
    "Pop-Location",
    ref="https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/pop-location",
)

# ── which / type / man ────────────────────────────────────────────────────────
_GCM = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/get-command"
_rule(r"^which\s+(\S+)$", lambda m: f"(Get-Command '{m.group(1)}').Source", ref=_GCM)
_rule(r"^type\s+(\S+)$", lambda m: f"Get-Command '{m.group(1)}'", ref=_GCM)
_rule(r"^man\s+(\S+)$", lambda m: f"{m.group(1)} --help", ref=_GCM)

# ── python3 → python alias ────────────────────────────────────────────────────
_rule(r"^python3\s+(.+)$", lambda m: f"python {m.group(1)}", ref="https://docs.python.org/3/")
_rule(r"^python3$", "python", ref="https://docs.python.org/3/")

# ── source ────────────────────────────────────────────────────────────────────
_PROFILE_REF = "https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_profiles"
_rule(r"^\.\s+\.venv/bin/activate$", ".venv\\Scripts\\Activate.ps1", ref=_PROFILE_REF)
_rule(r"^source\s+\.venv/bin/activate$", ".venv\\Scripts\\Activate.ps1", ref=_PROFILE_REF)
_rule(r"^source\s+(.+)$", lambda m: f". '{m.group(1).strip()}'", ref=_PROFILE_REF)
_rule(r"^\.\s+~/\.bashrc$", ". $PROFILE", ref=_PROFILE_REF)
_rule(r"^source\s+~/.bashrc$", ". $PROFILE", ref=_PROFILE_REF)


def apply(command: str, shell: Shell) -> tuple[str, str]:
    """Translate *command* for *shell*, applying rules iteratively until stable.

    Multi-pass loop (max 6 iterations) handles bash pipe chains like
    ``cmd | grep foo | head -n 10`` — each pass replaces one bash fragment,
    and subsequent passes translate the remaining ones.

    Returns ``(translated, ref)`` where *ref* is the canonical docs URL of the
    first rule that fired (empty string when no rule matched or not applicable).
    Only translates for PowerShell/CMD targets.
    """
    if shell not in (Shell.POWERSHELL, Shell.CMD):
        return command, ""

    cmd = command.strip()
    first_ref: str = ""

    for _ in range(6):
        fired = False
        for pattern, replacement, ref in _RULES:
            m = pattern.search(cmd)
            if not m:
                continue
            if callable(replacement):
                res = replacement(m)
                if res.startswith("|") or m.group(0) != cmd:
                    candidate = pattern.sub(replacement, cmd)
                    if candidate == cmd:
                        continue  # rule matched but produced no change — try next
                    if not first_ref:
                        first_ref = ref
                    cmd = candidate
                    fired = True
                    break  # restart rule scan with updated cmd
                else:
                    return res, ref  # full-string match — nothing more to do
            else:
                repl_str = str(replacement)
                if repl_str.startswith("|") or m.group(0) != cmd:
                    candidate = pattern.sub(repl_str, cmd)
                    if candidate == cmd:
                        continue
                    if not first_ref:
                        first_ref = ref
                    cmd = candidate
                    fired = True
                    break
                else:
                    return repl_str, ref  # full-string match — nothing more to do
        if not fired:
            break  # no rule made progress — stable

    return cmd, first_ref
