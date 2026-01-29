# backend/genre_discovery.py

"""
Genre discovery pipeline.

This module scans `files.genre` free-form metadata and populates
canonical genre taxonomy using the genre_service adapter.

No schema logic lives here.
No normalization logic lives here.
"""

from backend.genre_service import (
    split_genres,
    ensure_genre,
    map_raw_genre,
    link_file_to_genre,
)

# =============================
# discovery
# =============================

def discover_genres(conn, apply=True, clear_previous=False):
    """
    Discover genres from files.genre and populate canonical genre tables.

    Args:
        apply (bool): If False, run in preview mode.
        clear_previous (bool): Remove existing file_genres before discovery.

    Returns:
        stats dict
    """

    c = conn.cursor()

    # ---- optional cleanup ----
    if clear_previous and apply:
        c.execute("DELETE FROM file_genres")
        c.execute("DELETE FROM genre_mappings")

    rows = c.execute("""
        SELECT id, genre
        FROM files
        WHERE genre IS NOT NULL
          AND TRIM(genre) != ''
    """).fetchall()

    stats = {
        "files_seen": 0,
        "tokens_seen": 0,
        "genres_created": 0,
        "links_created": 0,
    }

    for row in rows:
        file_id = row["id"]
        raw_genre = row["genre"]

        stats["files_seen"] += 1

        for token in split_genres(raw_genre):
            stats["tokens_seen"] += 1

            res = ensure_genre(conn, token)
            genre_id = res["genre_id"]

            if res["key"] == "GENRE_CREATED":
                stats["genres_created"] += 1

            map_raw_genre(
                conn,
                raw_token=token,
                genre_id=genre_id,
                apply=apply,
            )

            link_file_to_genre(
                conn,
                file_id=file_id,
                genre_id=genre_id,
                apply=apply,
            )

            stats["links_created"] += 1

    if apply:
        conn.commit()

    return stats
