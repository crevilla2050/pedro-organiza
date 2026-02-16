"""
Pedro Organiza — Cluster Diagnostics
------------------------------------

Read-only analysis utilities for duplicate clusters.

This layer exists to:
- Validate alias quality
- Inspect cluster size distribution
- Support doctor/CLI diagnostics

No DB writes.
"""

from __future__ import annotations
from collections import Counter
from typing import Dict, Any
import sqlite3

from backend.cluster_service import build_duplicate_clusters


# ---------------------------------------------------------
# Core stats
# ---------------------------------------------------------

def compute_cluster_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    clusters = build_duplicate_clusters(conn)

    if not clusters:
        return {
            "cluster_count": 0,
            "largest_cluster": 0,
            "average_size": 0,
            "size_histogram": {},
        }

    sizes = [len(v) for v in clusters.values()]
    total_clusters = len(sizes)

    hist = Counter(sizes)

    stats = {
        "cluster_count": total_clusters,
        "largest_cluster": max(sizes),
        "average_size": round(sum(sizes) / total_clusters, 3),
        "size_histogram": dict(sorted(hist.items())),
    }

    return stats


# ---------------------------------------------------------
# Deep inspection helpers
# ---------------------------------------------------------

def get_largest_clusters(conn: sqlite3.Connection, top_n: int = 10):
    clusters = build_duplicate_clusters(conn)
    sorted_clusters = sorted(
        clusters.values(),
        key=lambda c: (-len(c), c[0])  # deterministic ordering
    )
    return sorted_clusters[:top_n]


def find_suspicious_clusters(conn: sqlite3.Connection, min_size: int = 10):
    """
    Large clusters often indicate:
    - Metadata collapse (e.g., "Track 01")
    - Fingerprint collisions
    - Compilation albums

    Useful for QA.
    """
    clusters = build_duplicate_clusters(conn)
    return [c for c in clusters.values() if len(c) >= min_size]