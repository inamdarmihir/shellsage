"""Core translation logic: bash→shell via stored-translation lookup then rule fallback."""

from __future__ import annotations

import logging

from shellsage import rules
from shellsage.config import DB_PATH as _DEFAULT_DB
from shellsage.config import OUTCOME_CONFIDENCE, SCORE_THRESHOLD
from shellsage.models import CommandOutcome, ShellContext, Translation

logger = logging.getLogger(__name__)


def translate(
    command: str,
    ctx: ShellContext,
    db_path: str = _DEFAULT_DB,
    score_threshold: float = SCORE_THRESHOLD,
) -> Translation:
    """
    Translate *command* for the given shell context.

    Resolution order:
      1. Rule-based translation  (built-in regex patterns, always works)
      2. SQLite memory lookup    (learned from past sessions + seed)
      3. Passthrough             (command already compatible)
    """
    if not ctx.needs_translation:
        return Translation(
            original=command,
            translated=command,
            shell=ctx.shell,
            confidence=1.0,
            source="passthrough",
        )

    # ── 1. Rule-based ────────────────────────────────────────────────────────
    translated = rules.apply(command, ctx.shell)
    if translated != command:
        return Translation(
            original=command,
            translated=translated,
            shell=ctx.shell,
            confidence=0.95,
            source="rules",
        )

    # ── 2. SQLite memory lookup ───────────────────────────────────────────────
    try:
        from shellsage import store

        hits = store.query_translation(
            bash_cmd=command,
            shell=ctx.shell.value,
            os_name=ctx.os.value,
            project_type=ctx.project_type,
            score_threshold=score_threshold,
            db_path=db_path,
        )
        if hits:
            best = hits[0]
            return Translation(
                original=command,
                translated=best["translated_cmd"],
                shell=ctx.shell,
                confidence=best.get("score", best.get("confidence", 0.8)),
                source="memory",
            )
    except Exception as exc:
        logger.debug("Memory lookup failed (%s) — falling through", exc)

    # ── 3. Passthrough ────────────────────────────────────────────────────────
    return Translation(
        original=command,
        translated=command,
        shell=ctx.shell,
        confidence=0.5,
        source="passthrough",
    )


def store_outcome(outcome: CommandOutcome, db_path: str = _DEFAULT_DB) -> bool:
    """
    Persist the result of running a translated command back to SQLite.

    On success  → upsert a high-confidence translation mapping.
    On failure  → record a failure pattern for replay / analysis.
    Returns False when storage fails (never raises).
    """
    try:
        from shellsage import store

        store.ensure_tables(db_path)
        if outcome.succeeded:
            store.upsert_translation(
                bash_cmd=outcome.original,
                translated_cmd=outcome.translated,
                shell=outcome.shell.value,
                os_name=outcome.os.value,
                project_type=outcome.project_type,
                confidence=OUTCOME_CONFIDENCE,
                db_path=db_path,
            )
        else:
            store.upsert_failure(
                command=outcome.original,
                error_text=outcome.error_snippet,
                shell=outcome.shell.value,
                os_name=outcome.os.value,
                project_type=outcome.project_type,
                db_path=db_path,
            )
        return True
    except Exception as exc:
        logger.debug("store_outcome failed (%s) — skipping", exc)
        return False
