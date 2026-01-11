import sqlite3
from collections import defaultdict, deque

DB_PATH = "databases/full_knowledge.sqlite"  # adjust if needed

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

edges = c.execute("""
    SELECT file_id, other_file_id
    FROM alias_strong_edges
""").fetchall()

graph = defaultdict(set)

for r in edges:
    graph[r["file_id"]].add(r["other_file_id"])
    graph[r["other_file_id"]].add(r["file_id"])

visited = set()
clusters = []

for node in graph:
    if node in visited:
        continue

    cluster = set()
    queue = deque([node])
    visited.add(node)

    while queue:
        cur = queue.popleft()
        cluster.add(cur)

        for nbr in graph[cur]:
            if nbr not in visited:
                visited.add(nbr)
                queue.append(nbr)

    clusters.append(cluster)

# ---- Inspection ----
clusters.sort(key=len, reverse=True)

for i, cluster in enumerate(clusters[:20], start=1):
    print(f"\nCluster {i} ({len(cluster)} files):")
    for fid in cluster:
        row = c.execute("""
            SELECT original_path, artist, title, album
            FROM files WHERE id = ?
        """, (fid,)).fetchone()
        print(f"  - {row['artist']} – {row['title']} [{row['album']}]")
