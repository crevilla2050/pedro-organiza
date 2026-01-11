"""
alias_engine.py

Pedro Organiza — Alias Clustering Engine

Purpose:
- Build transitive alias clusters from converged alias signals
- Aggregate signals per cluster
- Compute optimistic confidence scores
- Select a canonical candidate per cluster
- Expose UI-ready, read-only cluster records

This module is:
- Deterministic
- Side-effect free
- DB read-only
"""

import sqlite3
from typing import Dict, List, Set, Any
from collections import defaultdict


# ============================================================
# Low-level graph construction
# ============================================================

def build_alias_graph(conn: sqlite3.Connection) -> Dict[int, Set[int]]:
    """
    Build an undirected graph from strong alias edges.

    Returns:
        { file_id: {other_file_id, ...}, ... }
    """
    rows = conn.execute(
        """
        SELECT file_id, other_file_id
        FROM alias_strong_edges
        """
    ).fetchall()

    graph: Dict[int, Set[int]] = defaultdict(set)

    for a, b in rows:
        graph[a].add(b)
        graph[b].add(a)

    return graph


def connected_components(graph: Dict[int, Set[int]]) -> List[Set[int]]:
    """
    Compute connected components of an undirected graph.
    """
    visited: Set[int] = set()
    clusters: List[Set[int]] = []

    for node in graph:
        if node in visited:
            continue

        stack = [node]
        component = set()

        while stack:
            cur = stack.pop()
            if cur in visited:
                continue

            visited.add(cur)
            component.add(cur)
            stack.extend(graph.get(cur, []))

        clusters.append(component)

    return clusters


# ============================================================
# Signal aggregation
# ============================================================

def aggregate_signals(
    conn: sqlite3.Connection,
    cluster: set[int],
) -> dict[str, int]:
    """
    Count how many alias signals contributed inside a cluster.

    Returns:
        {
            "sha256": 12,
            "fingerprint": 8,
            "artist_title": 31,
            "album_title": 19
        }
    """
    if len(cluster) < 2:
        return {}

    placeholders = ",".join("?" for _ in cluster)

    rows = conn.execute(
        f"""
        SELECT
            signal_type,
            COUNT(*) AS count
        FROM alias_pairs_all
        WHERE
            file_id IN ({placeholders})
            AND other_file_id IN ({placeholders})
        GROUP BY signal_type
        """,
        tuple(cluster) * 2,
    ).fetchall()

    return {row["signal_type"]: row["count"] for row in rows}



# ============================================================
# Canonical candidate selection
# ============================================================

def choose_canonical_candidate(
    conn: sqlite3.Connection,
    cluster: Set[int],
    signals: Dict[str, int],
) -> int:
    """
    Deterministically select the canonical file for a cluster.

    Priority:
    1. Most metadata present
    2. Shortest normalized path
    3. Lowest file_id (stable tie-break)
    """
    placeholders = ",".join("?" for _ in cluster)

    rows = conn.execute(
        f"""
        SELECT
            id,
            artist,
            album,
            title,
            LENGTH(original_path) AS path_len
        FROM files
        WHERE id IN ({placeholders})
        """,
        tuple(cluster),
    ).fetchall()

    def score(row):
        meta_score = sum(1 for k in ("artist", "album", "title") if row[k])
        return (
            -meta_score,          # more metadata is better
            row["path_len"],      # shorter path preferred
            row["id"],            # stable tie-break
        )

    best = sorted(rows, key=score)[0]
    return best["id"]


# ============================================================
# Optimistic confidence calculation
# ============================================================

def compute_confidence(
    size: int,
    signals: Dict[str, int],
) -> float:
    """
    Optimistic confidence model.

    Philosophy:
    - Err on the side of grouping
    - UI/user can always split later
    """

    score = 0.0

    # Strong signals
    if signals.get("sha256", 0) > 0:
        score += 0.50

    if signals.get("fingerprint", 0) > 0:
        score += 0.30

    # Metadata agreement (soft boost)
    meta_hits = (
        signals.get("artist_title", 0)
        + signals.get("album_title", 0)
    )

    if meta_hits > 0:
        score += min(0.20, meta_hits * 0.05)

    # Size boost (more corroboration)
    if size >= 3:
        score += 0.05
    if size >= 5:
        score += 0.05

    return round(min(score, 1.0), 3)


# ============================================================
# Public API
# ============================================================

def clusters_as_records(
    conn: sqlite3.Connection,
    min_size: int = 2,
) -> List[Dict[str, Any]]:
    """
    High-level helper for API / UI.

    Returns clusters enriched with:
    - signals
    - confidence
    - canonical candidate
    """
    graph = build_alias_graph(conn)
    raw_clusters = connected_components(graph)

    results: List[Dict[str, Any]] = []

    for idx, cluster in enumerate(raw_clusters, start=1):
        if len(cluster) < min_size:
            continue

        signals = aggregate_signals(conn, cluster)
        confidence = compute_confidence(len(cluster), signals)
        canonical_id = choose_canonical_candidate(conn, cluster, signals)

        placeholders = ",".join("?" for _ in cluster)
        files = conn.execute(
            f"""
            SELECT
                id,
                artist,
                album,
                title,
                original_path
            FROM files
            WHERE id IN ({placeholders})
            ORDER BY id
            """,
            tuple(cluster),
        ).fetchall()

        results.append({
            "cluster_id": idx,
            "size": len(cluster),
            "confidence": confidence,
            "signals": signals,
            "canonical_candidate_id": canonical_id,

            # ---- inert metadata (future use) ----
            "resolution_status": "unresolved",
            "user_decision": None,
            "notes": None,
            "cluster_tags": [],

            "files": [dict(r) for r in files],
        })

    return results
