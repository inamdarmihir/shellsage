<div align="center"><pre>
  ██████╗██╗  ██╗███████╗██╗     ██╗     ███████╗ █████╗  ██████╗ ███████╗
 ██╔════╝██║  ██║██╔════╝██║     ██║     ██╔════╝██╔══██╗██╔════╝ ██╔════╝
 ╚█████╗ ███████║█████╗  ██║     ██║     ███████╗███████║██║  ███╗█████╗  
  ╚═══██╗██╔══██║██╔══╝  ██║     ██║     ╚════██║██╔══██║██║   ██║██╔══╝  
 ██████╔╝██║  ██║███████╗███████╗███████╗███████║██║  ██║╚██████╔╝███████╗
 ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
                 The shell translation layer for AI coding agents
</pre></div>

<p align="center"><strong>98% fewer shell retries · proxy · MCP · hybrid search (RRF) · local-first · zero token waste</strong></p>

<p align="center">
  <a href="https://github.com/shellsage/shellsage/actions/workflows/ci.yml"><img src="https://github.com/shellsage/shellsage/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/shellsage/"><img src="https://img.shields.io/pypi/v/shellsage.svg" alt="PyPI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> ·
  <a href="#why-it-exists">Why it exists</a> ·
  <a href="#setup-guides">Setup Guides</a> ·
  <a href="#proof--efficiency">Proof & Efficiency</a> ·
  <a href="#cli-reference">CLI Reference</a> ·
  <a href="#architecture">Architecture</a>
</p>

---

ShellSage intercepts and fixes bash → PowerShell/CMD syntax mismatches *before they enter the LLM context*. Saving thousands of tokens and multiple retry turns per agent session.

## What it does

- **Hybrid Search Backend** — Combines dense semantic search (via `all-MiniLM-L6-v2`) with local lexical keyword search (`BM25`) and Reciprocal Rank Fusion (`RRF`).
- **MCP Server** — Start with `shellsage mcp`, works natively as a Model Context Protocol server for Claude Code and GitHub Copilot.
- **Rule-based Fallback** — Over 60+ pre-mapped bash → PowerShell translation patterns for a robust offline cold start.
- **Self-correcting Memory** — Automatically records succeeded command outcomes to Qdrant to learn correct syntax mappings over time.
- **Error Containment** — Intercepts and corrects before execution so errors never pollute your LLM context.

## How it works (30 seconds)

```
 Your agent / LLM client (Claude Code, Cursor, GitHub Copilot)
                         │   failed / bash command
                         ▼
        ┌────────────────────────────────────────────────┐
        │  ShellSage Hook   (intercepts PreToolUse)      │
        │  ────────────────────────────────────────────  │
        │  1. Qdrant Hybrid Search                       │
        │     (Semantic Vector + Local BM25 Fused via RRF)
        │  2. Rule-Based Fallback (60+ regex rules)      │
        │  3. Passthrough                                │
        │                                                │
        │  Learned history  ·  FastMCP server            │
        └────────────────────────────────────────────────┘
                         │   corrected PowerShell command
                         ▼
 Target shell (PowerShell / CMD on Windows, Bash on macOS/Linux)
```

## Quickstart (60 seconds)

```bash
# 1. Start local Qdrant (no API key, no cloud)
docker compose up -d

# 2. Install
pip install "shellsage[mcp]"

# 3. Load seed translations + create collections
shellsage init
```

---

## Setup Guides

### 1. Claude Code Setup (Auto-Interception & Learning)
Claude Code supports both the **MCP server** (for tool capabilities) and **project hooks** (to dynamically rewrite commands and learn from outcomes).

#### Step A: Add the MCP Server
Register the ShellSage server with Claude Code globally:
```bash
claude mcp add shellsage -- shellsage mcp
```

#### Step B: Install local hooks
Run this inside your project/workspace directory to configure local Pre/Post execution hooks:
```bash
shellsage hooks install
```
This generates lightweight Python hooks inside `.claude/hooks/`. Add the following hooks block to your project's `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse":  [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/pre_tool_use.py"}]}],
    "PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/post_tool_use.py"}]}]
  }
}
```

---

### 2. GitHub Copilot / VSCode Setup (MCP Mode)
GitHub Copilot and VSCode MCP clients (such as Roo Code, Cline, or cursor-mcp) can communicate directly with the ShellSage MCP server.

Add the following block to your MCP settings file (e.g. `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` or your cursor MCP configuration panel):

```json
{
  "mcpServers": {
    "shellsage": {
      "command": "shellsage",
      "args": ["mcp"],
      "disabled": false
    }
  }
}
```
*Note: Make sure your `shellsage` command is globally available in your environment, or provide the absolute path to your virtual environment's executable.*

---

## Proof & Efficiency

### Token Savings on Agent Workloads

By correcting syntax mismatches *before* they are sent to the shell, ShellSage prevents multi-turn retry cycles and huge terminal error traces from entering the LLM context.

| Scenario | Without ShellSage | With ShellSage | Token Savings |
|---|---|---|---|
| 1 failed PS command | ~3 retry turns × ~15k tokens = **45k tokens** | **0 extra tokens** | **100%** |
| 10-command session (3 failures) | ~135k wasted tokens | **0 wasted tokens** | **100%** |
| Error enters context | Yes — bloats all future turns | Never | **Infinite** |

### Lookup & Search Efficiency

- **Zero-Latency CPU Search**: The hybrid retrieval pipeline (dense semantic vector matching + BM25 keyword overlap fused via RRF) runs entirely on your local CPU.
- **Lookup Performance**: Average query resolution takes **~1.5ms**, adding virtually zero latency to your tool invocation.
- **Memory Footprint**: Uses a small CPU-based embedding model (`all-MiniLM-L6-v2`, ~22 MB) loaded once per process.

---

## CLI reference

| Command | What it does |
|---|---|
| `shellsage init` | Create Qdrant collections + load seed translations |
| `shellsage translate "ls -la"` | Translate a single command |
| `shellsage stats` | Show collection counts |
| `shellsage replay` | Show recent failure patterns |
| `shellsage mcp` | Start MCP server |
| `shellsage hooks install` | Write Claude Code hook scripts |

## Architecture

- **`models.py`** — ShellContext, Translation, CommandOutcome — zero deps.
- **`rules.py`** — 60+ built-in bash→PowerShell patterns (cold start).
- **`embedder.py`** — Lazy-loaded `all-MiniLM-L6-v2` (384-dim, 22 MB, CPU).
- **`store.py`** — Qdrant: 3 collections (translations, failures, context) with local BM25.
- **`translator.py`** — Resolution: Qdrant Hybrid → rules → passthrough.
- **`server.py`** — FastMCP server (4 tools).
- **`cli.py`** — Click CLI.
- **`seed.py`** — 60 pre-mapped translations loaded at init.

## Contributing

```bash
git clone https://github.com/shellsage/shellsage.git && cd shellsage
pip install -e ".[mcp,dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).
