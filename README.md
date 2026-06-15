<div align="center"><pre>
  ██████╗██╗  ██╗███████╗██╗     ██╗     ███████╗ █████╗  ██████╗ ███████╗
 ██╔════╝██║  ██║██╔════╝██║     ██║     ██╔════╝██╔══██╗██╔════╝ ██╔════╝
 ╚█████╗ ███████║█████╗  ██║     ██║     ███████╗███████║██║  ███╗█████╗
  ╚═══██╗██╔══██║██╔══╝  ██║     ██║     ╚════██║██╔══██║██║   ██║██╔══╝
 ██████╔╝██║  ██║███████╗███████╗███████╗███████║██║  ██║╚██████╔╝███████╗
 ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
              The shell translation layer for AI coding agents
</pre></div>

<p align="center">
  <strong>300+ translations · hybrid search (RRF) · MCP server · hooks · local-first · zero token waste</strong>
</p>

<p align="center">
  <a href="https://github.com/shellsage/shellsage/actions/workflows/ci.yml">
    <img src="https://github.com/shellsage/shellsage/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://pypi.org/project/shellsage/">
    <img src="https://img.shields.io/pypi/v/shellsage.svg" alt="PyPI">
  </a>
  <a href="https://pypi.org/project/shellsage/">
    <img src="https://img.shields.io/pypi/pyversions/shellsage.svg" alt="Python">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License">
  </a>
</p>

<p align="center">
  <a href="#what-it-does">What it does</a> ·
  <a href="#quickstart">Quickstart</a> ·
  <a href="#setup-guides">Setup</a> ·
  <a href="#command-translation-reference">Translation Reference</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#cli-reference">CLI</a> ·
  <a href="#architecture">Architecture</a>
</p>

---

ShellSage intercepts every Bash tool call made by your AI coding agent (Claude Code, GitHub Copilot, Cursor, Cline …) and silently rewrites bash syntax into correct PowerShell/CMD before the shell sees it. The corrected command is stored back into local Qdrant so the system learns from every session.

**No API key. No cloud. Runs entirely on your machine.**

---

## What it does

| Without ShellSage | With ShellSage |
|---|---|
| Agent writes `ls -la` → PowerShell fails → retry loop → 45k wasted tokens | Agent writes `ls -la` → silently becomes `Get-ChildItem -Force` → works ✓ |
| 3 bash failures per session = ~135k wasted tokens | 0 failures · 0 wasted tokens |
| Error traces pollute all future turns | Errors never reach the LLM context |

**How it translates:**

1. **Qdrant hybrid search** — semantic embedding + BM25 lexical search fused via Reciprocal Rank Fusion (RRF). Finds the best match from 300+ seed translations plus everything learned in past sessions.
2. **Rule-based fallback** — 100+ regex patterns covering all common bash constructs. Zero Qdrant dependency.
3. **Passthrough** — if no translation is needed (bash on Linux/macOS, or git/docker commands that work everywhere), the command passes through unchanged.

---

## Quickstart

```bash
# 1. Start local Qdrant (no API key, no cloud)
docker compose up -d

# 2. Install
pip install "shellsage[mcp]"

# 3. Load 300+ seed translations into Qdrant
shellsage init

# 4. Register with Claude Code
claude mcp add shellsage -- shellsage mcp

# 5. Install hooks in your project
shellsage hooks install
```

That's it. ShellSage now intercepts every Bash call.

---

## Setup Guides

### Claude Code (recommended — hooks + MCP)

Claude Code supports **hooks** (silently rewrite before execution) and **MCP** (tools the model can call).

#### Step 1 — Register the MCP server

```bash
claude mcp add shellsage -- shellsage mcp
```

#### Step 2 — Install project hooks

Run inside your project directory:

```bash
shellsage hooks install
```

This creates `.claude/hooks/pre_tool_use.py` and `.claude/hooks/post_tool_use.py`.

