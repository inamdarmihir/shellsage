# Configuration

All settings are controlled via environment variables — no config file needed.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SHELLSAGE_DB_PATH` | `~/.shellsage/memory.db` | SQLite database path |
| `SHELLSAGE_PORT` | `7842` | Background MCP server port |
| `SHELLSAGE_HOST` | `127.0.0.1` | Background MCP server host |
| `SHELLSAGE_SCORE_THRESHOLD` | `0.1` | Minimum score to accept a stored-translation hit |
| `SHELLSAGE_SEED_LIMIT` | `75` | Number of seed examples loaded by `shellsage init` |
| `SHELLSAGE_SEED_CONFIDENCE` | `0.95` | Confidence assigned to seed translations |
| `SHELLSAGE_OUTCOME_CONFIDENCE` | `0.99` | Confidence assigned when a command succeeds in practice |

---

## Examples

### Custom port

```bash
export SHELLSAGE_PORT=8888
shellsage setup --port 8888
```

### Custom database location

```bash
export SHELLSAGE_DB_PATH=/data/shellsage/memory.db
shellsage init --all
shellsage start
```

### Lower score threshold (more permissive matching)

```bash
export SHELLSAGE_SCORE_THRESHOLD=0.05
```

### Load all seed translations

By default `shellsage init` loads 75 examples. To load the full 400+ corpus:

```bash
export SHELLSAGE_SEED_LIMIT=999
shellsage init
# or equivalently:
shellsage init --all
```

---

## Precedence

Environment variables take effect at process start time. Values in the environment override compiled defaults. There is no config file — set `SHELLSAGE_*` variables in your shell profile (`.bashrc`, `$PROFILE`, `.zshrc`) or in your IDE's environment configuration.

---

## Single source of truth

All configuration lives in `shellsage/config.py` as a module-level `Config` dataclass. Reading the file is the canonical reference:

```
shellsage/config.py   ← env-var-backed settings (single source of truth)
```
