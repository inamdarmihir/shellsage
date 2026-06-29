# Quickstart

Get ShellSage running in under two minutes.

---

## 1. Install

```bash
pip install "shellsage[mcp]"
```

This installs the core package plus the MCP server dependencies (`mcp`, `uvicorn`, `httpx`).

!!! tip "Python version"
    ShellSage requires Python 3.10 or later.

---

## 2. Run the setup wizard

```bash
shellsage setup
```

The wizard:

- :material-magnify: **Detects** which IDE/agent you have (Claude Code, Cursor, Windsurf)
- :material-database: **Seeds** the local SQLite database with 400+ curated translations
- :material-server: **Starts** the background MCP server on `http://127.0.0.1:7842`
- :material-link: **Registers** the MCP server with your IDE
- :material-hook: **Optionally installs** Claude Code hooks for transparent pre-execution translation

If you have multiple IDEs installed it will ask which to configure.

---

## 3. Try it

```bash
# Translate a single command
shellsage translate "ls -la"
# → Get-ChildItem -Force

shellsage translate "find . -name '*.py'"
# → Get-ChildItem -Recurse -Filter '*.py'

shellsage translate "grep -r 'TODO' ."
# → Get-ChildItem -Recurse | Select-String -Pattern 'TODO'
```

---

## 4. Check status

```bash
shellsage status
```

Shows the daemon state, database path, and record counts.

---

## What happens next

Once set up, ShellSage runs transparently. Your AI agent writes bash — ShellSage rewrites it to PowerShell before the shell ever sees it. The agent never knows anything changed.

Each successful translation is stored back to the local SQLite database, so ShellSage gets smarter as you use it.

---

## Next steps

| | |
|---|---|
| [Setup Guides](setup.md) | Manual setup for each IDE, custom ports, scripted environments |
| [Translation Reference](translation-reference.md) | Full table of 400+ bash → PowerShell pairs |
| [CLI Reference](cli.md) | All `shellsage` subcommands |
| [Configuration](configuration.md) | Environment variables |