Add this to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse":  [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/pre_tool_use.py"}]}],
    "PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/post_tool_use.py"}]}]
  }
}
```

**What each hook does:**
- `pre_tool_use.py` — translates the command before execution; writes original→translated to a temp cache
- `post_tool_use.py` — reads the cache, records success/failure back to Qdrant so the system learns

### GitHub Copilot / VSCode MCP

Add to your MCP settings (e.g. `cline_mcp_settings.json` or cursor MCP panel):

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

### Environment variable (optional)

Point ShellSage at a remote or differently-ported Qdrant:

```bash
export SHELLSAGE_QDRANT_URL=http://my-qdrant-host:6333
```

---

## Command Translation Reference

Every entry below is loaded into Qdrant on `shellsage init`. The hybrid search finds the best match for any command the LLM writes — including variations with different paths, flags, and arguments.

### File Listing

| bash | PowerShell |
|------|-----------|
| `ls` | `Get-ChildItem` |
| `ls -la` | `Get-ChildItem -Force` |
| `ls -l` | `Get-ChildItem \| Format-List` |
| `ls -R` | `Get-ChildItem -Recurse` |
| `ls *.py` | `Get-ChildItem *.py` |
| `ls -la src/` | `Get-ChildItem -Force 'src/'` |
| `ls ~` | `Get-ChildItem $HOME` |

### Find / Locate

| bash | PowerShell |
|------|-----------|
| `find . -name '*.py'` | `Get-ChildItem -Recurse -Filter '*.py'` |
| `find . -type f` | `Get-ChildItem -Recurse -File` |
| `find . -type d` | `Get-ChildItem -Recurse -Directory` |
| `find . -type f -name '*.log'` | `Get-ChildItem -Recurse -File -Filter '*.log'` |
| `find src/ -name '*.py'` | `Get-ChildItem -Path 'src/' -Recurse -Filter '*.py'` |
| `find . -mtime -7` | `Get-ChildItem -Recurse \| Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) }` |
| `find . -size +1M` | `Get-ChildItem -Recurse \| Where-Object { $_.Length -gt 1MB }` |
| `find . -name '*.tmp' -delete` | `Get-ChildItem -Recurse -Filter '*.tmp' \| Remove-Item -Force` |
| `find . -name '*.pyc' -delete` | `Get-ChildItem -Recurse -Filter '*.pyc' \| Remove-Item -Force` |

### Grep / Search

| bash | PowerShell |
|------|-----------|
| `grep 'error' app.log` | `Select-String -Pattern 'error' -Path 'app.log'` |
| `grep -r 'TODO' .` | `Get-ChildItem -Recurse \| Select-String -Pattern 'TODO'` |
| `grep -rn 'import' src/` | `Get-ChildItem -Recurse 'src/' \| Select-String -Pattern 'import'` |
| `grep -i 'error' app.log` | `Select-String -Pattern 'error' -Path 'app.log' -CaseSensitive:$false` |
| `grep -v 'debug' app.log` | `Get-Content 'app.log' \| Where-Object { $_ -notmatch 'debug' }` |
| `grep -c 'error' app.log` | `(Select-String -Pattern 'error' -Path 'app.log').Count` |
| `grep -l 'TODO' *.py` | `Select-String -Pattern 'TODO' -Path '*.py' \| Select-Object -ExpandProperty Path -Unique` |
| `grep 'error' *.log` | `Select-String -Pattern 'error' -Path '*.log'` |
| `grep -r 'password' . --include='*.py'` | `Get-ChildItem -Recurse -Filter '*.py' \| Select-String -Pattern 'password'` |

### View Files

| bash | PowerShell |
|------|-----------|
| `cat README.md` | `Get-Content 'README.md'` |
| `cat file1.txt file2.txt` | `Get-Content 'file1.txt', 'file2.txt'` |
| `head -n 20 file.txt` | `Get-Content 'file.txt' -TotalCount 20` |
| `tail -n 50 app.log` | `Get-Content 'app.log' -Tail 50` |
| `tail -f server.log` | `Get-Content -Wait 'server.log'` |

### File Management

| bash | PowerShell |
|------|-----------|
| `mkdir -p src/utils` | `New-Item -ItemType Directory -Force -Path 'src/utils'` |
| `rm -rf node_modules` | `Remove-Item -Recurse -Force 'node_modules'` |
| `rm -rf dist/` | `Remove-Item -Recurse -Force 'dist/'` |
| `rm -f output.log` | `Remove-Item -Force 'output.log'` |
| `cp -r src/ backup/` | `Copy-Item -Recurse 'src/' 'backup/'` |
| `cp config.json config.json.bak` | `Copy-Item 'config.json' 'config.json.bak'` |
| `mv old.txt new.txt` | `Move-Item 'old.txt' 'new.txt'` |
| `touch .gitkeep` | `New-Item -ItemType File -Force '.gitkeep'` |
| `ln -s src dest` | `New-Item -ItemType SymbolicLink -Name 'dest' -Target 'src'` |

### Text Processing

| bash | PowerShell |
|------|-----------|
| `wc -l file.txt` | `(Get-Content 'file.txt').Count` |
| `sort file.txt` | `Get-Content 'file.txt' \| Sort-Object` |
| `sort -u file.txt` | `Get-Content 'file.txt' \| Sort-Object -Unique` |
| `sort -r file.txt` | `Get-Content 'file.txt' \| Sort-Object -Descending` |
| `sort file.txt \| uniq -c` | `Get-Content 'file.txt' \| Group-Object \| Select-Object Count, Name` |
| `sed -i 's/foo/bar/g' file.txt` | `(Get-Content 'file.txt') -replace 'foo','bar' \| Set-Content 'file.txt'` |
| `sed '/^#/d' file.txt` | `Get-Content 'file.txt' \| Where-Object { $_ -notmatch '^#' }` |
| `awk '{print $1}' file.txt` | `Get-Content 'file.txt' \| ForEach-Object { ($_ -split '\s+')[0] }` |

### Echo / Redirect

| bash | PowerShell |
|------|-----------|
| `echo 'hello world'` | `Write-Output 'hello world'` |
| `echo $PATH` | `$env:PATH` |
| `echo $HOME` | `$env:USERPROFILE` |
| `echo 'line' > file.txt` | `Set-Content 'file.txt' 'line'` |
| `echo 'line' >> file.txt` | `Add-Content 'file.txt' 'line'` |

### Environment Variables

| bash | PowerShell |
|------|-----------|
| `export NODE_ENV=production` | `$env:NODE_ENV = 'production'` |
| `export PORT=3000` | `$env:PORT = '3000'` |
| `export DATABASE_URL=postgres://localhost/db` | `$env:DATABASE_URL = 'postgres://localhost/db'` |
| `unset NODE_ENV` | `Remove-Item Env:\NODE_ENV` |
| `env` | `Get-ChildItem Env:` |
| `printenv PATH` | `$env:PATH` |

