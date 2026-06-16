"""Qdrant store — three collections, local-first, no API key needed."""

from __future__ import annotations

import hashlib
import math
import re
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

TRANSLATIONS_COLLECTION = "shell_translations"
FAILURES_COLLECTION = "shell_failures"
CONTEXT_COLLECTION = "shell_project_context"

VECTOR_SIZE = 384  # all-MiniLM-L6-v2
DISTANCE = qm.Distance.COSINE


def _client(url: str = "http://localhost:6333") -> QdrantClient:
    return QdrantClient(url=url, timeout=5)


def ensure_collections(url: str = "http://localhost:6333") -> None:
    """Create all three collections if they don't already exist."""
    client = _client(url)
    existing = {c.name for c in client.get_collections().collections}

    for name in (TRANSLATIONS_COLLECTION, FAILURES_COLLECTION, CONTEXT_COLLECTION):
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=qm.VectorParams(size=VECTOR_SIZE, distance=DISTANCE),
            )


# ── translations ──────────────────────────────────────────────────────────────


def upsert_translation(
    *,
    bash_cmd: str,
    translated_cmd: str,
    shell: str,
    os_name: str,
    project_type: str,
    confidence: float,
    embedding: list[float],
    url: str = "http://localhost:6333",
) -> None:
    """Store or overwrite a bash→target mapping."""
    client = _client(url)
    point_id = _stable_id(bash_cmd + shell + os_name)
    client.upsert(
        collection_name=TRANSLATIONS_COLLECTION,
        points=[
            qm.PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "bash_cmd": bash_cmd,
                    "translated_cmd": translated_cmd,
                    "shell": shell,
                    "os": os_name,
                    "project_type": project_type,
                    "confidence": confidence,
                    "hits": 1,
                },
            )
        ],
    )


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _compute_bm25_scores(
    query: str,
    documents: list[dict],
    k1: float = 1.5,
    b: float = 0.75,
) -> list[tuple[dict, float]]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return [(doc, 0.0) for doc in documents]

    # Tokenize all documents
    doc_tokens_list = [_tokenize(doc.get("bash_cmd", "")) for doc in documents]
    doc_lengths = [len(tokens) for tokens in doc_tokens_list]
    avg_doc_len = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0

    # Calculate document frequencies
    doc_freqs: dict[str, int] = {}
    for tokens in doc_tokens_list:
        unique_tokens = set(tokens)
        for token in unique_tokens:
            doc_freqs[token] = doc_freqs.get(token, 0) + 1

    N = len(documents)
    scored_candidates = []
    for doc, tokens, doc_len in zip(documents, doc_tokens_list, doc_lengths, strict=False):
        score = 0.0
        # Term frequencies in this document
        tf: dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1

        for q in query_tokens:
            n_q = doc_freqs.get(q, 0)
            # IDF calculation
            idf = math.log((N - n_q + 0.5) / (n_q + 0.5) + 1.0)
            if idf < 0:
                idf = 0.0

            f_q = tf.get(q, 0)
            denom = f_q + k1 * (1.0 - b + b * (doc_len / avg_doc_len))
            if denom > 0:
                score += idf * (f_q * (k1 + 1.0)) / denom

        doc_copy = doc.copy()
        doc_copy["score"] = score
        scored_candidates.append((doc_copy, score))

    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    return scored_candidates


def _reciprocal_rank_fusion(
    semantic_results: list[dict],
    lexical_results: list[dict],
    k: int = 60,
    limit: int = 3,
) -> list[dict]:
    candidates = {}

    # Ranks in semantic
    semantic_ranks = {}
    for idx, item in enumerate(semantic_results):
        cmd = item["bash_cmd"]
        semantic_ranks[cmd] = idx + 1
        if cmd not in candidates:
            candidates[cmd] = item

    # Ranks in lexical
    lexical_ranks = {}
    for idx, item in enumerate(lexical_results):
        cmd = item["bash_cmd"]
        lexical_ranks[cmd] = idx + 1
        if cmd not in candidates:
            candidates[cmd] = item

    # Calculate RRF score for each unique bash_cmd
    rrf_scores = {}
    for cmd in candidates:
        r_sem = semantic_ranks.get(cmd, 10000)
        r_lex = lexical_ranks.get(cmd, 10000)
        rrf_scores[cmd] = (1.0 / (k + r_sem)) + (1.0 / (k + r_lex))

    # Sort candidates by RRF score descending
    sorted_cmds = sorted(rrf_scores.keys(), key=lambda c: rrf_scores[c], reverse=True)

    results = []
    for cmd in sorted_cmds[:limit]:
        item = candidates[cmd].copy()
        if cmd not in semantic_ranks:
            item["score"] = max(0.85, item.get("score", 0.0))
        results.append(item)

    return results


