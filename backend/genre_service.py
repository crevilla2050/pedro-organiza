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
# CLI / API facing wrappers
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
    """Normalize many genres into one."""
    result = normalize_canonical(
        conn,
        spec=GENRE_SPEC,
        source_names=source_genre_names,
        target_name=target_genre_name,
        apply=apply,
        clear_previous=clear_previous,
    )

    stats = result["stats"]

    # ⬇️ ADAPT taxonomy stats → genre stats
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
