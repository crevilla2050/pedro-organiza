#!/usr/bin/env python3
"""
inspect_alias_clusters.py

Pedro Organiza — Alias Cluster Inspector (CLI)

Purpose:
- Inspect transitive alias clusters produced by Phase 2
- Debug normalization + alias signals
- Provide human-readable output

This tool:
- Is read-only
- Never mutates the database
- Assumes consolidate_music.py has already run
"""

import os
import sqlite3
import argparse
from dotenv import load_dotenv
import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.alias_engine import (
    build_alias_clusters,
    get_cluster_for_file,
)

# ===================== ENV =====================

load_dotenv()
DB_PATH = os.getenv("MUSIC_DB")

if not DB_PATH:
    raise RuntimeError("MUSIC_DB_NOT_SET")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ===================== CLI =====================

def main():
    parser = argparse.ArgumentParser(
        description="Inspect alias clusters (Phase 2)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit number of clusters shown (default: 10)",
    )

    parser.add_argument(
        "--file-id",
        type=int,
        help="Show the alias cluster for a specific file ID",
    )

    parser.add_argument(
        "--min-size",
        type=int,
        default=2,
        help="Minimum cluster size (default: 2)",
    )

    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw file IDs only",
    )

    args = parser.parse_args()
    conn = get_db()

    # ===================== SINGLE FILE MODE =====================

    if args.file_id is not None:
        cluster = get_cluster_for_file(conn, args.file_id)

        if not cluster:
            print(f"No alias cluster found for file_id={args.file_id}")
            return

        print(f"Alias cluster for file_id={args.file_id} (size={len(cluster)}):")

        rows = conn.execute(
            f"""
            SELECT id, artist, album, title, original_path
            FROM files
            WHERE id IN ({",".join("?" for _ in cluster)})
            ORDER BY id
            """,
            tuple(cluster),
        ).fetchall()

        for r in rows:
            print(f"  [{r['id']}] {r['artist']} — {r['title']} ({r['album']})")
            print(f"       {r['original_path']}")

        return

    # ===================== CLUSTER LIST MODE =====================

    clusters = build_alias_clusters(conn, min_size=args.min_size)

    print(f"Found {len(clusters)} alias clusters (min_size={args.min_size})")
    print("-" * 60)

    shown = 0
    for idx, cluster in enumerate(clusters, start=1):
        if shown >= args.limit:
            break

        print(f"Cluster #{idx} — size {len(cluster)}")

        if args.raw:
            print(" ", sorted(cluster))
        else:
            rows = conn.execute(
                f"""
                SELECT id, artist, album, title
                FROM files
                WHERE id IN ({",".join("?" for _ in cluster)})
                ORDER BY id
                """,
                tuple(cluster),
            ).fetchall()

            for r in rows:
                print(f"  [{r['id']}] {r['artist']} — {r['title']} ({r['album']})")

        print("-" * 60)
        shown += 1

    conn.close()


if __name__ == "__main__":
    main()
# =============================================================================
# END OF FILE
# =============================================================================