### Process Management

| bash | PowerShell |
|------|-----------|
| `ps aux` | `Get-Process` |
| `ps aux \| grep node` | `Get-Process \| Where-Object { $_.Name -match 'node' }` |
| `pgrep python` | `Get-Process -Name '*python*'` |
| `pkill node` | `Stop-Process -Name 'node' -Force` |
| `kill -9 1234` | `Stop-Process -Id 1234 -Force` |
| `killall python` | `Stop-Process -Name 'python' -Force` |
| `sleep 5` | `Start-Sleep 5` |
| `nohup python app.py &` | `Start-Process -NoNewWindow python -ArgumentList 'app.py' -RedirectStandardOutput 'nohup.out'` |

### Network

| bash | PowerShell |
|------|-----------|
| `curl https://example.com` | `Invoke-WebRequest -Uri 'https://example.com'` |
| `curl -s https://api.github.com` | `Invoke-RestMethod 'https://api.github.com'` |
| `curl -o file.zip https://example.com/a.zip` | `Invoke-WebRequest -Uri 'https://example.com/a.zip' -OutFile 'file.zip'` |
| `curl -X POST URL -d '{"k":"v"}'` | `Invoke-RestMethod -Method POST -Uri URL -Body '{"k":"v"}' -ContentType 'application/json'` |
| `curl -H 'Authorization: Bearer TOKEN' URL` | `Invoke-RestMethod -Uri URL -Headers @{ Authorization = 'Bearer TOKEN' }` |
| `wget https://example.com/file.zip` | `Invoke-WebRequest -Uri 'https://example.com/file.zip' -OutFile 'file.zip'` |
| `ping google.com` | `Test-Connection -ComputerName 'google.com'` |
| `ping -c 4 google.com` | `Test-Connection -ComputerName 'google.com' -Count 4` |
| `netstat -tulpn` | `Get-NetTCPConnection \| Where-Object { $_.State -eq 'Listen' }` |
| `nslookup google.com` | `Resolve-DnsName 'google.com'` |

### Archive / Compression

| bash | PowerShell |
|------|-----------|
| `tar -czf archive.tar.gz dist/` | `Compress-Archive -Path 'dist/' -DestinationPath 'archive.zip'` |
| `tar -xzf archive.tar.gz` | `Expand-Archive -Path 'archive.zip' -DestinationPath '.'` |
| `tar -xzf archive.tar.gz -C out/` | `Expand-Archive -Path 'archive.zip' -DestinationPath 'out/'` |
| `zip -r archive.zip src/` | `Compress-Archive -Path 'src/' -DestinationPath 'archive.zip'` |
| `unzip archive.zip -d output/` | `Expand-Archive -Path 'archive.zip' -DestinationPath 'output/'` |

