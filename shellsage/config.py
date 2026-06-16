"""Central configuration — all tunables sourced from environment variables."""

from __future__ import annotations

import os

# Qdrant connection
QDRANT_URL: str = os.environ.get("SHELLSAGE_QDRANT_URL", "http://localhost:6333")

# Minimum cosine-similarity score to accept a Qdrant hit
SCORE_THRESHOLD: float = float(os.environ.get("SHELLSAGE_SCORE_THRESHOLD", "0.82"))

# Sentence-transformer model used for embedding
EMBED_MODEL: str = os.environ.get("SHELLSAGE_EMBED_MODEL", "all-MiniLM-L6-v2")

# Confidence assigned to seed translations loaded at init
SEED_CONFIDENCE: float = float(os.environ.get("SHELLSAGE_SEED_CONFIDENCE", "0.95"))

# Number of curated examples loaded by default. Keep startup fast; use
# `shellsage init --all` for the complete seed corpus.
DEFAULT_SEED_LIMIT: int = int(os.environ.get("SHELLSAGE_SEED_LIMIT", "75"))

# Confidence assigned when a command succeeds in practice
OUTCOME_CONFIDENCE: float = float(os.environ.get("SHELLSAGE_OUTCOME_CONFIDENCE", "0.99"))
