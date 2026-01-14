"""
backend/genre_service.py

Service layer for normalizing and mapping free-form genre tokens to a
canonical set of genres stored in the database.

Responsibilities:
- Extract distinct raw genre tokens from file metadata
- Create canonical `genres` entries when requested
- Create mappings from raw tokens -> canonical genre ids
- Link files to canonical genres with optional confidence/source

This module performs pure logic and database operations but does not
perform any user interaction. Instead of returning user-facing text it
returns message keys (i18n) and structured data so callers can localize
messages and present results in a UI.
"""

import re
from datetime import datetime, timezone

# ================= I18N MESSAGE KEYS =================

MSG_NO_GENRES_FOUND = "NO_GENRES_FOUND"
MSG_GENRES_LOADED = "GENRES_LOADED"
MSG_GENRE_CREATED = "GENRE_CREATED"
MSG_GENRE_MAPPING_CREATED = "GENRE_MAPPING_CREATED"
MSG_FILE_GENRE_LINKED = "FILE_GENRE_LINKED"
MSG_PREVIEW_ONLY = "PREVIEW_ONLY"

# ====================================================


def utcnow():
    """Return current UTC time as an ISO-8601 string for DB timestamps."""
    return datetime.now(timezone.utc).isoformat()


def normalize_token(token: str) -> str:
    """Normalize a genre token for consistent matching and storage.

    Normalization is intentionally minimal: trim, collapse internal
    whitespace and lowercase. This keeps normalized tokens readable while
    making equality checks deterministic.
    """
    return re.sub(r"\s+", " ", token.strip().lower())


def split_genres(raw: str):
    """Split a free-form genre string into individual tokens.

    The function splits on common separators (`,`, `;`, `/`) and trims
    whitespace. An empty input yields an empty list.
    """
    if not raw:
        return []
    return [g.strip() for g in re.split(r"[;,/]", raw) if g.strip()]


# ====================================================
# Core service functions
# ====================================================

def load_raw_genre_tokens(conn):
    """
    Returns a set of distinct raw genre tokens from files.genre
    """
    c = conn.cursor()
    tokens = set()

    for row in c.execute(
        "SELECT DISTINCT genre FROM files WHERE genre IS NOT NULL"
    ):
        for token in split_genres(row["genre"]):
            tokens.add(token)

    if not tokens:
        # No genres discovered — caller can present an i18n message
        return {
            "key": MSG_NO_GENRES_FOUND,
            "data": []
        }

    # Return a deterministic, sorted list of raw tokens for review or
    # mapping in UI workflows.
    return {
        "key": MSG_GENRES_LOADED,
        "data": sorted(tokens)
    }


def ensure_genre(conn, name, source="user"):
    """
    Create canonical genre if it doesn't exist.
    Returns genre_id.
    """
    c = conn.cursor()
    norm = normalize_token(name)

    # Create a canonical genre row if missing. We store both the
    # original `name` and a `normalized_name` for deterministic lookups.
    c.execute("""
        INSERT OR IGNORE INTO genres (
            name, normalized_name, source, created_at
        )
        VALUES (?, ?, ?, ?)
    """, (name, norm, source, utcnow()))

    # Return the canonical id for the normalized token so callers can
    # reference it when creating mappings or linking files.
    row = c.execute(
        "SELECT id FROM genres WHERE normalized_name=?",
        (norm,)
    ).fetchone()

    return {
        "key": MSG_GENRE_CREATED,
        "genre_id": row["id"]
    }


def map_raw_genre(conn, raw_token, genre_id=None, source="user", apply=True):
    """
    Map raw genre token to canonical genre.
    genre_id = None means ignored.
    """
    norm = normalize_token(raw_token)
    c = conn.cursor()

    if not apply:
        return {
            "key": MSG_PREVIEW_ONLY,
            "raw_token": raw_token,
            "normalized_token": norm,
            "genre_id": genre_id
        }

    c.execute("""
        INSERT OR REPLACE INTO genre_mappings (
            raw_token, normalized_token, genre_id, source, created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (raw_token, norm, genre_id, source, utcnow()))

    return {
        "key": MSG_GENRE_MAPPING_CREATED,
        "raw_token": raw_token,
        "genre_id": genre_id
    }



def link_file_to_genre(conn, file_id, genre_id, source="tag", confidence=1.0, apply=True):
    """
    Link a file to a canonical genre.
    """
    c = conn.cursor()

    if not apply:
        return {
            "key": MSG_PREVIEW_ONLY,
            "file_id": file_id,
            "genre_id": genre_id
        }

    c.execute("""
        INSERT OR IGNORE INTO file_genres (
            file_id, genre_id, source, confidence, created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (file_id, genre_id, source, confidence, utcnow()))

    return {
        "key": MSG_FILE_GENRE_LINKED,
        "file_id": file_id,
        "genre_id": genre_id
    }

def genres_for_selection(conn, file_ids: list[int]):

    """
    Compute genre state for a file selection.

    Returns:
        {
            "applied":   [ {id, name} ],
            "partial":   [ {id, name} ],
            "available": [ {id, name} ]
        }

    This function is UI-facing and intentionally ignores
    source/confidence/mappings.
    """
    c = conn.cursor()

    if not file_ids:
        rows = c.execute(
            "SELECT id, name FROM genres ORDER BY name"
        ).fetchall()

        return {
            "applied": [],
            "partial": [],
            "available": [dict(r) for r in rows],
        }

    placeholders = ",".join("?" for _ in file_ids)

    rows = c.execute(
        f"""
        WITH hits AS (
            SELECT
                fg.genre_id,
                COUNT(DISTINCT fg.file_id) AS hit_count
            FROM file_genres fg
            WHERE fg.file_id IN ({placeholders})
            GROUP BY fg.genre_id
        )
        SELECT
            g.id,
            g.name,
            h.hit_count,
            ? AS total
        FROM genres g
        LEFT JOIN hits h ON h.genre_id = g.id
        ORDER BY g.name
        """,
        (*file_ids, len(file_ids)),
    ).fetchall()

    applied, partial, available = [], [], []

    for r in rows:
        genre = {"id": r["id"], "name": r["name"]}

        if r["hit_count"] is None:
            available.append(genre)
        elif r["hit_count"] == r["total"]:
            applied.append(genre)
        else:
            partial.append(genre)

    return {
        "applied": applied,
        "partial": partial,
        "available": available,
    }
