"""
Pedro Organiza — Duplicate Cluster Service
------------------------------------------

Builds connected components over alias_strong_edges.

This is a pure analysis layer:
- No DB writes
- Deterministic output
- Safe for large libraries

Concept:
If A~B and B~C → cluster {A,B,C}

Graph source:
    alias_strong_edges view

Expected columns:
    file_id_a INTEGER
    file_id_b INTEGER

Author: Pedro core
"""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Iterable, Tuple
import sqlite3


# ---------------------------------------------------------
# Internal: deterministic union-find
# ---------------------------------------------------------

class UnionFind:
    """
    Deterministic Union-Find with path compression.

    Determinism rules:
    - Smaller root always wins
    - Guarantees stable cluster IDs across runs
    """

    def __init__(self):
        self.parent: Dict[int, int] = {}

    def find(self, x: int) -> int:
        parent = self.parent
        if x not in parent:
            parent[x] = x
            return x

        # Path compression
        root = x
        while parent[root] != root:
            root = parent[root]

        # Compress
        while parent[x] != x:
            nxt = parent[x]
            parent[x] = root
            x = nxt

        return root

    def union(self, a: int, b: int):
        ra = self.find(a)
        rb = self.find(b)

        if ra == rb:
            return

        # Deterministic root selection
        if ra < rb:
            self.parent[rb] = ra
        else:
            self.parent[ra] = rb


# ---------------------------------------------------------
# Core builder
# ---------------------------------------------------------

def build_duplicate_clusters(conn: sqlite3.Connection) -> Dict[int, List[int]]:
    """
    Build duplicate clusters using connected components.

    Returns:
        Dict[root_file_id, sorted_file_ids]
    """

    uf = UnionFind()

    cur = conn.cursor()

    # Pull edges from alias graph
    cur.execute("""
        SELECT file_id, other_file_id
        FROM alias_strong_edges
    """)

    # Build graph via union-find
    for a, b in cur:
        uf.union(int(a), int(b))

    # Group by root
    clusters: Dict[int, List[int]] = defaultdict(list)

    for node in uf.parent.keys():
        root = uf.find(node)
        clusters[root].append(node)

    # Sort members for determinism
    for members in clusters.values():
        members.sort()

    # Sort cluster keys deterministically
    return dict(sorted(clusters.items()))