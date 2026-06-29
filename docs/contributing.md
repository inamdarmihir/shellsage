# Contributing

Thank you for your interest in contributing to ShellSage!

---

## Development Setup

```bash
git clone https://github.com/inamdarmihir/shellsage.git
cd shellsage
pip install -e ".[mcp,dev]"
```

---

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=shellsage --cov-report=term-missing

# Single file
pytest tests/test_rules.py -v
```

---

## Code Quality

```bash
# Lint + auto-fix
ruff check --fix shellsage/ tests/

# Format
ruff format shellsage/ tests/

# Type check
mypy shellsage/
```

All CI checks must pass (Python 3.10, 3.11, 3.12) before a PR is merged.

---

## Adding Translations

### Seed entries (`shellsage/seed.py`)

Each entry is a `{"bash": "...", "ps": "..."}` dict:

```python
# Good: concrete, correct, grouped
{"bash": "find . -name '*.csv'", "ps": "Get-ChildItem -Recurse -Filter '*.csv'"},
```

**Requirements:**

1. The PowerShell equivalent must be syntactically correct and semantically equivalent.
2. No duplicate `bash` keys (enforced by `_validate_seed()` at import time).
3. Group related entries under a comment.

**Test your addition:**

```bash
python -c "from shellsage.seed import SEED_TRANSLATIONS; print(len(SEED_TRANSLATIONS), 'entries OK')"
shellsage translate "find . -name '*.csv'"
```

### Rule patterns (`shellsage/rules.py`)

Rules use compiled regex patterns ordered most-specific → least-specific.

```python
# Pattern with a capture group
_rule(r"^mycommand\s+(\S+)$", lambda m: f"New-PSEquivalent '{m.group(1)}'")

# Constant replacement
_rule(r"^mycommand$", "New-PSEquivalent")
```

Add a test in `tests/test_rules.py`:

```python
def test_mycommand():
    assert "New-PSEquivalent" in apply("mycommand", Shell.POWERSHELL)
```

---

## Pull Request Guidelines

1. **One concern per PR** — don't mix unrelated changes.
2. **Tests required** — new translations should have at least one test.
3. **No breaking changes** to `Translation`, `CommandOutcome`, or `ShellContext` dataclass signatures without a major version bump.
4. **CI must pass** — all three matrix Python versions (3.10, 3.11, 3.12).

---

## Commit Style

Use conventional commits:

```
feat: add 15 archive/compression translation pairs
fix: correct tar -xzf pattern to handle -C flag
test: add grep -v pattern coverage
docs: add npm/yarn to README translation reference
```

---

## Project Structure

```
shellsage/
├── config.py        ← env-var settings (single source of truth)
├── models.py        ← ShellContext, Translation, CommandOutcome
├── rules.py         ← 100+ regex patterns (no DB needed)
├── seed.py          ← 400+ curated translations loaded at init
├── store.py         ← SQLite: translations + failures, BM25-style lookup
├── translator.py    ← 2-tier resolution pipeline
├── server.py        ← FastMCP server (4 tools)
├── daemon.py        ← Background process management
├── setup_wizard.py  ← Interactive installer with IDE auto-detection
└── cli.py           ← Click CLI (10 commands)
tests/
├── test_models.py
├── test_rules.py
└── test_seed.py
```
