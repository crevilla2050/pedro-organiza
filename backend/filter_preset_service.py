#!/usr/bin/env python3
"""
filter_preset_service.py

Pedro Organiza — Filter Preset Service

Responsibilities:
- Store and retrieve named filter presets
- Treat filter state as opaque JSON
- No query execution
- No UI or API dependencies
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Any

# ===================== HELPERS =====================

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def i18n_error(key: str, params: dict | None = None):
    return ValueError({
        "key": key,
        "params": params or {}
    })

# ===================== SCHEMA =====================

def ensure_filter_preset_tables(c: sqlite3.Cursor):
    c.execute("""
        CREATE TABLE IF NOT EXISTS filter_presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            filters_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

# ===================== CRUD =====================

def list_filter_presets(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute("""
        SELECT id, name, description
        FROM filter_presets
        ORDER BY name
    """).fetchall()

    return [dict(r) for r in rows]


def get_filter_preset(
    conn: sqlite3.Connection,
    preset_id: int,
) -> Dict[str, Any]:
    row = conn.execute("""
        SELECT *
        FROM filter_presets
        WHERE id = ?
    """, (preset_id,)).fetchone()

    if not row:
        raise i18n_error("FILTER_PRESET_NOT_FOUND", {"id": preset_id})

    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "filters": json.loads(row["filters_json"]),
    }


def create_filter_preset(
    conn: sqlite3.Connection,
    *,
    name: str,
    filters: Dict[str, Any],
    description: str | None = None,
):
    now = utcnow()

    try:
        conn.execute(
            """
            INSERT INTO filter_presets
                (name, description, filters_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                description,
                json.dumps(filters),
                now,
                now,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise i18n_error(
            "FILTER_PRESET_ALREADY_EXISTS",
            {"name": name}
        )


def update_filter_preset(
    conn: sqlite3.Connection,
    *,
    preset_id: int,
    filters: Dict[str, Any],
    description: str | None = None,
):
    now = utcnow()

    conn.execute(
        """
        UPDATE filter_presets
        SET filters_json = ?,
            description = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            json.dumps(filters),
            description,
            now,
            preset_id,
        ),
    )
    conn.commit()


def delete_filter_preset(
    conn: sqlite3.Connection,
    preset_id: int,
):
    conn.execute(
        "DELETE FROM filter_presets WHERE id = ?",
        (preset_id,),
    )
    conn.commit()
# ===================== END OF FILE =====================