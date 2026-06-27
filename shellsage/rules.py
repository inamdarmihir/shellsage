"""
Built-in rule-based bash → PowerShell translations.

These run with zero external dependencies — they are the cold-start safety net.
Rules are ordered from most-specific to least-specific so the first match wins.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from shellsage.models import Shell

# Each entry: (compiled_pattern, powershell_replacement_or_callable)
_Replacement = str | Callable[[re.Match[str]], str]
_RULES: list[tuple[re.Pattern[str], _Replacement]] = []


def _rule(pattern: str, replacement: _Replacement) -> None:
    _RULES.append((re.compile(pattern, re.IGNORECASE), replacement))


# ── shebang / heredoc guards (must come first) ───────────────────────────────
_rule(r"^#!/", "# ShellSage: shebang line not valid in PowerShell — use a .ps1 file")
_rule(
    r"<<\s*'?EOF'?",
    "# ShellSage: heredoc not supported in PowerShell — use @'...'@ here-string syntax",
)

# ── compound pipe rules (must come first — beat component rules at matching) ──
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*head\s+-n\s+(\d+)\s*$",
    lambda m: f"Get-Content '{m.group(1).strip()}' -TotalCount {m.group(2)}",
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*head\s*$",
    lambda m: f"Get-Content '{m.group(1).strip()}' -TotalCount 10",
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*tail\s+-n\s+(\d+)\s*$",
    lambda m: f"Get-Content '{m.group(1).strip()}' -Tail {m.group(2)}",
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*tail\s*$",
    lambda m: f"Get-Content '{m.group(1).strip()}' -Tail 10",
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*wc\s+-l\s*$",
    lambda m: f"(Get-Content '{m.group(1).strip()}').Count",
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*grep\s+-i\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Select-String -Pattern '{m.group(2).strip()}' -Path '{m.group(1).strip()}' -CaseSensitive:$false",
)
_rule(
    r"^cat\s+([^|]+?)\s*\|\s*grep\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Select-String -Pattern '{m.group(2).strip()}' -Path '{m.group(1).strip()}'",
)
_rule(
    r"^ls\s*\|\s*grep\s+-i\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Get-ChildItem | Where-Object {{ $_.Name -imatch '{m.group(1).strip()}' }}",
)
_rule(
    r"^ls\s*\|\s*grep\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Get-ChildItem | Where-Object {{ $_.Name -match '{m.group(1).strip()}' }}",
)
_rule(
    r"^find\s+\.\s+-name\s+['\"]?([^'\"]+)['\"]?\s*\|\s*xargs\s+grep\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Get-ChildItem -Recurse -Filter '{m.group(1)}' | Select-String '{m.group(2).strip()}'",
)
_rule(
    r"^find\s+\.\s+-type\s+f\s+\|\s*xargs\s+grep\s+['\"]?([^'\"|]+?)['\"]?\s*$",
    lambda m: f"Get-ChildItem -Recurse -File | Select-String '{m.group(1).strip()}'",
)

# ── file listing ──────────────────────────────────────────────────────────────
_rule(r"^ls\s+(-la?|-al)\s*$", "Get-ChildItem -Force")
_rule(r"^ls\s+(-la?|-al)\s+([^|]+)$", lambda m: f"Get-ChildItem -Force '{m.group(2).strip()}'")
_rule(r"^ls\s+-lh\s*$", "Get-ChildItem | Format-List Name, Length, LastWriteTime")
_rule(r"^ls\s+-R\s*$", "Get-ChildItem -Recurse")
_rule(r"^ls\s+([^|]+)$", lambda m: f"Get-ChildItem '{m.group(1).strip()}'")
_rule(r"^ls\s*$", "Get-ChildItem")

# ── grep (context lines + line numbers — must precede general grep rules) ────
_rule(
    r"^grep\s+-A\s+(\d+)\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(2).strip()}' -Path '{m.group(3).strip()}' -Context 0,{m.group(1)}",
)
_rule(
    r"^grep\s+-B\s+(\d+)\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(2).strip()}' -Path '{m.group(3).strip()}' -Context {m.group(1)},0",
)
_rule(
    r"^grep\s+-C\s+(\d+)\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(2).strip()}' -Path '{m.group(3).strip()}' -Context {m.group(1)},{m.group(1)}",
)
_rule(
    r"^grep\s+-n\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}' | Select-Object LineNumber, Line",
)
_rule(
    r"^grep\s+-rn\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Get-ChildItem -Recurse '{m.group(2).strip()}' | Select-String -Pattern '{m.group(1).strip()}' | Select-Object Path, LineNumber, Line",
)

# ── grep ──────────────────────────────────────────────────────────────────────
_rule(
    r"^grep\s+-ri\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Get-ChildItem -Recurse '{m.group(2).strip()}' | Select-String -Pattern '{m.group(1).strip()}' -CaseSensitive:$false",
)
_rule(
    r"^grep\s+-r[ni]*\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Get-ChildItem -Recurse '{m.group(2).strip()}' | Select-String -Pattern '{m.group(1).strip()}'",
)
_rule(
    r"^grep\s+-i\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}' -CaseSensitive:$false",
)
_rule(
    r"^grep\s+-v\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(2).strip()}' | Where-Object {{ $_ -notmatch '{m.group(1).strip()}' }}",
)
_rule(
    r"^grep\s+-c\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"(Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}').Count",
)
_rule(
    r"^grep\s+-l\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}' | Select-Object -ExpandProperty Path -Unique",
)
_rule(
    r"^grep\s+-E\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}'",
)
_rule(
    r"^grep\s+['\"]?([^|]+?)['\"]?\s+([^|]+)$",
    lambda m: f"Select-String -Pattern '{m.group(1).strip()}' -Path '{m.group(2).strip()}'",
)
_rule(
    r"\|\s*grep\s+-i\s+['\"]?([^|]+?)['\"]?\s*(?=\||$)",
    lambda m: f"| Where-Object {{ $_ -imatch '{m.group(1).strip()}' }}",
)
_rule(
    r"\|\s*grep\s+-v\s+['\"]?([^|]+?)['\"]?\s*(?=\||$)",
    lambda m: f"| Where-Object {{ $_ -notmatch '{m.group(1).strip()}' }}",
)
_rule(
    r"\|\s*grep\s+['\"]?([^|]+?)['\"]?\s*(?=\||$)",
    lambda m: f"| Where-Object {{ $_ -match '{m.group(1).strip()}' }}",
)

# ── find ──────────────────────────────────────────────────────────────────────
_rule(
    r"^find\s+\.\s+-type\s+f\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Recurse -File -Filter '{m.group(1)}'",
)
_rule(
    r"^find\s+\.\s+-type\s+d\s*$",
    "Get-ChildItem -Recurse -Directory",
)
_rule(
    r"^find\s+\.\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Recurse -Filter '{m.group(1)}'",
)
_rule(
    r"^find\s+(\S+)\s+-type\s+f\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Path '{m.group(1)}' -Recurse -File -Filter '{m.group(2)}'",
)
_rule(
    r"^find\s+(\S+)\s+-name\s+['\"]?(.+?)['\"]?$",
    lambda m: f"Get-ChildItem -Path '{m.group(1)}' -Recurse -Filter '{m.group(2)}'",
)
_rule(
    r"^find\s+\.\s+-mtime\s+-(\d+)$",
    lambda m: f"Get-ChildItem -Recurse | Where-Object {{ $_.LastWriteTime -gt (Get-Date).AddDays(-{m.group(1)}) }}",
)
_rule(
    r"^find\s+\.\s+-size\s+\+(\d+)[Mm]$",
    lambda m: f"Get-ChildItem -Recurse | Where-Object {{ $_.Length -gt {m.group(1)}MB }}",
)
_rule(
    r"^find\s+\.\s+-size\s+\+(\d+)[Kk]$",
    lambda m: f"Get-ChildItem -Recurse | Where-Object {{ $_.Length -gt {m.group(1)}KB }}",
)
_rule(
    r"^find\s+\.\s+-empty$",
    "Get-ChildItem -Recurse | Where-Object { $_.Length -eq 0 }",
)

# ── cat ───────────────────────────────────────────────────────────────────────
_rule(
    r"^cat\s+-n\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | ForEach-Object -Begin {{$i=1}} -Process {{\"{{0,4}}: {{1}}\" -f $i++,$_}}",
)
_rule(r"^cat\s+([^|]+)$", lambda m: f"Get-Content '{m.group(1).strip()}'")

# ── mkdir ─────────────────────────────────────────────────────────────────────
_rule(
    r"^mkdir\s+-p\s+([^|]+)$",
    lambda m: f"New-Item -ItemType Directory -Force -Path '{m.group(1).strip()}'",
)
_rule(r"^mkdir\s+([^|]+)$", lambda m: f"New-Item -ItemType Directory -Path '{m.group(1).strip()}'")

# ── rm ────────────────────────────────────────────────────────────────────────
_rule(r"^rm\s+-rf\s+([^|]+)$", lambda m: f"Remove-Item -Recurse -Force '{m.group(1).strip()}'")
_rule(r"^rm\s+-fr\s+([^|]+)$", lambda m: f"Remove-Item -Recurse -Force '{m.group(1).strip()}'")
_rule(r"^rm\s+-r\s+([^|]+)$", lambda m: f"Remove-Item -Recurse '{m.group(1).strip()}'")
_rule(r"^rm\s+-f\s+([^|]+)$", lambda m: f"Remove-Item -Force '{m.group(1).strip()}'")
_rule(r"^rm\s+([^|]+)$", lambda m: f"Remove-Item '{m.group(1).strip()}'")

# ── cp / mv ───────────────────────────────────────────────────────────────────
_rule(r"^cp\s+-r\s+(\S+)\s+(\S+)$", lambda m: f"Copy-Item -Recurse '{m.group(1)}' '{m.group(2)}'")
_rule(r"^cp\s+(\S+)\s+(\S+)$", lambda m: f"Copy-Item '{m.group(1)}' '{m.group(2)}'")
_rule(r"^mv\s+(\S+)\s+(\S+)$", lambda m: f"Move-Item '{m.group(1)}' '{m.group(2)}'")

# ── touch / ln ────────────────────────────────────────────────────────────────
_rule(r"^touch\s+([^|]+)$", lambda m: f"New-Item -ItemType File -Force '{m.group(1).strip()}'")
_rule(
    r"^ln\s+-s\s+(\S+)\s+(\S+)$",
    lambda m: f"New-Item -ItemType SymbolicLink -Name '{m.group(2)}' -Target '{m.group(1)}'",
)
_rule(
    r"^ln\s+(\S+)\s+(\S+)$",
    lambda m: f"New-Item -ItemType HardLink -Name '{m.group(2)}' -Target '{m.group(1)}'",
)

# ── echo / printf ─────────────────────────────────────────────────────────────
_rule(r"^echo\s+\$(\w+)$", lambda m: f"$env:{m.group(1)}")
_rule(
    r"^echo\s+(.+)\s*>>\s*(.+)$",
    lambda m: f"Add-Content '{m.group(2).strip()}' '{m.group(1).strip()}'",
)
_rule(
    r"^echo\s+(.+)\s*>\s*(.+)$",
    lambda m: f"Set-Content '{m.group(2).strip()}' '{m.group(1).strip()}'",
)
_rule(r"^echo\s+([^|]+)$", lambda m: f"Write-Output '{m.group(1).strip()}'")
_rule(r"^printf\s+'([^']+)'$", lambda m: f"Write-Output '{m.group(1)}'")

# ── export / env / unset ──────────────────────────────────────────────────────
_rule(
    r"^export\s+(\w+)=(.+)$",
    lambda m: f"$env:{m.group(1)} = '{m.group(2).strip()}'",
)
_rule(r"^unset\s+(\w+)$", lambda m: f"Remove-Item Env:\\{m.group(1)}")
_rule(r"^env\s*$", "Get-ChildItem Env:")
_rule(r"^printenv\s+(\w+)$", lambda m: f"$env:{m.group(1)}")
_rule(r"^printenv\s*$", "Get-ChildItem Env:")

# ── process / service ─────────────────────────────────────────────────────────
_rule(r"^ps\s+(aux|ef|-ef|-a|-e)\s*$", "Get-Process")
_rule(r"^ps\s+(aux|ef|-ef|-a|-e)\s*\|", "Get-Process |")
_rule(r"^pgrep\s+(-l\s+)?(\S+)$", lambda m: f"Get-Process -Name '*{m.group(2)}*'")
_rule(r"^pkill\s+(-9\s+)?(\S+)$", lambda m: f"Stop-Process -Name '{m.group(2)}' -Force")
_rule(r"^kill\s+-9\s+(\d+)$", lambda m: f"Stop-Process -Id {m.group(1)} -Force")
_rule(r"^kill\s+(-SIGTERM\s+)?(\d+)$", lambda m: f"Stop-Process -Id {m.group(2)}")
_rule(r"^killall\s+(\S+)$", lambda m: f"Stop-Process -Name '{m.group(1)}' -Force")
_rule(r"^sleep\s+(\d+)$", lambda m: f"Start-Sleep {m.group(1)}")
_rule(
    r"^sleep\s+(\d+\.\d+)$", lambda m: f"Start-Sleep -Milliseconds {int(float(m.group(1)) * 1000)}"
)

# ── networking ────────────────────────────────────────────────────────────────
_rule(
    r"^curl\s+-X\s+POST\s+([^\s]+)\s+-d\s+'([^']+)'",
    lambda m: f"Invoke-RestMethod -Method POST -Uri '{m.group(1)}' -Body '{m.group(2)}' -ContentType 'application/json'",
)
_rule(
    r"^curl\s+-X\s+POST\s+([^\s]+)\s+-d\s+\"([^\"]+)\"",
    lambda m: f"Invoke-RestMethod -Method POST -Uri '{m.group(1)}' -Body '{m.group(2)}' -ContentType 'application/json'",
)
_rule(
    r"^curl\s+-X\s+(PUT|DELETE|PATCH)\s+([^\s]+)$",
    lambda m: f"Invoke-RestMethod -Method {m.group(1)} -Uri '{m.group(2)}'",
)
_rule(
    r"^curl\s+-o\s+(\S+)\s+([^\s]+)$",
    lambda m: f"Invoke-WebRequest -Uri '{m.group(2)}' -OutFile '{m.group(1)}'",
)
_rule(r"^curl\s+-s\s+([^|]+)$", lambda m: f"Invoke-RestMethod '{m.group(1).strip()}'")
_rule(r"^curl\s+([^|]+)$", lambda m: f"Invoke-WebRequest -Uri '{m.group(1).strip()}'")
_rule(
    r"^wget\s+-O\s+(\S+)\s+([^\s]+)$",
    lambda m: f"Invoke-WebRequest -Uri '{m.group(2)}' -OutFile '{m.group(1)}'",
)
_rule(
    r"^wget\s+-q\s+([^|]+)$",
    lambda m: f"Invoke-WebRequest -Uri '{m.group(1).strip()}' -OutFile 'download'",
)
_rule(
    r"^wget\s+([^|]+)$",
    lambda m: f"Invoke-WebRequest -Uri '{m.group(1).strip()}' -OutFile './download'",
)
_rule(
    r"^ping\s+-c\s+(\d+)\s+(\S+)$",
    lambda m: f"Test-Connection -ComputerName '{m.group(2)}' -Count {m.group(1)}",
)
_rule(r"^ping\s+(\S+)$", lambda m: f"Test-Connection -ComputerName '{m.group(1)}'")
_rule(r"^nslookup\s+(\S+)$", lambda m: f"Resolve-DnsName '{m.group(1)}'")
_rule(r"^host\s+(\S+)$", lambda m: f"Resolve-DnsName '{m.group(1)}'")
_rule(r"^netstat\s+-[a-z]+$", "Get-NetTCPConnection")
_rule(r"^ss\s+-[a-z]+$", "Get-NetTCPConnection | Where-Object { $_.State -eq 'Listen' }")

# ── text processing ───────────────────────────────────────────────────────────
_rule(r"^wc\s+-l\s+([^|]+)$", lambda m: f"(Get-Content '{m.group(1).strip()}').Count")
_rule(
    r"^wc\s+-w\s+([^|]+)$", lambda m: f"((Get-Content '{m.group(1).strip()}') -split '\\s+').Count"
)
_rule(r"^wc\s+-c\s+([^|]+)$", lambda m: f"(Get-Item '{m.group(1).strip()}').Length")
_rule(r"\|\s*wc\s+-l\s*$", "| Measure-Object -Line")
_rule(r"\|\s*wc\s*$", "| Measure-Object -Line")
_rule(
    r"^head\s+-n\s+(\d+)\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(2).strip()}' -TotalCount {m.group(1)}",
)
_rule(r"^head\s+([^|]+)$", lambda m: f"Get-Content '{m.group(1).strip()}' -TotalCount 10")
_rule(
    r"^tail\s+-n\s+(\d+)\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(2).strip()}' -Tail {m.group(1)}",
)
_rule(r"^tail\s+-f\s+([^|]+)$", lambda m: f"Get-Content -Wait '{m.group(1).strip()}'")
_rule(r"^tail\s+([^|]+)$", lambda m: f"Get-Content '{m.group(1).strip()}' -Tail 10")
_rule(
    r"^sort\s+-u\s+([^|]+)$", lambda m: f"Get-Content '{m.group(1).strip()}' | Sort-Object -Unique"
)
_rule(
    r"^sort\s+-r\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | Sort-Object -Descending",
)
_rule(r"^sort\s+([^|]+)$", lambda m: f"Get-Content '{m.group(1).strip()}' | Sort-Object")
_rule(r"\|\s*sort\s+-u\s*$", "| Sort-Object -Unique")
_rule(r"\|\s*sort\s+-r\s*$", "| Sort-Object -Descending")
_rule(r"\|\s*sort\s*$", "| Sort-Object")
_rule(r"\|\s*uniq\s+-c\s*$", "| Group-Object | Select-Object Count, Name")
_rule(r"\|\s*uniq\s*$", "| Select-Object -Unique")
_rule(r"\|\s*head\s+-n\s+(\d+)\s*$", lambda m: f"| Select-Object -First {m.group(1)}")
_rule(r"\|\s*head\s*$", "| Select-Object -First 10")
_rule(r"\|\s*tail\s+-n\s+(\d+)\s*$", lambda m: f"| Select-Object -Last {m.group(1)}")
_rule(r"\|\s*tail\s*$", "| Select-Object -Last 10")
_rule(r"\|\s*tee\s+([^\s]+)\s*$", lambda m: f"| Tee-Object -FilePath '{m.group(1)}'")

# ── sed ───────────────────────────────────────────────────────────────────────
_rule(
    r"^sed\s+-i\s+'s/([^/]+)/([^/]*)/(g?)'\s+([^|]+)$",
    lambda m: f"(Get-Content '{m.group(4).strip()}') -replace '{m.group(1)}','{m.group(2)}' | Set-Content '{m.group(4).strip()}'",
)
_rule(
    r"^sed\s+'s/([^/]+)/([^/]*)/(g?)'\s+([^|]+)$",
    lambda m: f"(Get-Content '{m.group(4).strip()}') -replace '{m.group(1)}','{m.group(2)}'",
)
_rule(
    r"^sed\s+'/\^#/d'\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | Where-Object {{ $_ -notmatch '^#' }}",
)
_rule(
    r"^sed\s+'/\^\$/d'\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | Where-Object {{ $_.Trim() -ne '' }}",
)

# ── awk ───────────────────────────────────────────────────────────────────────
_rule(
    r"^awk\s+'\{print \$1\}'\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | ForEach-Object {{ ($_ -split '\\s+')[0] }}",
)
_rule(
    r"^awk\s+'\{print \$NF\}'\s+([^|]+)$",
    lambda m: f"Get-Content '{m.group(1).strip()}' | ForEach-Object {{ ($_ -split '\\s+')[-1] }}",
)

# ── archive ───────────────────────────────────────────────────────────────────
_rule(
    r"^tar\s+-czf\s+(\S+)\s+(.+)$",
    lambda m: f"Compress-Archive -Path '{m.group(2).strip()}' -DestinationPath '{m.group(1)}'",
)
_rule(
    r"^tar\s+-(x|xz|xzf|xf)\s+(\S+)$",
    lambda m: f"Expand-Archive -Path '{m.group(2)}' -DestinationPath '.'",
)
_rule(
    r"^tar\s+-(x|xz|xzf|xf)\s+(\S+)\s+-C\s+(\S+)$",
    lambda m: f"Expand-Archive -Path '{m.group(2)}' -DestinationPath '{m.group(3)}'",
)
_rule(
    r"^zip\s+(-r\s+)?(\S+)\s+(.+)$",
    lambda m: f"Compress-Archive -Path '{m.group(3).strip()}' -DestinationPath '{m.group(2)}'",
)
_rule(
    r"^unzip\s+(\S+)\s+-d\s+(\S+)$",
    lambda m: f"Expand-Archive -Path '{m.group(1)}' -DestinationPath '{m.group(2)}'",
)
_rule(
    r"^unzip\s+(\S+)$",
    lambda m: f"Expand-Archive -Path '{m.group(1)}' -DestinationPath '.'",
)

# ── disk / system info ────────────────────────────────────────────────────────
_rule(r"^df\s+-[hH]\s*$", "Get-PSDrive -PSProvider FileSystem")
_rule(r"^df\s*$", "Get-PSDrive -PSProvider FileSystem")
_rule(
    r"^du\s+-sh\s+([^|]+)$",
    lambda m: f"(Get-ChildItem -Recurse '{m.group(1).strip()}' | Measure-Object -Property Length -Sum).Sum / 1MB",
)
_rule(
    r"^du\s+-sh\s*\.$", "(Get-ChildItem -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"
)
_rule(r"^uname\s+-a$", "Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion")
_rule(r"^uname\s+-r$", "(Get-CimInstance Win32_OperatingSystem).Version")
_rule(r"^uname\s+-m$", "$env:PROCESSOR_ARCHITECTURE")
_rule(r"^uname\s*$", "(Get-CimInstance Win32_OperatingSystem).Caption")
_rule(r"^hostname\s*$", "$env:COMPUTERNAME")
_rule(r"^whoami\s*$", "$env:USERNAME")
_rule(r"^date\s*$", "Get-Date")
_rule(r"^date\s+'\+%Y-%m-%d'$", "Get-Date -Format 'yyyy-MM-dd'")
_rule(r"^date\s+'\+%H:%M:%S'$", "Get-Date -Format 'HH:mm:ss'")
_rule(r"^uptime\s*$", "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime")
_rule(r"^clear\s*$", "Clear-Host")
_rule(r"^history\s*$", "Get-History")

# ── permissions ───────────────────────────────────────────────────────────────
_rule(
    r"^chmod\s+\+x\s+(.+)$",
    lambda m: f"# chmod +x not needed in PowerShell — rename to '{m.group(1).strip().replace('.sh', '.ps1')}' or use Set-ExecutionPolicy",
)
_rule(
    r"^chmod\s+[0-7]{{3}}\s+(.+)$",
    "# chmod not available in PowerShell — use icacls for ACL management",
)
_rule(
    r"^chown\s+.+$",
    "# chown not available in PowerShell — use icacls: icacls <path> /setowner <user>",
)
_rule(r"^sudo\s+(.+)$", lambda m: f"# Run as Administrator, then: {m.group(1)}")

# ── directory navigation ──────────────────────────────────────────────────────
_rule(r"^pwd\s*$", "Get-Location")
_rule(r"^cd\s+~\s*$", "Set-Location $HOME")
_rule(r"^cd\s+/\s*$", "Set-Location C:\\")
_rule(r"^cd\s+\.\.\s*$", "Set-Location ..")
_rule(r"^cd\s+([^|]+)$", lambda m: f"Set-Location '{m.group(1).strip()}'")
_rule(r"^pushd\s+([^|]+)$", lambda m: f"Push-Location '{m.group(1).strip()}'")
_rule(r"^popd\s*$", "Pop-Location")

# ── which / type / man ────────────────────────────────────────────────────────
_rule(r"^which\s+(\S+)$", lambda m: f"(Get-Command '{m.group(1)}').Source")
_rule(r"^type\s+(\S+)$", lambda m: f"Get-Command '{m.group(1)}'")
_rule(r"^man\s+(\S+)$", lambda m: f"{m.group(1)} --help")

# ── python3 → python alias ────────────────────────────────────────────────────
_rule(r"^python3\s+(.+)$", lambda m: f"python {m.group(1)}")
_rule(r"^python3$", "python")

# ── source ───────────────────────────────────────────────────────────────────
_rule(r"^\.\s+\.venv/bin/activate$", ".venv\\Scripts\\Activate.ps1")
_rule(r"^source\s+\.venv/bin/activate$", ".venv\\Scripts\\Activate.ps1")
_rule(r"^source\s+(.+)$", lambda m: f". '{m.group(1).strip()}'")
_rule(r"^\.\s+~/\.bashrc$", ". $PROFILE")
_rule(r"^source\s+~/.bashrc$", ". $PROFILE")


def apply(command: str, shell: Shell) -> str:
    """Translate *command* for *shell*, applying rules iteratively until stable.

    Multi-pass loop (max 6 iterations) handles bash pipe chains like
    ``cmd | grep foo | head -n 10`` — each pass replaces one bash fragment,
    and subsequent passes translate the remaining ones.

    Returns the translated string, or the original if no rule matched.
    Only translates for PowerShell/CMD targets.
    """
    if shell not in (Shell.POWERSHELL, Shell.CMD):
        return command

    cmd = command.strip()

    for _ in range(6):
        fired = False
        for pattern, replacement in _RULES:
            m = pattern.search(cmd)
            if not m:
                continue
            if callable(replacement):
                res = replacement(m)
                if res.startswith("|") or m.group(0) != cmd:
                    candidate = pattern.sub(replacement, cmd)
                    if candidate == cmd:
                        continue  # rule matched but produced no change — try next
                    cmd = candidate
                    fired = True
                    break  # restart rule scan with updated cmd
                else:
                    return res  # full-string match — nothing more to do
            else:
                repl_str = str(replacement)
                if repl_str.startswith("|") or m.group(0) != cmd:
                    candidate = pattern.sub(repl_str, cmd)
                    if candidate == cmd:
                        continue
                    cmd = candidate
                    fired = True
                    break
                else:
                    return repl_str  # full-string match — nothing more to do
        if not fired:
            break  # no rule made progress — stable

    return cmd