def query_translation(
    *,
    bash_cmd: str | None = None,
    embedding: list[float],
    shell: str,
    os_name: str,
    project_type: str,
    limit: int = 3,
    score_threshold: float = 0.82,
    url: str = "http://localhost:6333",
) -> list[dict]:
    """Search for matching translations using hybrid search (semantic + lexical fused via RRF)."""
    client = _client(url)
    must_filters = [
        qm.FieldCondition(key="shell", match=qm.MatchValue(value=shell)),
        qm.FieldCondition(key="os", match=qm.MatchValue(value=os_name)),
    ]

    # 1. Semantic search
    semantic_hits = []
    try:
        results = client.search(
            collection_name=TRANSLATIONS_COLLECTION,
            query_vector=embedding,
            query_filter=qm.Filter(must=must_filters),
            limit=limit * 3,
            score_threshold=score_threshold,
            with_payload=True,
        )
        semantic_hits = [{"score": r.score, **r.payload} for r in results]
    except Exception:
        pass

    if not bash_cmd:
        return semantic_hits[:limit]

    # 2. Lexical search (BM25)
    lexical_hits = []
    try:
        records, _ = client.scroll(
            collection_name=TRANSLATIONS_COLLECTION,
            scroll_filter=qm.Filter(must=must_filters),
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )
        candidates = [{"score": 0.0, **r.payload} for r in records]
        if candidates:
            scored_candidates = _compute_bm25_scores(bash_cmd, candidates)
            scored_candidates = [item for item, score in scored_candidates if score > 0.0]
            lexical_hits = scored_candidates
    except Exception:
        pass

    # 3. Reciprocal Rank Fusion (RRF)
    return _reciprocal_rank_fusion(semantic_hits, lexical_hits, limit=limit)


# ── failures ──────────────────────────────────────────────────────────────────


def upsert_failure(
    *,
    command: str,
    error_text: str,
    shell: str,
    os_name: str,
    project_type: str,
    embedding: list[float],
    url: str = "http://localhost:6333",
) -> None:
    """Record a failed command for later clustering / analysis."""
    client = _client(url)
    client.upsert(
        collection_name=FAILURES_COLLECTION,
        points=[
            qm.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "command": command,
                    "error_text": error_text[:300],
                    "shell": shell,
                    "os": os_name,
                    "project_type": project_type,
                },
            )
        ],
    )


def query_similar_failures(
    *,
    embedding: list[float],
    shell: str,
    limit: int = 5,
    url: str = "http://localhost:6333",
) -> list[dict]:
    client = _client(url)
    results = client.search(
        collection_name=FAILURES_COLLECTION,
        query_vector=embedding,
        query_filter=qm.Filter(
            must=[qm.FieldCondition(key="shell", match=qm.MatchValue(value=shell))]
        ),
        limit=limit,
        with_payload=True,
    )
    return [{"score": r.score, **r.payload} for r in results]


# ── project context ───────────────────────────────────────────────────────────


def upsert_project_context(
    *,
    project_root: str,
    shell: str,
    os_name: str,
    project_type: str,
    embedding: list[float],
    url: str = "http://localhost:6333",
) -> None:
    client = _client(url)
    point_id = _stable_id(project_root)
    client.upsert(
        collection_name=CONTEXT_COLLECTION,
        points=[
            qm.PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "project_root": project_root,
                    "shell": shell,
                    "os": os_name,
                    "project_type": project_type,
                },
            )
        ],
    )


def get_collection_counts(url: str = "http://localhost:6333") -> dict[str, int]:
    client = _client(url)
    return {
        name: client.get_collection(name).points_count
        for name in (TRANSLATIONS_COLLECTION, FAILURES_COLLECTION, CONTEXT_COLLECTION)
    }


# ── helpers ───────────────────────────────────────────────────────────────────


def _stable_id(text: str) -> str:
    """Deterministic UUID from text so upserts are idempotent."""
    digest = hashlib.md5(text.encode()).hexdigest()
    return str(uuid.UUID(digest))
