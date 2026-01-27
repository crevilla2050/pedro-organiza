# backend/startup_service.py

import os
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

from backend.consolidate_music import (
    ensure_metadata_columns,
    ensure_normalized_columns,
    ensure_alias_views,
    create_db,
    _update_env,
)
from backend.normalization import normalize_text

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def _open_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(c, name: str) -> bool:
    row = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _view_exists(c, name: str) -> bool:
    row = c.execute(
        "SELECT name FROM sqlite_master WHERE type='view' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _columns_in_table(c, table: str) -> List[str]:
    rows = c.execute(f"PRAGMA table_info({table})").fetchall()
    return [r["name"] for r in rows]


# -------------------------------------------------
# 1. Inspect DB (read-only)
# -------------------------------------------------

def inspect_pedro_db(db_path: str) -> Dict[str, Any]:
    """
    Inspect a candidate database without mutating it.

    Returns structured information about:
    - file validity
    - core tables
    - row counts
    - missing columns
    - missing alias views
    - migration needs
    """

    result: Dict[str, Any] = {
        "is_valid_path": False,
        "is_valid_sqlite": False,
        "is_pedro_db": False,
        "tables": {},
        "counts": {},
        "schema": {},
        "warnings": [],
    }

    # ---------- Path checks ----------
    if not db_path:
        result["warnings"].append("NO_PATH_PROVIDED")
        return result

    p = Path(db_path)
    if not p.exists():
        result["warnings"].append("PATH_NOT_FOUND")
        return result

    if not p.is_file():
        result["warnings"].append("PATH_NOT_FILE")
        return result

    result["is_valid_path"] = True

    # ---------- SQLite open ----------
    try:
        conn = _open_db(db_path)
        c = conn.cursor()
    except Exception as e:
        result["warnings"].append("NOT_SQLITE")
        result["error"] = str(e)
        return result

    result["is_valid_sqlite"] = True

    # ---------- Core Pedro tables ----------
    core_tables = [
        "files",
        "actions",
        "album_art",
        "genres",
        "file_genres",
        "pedro_environment",
    ]


    tables_present = {}
    for t in core_tables:
        tables_present[t] = _table_exists(c, t)

    result["tables"] = tables_present

    if not tables_present.get("files"):
        result["warnings"].append("MISSING_FILES_TABLE")
        conn.close()
        return result

    # At minimum, a Pedro DB must have `files`
    result["is_pedro_db"] = True

    # ---------- Counts ----------
    try:
        result["counts"]["tracks"] = c.execute(
            "SELECT COUNT(*) FROM files"
        ).fetchone()[0]
    except Exception:
        result["counts"]["tracks"] = None
        result["warnings"].append("CANNOT_COUNT_FILES")

    if tables_present.get("actions"):
        try:
            result["counts"]["actions"] = c.execute(
                "SELECT COUNT(*) FROM actions"
            ).fetchone()[0]
        except Exception:
            result["counts"]["actions"] = None

    # ---------- Column checks (files table) ----------
    existing_columns = _columns_in_table(c, "files")

    expected_metadata_cols = [
        "composer", "year", "bpm", "disc", "track_total",
        "disc_total", "comment", "lyrics", "publisher"
    ]

    expected_norm_cols = [
        "artist_norm", "album_artist_norm",
        "album_norm", "title_norm"
    ]

    missing_metadata = [
        col for col in expected_metadata_cols
        if col not in existing_columns
    ]

    missing_norm = [
        col for col in expected_norm_cols
        if col not in existing_columns
    ]

    # ---------- Alias views ----------
    expected_views = [
        "alias_pairs_sha256",
        "alias_pairs_fingerprint",
        "alias_pairs_artist_title",
        "alias_pairs_album_title",
        "alias_pairs_all",
        "alias_pair_confidence",
        "alias_strong_edges",
        "alias_edges_with_signals",
    ]

    missing_views = [
        v for v in expected_views
        if not _view_exists(c, v)
    ]

    # ---------- Migration need summary ----------
    needs_migration = bool(missing_metadata or missing_norm or missing_views)

    result["schema"] = {
        "existing_columns": existing_columns,
        "missing_metadata_columns": missing_metadata,
        "missing_normalized_columns": missing_norm,
        "missing_views": missing_views,
        "needs_migration": needs_migration,
    }

    if missing_metadata:
        result["warnings"].append("MISSING_METADATA_COLUMNS")

    if missing_norm:
        result["warnings"].append("MISSING_NORMALIZED_COLUMNS")

    if missing_views:
        result["warnings"].append("MISSING_ALIAS_VIEWS")

        # ---------- Environment (pedro_environment) ----------
    environment = None
    if tables_present.get("pedro_environment"):
        try:
            row = c.execute("""
                SELECT
                    source_root,
                    library_root,
                    schema_version,
                    created_at,
                    last_update
                FROM pedro_environment
                WHERE id = 1
            """).fetchone()

            if row:
                environment = {
                    "source_root": row["source_root"],
                    "library_root": row["library_root"],
                    "schema_version": row["schema_version"],
                    "created_at": row["created_at"],
                    "last_update": row["last_update"],
                }
        except Exception as e:
            result["warnings"].append("CANNOT_READ_ENVIRONMENT")

    result["environment"] = environment

    conn.close()
    return result


# -------------------------------------------------
# 2. Dry-run migration (no mutations)
# -------------------------------------------------

def dry_run_migration(db_path: str) -> Dict[str, Any]:
    """
    Simulate what create_db() would add, without executing it.
    """

    info = inspect_pedro_db(db_path)

    operations = []

    schema = info.get("schema", {})

    for col in schema.get("missing_metadata_columns", []):
        operations.append({
            "type": "ADD_COLUMN",
            "table": "files",
            "column": col,
        })

    for col in schema.get("missing_normalized_columns", []):
        operations.append({
            "type": "ADD_COLUMN",
            "table": "files",
            "column": col,
        })

    for view in schema.get("missing_views", []):
        operations.append({
            "type": "CREATE_VIEW",
            "view": view,
        })

    return {
        "upgrade_needed": bool(operations),
        "operations": operations,
        "is_destructive": False,
    }


# -------------------------------------------------
# 3. Activate DB (this mutates state)
# -------------------------------------------------

def activate_pedro_db(db_path: str) -> Dict[str, Any]:
    """
    Make this DB the active one:
    - run create_db() to apply migrations
    - update MUSIC_DB in .env
    """

    # Apply real migrations (idempotent)
    conn = create_db(db_path)
    conn.close()

    # Update .env
    _update_env("MUSIC_DB", str(Path(db_path).resolve()))

    return {
        "status": "ok",
        "active_db_path": str(Path(db_path).resolve()),
    }

# -------------------------------------------------
# 4. Rescan DB (re-ingest tags / normalize / etc.)
# -------------------------------------------------

from backend.consolidate_music import analyze_files, resolve_env_path, resolve_database_path


def rescan_pedro_db(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Re-run consolidate_music.analyze_files on the current active DB.

    This is used when:
    - User imported an existing DB
    - External tag edits happened
    - User wants to refresh tags / normalization without recreating DB
    """

    if "src" not in payload:
        return {
            "status": "error",
            "error": "SRC_NOT_PROVIDED",
        }

    src = payload["src"]
    db_mode = payload.get("db_mode", "full")
    progress = bool(payload.get("progress", False))

    # Resolve current active paths from .env
    lib = resolve_env_path("MUSIC_LIB")
    db_path = resolve_database_path()

    analyze_files(
        src=src,
        lib=lib,
        db_path=db_path,
        db_mode=db_mode,
        progress=progress,
    )

    return {
        "status": "ok",
        "db_path": db_path,
        "db_mode": db_mode,
        "progress": progress,
    }

# -------------------------------------------------
# 4. Inspect Source Folder (read-only)
# -------------------------------------------------

def inspect_source_path(src_path: str) -> Dict[str, Any]:
    """
    Inspect a candidate source music folder without mutating anything.

    Checks:
    - path exists
    - is directory
    - readable
    - contains audio files
    """

    result: Dict[str, Any] = {
        "is_valid_path": False,
        "is_directory": False,
        "is_readable": False,
        "audio_file_count": 0,
        "warnings": [],
        "is_acceptable": False,
    }

    if not src_path:
        result["warnings"].append("NO_PATH_PROVIDED")
        return result

    p = Path(src_path)

    if not p.exists():
        result["warnings"].append("PATH_NOT_FOUND")
        return result

    result["is_valid_path"] = True

    if not p.is_dir():
        result["warnings"].append("PATH_NOT_DIRECTORY")
        return result

    result["is_directory"] = True

    # Check readability
    try:
        test_iter = next(p.iterdir(), None)
        result["is_readable"] = True
    except Exception:
        result["warnings"].append("PERMISSION_DENIED")
        return result

    # Count audio files (light scan, fast)
    AUDIO_EXTS = {".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wav", ".aiff"}

    count = 0
    try:
        for root, dirs, files in os.walk(p):
            for name in files:
                if Path(name).suffix.lower() in AUDIO_EXTS:
                    count += 1
    except Exception:
        result["warnings"].append("SCAN_FAILED")
        return result

    result["audio_file_count"] = count

    if count == 0:
        result["warnings"].append("NO_AUDIO_FILES")
        return result

    # If we reached here, this is acceptable
    result["is_acceptable"] = True

    return result


# -------------------------------------------------
# 5. Inspect Target Directory (read-only safety check)
# -------------------------------------------------

def _is_relative_to(child: Path, parent: Path) -> bool:
    """
    Return True if child is inside parent (after resolve).
    Compatible with Python <3.9.
    """
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def inspect_target_dir(src: str, dst: str) -> Dict[str, Any]:
    """
    Inspect a target directory for safety.

    Enforces:
    - dst exists or can be created
    - dst is directory
    - dst is writable (or parent is writable)
    - dst != src
    - dst not inside src
    - src not inside dst
    """

    result: Dict[str, Any] = {
        "is_valid_path": False,
        "is_directory": False,
        "is_writable": False,
        "exists": False,
        "is_empty": None,

        "is_same_as_source": False,
        "is_inside_source": False,
        "is_source_inside_target": False,

        "warnings": [],
        "is_acceptable": False,
    }

    if not src or not dst:
        result["warnings"].append("NO_PATH_PROVIDED")
        return result

    try:
        src_p = Path(src).resolve()
        dst_p = Path(dst).resolve()
    except Exception:
        result["warnings"].append("PATH_RESOLVE_FAILED")
        return result

    # ---------- Source checks ----------
    if not src_p.exists() or not src_p.is_dir():
        result["warnings"].append("INVALID_SOURCE_PATH")
        return result

    # ---------- Target existence / parent viability ----------
    if dst_p.exists():
        result["exists"] = True

        if not dst_p.is_dir():
            result["warnings"].append("TARGET_NOT_DIRECTORY")
            return result

        # Directory exists → we'll test writability later
        result["is_directory"] = True

    else:
        # Target does not exist: check parent
        parent = dst_p.parent

        if not parent.exists() or not parent.is_dir():
            result["warnings"].append("TARGET_PARENT_NOT_FOUND")
            return result

        # Check parent writability (can we create dst later?)
        if not os.access(parent, os.W_OK):
            result["warnings"].append("TARGET_PARENT_NOT_WRITABLE")
            return result

        # Valid case: target can be created later
        result["exists"] = False
        result["is_directory"] = True
        result["warnings"].append("TARGET_WILL_BE_CREATED")

    result["is_valid_path"] = True

    # ---------- Path relationship checks ----------
    if dst_p == src_p:
        result["is_same_as_source"] = True
        result["warnings"].append("TARGET_EQUALS_SOURCE")
        return result

    if _is_relative_to(dst_p, src_p):
        result["is_inside_source"] = True
        result["warnings"].append("TARGET_INSIDE_SOURCE")
        return result

    if _is_relative_to(src_p, dst_p):
        result["is_source_inside_target"] = True
        result["warnings"].append("SOURCE_INSIDE_TARGET")
        return result

    # ---------- Writability check ----------
    try:
        test_dir = dst_p if dst_p.exists() else dst_p.parent
        test_file = test_dir / ".pedro_write_test.tmp"

        with open(test_file, "w") as f:
            f.write("test")

        test_file.unlink()

        result["is_writable"] = True
    except Exception:
        result["warnings"].append("TARGET_NOT_WRITABLE")
        return result

    # ---------- Emptiness check (warning only) ----------
    try:
        if dst_p.exists():
            entries = list(dst_p.iterdir())
            result["is_empty"] = len(entries) == 0
            if not result["is_empty"]:
                result["warnings"].append("TARGET_NOT_EMPTY")
        else:
            # Non-existing target is implicitly empty
            result["is_empty"] = True
    except Exception:
        result["warnings"].append("CANNOT_LIST_TARGET")
        return result

    # ---------- Final acceptability ----------
    result["is_acceptable"] = True
    return result
