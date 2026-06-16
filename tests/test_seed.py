"""Validate seed translation data integrity."""

from shellsage.seed import SEED_TRANSLATIONS, select_seed_translations


def test_seed_not_empty():
    assert len(SEED_TRANSLATIONS) > 0


def test_seed_minimum_count():
    assert len(SEED_TRANSLATIONS) >= 50


def test_select_seed_translations_respects_limit():
    selected = select_seed_translations(10)
    assert len(selected) == 10
    assert selected == SEED_TRANSLATIONS[:10]


def test_select_seed_translations_all_when_limit_is_none():
    assert select_seed_translations(None) == SEED_TRANSLATIONS


def test_seed_all_have_bash_and_ps():
    for entry in SEED_TRANSLATIONS:
        assert "bash" in entry, f"Missing 'bash' key: {entry}"
        assert "ps" in entry, f"Missing 'ps' key: {entry}"


def test_seed_no_empty_values():
    for entry in SEED_TRANSLATIONS:
        assert entry["bash"].strip(), f"Empty bash command: {entry}"
        assert entry["ps"].strip(), f"Empty ps command: {entry}"


def test_seed_no_duplicates():
    bash_cmds = [e["bash"] for e in SEED_TRANSLATIONS]
    assert len(bash_cmds) == len(set(bash_cmds)), "Duplicate bash commands in seed data"


def test_seed_bash_commands_are_bash_like():
    """Sanity check: bash commands shouldn't contain PowerShell patterns."""
    ps_patterns = ["Get-ChildItem", "Invoke-", "Write-Output", "$env:"]
    for entry in SEED_TRANSLATIONS:
        for pat in ps_patterns:
            assert pat not in entry["bash"], f"Bash command looks like PowerShell: {entry['bash']}"
