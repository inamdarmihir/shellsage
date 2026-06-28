"""Core translation logic: bash→shell via stored-translation lookup then rule fallback."""

from __future__ import annotations

import logging
import re

from shellsage import rules
from shellsage.config import DB_PATH as _DEFAULT_DB
from shellsage.config import OUTCOME_CONFIDENCE, SCORE_THRESHOLD
from shellsage.models import CommandOutcome, Shell, ShellContext, Translation

logger = logging.getLogger(__name__)

# ── Passthrough ref lookup (Linux/macOS/bash/zsh) ─────────────────────────────
# Maps known root command names → canonical documentation URL.
# Used when no translation is needed (native shell) so supported commands still
# get citable sources without fabricating URLs for unknown project tools.
_MAN7 = "https://man7.org/linux/man-pages/man1/{cmd}.1.html"
_SS64_BASH = "https://ss64.com/bash/{cmd}.html"
_SS64_ZSH = "https://ss64.com/bash/{cmd}.html"  # ss64 bash pages cover zsh builtins too
_SS64_CMD = "https://ss64.com/nt/{cmd}.html"

# Per-command overrides. Unknown commands return no ref instead of a guessed URL.
_BASH_REFS: dict[str, str] = {
    "ls": _MAN7.format(cmd="ls"),
    "grep": _MAN7.format(cmd="grep"),
    "find": _MAN7.format(cmd="find"),
    "cat": _MAN7.format(cmd="cat"),
    "head": _MAN7.format(cmd="head"),
    "tail": _MAN7.format(cmd="tail"),
    "sort": _MAN7.format(cmd="sort"),
    "uniq": _MAN7.format(cmd="uniq"),
    "wc": _MAN7.format(cmd="wc"),
    "sed": _MAN7.format(cmd="sed"),
    "awk": _MAN7.format(cmd="awk"),
    "cut": _MAN7.format(cmd="cut"),
    "tr": _MAN7.format(cmd="tr"),
    "tee": _MAN7.format(cmd="tee"),
    "touch": _MAN7.format(cmd="touch"),
    "mkdir": _MAN7.format(cmd="mkdir"),
    "rm": _MAN7.format(cmd="rm"),
    "cp": _MAN7.format(cmd="cp"),
    "mv": _MAN7.format(cmd="mv"),
    "ln": _MAN7.format(cmd="ln"),
    "chmod": _MAN7.format(cmd="chmod"),
    "chown": _MAN7.format(cmd="chown"),
    "chgrp": _MAN7.format(cmd="chgrp"),
    "echo": _MAN7.format(cmd="echo"),
    "printf": _MAN7.format(cmd="printf"),
    "export": _SS64_BASH.format(cmd="export"),
    "source": _SS64_BASH.format(cmd="source"),
    "env": _MAN7.format(cmd="env"),
    "printenv": _MAN7.format(cmd="printenv"),
    "unset": _SS64_BASH.format(cmd="unset"),
    "cd": _SS64_BASH.format(cmd="cd"),
    "pwd": _MAN7.format(cmd="pwd"),
    "pushd": _SS64_BASH.format(cmd="pushd"),
    "popd": _SS64_BASH.format(cmd="popd"),
    "ps": _MAN7.format(cmd="ps"),
    "kill": _MAN7.format(cmd="kill"),
    "killall": _MAN7.format(cmd="killall"),
    "pgrep": _MAN7.format(cmd="pgrep"),
    "pkill": _MAN7.format(cmd="pkill"),
    "sleep": _MAN7.format(cmd="sleep"),
    "curl": "https://curl.se/docs/manpage.html",
    "wget": "https://www.gnu.org/software/wget/manual/wget.html",
    "ping": _MAN7.format(cmd="ping"),
    "ssh": _MAN7.format(cmd="ssh"),
    "scp": _MAN7.format(cmd="scp"),
    "rsync": _MAN7.format(cmd="rsync"),
    "tar": _MAN7.format(cmd="tar"),
    "zip": _SS64_BASH.format(cmd="zip"),
    "unzip": _SS64_BASH.format(cmd="unzip"),
    "gzip": _MAN7.format(cmd="gzip"),
    "gunzip": _MAN7.format(cmd="gzip"),
    "df": _MAN7.format(cmd="df"),
    "du": _MAN7.format(cmd="du"),
    "uname": _MAN7.format(cmd="uname"),
    "hostname": _MAN7.format(cmd="hostname"),
    "whoami": _MAN7.format(cmd="whoami"),
    "date": _MAN7.format(cmd="date"),
    "uptime": _MAN7.format(cmd="uptime"),
    "clear": _SS64_BASH.format(cmd="clear"),
    "history": _SS64_BASH.format(cmd="history"),
    "which": _MAN7.format(cmd="which"),
    "man": _MAN7.format(cmd="man"),
    "sudo": _MAN7.format(cmd="sudo"),
    "su": _MAN7.format(cmd="su"),
    "git": "https://git-scm.com/docs",
    "docker": "https://docs.docker.com/engine/reference/commandline/cli/",
    "kubectl": "https://kubernetes.io/docs/reference/kubectl/",
    "npm": "https://docs.npmjs.com/cli/",
    "yarn": "https://yarnpkg.com/cli/",
    "pip": "https://pip.pypa.io/en/stable/cli/",
    "python": "https://docs.python.org/3/",
    "python3": "https://docs.python.org/3/",
    "node": "https://nodejs.org/api/",
    "cargo": "https://doc.rust-lang.org/cargo/commands/",
    "go": "https://pkg.go.dev/cmd/go",
    "make": "https://www.gnu.org/software/make/manual/make.html",
    "xargs": _MAN7.format(cmd="xargs"),
    "diff": _MAN7.format(cmd="diff"),
    "patch": _MAN7.format(cmd="patch"),
    "nslookup": _SS64_BASH.format(cmd="nslookup"),
    "host": _MAN7.format(cmd="host"),
    "netstat": _MAN7.format(cmd="netstat"),
    "ss": _MAN7.format(cmd="ss"),
}

