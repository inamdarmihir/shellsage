"""Central configuration — all tunables sourced from environment variables."""

from __future__ import annotations

import os
from pathlib import Path


# SQLite database path (no external service needed)
def _default_db_path() -> str:
    return str(Path.home() / ".shellsage" / "memory.db")


DB_PATH: str = os.environ.get("SHELLSAGE_DB_PATH", "") or _default_db_path()

# Background MCP server
SERVER_PORT: int = int(os.environ.get("SHELLSAGE_PORT", "7842"))
SERVER_HOST: str = os.environ.get("SHELLSAGE_HOST", "127.0.0.1")

# Minimum BM25-derived score (0–1) to accept a stored-translation hit
SCORE_THRESHOLD: float = float(os.environ.get("SHELLSAGE_SCORE_THRESHOLD", "0.1"))

# Confidence assigned to seed translations loaded at init
SEED_CONFIDENCE: float = float(os.environ.get("SHELLSAGE_SEED_CONFIDENCE", "0.95"))

# Number of curated examples loaded by default (use `shellsage init --all` for full corpus)
DEFAULT_SEED_LIMIT: int = int(os.environ.get("SHELLSAGE_SEED_LIMIT", "75"))

# Confidence assigned when a command succeeds in practice
OUTCOME_CONFIDENCE: float = float(os.environ.get("SHELLSAGE_OUTCOME_CONFIDENCE", "0.99"))
