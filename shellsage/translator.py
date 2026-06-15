"""Core translation logic: bash→shell via Qdrant lookup then rule fallback."""

from __future__ import annotations

import logging

from shellsage import embedder, rules, store
from shellsage.config import QDRANT_URL as _QDRANT_URL, SCORE_THRESHOLD, OUTCOME_CONFIDENCE
from shellsage.models import CommandOutcome, ShellContext, Translation

logger = logging.getLogger(__name__)


def translate(
    command: str,
    ctx: ShellContext,
    qdrant_url: str = _QDRANT_URL,
    score_threshold: float = SCORE_THRESHOLD,
) -> Translation:
    """
    Translate *command* for the given shell context.

    Resolution order:
      1. Qdrant hybrid search  (learned from past sessions + seed)
      2. Rule-based translation (built-in patterns, no Qdrant needed)
      3. Passthrough            (command already compatible)
    """
    if not ctx.needs_translation:
        return Translation(
            original=command,
            translated=command,
            shell=ctx.shell,
            confidence=1.0,
            source="passthrough",
        )

    # ── 1. Qdrant lookup ──────────────────────────────────────────────────────
    try:
        vec = embedder.embed(command)
        hits = store.query_translation(
            bash_cmd=command,
            embedding=vec,
            shell=ctx.shell.value,
            os_name=ctx.os.value,
            project_type=ctx.project_type,
            score_threshold=score_threshold,
            url=qdrant_url,
        )
        if hits:
            best = hits[0]
            return Translation(
                original=command,
                translated=best["translated_cmd"],
                shell=ctx.shell,
                confidence=best["score"],
                source="qdrant",
            )
    except Exception as exc:
        logger.debug("Qdrant lookup failed (%s) — falling back to rules", exc)

    # ── 2. Rule-based translation ─────────────────────────────────────────────
    translated = rules.apply(command, ctx.shell)
    if translated != command:
        return Translation(
            original=command,
            translated=translated,
            shell=ctx.shell,
            confidence=0.95,
            source="rules",
        )

    # ── 3. Passthrough ────────────────────────────────────────────────────────
    return Translation(
        original=command,
        translated=command,
        shell=ctx.shell,
        confidence=0.5,
        source="passthrough",
    )


def store_outcome(outcome: CommandOutcome, qdrant_url: str = _QDRANT_URL) -> None:
    """
    Persist the result of running a translated command back to Qdrant.

    On success  → upsert a high-confidence translation mapping.
    On failure  → upsert a failure pattern for future clustering.
    """
    try:
        vec = embedder.embed(outcome.original)
        if outcome.succeeded:
            store.upsert_translation(
                bash_cmd=outcome.original,
                translated_cmd=outcome.translated,
                shell=outcome.shell.value,
                os_name=outcome.os.value,
                project_type=outcome.project_type,
                confidence=OUTCOME_CONFIDENCE,
                embedding=vec,
                url=qdrant_url,
            )
        else:
            store.upsert_failure(
                command=outcome.original,
                error_text=outcome.error_snippet,
                shell=outcome.shell.value,
                os_name=outcome.os.value,
                project_type=outcome.project_type,
                embedding=vec,
                url=qdrant_url,
            )
    except Exception as exc:
        logger.debug("store_outcome failed (%s) — skipping", exc)
