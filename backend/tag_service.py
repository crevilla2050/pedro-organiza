#!/usr/bin/env python3
"""
tag_service.py

Pedro Organiza — Tag Service (Core Backend)

Responsibilities:
- Manage soft tags (DB-only metadata)
- Apply / remove tags to entities (files, alias clusters)
- Compute applied / partial / available tag sets for selections

Design rules:
- No filesystem mutation
- No inference or "smart" behavior
- No FastAPI or CLI dependencies
- Explicit, deterministic behavior only
"""

import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any

# ===================== CONSTANTS =====================

ENTITY_FILE = "file"
ENTITY_ALIAS_CLUSTER = "alias_cluster"

VALID_ENTITY_TYPES = {
    ENTITY_FILE,
    ENTITY_ALIAS_CLUSTER,
}

# ===================== HELPERS =====================

def i18n_error(key: str, params: dict | None = None):
    return ValueError({
        "key": key,
        "params": params or {}
    })

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _validate_entity_type(entity_type: str):
    if entity_type not in VALID_ENTITY_TYPES:
        raise i18n_error(
            "INVALID_ENTITY_TYPE",
            {"entity_type": entity_type}
        )

def _normalize_tag_name(name: str) -> str:
    if not name:
        raise i18n_error("TAG_NAME_EMPTY")
    return " ".join(name.strip().lower().split())

# ===================== SCHEMA =====================

def ensure_tag_tables(c: sqlite3.Cursor):
    """
    Create tag tables if they do not exist.
    Safe to run multiple times.
    """
    c.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT,
            created_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tag_assignments (
            tag_id INTEGER NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (tag_id, entity_type, entity_id),
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)

# ===================== TAG CRUD =====================

def list_tags(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute("""
        SELECT id, name, color
        FROM tags
        ORDER BY name
    """).fetchall()

    return [dict(r) for r in rows]


def create_tag(
    conn: sqlite3.Connection,
    name: str,
    color: str | None = None,
) -> Dict[str, Any]:
    """
    Create a new tag.

    - Name is normalized and case-insensitive
    - Duplicate names are rejected
    """
    name_norm = _normalize_tag_name(name)
    now = utcnow()

    try:
        conn.execute(
            """
            INSERT INTO tags (name, color, created_at)
            VALUES (?, ?, ?)
            """,
            (name_norm, color, now),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise i18n_error(
            "TAG_ALREADY_EXISTS",
            {"tag": name_norm}
        )

    row = conn.execute(
        "SELECT id, name, color FROM tags WHERE name = ?",
        (name_norm,),
    ).fetchone()

    return dict(row)

# ===================== TAG ASSIGNMENT =====================

def apply_tags(
    conn: sqlite3.Connection,
    *,
    entity_type: str,
    entity_ids: List[int],
    tag_ids: List[int],
):
    """
    Apply tags to all entities in the selection.

    Idempotent:
    - Existing assignments are ignored
    """
    _validate_entity_type(entity_type)

    if not entity_ids or not tag_ids:
        return

    now = utcnow()

    for tag_id in tag_ids:
        for entity_id in entity_ids:
            conn.execute(
                """
                INSERT OR IGNORE INTO tag_assignments
                    (tag_id, entity_type, entity_id, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (tag_id, entity_type, entity_id, now),
            )

    conn.commit()


def remove_tags(
    conn: sqlite3.Connection,
    *,
    entity_type: str,
    entity_ids: List[int],
    tag_ids: List[int],
):
    """
    Remove tags from all entities in the selection.

    Safe:
    - Removing non-existing assignments is allowed
    """
    _validate_entity_type(entity_type)

    if not entity_ids or not tag_ids:
        return

    conn.execute(
        f"""
        DELETE FROM tag_assignments
        WHERE entity_type = ?
          AND entity_id IN ({",".join("?" for _ in entity_ids)})
          AND tag_id IN ({",".join("?" for _ in tag_ids)})
        """,
        (entity_type, *entity_ids, *tag_ids),
    )

    conn.commit()

# ===================== SELECTION LOGIC =====================

def tags_for_selection(
    conn: sqlite3.Connection,
    *,
    entity_type: str,
    entity_ids: List[int],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Compute tag state for a selection.

    Returns:
        {
            "applied":   [tag...],
            "partial":   [tag...],
            "available": [tag...]
        }
    """
    _validate_entity_type(entity_type)

    if not entity_ids:
        return {
            "applied": [],
            "partial": [],
            "available": list_tags(conn),
        }

    placeholders = ",".join("?" for _ in entity_ids)

    rows = conn.execute(
        f"""
        WITH counts AS (
            SELECT
                ta.tag_id,
                COUNT(DISTINCT ta.entity_id) AS hit_count
            FROM tag_assignments ta
            WHERE ta.entity_type = ?
              AND ta.entity_id IN ({placeholders})
            GROUP BY ta.tag_id
        )
        SELECT
            t.id,
            t.name,
            t.color,
            c.hit_count,
            ? AS total
        FROM tags t
        LEFT JOIN counts c ON c.tag_id = t.id
        """,
        (entity_type, *entity_ids, len(entity_ids)),
    ).fetchall()

    applied = []
    partial = []
    available = []

    for r in rows:
        tag = {
            "id": r["id"],
            "name": r["name"],
            "color": r["color"],
        }

        if r["hit_count"] is None:
            available.append(tag)
        elif r["hit_count"] == r["total"]:
            applied.append(tag)
        else:
            partial.append(tag)

    return {
        "applied": applied,
        "partial": partial,
        "available": available,
    }
# ===================== TAG LISTING =====================