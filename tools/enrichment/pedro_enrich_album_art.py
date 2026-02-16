#!/usr/bin/env python3
"""
pedro_enrich_album_art.py

Driver script that runs the Pedro album-art enrichment step for each
album-level cluster discovered in the staging `files` table.

This script is advisory only:
- No files are modified
- No images are embedded
- Results are stored as suggestions
"""

import sqlite3
import os
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv

from new_pedro_tagger import pedro_enrich_cluster

# ---------------- I18N KEYS ----------------

MSG_DB_NOT_SET = "ERROR_DB_NOT_SET"
MSG_CLUSTERS_FOUND = "ALBUM_CLUSTERS_FOUND"
MSG_ART_SUGGESTIONS_CREATED = "ALBUM_ART_SUGGESTIONS_CREATED"

# ------------------------------------------

load_dotenv()

DB_PATH = os.getenv("MUSIC_DB")
if not DB_PATH:
    raise SystemExit({"key": MSG_DB_NOT_SET})


def utcnow():
    """Return UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def hash_image(data: bytes) -> str:
    """Return SHA-256 hex digest for image bytes."""
    return hashlib.sha256(data).hexdigest()


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Fetch album clusters
    c.execute("""
        SELECT
            album_artist,
            album,
            is_compilation,
            GROUP_CONCAT(original_path) AS paths
        FROM files
        WHERE album IS NOT NULL
        GROUP BY album_artist, album, is_compilation
    """)

    clusters = c.fetchall()
    print({
        "key": MSG_CLUSTERS_FOUND,
        "params": {"count": len(clusters)}
    })

    created = 0

    for row in clusters:
        paths = row["paths"].split(",")

        result = pedro_enrich_cluster(
            album_artist=row["album_artist"],
            album=row["album"],
            is_compilation=row["is_compilation"],
            source_paths=paths,
        )

        if not result.get("success"):
            continue

        art = result.get("art") or {}
        img = art.get("image_bytes")
        if not img:
            continue

        img_hash = hash_image(img)

        c.execute("""
            INSERT OR IGNORE INTO album_art (
                album_artist,
                album,
                is_compilation,
                image_hash,
                source,
                confidence,
                mime,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'suggested', ?)
        """, (
            row["album_artist"],
            row["album"],
            row["is_compilation"],
            img_hash,
            art.get("source"),
            art.get("confidence"),
            art.get("mime"),
            utcnow(),
        ))

        created += 1

    conn.commit()
    conn.close()

    print({
        "key": MSG_ART_SUGGESTIONS_CREATED,
        "params": {"count": created}
    })


if __name__ == "__main__":
    main()