# CMD refs — common Windows CMD built-ins
_CMD_REFS: dict[str, str] = {
    "dir": _SS64_CMD.format(cmd="dir"),
    "del": _SS64_CMD.format(cmd="del"),
    "copy": _SS64_CMD.format(cmd="copy"),
    "move": _SS64_CMD.format(cmd="move"),
    "ren": _SS64_CMD.format(cmd="ren"),
    "mkdir": _SS64_CMD.format(cmd="md"),
    "rmdir": _SS64_CMD.format(cmd="rd"),
    "type": _SS64_CMD.format(cmd="type"),
    "echo": _SS64_CMD.format(cmd="echo"),
    "set": _SS64_CMD.format(cmd="set"),
    "cd": _SS64_CMD.format(cmd="cd"),
    "cls": _SS64_CMD.format(cmd="cls"),
    "find": _SS64_CMD.format(cmd="find"),
    "sort": _SS64_CMD.format(cmd="sort"),
    "more": _SS64_CMD.format(cmd="more"),
    "fc": _SS64_CMD.format(cmd="fc"),
    "xcopy": _SS64_CMD.format(cmd="xcopy"),
    "ping": _SS64_CMD.format(cmd="ping"),
    "ipconfig": _SS64_CMD.format(cmd="ipconfig"),
    "netstat": _SS64_CMD.format(cmd="netstat"),
    "tasklist": _SS64_CMD.format(cmd="tasklist"),
    "taskkill": _SS64_CMD.format(cmd="taskkill"),
    "where": _SS64_CMD.format(cmd="where"),
}


def _passthrough_ref(command: str, shell: Shell) -> str:
    """Return a docs URL for a known native command; otherwise return empty."""
    cmd_name = re.split(r"[\s|<>&;]", command.strip())[0].lstrip("./ \t").lower()
    if not cmd_name:
        return ""
    if shell == Shell.CMD:
        return _CMD_REFS.get(cmd_name, "")
    # bash / zsh / fish / unknown POSIX
    return _BASH_REFS.get(cmd_name, "")


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

    Known rule, memory, and native passthrough mappings carry a ``ref`` URL so
    the LLM agent can cite the source without inventing docs for unknown tools.
    """
    if not ctx.needs_translation:
        return Translation(
            original=command,
            translated=command,
            shell=ctx.shell,
            confidence=1.0,
            source="passthrough",
            ref=_passthrough_ref(command, ctx.shell),
        )

    # ── 1. Rule-based ────────────────────────────────────────────────────────
    translated, ref = rules.apply(command, ctx.shell)
    if translated != command:
        return Translation(
            original=command,
            translated=translated,
            shell=ctx.shell,
            confidence=0.95,
            source="rules",
            ref=ref,
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
                ref=best.get("ref", ""),
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
        ref=_passthrough_ref(command, ctx.shell),
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
