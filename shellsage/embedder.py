"""Lazy-loaded embedding model.  Loaded once per process, never per call."""

from __future__ import annotations

from functools import lru_cache

from shellsage.config import EMBED_MODEL

MODEL_NAME = EMBED_MODEL  # default: all-MiniLM-L6-v2, 384-dim, CPU-friendly


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer  # type: ignore

    return SentenceTransformer(MODEL_NAME)


def embed(text: str) -> list[float]:
    """Embed a single string.  Thread-safe after first call."""
    return _model().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple strings in one forward pass."""
    return _model().encode(texts, normalize_embeddings=True).tolist()
