"""Tests for SQLite translation storage."""

import sqlite3

from shellsage import store
from shellsage.models import OS, Shell, ShellContext
from shellsage.translator import translate

REF = "https://docs.example.invalid/custom-build"


def test_query_translation_returns_stored_ref(tmp_path):
    db_path = str(tmp_path / "shellsage.db")
    store.ensure_tables(db_path)
    store.upsert_translation(
        bash_cmd="custom-build target",
        translated_cmd="Invoke-CustomBuild target",
        shell="powershell",
        os_name="windows",
        project_type="unknown",
        confidence=0.91,
        ref=REF,
        db_path=db_path,
    )

    hits = store.query_translation(
        bash_cmd="custom-build target",
        shell="powershell",
        os_name="windows",
        db_path=db_path,
    )

    assert hits
    assert hits[0]["translated_cmd"] == "Invoke-CustomBuild target"
    assert hits[0]["ref"] == REF


def test_translate_memory_result_carries_ref(tmp_path):
    db_path = str(tmp_path / "shellsage.db")
    store.ensure_tables(db_path)
    store.upsert_translation(
        bash_cmd="custom-build target",
        translated_cmd="Invoke-CustomBuild target",
        shell="powershell",
        os_name="windows",
        project_type="unknown",
        confidence=0.91,
        ref=REF,
        db_path=db_path,
    )
    ctx = ShellContext(
        os=OS.WINDOWS,
        shell=Shell.POWERSHELL,
        shell_version="7.4",
        project_type="unknown",
        project_root=".",
    )

    result = translate("custom-build target", ctx, db_path=db_path)

    assert result.source == "memory"
    assert result.translated == "Invoke-CustomBuild target"
    assert result.ref == REF


def test_ensure_tables_migrates_existing_database_with_ref_column(tmp_path):
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE translations (
            id TEXT PRIMARY KEY,
            bash_cmd TEXT NOT NULL,
            translated_cmd TEXT NOT NULL,
            shell TEXT NOT NULL DEFAULT 'powershell',
            os_name TEXT NOT NULL DEFAULT 'windows',
            project_type TEXT NOT NULL DEFAULT 'unknown',
            confidence REAL NOT NULL DEFAULT 0.9,
            hits INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE failures (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
            command TEXT NOT NULL,
            error_text TEXT NOT NULL DEFAULT '',
            shell TEXT NOT NULL,
            os_name TEXT NOT NULL,
            project_type TEXT NOT NULL DEFAULT 'unknown',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        )
        """
    )
    conn.commit()
    conn.close()

    store.ensure_tables(str(db_path))

    migrated = sqlite3.connect(db_path)
    columns = {row[1] for row in migrated.execute("PRAGMA table_info(translations)")}
    migrated.close()
    assert "ref" in columns
