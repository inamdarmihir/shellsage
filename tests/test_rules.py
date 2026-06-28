"""Tests for rule-based bash→PowerShell translation."""

from shellsage.models import Shell
from shellsage.rules import apply


# Helper: run apply() and assert the result (only the translated string)
def ps(cmd: str) -> str:
    translated, _ref = apply(cmd, Shell.POWERSHELL)
    return translated


def ps_ref(cmd: str) -> str:
    """Return the ref URL for a PowerShell translation."""
    _translated, ref = apply(cmd, Shell.POWERSHELL)
    return ref


def passthrough(cmd: str) -> str:
    """Commands that should pass through unchanged on bash."""
    translated, _ref = apply(cmd, Shell.BASH)
    return translated


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


# ── grep context lines & line numbers ────────────────────────────────────────


def test_grep_n_line_numbers():
    result = ps("grep -n 'error' app.log")
    assert "Select-String" in result
    assert "LineNumber" in result


def test_grep_rn_recursive_line_numbers():
    result = ps("grep -rn 'TODO' src/")
    assert "Select-String" in result
    assert "LineNumber" in result
    assert "Path" in result


def test_grep_A_context_after():
    result = ps("grep -A 3 'error' app.log")
    assert "Select-String" in result
    assert "-Context 0,3" in result


def test_grep_B_context_before():
    result = ps("grep -B 2 'error' app.log")
    assert "Select-String" in result
    assert "-Context 2,0" in result


def test_grep_C_context_both():
    result = ps("grep -C 5 'error' app.log")
    assert "Select-String" in result
    assert "-Context 5,5" in result


# ── compound cat | filter rules ───────────────────────────────────────────────


def test_cat_pipe_head_n():
    result = ps("cat bigfile.py | head -n 50")
    assert "Get-Content" in result
    assert "bigfile.py" in result
    assert "-TotalCount 50" in result
    # must NOT contain bare 'head' (would be untranslated bash)
    assert "head" not in result


def test_cat_pipe_head_bare():
    result = ps("cat bigfile.py | head")
    assert "-TotalCount 10" in result
    assert "head" not in result


def test_cat_pipe_tail_n():
    result = ps("cat app.log | tail -n 20")
    assert "Get-Content" in result
    assert "-Tail 20" in result
    assert "tail" not in result


def test_cat_pipe_wc_l():
    result = ps("cat file.txt | wc -l")
    assert "Get-Content" in result
    assert "Count" in result
    assert "wc" not in result


def test_cat_pipe_grep():
    result = ps("cat app.log | grep 'error'")
    assert "Select-String" in result
    assert "app.log" in result
    assert "error" in result
    assert "cat" not in result


def test_cat_pipe_grep_i():
    result = ps("cat app.log | grep -i 'ERROR'")
    assert "Select-String" in result
    assert "CaseSensitive" in result
    assert "cat" not in result


# ── ls | grep ─────────────────────────────────────────────────────────────────


def test_ls_pipe_grep():
    result = ps("ls | grep '.py'")
    assert "Get-ChildItem" in result
    assert "Where-Object" in result
    assert "grep" not in result


def test_ls_pipe_grep_i():
    result = ps("ls | grep -i 'test'")
    assert "Get-ChildItem" in result
    assert "imatch" in result


# ── find | xargs grep ─────────────────────────────────────────────────────────


def test_find_xargs_grep():
    result = ps("find . -name '*.py' | xargs grep 'import'")
    assert "Get-ChildItem" in result
    assert "Select-String" in result
    assert "xargs" not in result
    assert "grep" not in result


def test_find_type_f_xargs_grep():
    result = ps("find . -type f | xargs grep 'TODO'")
    assert "Get-ChildItem" in result
    assert "Select-String" in result
    assert "xargs" not in result


# ── multi-pass: pipe chains of bash filters ───────────────────────────────────


def test_multipass_pipe_grep_then_head():
    """grep | head — both filters translated even though they're stacked."""
    result = ps("some_tool | grep 'error' | head -n 5")
    assert "Where-Object" in result
    assert "Select-Object -First 5" in result
    assert "grep" not in result
    assert "head" not in result


def test_multipass_pipe_grep_then_sort():
    result = ps("some_tool | grep 'warn' | sort")
    assert "Where-Object" in result
    assert "Sort-Object" in result
    assert "grep" not in result
    assert "sort" not in result


def test_multipass_pipe_grep_v_then_head():
    result = ps("some_tool | grep -v 'debug' | head -n 10")
    assert "notmatch" in result
    assert "Select-Object -First 10" in result


# ── ref / citation tests ──────────────────────────────────────────────────────


def test_ref_returned_for_ls():
    ref = ps_ref("ls")
    assert ref.startswith("https://learn.microsoft.com"), ref
    assert "get-childitem" in ref.lower()


def test_ref_returned_for_grep():
    ref = ps_ref("grep 'error' app.log")
    assert ref.startswith("https://learn.microsoft.com"), ref
    assert "select-string" in ref.lower()


def test_ref_returned_for_rm():
    ref = ps_ref("rm -rf dist/")
    assert ref.startswith("https://learn.microsoft.com"), ref
    assert "remove-item" in ref.lower()


def test_ref_returned_for_curl():
    ref = ps_ref("curl https://api.example.com")
    assert ref.startswith("https://learn.microsoft.com"), ref


def test_ref_returned_for_find():
    ref = ps_ref("find . -name '*.py'")
    assert ref.startswith("https://learn.microsoft.com"), ref
    assert "get-childitem" in ref.lower()


def test_no_ref_on_bash_passthrough():
    """apply() on bash shell returns empty ref — no translation needed."""
    _translated, ref = apply("ls -la", Shell.BASH)
    assert ref == ""


def test_apply_returns_tuple():
    result = apply("ls", Shell.POWERSHELL)
    assert isinstance(result, tuple)
    assert len(result) == 2
    translated, ref = result
    assert isinstance(translated, str)
    assert isinstance(ref, str)
