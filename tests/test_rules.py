"""Tests for rule-based bash→PowerShell translation."""

from shellsage.models import Shell
from shellsage.rules import apply


# Helper: run apply() and assert the result
def ps(cmd: str) -> str:
    return apply(cmd, Shell.POWERSHELL)


def passthrough(cmd: str) -> str:
    """Commands that should pass through unchanged on bash."""
    return apply(cmd, Shell.BASH)


# ── ls ────────────────────────────────────────────────────────────────────────


def test_ls_bare():
    assert ps("ls") == "Get-ChildItem"


def test_ls_la():
    assert ps("ls -la") == "Get-ChildItem -Force"


def test_ls_l():
    assert ps("ls -l") == "Get-ChildItem -Force"


def test_ls_with_path():
    result = ps("ls -la /tmp")
    assert "Get-ChildItem" in result
    assert "/tmp" in result


# ── grep ─────────────────────────────────────────────────────────────────────


def test_grep_recursive():
    result = ps("grep -r 'TODO' .")
    assert "Select-String" in result or "Get-ChildItem" in result


def test_grep_pipe():
    result = ps("ls | grep '*.py'")
    assert "Where-Object" in result or "Select-String" in result


def test_grep_file():
    result = ps("grep 'error' log.txt")
    assert "Select-String" in result


# ── find ──────────────────────────────────────────────────────────────────────


def test_find_name():
    result = ps("find . -name '*.py'")
    assert "Get-ChildItem" in result
    assert "*.py" in result


def test_find_type_file():
    result = ps("find . -type f -name '*.txt'")
    assert "Get-ChildItem" in result
    assert "-File" in result


def test_find_with_path():
    result = ps("find src/ -name '*.js'")
    assert "Get-ChildItem" in result
    assert "*.js" in result


# ── cat / head / tail ─────────────────────────────────────────────────────────


def test_cat():
    result = ps("cat README.md")
    assert "Get-Content" in result
    assert "README.md" in result


def test_head():
    result = ps("head -n 20 file.txt")
    assert "Get-Content" in result
    assert "20" in result


def test_tail():
    result = ps("tail -n 50 app.log")
    assert "Get-Content" in result
    assert "50" in result


def test_tail_follow():
    result = ps("tail -f server.log")
    assert "-Wait" in result


# ── mkdir / rm / cp / mv ──────────────────────────────────────────────────────


def test_mkdir_p():
    result = ps("mkdir -p src/utils")
    assert "New-Item" in result
    assert "-Force" in result


def test_rm_rf():
    result = ps("rm -rf node_modules")
    assert "Remove-Item" in result
    assert "-Recurse" in result
    assert "-Force" in result


def test_rm_f():
    result = ps("rm -f output.log")
    assert "Remove-Item" in result
    assert "-Force" in result


def test_cp_r():
    result = ps("cp -r src/ backup/")
    assert "Copy-Item" in result
    assert "-Recurse" in result


def test_mv():
    result = ps("mv old.txt new.txt")
    assert "Move-Item" in result


# ── env / export ──────────────────────────────────────────────────────────────


def test_export():
    result = ps("export NODE_ENV=production")
    assert "$env:NODE_ENV" in result
    assert "production" in result


def test_env():
    result = ps("env")
    assert "Env:" in result


def test_printenv():
    result = ps("printenv PATH")
    assert "$env:PATH" in result


# ── process ───────────────────────────────────────────────────────────────────


def test_ps_aux():
    result = ps("ps aux")
    assert "Get-Process" in result


def test_kill():
    result = ps("kill -9 1234")
    assert "Stop-Process" in result
    assert "1234" in result


# ── network ───────────────────────────────────────────────────────────────────


def test_curl_silent():
    result = ps("curl -s https://api.github.com")
    assert "Invoke-RestMethod" in result


def test_curl():
    result = ps("curl https://example.com")
    assert "Invoke-WebRequest" in result


def test_wget():
    result = ps("wget https://example.com/file.zip")
    assert "Invoke-WebRequest" in result


# ── text processing ───────────────────────────────────────────────────────────


def test_wc_l():
    result = ps("wc -l file.txt")
    assert "Get-Content" in result
    assert "Count" in result


def test_echo():
    result = ps("echo 'hello world'")
    assert "Write-Output" in result


def test_pipe_sort():
    result = ps("ls | sort")
    assert "Sort-Object" in result


def test_pipe_sort_unique():
    result = ps("ls | sort -u")
    assert "Sort-Object" in result
    assert "Unique" in result


# ── shebang / heredoc guards ──────────────────────────────────────────────────


def test_shebang_flagged():
    result = ps("#!/usr/bin/env python3")
    assert "ShellSage" in result


def test_heredoc_flagged():
    result = ps("cat << 'EOF'")
    assert "ShellSage" in result


# ── passthrough on bash ───────────────────────────────────────────────────────


def test_bash_passthrough():
    assert passthrough("ls -la") == "ls -la"
    assert passthrough("grep -r 'TODO' .") == "grep -r 'TODO' ."
    assert passthrough("rm -rf node_modules") == "rm -rf node_modules"


def test_no_translation_needed():
    # git commands are identical on both shells
    result = ps("git status")
    assert result == "git status"


# ── edge cases ────────────────────────────────────────────────────────────────


def test_empty_string():
    assert ps("") == ""


def test_whitespace_only():
    result = ps("   ")
    assert result.strip() == ""


def test_unknown_command_passes_through():
    exotic = "some-unknown-tool --flag value"
    assert ps(exotic) == exotic
