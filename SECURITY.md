# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅ Active  |
| 0.1.x   | ❌ EOL     |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email **security@shellsage.dev** with:

1. A description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. (Optional) A suggested fix

You will receive an acknowledgement within **48 hours** and a resolution timeline within **7 days**.

## Security Design

ShellSage is designed with a local-first, minimal-footprint security model:

- **No API keys stored** — Qdrant runs locally with no authentication by default.
- **No network egress** — all translation happens on your machine. The only outbound connections are those you initiate via `curl`/`wget` commands being translated.
- **Hook scripts are minimal** — `pre_tool_use.py` and `post_tool_use.py` only read stdin JSON and call local Python; they never execute arbitrary code from Qdrant payloads.
- **Translation cache is scoped to `%TEMP%`** — the `shellsage_pending.json` file holds only `{original, translated}` strings and is deleted after each command.
- **Embeddings run fully locally** — `all-MiniLM-L6-v2` is loaded from the Hugging Face cache; no telemetry.

## Dependency Security

Dependencies are pinned in `pyproject.toml`. Run `pip-audit` to check for known vulnerabilities:

```bash
pip install pip-audit
pip-audit
```
