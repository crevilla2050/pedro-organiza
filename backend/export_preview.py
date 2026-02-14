import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any

from backend.export_layout import resolve_layout_path
from backend.export_conflicts import detect_conflicts
from backend.export_hashing import canonical_json, sha256_hex

# ---------------------------------------------------------
# Preset Loader
# ---------------------------------------------------------

def load_preset(preset_path: str) -> Dict[str, Any]:
    with open(preset_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------

def connect_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_export_candidates(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """
    Fetch all files eligible for export.

    For 0.8.5 we keep it simple:
    - Not marked for deletion
    - Not quarantined
    """

    return conn.execute("""
        SELECT
            id,
            original_path,
            artist,
            album,
            title,
            track,
            bitrate,
            size_bytes,
            sha256
        FROM files
        WHERE mark_delete = 0
          AND (quarantined_path IS NULL OR quarantined_path = '')
    """).fetchall()


# ---------------------------------------------------------
# Core Engine
# ---------------------------------------------------------

def build_preview(db_path: str, preset_path: str) -> Dict[str, Any]:
    preset = load_preset(preset_path)
    conn = connect_db(db_path)

    rows = fetch_export_candidates(conn)

    target_root = Path(preset["target_root"]).resolve()
    layout_pattern = preset["layout"]["pattern"]

    items = []
    total_size = 0

    for row in rows:
        meta = dict(row)

        export_rel = resolve_layout_path(meta, layout_pattern)
        export_abs = target_root / export_rel

        size = meta.get("size_bytes") or 0
        total_size += size

        items.append({
            "file_id": meta["id"],
            "source": meta["original_path"],
            "destination": str(export_abs),
            "size_bytes": size,
            "sha256": meta["sha256"],
        })
        items.sort(
            key=lambda x: (
                x["destination"],
                x["source"],
                x["file_id"],
            )
        )

    # Detect conflicts AFTER building all items
    conflicts = detect_conflicts(items)

    summary = {
        "total_files": len(items),
        "total_size_bytes": total_size,
        "conflict_count": len(conflicts),
        "target_root": str(target_root),
        "preset_name": preset.get("name"),
    }

    preview_core = {
        "summary": summary,
        "items": items,
        "conflicts": conflicts,
    }

    # ---------- Deterministic fingerprint ----------
    fingerprint_bytes = canonical_json(preview_core)
    preview_hash = sha256_hex(fingerprint_bytes)

    preview_core["preview_hash"] = preview_hash

    return preview_core

    