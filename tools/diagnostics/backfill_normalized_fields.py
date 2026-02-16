from backend.normalization import normalize_text
import sqlite3

conn = sqlite3.connect("databases/full_knowledge.sqlite")
c = conn.cursor()

rows = c.execute("""
    SELECT id, artist, album_artist, album, title
    FROM files
""").fetchall()

for r in rows:
    c.execute("""
        UPDATE files SET
            artist_norm = ?,
            album_artist_norm = ?,
            album_norm = ?,
            title_norm = ?
        WHERE id = ?
    """, (
        normalize_text(r[1]),
        normalize_text(r[2]),
        normalize_text(r[3]),
        normalize_text(r[4]),
        r[0],
    ))

conn.commit()
conn.close()
