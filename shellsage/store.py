"""SQLite-backed store — zero external dependencies, BM25 text search built-in."""

from __future__ import annotations

import hashlib
import math
import re
import sqlite3
from contextlib import suppress
from pathlib import Path

from shellsage.config import DB_PATH as _DEFAULT_DB

# Paths where ensure_tables() has already run this process — skips the DDL on re-entry.
_ensured_paths: set[str] = set()


# ── connection ────────────────────────────────────────────────────────────────


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or _DEFAULT_DB
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


# ── schema ────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS translations (
    id          TEXT PRIMARY KEY,
    bash_cmd    TEXT NOT NULL,
    translated_cmd TEXT NOT NULL,
    shell       TEXT NOT NULL DEFAULT 'powershell',
    os_name     TEXT NOT NULL DEFAULT 'windows',
    project_type TEXT NOT NULL DEFAULT 'unknown',
    confidence  REAL NOT NULL DEFAULT 0.9,
    hits        INTEGER NOT NULL DEFAULT 1,
    ref         TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_trl_os_shell ON translations(os_name, shell);

CREATE TABLE IF NOT EXISTS failures (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
    command     TEXT NOT NULL,
    error_text  TEXT NOT NULL DEFAULT '',
    shell       TEXT NOT NULL,
    os_name     TEXT NOT NULL,
    project_type TEXT NOT NULL DEFAULT 'unknown',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
"""

# Migration: add ref column to existing databases that pre-date this schema.
_MIGRATIONS = [
    "ALTER TABLE translations ADD COLUMN ref TEXT NOT NULL DEFAULT ''",
]

_FTS5_CREATE = """
CREATE VIRTUAL TABLE IF NOT EXISTS translations_fts USING fts5(
    bash_cmd,
    content=translations,
    content_rowid=rowid
)
"""

# Triggers must be executed individually — they contain embedded `;` inside BEGIN…END.
_FTS5_TRIGGERS = [
    """CREATE TRIGGER IF NOT EXISTS trl_ai AFTER INSERT ON translations BEGIN
    INSERT INTO translations_fts(rowid, bash_cmd) VALUES (new.rowid, new.bash_cmd);
END""",
    """CREATE TRIGGER IF NOT EXISTS trl_au AFTER UPDATE ON translations BEGIN
    INSERT INTO translations_fts(translations_fts, rowid, bash_cmd)
        VALUES('delete', old.rowid, old.bash_cmd);
    INSERT INTO translations_fts(rowid, bash_cmd) VALUES (new.rowid, new.bash_cmd);
END""",
    """CREATE TRIGGER IF NOT EXISTS trl_ad AFTER DELETE ON translations BEGIN
    INSERT INTO translations_fts(translations_fts, rowid, bash_cmd)
        VALUES('delete', old.rowid, old.bash_cmd);
END""",
]


def ensure_tables(db_path: str | None = None) -> bool:
    """Create schema and run migrations. Returns True if FTS5 is available.

    Idempotent per process: subsequent calls for the same path are a no-op.
    """
    path = db_path or _DEFAULT_DB
    if path in _ensured_paths:
        return True
    conn = _connect(db_path)
    with conn:
        for stmt in _DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        # Run migrations for existing DBs (ALTER TABLE is idempotent via try/except)
        for migration in _MIGRATIONS:
            with suppress(sqlite3.OperationalError):
                conn.execute(migration)
    has_fts5 = _setup_fts5(conn)
    conn.close()
    _ensured_paths.add(path)
    return has_fts5


def _setup_fts5(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute(_FTS5_CREATE)
        for trigger in _FTS5_TRIGGERS:
            conn.execute(trigger)
        conn.commit()
        return True
    except sqlite3.OperationalError:
        with suppress(Exception):
            conn.rollback()
        return False


# ── translations ──────────────────────────────────────────────────────────────


def upsert_translation(
    *,
    bash_cmd: str,
    translated_cmd: str,
    shell: str,
    os_name: str,
    project_type: str,
    confidence: float,
    ref: str = "",
    db_path: str | None = None,
) -> None:
    row_id = _stable_id(bash_cmd + shell + os_name)
    conn = _connect(db_path)
    with conn:
        existing = conn.execute("SELECT hits FROM translations WHERE id = ?", (row_id,)).fetchone()
        hits = (existing["hits"] + 1) if existing else 1
        conn.execute(
            """
            INSERT INTO translations(id, bash_cmd, translated_cmd, shell, os_name, project_type, confidence, hits, ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                translated_cmd = excluded.translated_cmd,
                confidence     = excluded.confidence,
                hits           = excluded.hits,
                ref            = excluded.ref
            """,
            (row_id, bash_cmd, translated_cmd, shell, os_name, project_type, confidence, hits, ref),
        )
    conn.close()


def query_translation(
    *,
    bash_cmd: str,
    shell: str,
    os_name: str,
    project_type: str = "unknown",  # noqa: ARG001 — kept for API compat
    limit: int = 3,
    score_threshold: float = 0.1,
    db_path: str | None = None,
) -> list[dict]:
    conn = _connect(db_path)

    # Cheap existence check — avoids a full-table scan when the DB is empty.
    has_rows = conn.execute(
        "SELECT 1 FROM translations WHERE os_name=? AND shell=? LIMIT 1",
        (os_name, shell),
    ).fetchone()
    if not has_rows:
        conn.close()
        return []

    # Prefer FTS5 (fast, index-backed).  Returns None only when FTS5 is unavailable.
    fts_results = _query_fts5(conn, bash_cmd, shell, os_name, limit, score_threshold)
    if fts_results is not None:
        conn.close()
        return fts_results

    # FTS5 unavailable: Python-side BM25 over a bounded corpus (≤500 rows).
    rows = conn.execute(
        "SELECT bash_cmd, translated_cmd, confidence, hits, ref "
        "FROM translations WHERE os_name=? AND shell=? LIMIT 500",
        (os_name, shell),
    ).fetchall()
    conn.close()

    if not rows:
        return []

    docs = [
        {
            "bash_cmd": r["bash_cmd"],
            "translated_cmd": r["translated_cmd"],
            "confidence": r["confidence"],
            "hits": r["hits"],
            "ref": r["ref"],
        }
        for r in rows
    ]
    scored = _bm25_scores(bash_cmd, docs)
    results = []
    max_score = scored[0][1] if scored else 1.0
    for doc, score in scored:
        if score <= 0:
            break
        norm = min(0.97, score / max(max_score, 1e-9))
        if norm >= score_threshold:
            results.append({**doc, "score": norm})
    return results[:limit]


def _query_fts5(
    conn: sqlite3.Connection,
    bash_cmd: str,
    shell: str,
    os_name: str,
    limit: int,
    score_threshold: float,
) -> list[dict] | None:
    fts_query = _to_fts_query(bash_cmd)
    if not fts_query:
        return []
    try:
        rows = conn.execute(
            """
            SELECT t.bash_cmd, t.translated_cmd, t.confidence, t.hits, t.ref,
                   -bm25(translations_fts) AS raw_score
            FROM translations_fts fts
            JOIN translations t ON fts.rowid = t.rowid
            WHERE translations_fts MATCH ?
              AND t.os_name = ?
              AND t.shell   = ?
            ORDER BY bm25(translations_fts)
            LIMIT ?
            """,
            (fts_query, os_name, shell, limit * 3),
        ).fetchall()
    except sqlite3.OperationalError:
        return None  # FTS5 not available

    if not rows:
        return []

    max_score = rows[0]["raw_score"] if rows else 1.0
    results = []
    for row in rows:
        norm = min(0.97, row["raw_score"] / max(max_score, 1e-9))
        if norm >= score_threshold:
            results.append(
                {
                    "bash_cmd": row["bash_cmd"],
                    "translated_cmd": row["translated_cmd"],
                    "confidence": row["confidence"],
                    "hits": row["hits"],
                    "ref": row["ref"],
                    "score": norm,
                }
            )
    return results[:limit]


def _to_fts_query(cmd: str) -> str:
    tokens = re.findall(r"\w+", cmd.lower())
    return " ".join(tokens)


# ── failures ──────────────────────────────────────────────────────────────────


def upsert_failure(
    *,
    command: str,
    error_text: str,
    shell: str,
    os_name: str,
    project_type: str,
    db_path: str | None = None,
) -> None:
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """
            INSERT INTO failures(command, error_text, shell, os_name, project_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            (command, error_text[:300], shell, os_name, project_type),
        )
    conn.close()


def get_recent_failures(
    *,
    shell: str | None = None,
    limit: int = 20,
    db_path: str | None = None,
) -> list[dict]:
    conn = _connect(db_path)
    if shell:
        rows = conn.execute(
            "SELECT * FROM failures WHERE shell=? ORDER BY created_at DESC LIMIT ?",
            (shell, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM failures ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── stats ─────────────────────────────────────────────────────────────────────


def get_stats(db_path: str | None = None) -> dict[str, int]:
    conn = _connect(db_path)
    translations = conn.execute("SELECT COUNT(*) FROM translations").fetchone()[0]
    failures = conn.execute("SELECT COUNT(*) FROM failures").fetchone()[0]
    conn.close()
    return {"translations": translations, "failures": failures}


# ── helpers ───────────────────────────────────────────────────────────────────


def _stable_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _bm25_scores(
    query: str,
    documents: list[dict],
    k1: float = 1.5,
    b: float = 0.75,
) -> list[tuple[dict, float]]:
    query_tokens = re.findall(r"\w+", query.lower())
    if not query_tokens:
        return [(doc, 0.0) for doc in documents]

    doc_tokens_list = [re.findall(r"\w+", doc.get("bash_cmd", "").lower()) for doc in documents]
    doc_lengths = [len(t) for t in doc_tokens_list]
    avg_len = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0

    df: dict[str, int] = {}
    for tokens in doc_tokens_list:
        for tok in set(tokens):
            df[tok] = df.get(tok, 0) + 1

    N = len(documents)
    results = []
    for doc, tokens, doc_len in zip(documents, doc_tokens_list, doc_lengths, strict=False):
        tf: dict[str, int] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1

        score = 0.0
        for q in query_tokens:
            n_q = df.get(q, 0)
            idf = math.log((N - n_q + 0.5) / (n_q + 0.5) + 1.0)
            f_q = tf.get(q, 0)
            denom = f_q + k1 * (1.0 - b + b * (doc_len / avg_len))
            if denom > 0:
                score += max(0.0, idf) * (f_q * (k1 + 1.0)) / denom

        results.append((doc, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
