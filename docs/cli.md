# CLI Reference

All commands are accessed via the `shellsage` entry point.

---

## Installation & Setup

### `shellsage setup`

Interactive one-command install wizard. Auto-detects your IDE and configures everything.

```bash
shellsage setup               # auto-detects IDE
shellsage setup --port 8888   # wizard with custom port
```

**What it does:**

1. Detects installed IDEs (Claude Code, Cursor, Windsurf)
2. Seeds the local SQLite database with 400+ curated translations
3. Starts the background MCP server
4. Registers the MCP server with your IDE
5. Optionally installs Claude Code hooks

---

### `shellsage init`

Seed the local SQLite database.

```bash
shellsage init         # load 75 seed examples (default)
shellsage init --all   # load the complete 400+ corpus
```

---

## Translation

### `shellsage translate`

Translate a single bash command to PowerShell.

```bash
shellsage translate "ls -la"
shellsage translate "find . -name '*.py'"
shellsage translate "grep -r 'TODO' ." --json-out
```

| Flag | Description |
|---|---|
| `--json-out` | Machine-readable JSON output |

---

## Diagnostics

### `shellsage stats`

Show local database record counts.

```bash
shellsage stats
```

### `shellsage replay`

Show recent failure patterns from the local database.

```bash
shellsage replay
```

---

## Server Management

### `shellsage start`

Start the background MCP server (HTTP/SSE on `http://127.0.0.1:7842`).

```bash
shellsage start
```

### `shellsage stop`

Stop the background MCP server.

```bash
shellsage stop
```

### `shellsage status`

Show daemon and database status.

```bash
shellsage status
```

---

## MCP Server (foreground)

### `shellsage mcp`

Start the MCP server in the foreground.

```bash
shellsage mcp          # stdio transport (for IDE stdio MCP config)
shellsage mcp --http   # HTTP/SSE transport
```

---

## Hooks

### `shellsage hooks install`

Write Claude Code pre/post hook scripts to `.claude/hooks/` in the current directory and print the settings snippet to add to `.claude/settings.json`.

```bash
# Run inside your project directory
shellsage hooks install
```

---

## Other

### `shellsage --version`

Print the installed version.

```bash
shellsage --version
```
