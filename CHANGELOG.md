# Changelog

All notable changes to ShellSage are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [0.2.0] — 2026-06-15

### Added
- **300+ seed translations** across 25 categories: file listing, find, grep, text processing, sed/awk, echo, env, process, network, archive, disk, system info, permissions, git, docker, python, node/npm, rust/cargo, directory navigation, pipes/redirects, and misc.
- **100+ rule patterns** in `rules.py` covering all new categories (sed, awk, archive, permissions, network variants, process management, system info, more grep/find flags, pipe operators).
- **`shellsage/config.py`** — centralized env-var-backed configuration. All 13+ hardcoded `localhost:6333` occurrences replaced with `SHELLSAGE_QDRANT_URL`.
- **Post-hook translation tracking fix** — `pre_tool_use.py` now writes `original→translated` to a temp cache file; `post_tool_use.py` reads it to correctly record the original bash command in `CommandOutcome`, fixing a feedback-loop corruption bug.
- **GitHub Actions CI** (`.github/workflows/ci.yml`) — lint, format, type-check, tests on Python 3.10/3.11/3.12, plus a dedicated seed/rule smoke-test job.
- **`SECURITY.md`**, **`CONTRIBUTING.md`**, **`CHANGELOG.md`**.
- Comprehensive **README** with full translation reference table for every category.
- `_validate_seed()` — runs at import time to enforce no duplicates and no empty values.
- `rules.py` source label changed from `"seed"` to `"rules"` for clarity.

### Changed
- `translator.py` — uses `config.QDRANT_URL`, `config.SCORE_THRESHOLD`, `config.OUTCOME_CONFIDENCE` instead of hardcoded values.
- `cli.py` — `--qdrant-url` defaults to `SHELLSAGE_QDRANT_URL` env var; hook template strings updated to match fixed hooks.
- `models.py` — `_detect_project_type` now wraps `os.listdir` in `try/except OSError` (was crashing on missing root); Windows shell detection falls back to `Shell.POWERSHELL` instead of `Shell.CMD` when neither `pwsh` nor `powershell` binaries are found.
- MCP server import updated from `fastmcp.FastMCP` → `mcp.server.fastmcp.FastMCP` (fixes `fastmcp` 2.x incompatibility with pydantic 2.13+).
- `pyproject.toml` `[mcp]` extra updated from `fastmcp>=0.9.0` → `mcp>=1.9.4`.

### Fixed
- **Critical:** Post-hook always stored `original == translated` (the translated command), making the feedback loop learn the wrong mappings.
- `fastmcp` 2.x incompatibility with pydantic 2.13.4 (`TypeError: cannot specify both default and default_factory`).
- Path separator rule was too broad — `./build.py` would be incorrectly rewritten to `.\build.py`.

---

## [0.1.0] — 2026-06-10

### Added
- Initial release.
- Hybrid search backend: dense semantic search (all-MiniLM-L6-v2) + BM25 + RRF.
- MCP server with 4 tools: `translate_command`, `store_command_result`, `get_shell_context`, `get_stats`.
- Claude Code hook integration (`pre_tool_use.py`, `post_tool_use.py`).
- 60 seed translations (bash → PowerShell).
- 60+ rule-based patterns.
- CLI: `init`, `translate`, `stats`, `replay`, `mcp`, `hooks install`.
- Local Qdrant backend (3 collections).
