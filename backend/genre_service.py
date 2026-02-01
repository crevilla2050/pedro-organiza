"""
backend/genre_service.py

Genre-specific adapter layer built on top of taxonomy_core.

This module:
- Defines the GENRE taxonomy spec
- Provides thin wrappers for generic taxonomy operations
- Preserves backwards compatibility for API and discovery code
"""

from backend.taxonomy_core import (
    split_tokens,
    normalize_token,
    list_canonical,
    ensure_canonical,
    normalize_canonical,
    find_empty_canonical,
    purge_empty_canonical,
    taxonomy_for_selection,
)

from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List
import sqlite3


# ====================================================
# API MODELS
# ====================================================

class GenreNormalizeRequest(BaseModel):
    old_genre_ids: List[int] = Field(..., min_items=2)
    canonical_name: str = Field(..., min_length=1)

class GenreNormalizeResponse(BaseModel):
    canonical_genre_id: int
    files_affected: int
    genres_deactivated: int


# ====================================================
# GENRE TAXONOMY SPEC
# ====================================================

GENRE_SPEC = {
    "canonical_table": "genres",
    "canonical_id": "id",
    "canonical_name": "name",
    "canonical_norm": "normalized_name",
    "file_link_table": "file_genres",
    "file_link_file_id": "file_id",
    "file_link_taxonomy_id": "genre_id",
}

# ====================================================
# helpers
# ====================================================

def utcnow():
    return datetime.now(timezone.utc).isoformat()


def ensure_active_column(conn):
    """
    Ensure soft-delete support exists for genres.
    """
    c = conn.cursor()
    cols = [r[1] for r in c.execute("PRAGMA table_info(genres)").fetchall()]
    if "active" not in cols:
        c.execute("ALTER TABLE genres ADD COLUMN active INTEGER DEFAULT 1")
        conn.commit()


# ====================================================
# Backwards-compatible aliases (used by discovery)
# ====================================================

def split_genres(raw: str):
    """Alias kept for genre_discovery compatibility."""
    return split_tokens(raw)


def ensure_genre(conn, name, source="user"):
    """Genre-specific wrapper."""
    res = ensure_canonical(conn, GENRE_SPEC, name, source)
    return {
        "key": "GENRE_CREATED" if res["created"] else "GENRE_EXISTS",
        "genre_id": res["id"],
    }


