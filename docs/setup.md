# Setup Guides

`shellsage setup` handles everything automatically. The manual steps below are for reference or scripted environments.

---

## Claude Code (recommended — hooks + MCP)

Claude Code supports **hooks** (silently rewrite before execution) and **MCP** (tools the model can call).

=== "Automatic (recommended)"

    ```bash
    shellsage setup
    ```

=== "Manual"

    ```bash
    # 1. Start the background server
    shellsage start

    # 2. Register the MCP server
    claude mcp add --transport sse shellsage http://127.0.0.1:7842/sse

    # 3. Install project hooks (run inside your project directory)
    shellsage hooks install
    ```

### What the hooks do

`shellsage hooks install` creates two files inside `.claude/hooks/` and prints the settings snippet to add to `.claude/settings.json`.

| Hook | Role |
|---|---|
| `pre_tool_use.py` | Translates the command before execution; caches `original → translated` to a temp file |
| `post_tool_use.py` | Reads the cache and records the outcome to local SQLite memory |

---

## Cursor

=== "Automatic"

    ```bash
    shellsage setup   # auto-writes ~/.cursor/mcp.json
    ```

=== "Manual"

    Add to `~/.cursor/mcp.json`:

    ```json
    {
      "mcpServers": {
        "shellsage": {
          "url": "http://127.0.0.1:7842/sse"
        }
      }
    }
    ```

    Then start the server: `shellsage start`

---

## Windsurf

=== "Automatic"

    ```bash
    shellsage setup   # auto-writes ~/.codeium/windsurf/mcp_config.json
    ```

=== "Manual"

    Add to `~/.codeium/windsurf/mcp_config.json`:

    ```json
    {
      "mcpServers": {
        "shellsage": {
          "serverUrl": "http://127.0.0.1:7842/sse"
        }
      }
    }
    ```

    Then start the server: `shellsage start`

---

## Other IDEs (stdio transport)

For any MCP-compatible IDE that supports stdio transport:

```json
{
  "mcpServers": {
    "shellsage": {
      "command": "shellsage",
      "args": ["mcp"]
    }
  }
}
```

No background server needed — the IDE spawns the process directly.

---

## Custom port

```bash
export SHELLSAGE_PORT=8888
shellsage setup --port 8888
```

All `shellsage start` / `stop` / `status` commands respect `SHELLSAGE_PORT`.

---

## Scripted / headless environments

Skip the interactive wizard and drive each step directly:

```bash
# 1. Seed the local database
shellsage init --all

# 2. Start the background server
shellsage start

# 3. Verify
shellsage status
```
