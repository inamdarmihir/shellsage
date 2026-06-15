# Contributing to ShellSage

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/shellsage/shellsage.git
cd shellsage
pip install -e ".[mcp,dev]"
```

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=shellsage --cov-report=term-missing

# Single file
pytest tests/test_rules.py -v
```

## Code Quality

```bash
# Lint + auto-fix
ruff check --fix shellsage/ tests/

# Format
ruff format shellsage/ tests/

# Type check
mypy shellsage/
```

All CI checks must pass before a PR is merged.

## Adding Translations

### Adding seed entries (`shellsage/seed.py`)

Each entry is a `{"bash": "...", "ps": "..."}` dict. Requirements:

1. The PowerShell equivalent must be **syntactically correct** and **semantically equivalent**.
2. No duplicate `bash` keys (enforced by `_validate_seed()` at import time).
3. Group related entries under a comment.

```python
# Good: concrete, correct, grouped
{"bash": "find . -name '*.csv'", "ps": "Get-ChildItem -Recurse -Filter '*.csv'"},
```

Test your addition:

```bash
python -c "from shellsage.seed import SEED_TRANSLATIONS; print(len(SEED_TRANSLATIONS), 'entries OK')"
shellsage translate "find . -name '*.csv'"   # verify rule also works
```

### Adding rules (`shellsage/rules.py`)

Rules use compiled regex patterns and are ordered most-specific → least-specific.

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

## Pull Request Guidelines

1. **One concern per PR** — don't mix unrelated changes.
2. **Tests required** — new translations should have at least one test.
3. **No breaking changes** to the `Translation`, `CommandOutcome`, or `ShellContext` dataclass signatures without a major version bump.
4. **CI must pass** — all three matrix Python versions (3.10, 3.11, 3.12).

## Commit Style

Use conventional commits:

```
feat: add 15 archive/compression translation pairs
fix: correct tar -xzf pattern to handle -C flag
test: add grep -v pattern coverage
docs: add npm/yarn to README translation reference
```

## Project Structure

```
shellsage/
├── config.py        ← env-var settings (single source of truth)
├── models.py        ← ShellContext, Translation, CommandOutcome
├── rules.py         ← 100+ regex patterns (no Qdrant needed)
├── seed.py          ← 300+ curated translations loaded at init
├── embedder.py      ← lazy all-MiniLM-L6-v2
├── store.py         ← Qdrant client (3 collections, BM25 + cosine + RRF)
├── translator.py    ← 3-tier resolution pipeline
├── server.py        ← FastMCP server (4 tools)
└── cli.py           ← Click CLI
tests/
├── test_models.py
├── test_rules.py
├── test_seed.py
├── test_translator.py
└── test_store_hybrid.py
```
