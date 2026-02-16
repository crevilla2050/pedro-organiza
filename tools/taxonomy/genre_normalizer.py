#!/usr/bin/env python3
"""
tools/genre_normalizer.py

Small utility that maps free-form genre strings stored on `files.genre`
to canonical genres via the `genre_mappings` table.

Behaviour summary:
- Tokenizes a genre string using common delimiters
- Normalizes tokens to a compact key suitable for lookup
- If a mapping exists and is not explicitly ignored, links the file to
  the canonical genre via `file_genres` (confidence 0.7)
- Operates in `dry_run` mode when requested so callers can preview
  without mutating the DB

The function returns a count of applied links and a sorted list of raw
tokens that could not be mapped so the caller can present them for
manual mapping.
"""

import re
import sqlite3
from datetime import datetime, timezone

# Delimiters commonly used in genre tags
SPLIT_RE = re.compile(r"[;/,|]+")


def utcnow():
    """Return current UTC time as ISO-8601 string for DB timestamps."""
    return datetime.now(timezone.utc).isoformat()


def normalize_token(token: str) -> str:
    """
    Normalize a genre token for deterministic lookup.

    The normalization is intentionally minimal and conservative:
    - lowercase
    - remove non-alphanumeric characters

    This produces short keys suitable for matching user-supplied tokens
    against normalized mappings stored in the DB.
    """
    return re.sub(r"\W+", "", token.lower())


def tokenize(raw: str):
    """
    Split a raw genre string into candidate tokens.

    Splits on common separators and trims whitespace. Returns an empty
    list for empty inputs.
    """
    if not raw:
        return []
    return [t.strip() for t in SPLIT_RE.split(raw) if t.strip()]


def normalize_genres(db_path, dry_run=False):
    """
    Normalize genre tags into canonical genre relations.

    Walks the `files` table, tokenizes each non-empty `genre` value and
    attempts to map each token via `genre_mappings.normalized_token`.

    If a mapping is found and `genre_id` is not NULL, a row is inserted
    into `file_genres` linking the file to the canonical genre. Inserts
    are `INSERT OR IGNORE` to keep the operation idempotent.

    Returns a dict with `applied` (count) and `unmapped` (sorted list)
    for caller review.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    files = c.execute("""
        SELECT id, genre
        FROM files
        WHERE genre IS NOT NULL AND TRIM(genre) != ''
    """).fetchall()

    unmapped = set()
    applied = 0

    for f in files:
        tokens = tokenize(f["genre"])

        for raw_token in tokens:
            # Compact normalized key used for lookup
            norm = normalize_token(raw_token)

            mapping = c.execute("""
                SELECT genre_id
                FROM genre_mappings
                WHERE normalized_token = ?
            """, (norm,)).fetchone()

            if mapping is None:
                # No mapping exists for this normalized token
                unmapped.add(raw_token)
                continue

            if mapping["genre_id"] is None:
                # Explicitly ignored token mapping (do nothing)
                continue

            if not dry_run:
                # Link file to canonical genre; idempotent due to INSERT OR IGNORE
                c.execute("""
                    INSERT OR IGNORE INTO file_genres (
                        file_id, genre_id, source, confidence, created_at
                    )
                    VALUES (?, ?, 'tag', 0.7, ?)
                """, (f["id"], mapping["genre_id"], utcnow()))

            applied += 1

    if not dry_run:
        conn.commit()

    conn.close()

    return {
        "applied": applied,
        "unmapped": sorted(unmapped),
    }
