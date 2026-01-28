# backend/genre_discovery.py

from backend.genre_service import (
    split_genres,
    normalize_token,
    ensure_genre,
    map_raw_genre,
    link_file_to_genre,
)

def discover_genres(conn, apply=True, clear_previous=False):
    c = conn.cursor()

    rows = c.execute("""
        SELECT id, genre
        FROM files
        WHERE genre IS NOT NULL AND TRIM(genre) != ''
    """).fetchall()

    if clear_previous and apply:
        c.execute("DELETE FROM file_genres")
        c.execute("DELETE FROM genre_mappings")

    stats = {
        "files_seen": 0,
        "tokens_seen": 0,
        "genres_created": 0,
        "links_created": 0,
    }

    for row in rows:
        file_id = row["id"]
        raw = row["genre"]
        stats["files_seen"] += 1

        for token in split_genres(raw):
            stats["tokens_seen"] += 1

            res = ensure_genre(conn, token)
            genre_id = res["genre_id"]
            if res["key"] == "GENRE_CREATED":
                stats["genres_created"] += 1

            map_raw_genre(conn, token, genre_id, apply=apply)
            link_file_to_genre(conn, file_id, genre_id, apply=apply)
            stats["links_created"] += 1

    if apply:
        conn.commit()

    return stats
