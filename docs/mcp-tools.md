# MCP Tools

The ShellSage MCP server exposes 4 tools that your AI agent can call directly.

The server listens at `http://127.0.0.1:7842/sse` by default (configurable via `SHELLSAGE_PORT`).

---

## `translate_command`

Translate a bash command to the correct PowerShell equivalent for the current environment.

```python
translate_command(
    command: str,       # The bash command to translate
    project_root: str,  # Absolute path to the project root (used for context detection)
)
```

**Returns:** `str` — the translated PowerShell command, or the original if no translation is needed.

**Resolution order:**

1. Rule-based translation (100+ regex patterns, instant, no DB)
2. SQLite lookup (400+ seeds + session-learned translations)
3. Passthrough (returns original unchanged)

**Example:**

```json
{
  "command": "ls -la src/",
  "project_root": "C:/Users/you/myproject"
}
```

Returns: `"Get-ChildItem -Force 'src/'"`

---

## `store_command_result`

Record a command outcome to the local SQLite database. Called automatically by the Claude Code post-hook.

```python
store_command_result(
    original: str,        # The original bash command
    translated: str,      # The translated PowerShell command
    shell: str,           # "powershell" | "cmd" | "bash"
    os_name: str,         # "windows" | "linux" | "macos"
    project_type: str,    # "python" | "node" | "rust" | "generic"
    exit_code: int,       # Shell exit code (0 = success)
    error_snippet: str,   # First few lines of stderr (empty on success)
)
```

**Returns:** `str` — confirmation message.

Successful outcomes (exit code 0) are stored with confidence `0.99` (`SHELLSAGE_OUTCOME_CONFIDENCE`) and improve future lookup quality.

---

## `get_shell_context`

Return the detected OS, shell, and project type for the given project root.

```python
get_shell_context(
    project_root: str,  # Absolute path to the project root
)
```

**Returns:** JSON object with fields:

```json
{
  "os": "windows",
  "shell": "powershell",
  "project_type": "python",
  "project_root": "C:/Users/you/myproject"
}
```

---

## `get_stats`

Health check — return collection counts from the local SQLite database.

```python
get_stats()
```

**Returns:** JSON object with counts:

```json
{
  "translations": 412,
  "failures": 3
}
```

---

## Transport options

| Mode | Command | Use case |
|---|---|---|
| HTTP/SSE (background) | `shellsage start` | Claude Code, Cursor, Windsurf via URL |
| HTTP/SSE (foreground) | `shellsage mcp --http` | Debugging, scripted environments |
| stdio (foreground) | `shellsage mcp` | IDEs that spawn the process directly |