def map_raw_genre(conn, raw_token, genre_id=None, source="user", apply=True):
    """
    Map raw genre token to canonical genre.
    Kept here because genre_mappings is genre-specific.
    """
    if not apply:
        return {
            "key": "PREVIEW_ONLY",
            "raw_token": raw_token,
            "genre_id": genre_id,
        }

    c = conn.cursor()
    c.execute(
        """
        INSERT OR REPLACE INTO genre_mappings (
            raw_token, normalized_token, genre_id, source, created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            raw_token,
            normalize_token(raw_token),
            genre_id,
            source,
            utcnow(),
        ),
    )

    return {
        "key": "GENRE_MAPPING_CREATED",
        "raw_token": raw_token,
        "genre_id": genre_id,
    }


def link_file_to_genre(
    conn,
    file_id,
    genre_id,
    source="tag",
    confidence=1.0,
    apply=True,
):
    """Genre-specific file link."""
    if not apply:
        return {
            "key": "PREVIEW_ONLY",
            "file_id": file_id,
            "genre_id": genre_id,
        }

    c = conn.cursor()
    c.execute(
        """
        INSERT OR IGNORE INTO file_genres (
            file_id, genre_id, source, confidence, created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (file_id, genre_id, source, confidence, utcnow()),
    )

    return {
        "key": "FILE_GENRE_LINKED",
        "file_id": file_id,
        "genre_id": genre_id,
    }

# ====================================================
# CLI / API facing wrappers (existing)
# ====================================================

def list_genres(conn, pattern="*"):
    """List canonical genres with wildcard support."""
    result = list_canonical(conn, GENRE_SPEC, pattern)
    result["key"] = "GENRES_LISTED"
    return result


def normalize_genres(
    conn,
    source_genre_names,
    target_genre_name,
    apply=False,
    clear_previous=False,
):
    """Normalize many genres into one (name-based, legacy)."""
    result = normalize_canonical(
        conn,
        spec=GENRE_SPEC,
        source_names=source_genre_names,
        target_name=target_genre_name,
        apply=apply,
        clear_previous=clear_previous,
    )

    stats = result["stats"]

    adapted_stats = {
        "source_genres": stats["source_values"],
        "target_genre": stats["target_value"],
        "files_affected": stats["files_affected"],
        "links_added": stats["links_added"],
        "links_removed": stats["links_removed"],
        "preview": stats["preview"],
    }

    return {
        "key": "GENRES_NORMALIZED",
        "stats": adapted_stats,
    }

def normalize_genres_by_ids(
    conn,
    *,
    old_genre_ids: List[int],
    canonical_name: str,
    apply: bool = False,
    clear_previous: bool = False,
):
    """
    Normalize multiple genres (by ID) into a single canonical genre.

    This is the preferred, unambiguous path used by:
    - API
    - UI
    - Advanced CLI workflows
    """

    if len(old_genre_ids) < 2:
        raise ValueError("At least two genre IDs are required")

    c = conn.cursor()

    # -------------------------------------------------
    # 1. Ensure / fetch canonical target genre
    # -------------------------------------------------
    target = ensure_canonical(
        conn,
        GENRE_SPEC,
        canonical_name,
        source="user",
    )

    target_genre_id = target["id"]

    # -------------------------------------------------
    # 2. Fetch affected files
    # -------------------------------------------------
    q = f"""
        SELECT DISTINCT file_id
        FROM file_genres
        WHERE genre_id IN ({",".join("?" for _ in old_genre_ids)})
    """
    rows = c.execute(q, old_genre_ids).fetchall()
    file_ids = [r["file_id"] for r in rows]

    # -------------------------------------------------
    # 3. Preview mode → no mutation
    # -------------------------------------------------
    if not apply:
        return {
            "key": "GENRES_NORMALIZE_PREVIEW",
            "canonical_genre_id": target_genre_id,
            "files_affected": len(file_ids),
            "genres_deactivated": len(old_genre_ids),
            "preview": True,
        }

    # -------------------------------------------------
    # 4. Apply: link files to canonical genre
    # -------------------------------------------------
    for fid in file_ids:
        c.execute(
            """
            INSERT OR IGNORE INTO file_genres (
                file_id, genre_id, source, confidence, created_at
            )
            VALUES (?, ?, 'normalize', 1.0, ?)
            """,
            (fid, target_genre_id, utcnow()),
        )

    # -------------------------------------------------
    # 5. Optionally remove previous links
    # -------------------------------------------------
    if clear_previous:
        c.execute(
            f"""
            DELETE FROM file_genres
            WHERE genre_id IN ({",".join("?" for _ in old_genre_ids)})
              AND genre_id != ?
            """,
            (*old_genre_ids, target_genre_id),
        )

    # -------------------------------------------------
    # 6. Soft-deactivate old genres (NOT delete)
    # -------------------------------------------------
    # 6. Soft-deactivate old genres (NOT delete)
    ensure_active_column(conn)

    c.execute(
        f"""
        UPDATE genres
        SET active = 0
        WHERE id IN ({",".join("?" for _ in old_genre_ids)})
        AND id != ?
        """,
        (*old_genre_ids, target_genre_id),
    )

    conn.commit()

    return {
        "key": "GENRES_NORMALIZED",
        "canonical_genre_id": target_genre_id,
        "files_affected": len(file_ids),
        "genres_deactivated": len(old_genre_ids) - 1,
        "preview": False,
    }


def find_empty_genres(conn):
    result = find_empty_canonical(conn, GENRE_SPEC)
    result["key"] = "EMPTY_GENRES_FOUND"
    return result


def purge_empty_genres(conn, apply=True):
    result = purge_empty_canonical(conn, GENRE_SPEC, apply=apply)
    result["key"] = (
        "EMPTY_GENRES_PURGED" if apply else "EMPTY_GENRES_PREVIEW"
    )
    return result


def genres_for_selection(conn, file_ids):
    """
    Adapter for API/UI selection logic.
    """
    return taxonomy_for_selection(conn, GENRE_SPEC, file_ids)

