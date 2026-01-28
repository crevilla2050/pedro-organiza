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
import fnmatch
from datetime import datetime, timezone

# ================= I18N MESSAGE KEYS =================

MSG_NO_GENRES_FOUND = "NO_GENRES_FOUND"
MSG_GENRES_LOADED = "GENRES_LOADED"
MSG_GENRE_CREATED = "GENRE_CREATED"
MSG_GENRE_MAPPING_CREATED = "GENRE_MAPPING_CREATED"
MSG_FILE_GENRE_LINKED = "FILE_GENRE_LINKED"
MSG_PREVIEW_ONLY = "PREVIEW_ONLY"
MSG_GENRES_LISTED = "GENRES_LISTED"

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

def normalize_genres(
    conn,
    source_genre_names: list[str],
    target_genre_name: str,
    apply: bool = False,
    clear_previous: bool = False,
):
    """
    Normalize multiple canonical genres into a target canonical genre.

    Behavior:
    - Exact genre name matching only (no wildcards)
    - By default: APPEND target genre
    - With clear_previous: REPLACE source genres with target
    - Never deletes canonical genres
    - Never mutates files.genre
    """

    c = conn.cursor()

    stats = {
        "source_genres": source_genre_names,
        "target_genre": target_genre_name,
        "files_affected": 0,
        "links_added": 0,
        "links_removed": 0,
        "preview": not apply,
    }

    # ---- Resolve target genre (create if needed) ----
    res = ensure_genre(conn, target_genre_name)
    target_genre_id = res["genre_id"]

    # ---- Resolve source genre IDs (exact match only) ----
    placeholders = ",".join("?" for _ in source_genre_names)

    rows = c.execute(
        f"""
        SELECT id, name
        FROM genres
        WHERE name IN ({placeholders})
        """,
        source_genre_names,
    ).fetchall()

    if not rows:
        return {
            "key": MSG_NO_GENRES_FOUND,
            "stats": stats,
        }

    source_ids = [r["id"] for r in rows]

    # ---- Find affected files ----
    file_rows = c.execute(
        f"""
        SELECT DISTINCT file_id
        FROM file_genres
        WHERE genre_id IN ({",".join("?" for _ in source_ids)})
        """,
        source_ids,
    ).fetchall()

    file_ids = [r["file_id"] for r in file_rows]
    stats["files_affected"] = len(file_ids)

    # ---- Apply changes ----
    for file_id in file_ids:
        if clear_previous:
            if apply:
                cur = c.execute(
                    f"""
                    DELETE FROM file_genres
                    WHERE file_id = ?
                      AND genre_id IN ({",".join("?" for _ in source_ids)})
                    """,
                    (file_id, *source_ids),
                )
                stats["links_removed"] += cur.rowcount
            else:
                # Preview: count how many would be removed
                cur = c.execute(
                    f"""
                    SELECT COUNT(*) AS cnt
                    FROM file_genres
                    WHERE file_id = ?
                      AND genre_id IN ({",".join("?" for _ in source_ids)})
                    """,
                    (file_id, *source_ids),
                ).fetchone()
                stats["links_removed"] += cur["cnt"]

        # Add target genre link
        if apply:
            c.execute(
                """
                INSERT OR IGNORE INTO file_genres (
                    file_id, genre_id, source, confidence, created_at
                )
                VALUES (?, ?, 'normalize', 1.0, ?)
                """,
                (file_id, target_genre_id, utcnow()),
            )
            stats["links_added"] += c.rowcount
        else:
            stats["links_added"] += 1

    if apply:
        conn.commit()

    return {
        "key": "GENRES_NORMALIZED",
        "stats": stats,
    }

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
    c = conn.cursor()
    norm = normalize_token(name)

    existing = c.execute(
        "SELECT id FROM genres WHERE normalized_name=?",
        (norm,)
    ).fetchone()

    if existing:
        return {
            "key": "GENRE_EXISTS",
            "genre_id": existing["id"]
        }

    c.execute("""
        INSERT INTO genres (name, normalized_name, source, created_at)
        VALUES (?, ?, ?, ?)
    """, (name, norm, source, utcnow()))

    return {
        "key": MSG_GENRE_CREATED,
        "genre_id": c.lastrowid
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

import fnmatch

def list_genres(conn, pattern="*"):
    """
    List canonical genres matching a wildcard pattern.
    Includes file usage count.

    Returns message key + structured data (no formatting here).
    """
    c = conn.cursor()

    rows = c.execute("""
        SELECT
            g.id,
            g.name,
            g.normalized_name,
            COUNT(fg.file_id) AS file_count
        FROM genres g
        LEFT JOIN file_genres fg ON fg.genre_id = g.id
        GROUP BY g.id
        ORDER BY g.name
    """).fetchall()

    matched = []

    for r in rows:
        if (
            fnmatch.fnmatchcase(r["name"], pattern)
            or fnmatch.fnmatchcase(r["normalized_name"], pattern.lower())
        ):
            matched.append({
                "id": r["id"],
                "name": r["name"],
                "normalized_name": r["normalized_name"],
                "file_count": r["file_count"],
            })

    return {
        "key": MSG_GENRES_LISTED,
        "data": matched,
        "pattern": pattern,
        "count": len(matched),
    }

def find_empty_genres(conn):
    c = conn.cursor()

    rows = c.execute("""
        SELECT g.id, g.name, g.normalized_name
        FROM genres g
        LEFT JOIN file_genres fg ON fg.genre_id = g.id
        WHERE fg.genre_id IS NULL
        ORDER BY g.name
    """).fetchall()

    return {
        "key": "EMPTY_GENRES_FOUND",
        "data": [
            {
                "id": r["id"],
                "name": r["name"],
                "normalized_name": r["normalized_name"],
            }
            for r in rows
        ],
        "count": len(rows),
    }

def purge_empty_genres(conn, apply=True):
    c = conn.cursor()

    empty = c.execute("""
        SELECT g.id, g.name
        FROM genres g
        LEFT JOIN file_genres fg ON fg.genre_id = g.id
        WHERE fg.genre_id IS NULL
    """).fetchall()

    if not apply:
        return {
            "key": "EMPTY_GENRES_PREVIEW",
            "count": len(empty),
            "genres": [r["name"] for r in empty],
            "preview": True,
        }

    ids = [r["id"] for r in empty]

    if ids:
        placeholders = ",".join("?" for _ in ids)
        c.execute(f"DELETE FROM genres WHERE id IN ({placeholders})", ids)
        conn.commit()

    return {
        "key": "EMPTY_GENRES_PURGED",
        "count": len(ids),
        "preview": False,
    }