### Disk / System Info

| bash | PowerShell |
|------|-----------|
| `df -h` | `Get-PSDrive -PSProvider FileSystem` |
| `du -sh .` | `(Get-ChildItem -Recurse \| Measure-Object -Property Length -Sum).Sum / 1MB` |
| `du -sh node_modules/` | `(Get-ChildItem -Recurse 'node_modules/' \| Measure-Object -Property Length -Sum).Sum / 1MB` |
| `uname -a` | `Get-ComputerInfo \| Select-Object WindowsProductName, WindowsVersion` |
| `hostname` | `$env:COMPUTERNAME` |
| `whoami` | `$env:USERNAME` |
| `date` | `Get-Date` |
| `date '+%Y-%m-%d'` | `Get-Date -Format 'yyyy-MM-dd'` |
| `uptime` | `(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime` |

### Permissions

| bash | PowerShell |
|------|-----------|
| `chmod +x script.sh` | `# Rename to script.ps1 or use Set-ExecutionPolicy` |
| `chmod 755 dir/` | `# Use icacls for Windows ACL management` |
| `chown user file` | `# Use icacls: icacls 'file' /setowner 'user'` |
| `sudo command` | `# Run PowerShell as Administrator, then: command` |

### Python

| bash | PowerShell |
|------|-----------|
| `python3 script.py` | `python script.py` |
| `python3 -m pytest` | `python -m pytest` |
| `python3 -m pytest -v` | `python -m pytest -v` |
| `python3 -m pip install -r requirements.txt` | `python -m pip install -r requirements.txt` |
| `python3 -m pip install -e .` | `python -m pip install -e .` |
| `python3 -m venv .venv` | `python -m venv .venv` |
| `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` |
| `python3 -m pip freeze > requirements.txt` | `python -m pip freeze \| Set-Content 'requirements.txt'` |
| `which python3` | `(Get-Command python).Source` |

### Node.js / npm

| bash | PowerShell |
|------|-----------|
| `npm install` | `npm install` |
| `npm install package` | `npm install package` |
| `npm run build` | `npm run build` |
| `npm run dev` | `npm run dev` |
| `npm test` | `npm test` |
| `npx tsc` | `npx tsc` |
| `yarn install` | `yarn install` |
| `yarn add package` | `yarn add package` |

### Docker

| bash | PowerShell |
|------|-----------|
| `docker ps -a` | `docker ps -a` |
| `docker build -t myapp .` | `docker build -t myapp .` |
| `docker run -d -p 8080:8080 myapp` | `docker run -d -p 8080:8080 myapp` |
| `docker exec -it mycontainer bash` | `docker exec -it mycontainer bash` |
| `docker logs -f mycontainer` | `docker logs -f mycontainer` |
| `docker-compose up -d` | `docker-compose up -d` |
| `docker-compose down` | `docker-compose down` |
| `docker system prune -f` | `docker system prune -f` |

### Git

Git commands are identical on all platforms — ShellSage passes them through unchanged.

| bash / PowerShell |
|---|
| `git init` · `git clone URL` · `git status` · `git add .` |
| `git commit -m 'message'` · `git push origin main` · `git pull` |
| `git checkout -b feature/name` · `git merge branch` · `git rebase main` |
| `git log --oneline -10` · `git diff --stat` · `git stash` |

### Directory Navigation

| bash | PowerShell |
|------|-----------|
| `pwd` | `Get-Location` |
| `cd src/` | `Set-Location 'src/'` |
| `cd ..` | `Set-Location ..` |
| `cd ~` | `Set-Location $HOME` |
| `pushd src/` | `Push-Location 'src/'` |
| `popd` | `Pop-Location` |

### Pipes and Redirects

| bash | PowerShell |
|------|-----------|
| `ls \| grep '.py'` | `Get-ChildItem \| Where-Object { $_.Name -match '\.py' }` |
| `ls \| wc -l` | `(Get-ChildItem).Count` |
| `cat file.txt \| sort \| uniq` | `Get-Content 'file.txt' \| Sort-Object -Unique` |
| `find . -name '*.py' \| xargs grep 'import'` | `Get-ChildItem -Recurse -Filter '*.py' \| Select-String -Pattern 'import'` |
| `command > /dev/null 2>&1` | `command > $null 2>&1` |

---

## Configuration

All settings can be overridden via environment variables:

| Variable | Default | Description |
|---|---|---|
| `SHELLSAGE_QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `SHELLSAGE_SCORE_THRESHOLD` | `0.82` | Minimum cosine similarity to accept a Qdrant hit |
| `SHELLSAGE_EMBED_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model (384-dim, ~22 MB) |
| `SHELLSAGE_SEED_CONFIDENCE` | `0.95` | Confidence assigned to seed translations |
| `SHELLSAGE_OUTCOME_CONFIDENCE` | `0.99` | Confidence assigned when a command succeeds in practice |

Example:

```bash
export SHELLSAGE_QDRANT_URL=http://my-server:6333
export SHELLSAGE_SCORE_THRESHOLD=0.85
shellsage init
```

---

## MCP Tools

The MCP server exposes 4 tools that your AI agent can call directly:

| Tool | Description |
|---|---|
| `translate_command(command, project_root)` | Translate a bash command for the current shell |
| `store_command_result(original, translated, shell, os_name, project_type, exit_code, error_snippet)` | Record command outcome back to Qdrant |
| `get_shell_context(project_root)` | Return detected OS/shell/project environment |
| `get_stats()` | Health check — return Qdrant collection counts |

---

## CLI Reference

```
shellsage init                       # Create collections + load 300+ seed translations
shellsage translate "ls -la"         # Translate a single command (--json-out for JSON)
shellsage stats                      # Show Qdrant collection counts
shellsage replay                     # Show recent failure patterns
shellsage mcp                        # Start MCP server
shellsage hooks install              # Write pre/post hook scripts to .claude/hooks/
shellsage --version                  # Print version
```

Options available on most commands:
- `--qdrant-url URL` — override Qdrant URL (also reads `SHELLSAGE_QDRANT_URL`)

---

## Architecture

```
 Claude Code / Copilot / Cursor
         │  bash command
         ▼
 ┌───────────────────────────────────────────────┐
 │  PreToolUse Hook  (.claude/hooks/pre_*.py)    │
 │  ─────────────────────────────────────────    │
 │  1. Qdrant hybrid search                      │
 │     ├─ Dense: all-MiniLM-L6-v2 embeddings     │
 │     └─ Lexical: BM25 over stored commands     │
 │     └─ Fused via Reciprocal Rank Fusion (RRF)  │
 │  2. Rule-based fallback  (100+ patterns)       │
 │  3. Passthrough                               │
 │  Writes cache: original → translated          │
 └───────────────────────────────────────────────┘
         │  corrected PowerShell command
         ▼
    [Shell execution]
         │
         ▼
 ┌───────────────────────────────────────────────┐
 │  PostToolUse Hook (.claude/hooks/post_*.py)   │
 │  Reads cache, stores outcome → Qdrant         │
 │  Success → upsert translation (confidence=0.99)│
 │  Failure → upsert failure pattern             │
 └───────────────────────────────────────────────┘
         │
         ▼
   Qdrant (local, http://localhost:6333)
   ├─ shell_translations  (300+ entries + learned)
   ├─ shell_failures      (error patterns)
   └─ shell_project_context
```

**Module map:**

| Module | Role |
|---|---|
| `config.py` | Env-var-backed settings (single source of truth) |
| `models.py` | `ShellContext`, `Translation`, `CommandOutcome` — zero deps |
| `rules.py` | 100+ regex patterns (cold-start, no Qdrant needed) |
| `seed.py` | 300+ curated bash→PS translations loaded at init |
| `embedder.py` | Lazy `all-MiniLM-L6-v2` (384-dim, 22 MB, CPU) |
| `store.py` | Qdrant: 3 collections, hybrid search (BM25 + cosine + RRF) |
| `translator.py` | 3-tier resolution: Qdrant → rules → passthrough |
| `server.py` | FastMCP server (4 tools) |
| `cli.py` | Click CLI (6 commands) |

---

## Development

```bash
git clone https://github.com/shellsage/shellsage.git
cd shellsage
pip install -e ".[mcp,dev]"

# Run tests
pytest

# Lint
ruff check shellsage/ tests/
ruff format shellsage/ tests/

# Type check
mypy shellsage/

# Validate seed data
python -c "from shellsage.seed import SEED_TRANSLATIONS; print(len(SEED_TRANSLATIONS))"

# Test a translation (no Qdrant needed)
shellsage translate "find . -name '*.py'"
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full contribution guidelines.

---

## License

MIT — see [LICENSE](LICENSE).

## Security

Please report vulnerabilities to **security@shellsage.dev** — see [SECURITY.md](SECURITY.md).
