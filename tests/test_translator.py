"""Tests for high-level translation behavior."""

from shellsage.models import OS, Shell, ShellContext
from shellsage.translator import translate


def test_known_native_passthrough_gets_ref():
    ctx = ShellContext(
        os=OS.LINUX,
        shell=Shell.BASH,
        shell_version="5.2",
        project_type="unknown",
        project_root=".",
    )

    result = translate("git status", ctx)

    assert result.source == "passthrough"
    assert result.translated == "git status"
    assert result.ref == "https://git-scm.com/docs"


def test_unknown_native_passthrough_does_not_get_fake_ref():
    ctx = ShellContext(
        os=OS.LINUX,
        shell=Shell.BASH,
        shell_version="5.2",
        project_type="unknown",
        project_root=".",
    )

    result = translate("project-local-helper --flag", ctx)

    assert result.source == "passthrough"
    assert result.translated == "project-local-helper --flag"
    assert result.ref == ""
