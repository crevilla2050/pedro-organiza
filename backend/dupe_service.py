"""
Pedro Organiza — Dupe Service Adapter
-------------------------------------

Semantic adapter layer for duplicate clusters.

This module:
- Wraps cluster_service output into stable shapes
- Provides CLI/UI friendly helpers
- Preserves Pedro preview-first philosophy

No DB writes (for now).
"""

from __future__ import annotations
from typing import List, Dict, Any
import sqlite3
import os


from backend.cluster_service import build_duplicate_clusters
from backend.db_views import ensure_alias_views

def _ensure_alias_views(conn):
    try:
        ensure_alias_views(conn)
    except Exception:
        # Alias views depend on alias data.
        # If not present yet, dupes should behave as empty.
        pass

# ====================================================
# Core wrappers
# ====================================================

def list_clusters(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Return clusters in a stable, semantic shape.

    Deterministic ordering:
    - Larger clusters first
    - Then by cluster_id (root)
    """
    _ensure_alias_views(conn)
    raw = build_duplicate_clusters(conn)

    clusters = []
    for root, members in raw.items():
        clusters.append({
            "cluster_id": root,
            "members": members,
            "size": len(members),
        })

    clusters.sort(key=lambda c: (-c["size"], c["cluster_id"]))
    return clusters


def get_cluster(conn: sqlite3.Connection, cluster_id: int) -> Dict[str, Any] | None:
    """
    Fetch a single cluster by root ID.
    """
    _ensure_alias_views(conn)
    raw = build_duplicate_clusters(conn)
    members = raw.get(cluster_id)
    if not members:
        return None

    return {
        "cluster_id": cluster_id,
        "members": members,
        "size": len(members),
    }


# ====================================================
# Selection helpers (genre_service symmetry)
# ====================================================

def clusters_for_selection(conn: sqlite3.Connection, file_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Return clusters intersecting with given file IDs.
    Mirrors genres_for_selection() pattern.
    """
    _ensure_alias_views(conn)
    raw = build_duplicate_clusters(conn)

    result = []
    file_set = set(file_ids)

    for root, members in raw.items():
        intersection = file_set.intersection(members)
        if intersection:
            result.append({
                "cluster_id": root,
                "members": members,
                "selected_members": sorted(intersection),
                "size": len(members),
            })

    result.sort(key=lambda c: (-c["size"], c["cluster_id"]))
    return result


# ====================================================
# Diagnostics-style helpers (adapter-friendly)
# ====================================================

def cluster_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Lightweight stats without importing cluster_diagnostics.
    Keeps adapter self-contained for CLI usage.
    """
    _ensure_alias_views(conn)
    raw = build_duplicate_clusters(conn)
    sizes = [len(v) for v in raw.values()]

    if not sizes:
        return {
            "cluster_count": 0,
            "largest_cluster": 0,
            "average_size": 0,
        }

    return {
        "cluster_count": len(sizes),
        "largest_cluster": max(sizes),
        "average_size": round(sum(sizes) / len(sizes), 3),
    }


# ====================================================
# Preview-first placeholders (future normalization)
# ====================================================

def preview_cluster(conn: sqlite3.Connection, cluster_id: int) -> Dict[str, Any]:
    """
    Preview cluster details.
    Future-safe wrapper for normalization workflows.
    """
    _ensure_alias_views(conn)
    cluster = get_cluster(conn, cluster_id)
    if not cluster:
        return {
            "key": "CLUSTER_NOT_FOUND",
            "cluster_id": cluster_id,
        }

    return {
        "key": "CLUSTER_PREVIEW",
        "cluster": cluster,
        "preview": True,
    }

# ====================================================
# Suggestions (advisory only, deterministic)
# ====================================================

def suggest_primary(
    conn: sqlite3.Connection,
    cluster_id: int,
    *,
    prefer_lossless: bool = True,
    prefer_largest: bool = True,
    prefer_containers: list[str] | None = None,
    ignore_detected: bool = False,
):
    """
    Suggest a primary file using deterministic, user-adjustable policy.
    """
    _ensure_alias_views(conn)  # for get_cluster and detected_container
    raw = build_duplicate_clusters(conn)

    cluster = get_cluster(conn, cluster_id)
    if not cluster:
        return {"key": "CLUSTER_NOT_FOUND", "cluster_id": cluster_id}

    c = conn.cursor()
    rows = c.execute(
        f"""
        SELECT id, original_path, size_bytes, detected_container
        FROM files
        WHERE id IN ({",".join("?" for _ in cluster["members"])})
        """,
        cluster["members"],
    ).fetchall()

    LOSSLESS = {"flac", "wav", "aiff", "alac"}
    prefer_containers = prefer_containers or []

    scored = []
    for r in rows:
        path = r["original_path"] or ""

        ext_container = os.path.splitext(path)[1].lower().lstrip(".")
        detected = (r["detected_container"] or "").lower()

        # Hybrid resolution
        container = ext_container if ignore_detected else (detected or ext_container)
        size = r["size_bytes"] or 0

        score = {
            "file_id": r["id"],
            "path": path,
            "container": container,
            "lossless": container in LOSSLESS,
            "size": size,
        }

        scored.append(score)

    def sort_key(x):
        container_rank = 0
        if prefer_containers:
            container_rank = (
                prefer_containers.index(x["container"])
                if x["container"] in prefer_containers
                else len(prefer_containers)
            )

        lossless_rank = 0 if (prefer_lossless and x["lossless"]) else 1
        size_rank = -x["size"] if prefer_largest else x["size"]

        return (
            container_rank,
            lossless_rank,
            size_rank,
            x["file_id"],
        )

    scored.sort(key=sort_key)

    return {
        "key": "PRIMARY_SUGGESTED",
        "cluster_id": cluster_id,
        "suggested_primary": scored[0]["file_id"],
        "policy": {
            "prefer_lossless": prefer_lossless,
            "prefer_largest": prefer_largest,
            "prefer_containers": prefer_containers,
            "ignore_detected": ignore_detected,
        },
        "ranking": scored,
        "preview": True,
    }

def find_cluster_by_member(conn, file_id: int):
    _ensure_alias_views(conn)
    raw = build_duplicate_clusters(conn)
    for root, members in raw.items():
        if file_id in members:
            return root
    return None
