# backend/diagnostics.py

"""
Pedro Organiza — Deterministic diagnostics

Goals:
- Reproducible state capture
- Deterministic hashing
- CLI-independent core logic
"""

import json
import hashlib
import os
import sqlite3
from datetime import datetime, timezone


# ============================================================
# Helpers
# ============================================================

def utcnow():
    return datetime.now(timezone.utc).isoformat()


def canonical_json(data) -> str:
    """Stable JSON encoding (deterministic ordering)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def deterministic_hash(data) -> str:
    """Hash a structure deterministically."""
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


# ============================================================
# Core collectors
# ============================================================

def collect_db_stats(conn):
    stats = {}

    try:
        stats["files"] = conn.execute(
            "SELECT COUNT(*) FROM files"
        ).fetchone()[0]
    except Exception:
        stats["files"] = None

    try:
        stats["genres"] = conn.execute(
            "SELECT COUNT(*) FROM genres"
        ).fetchone()[0]
    except Exception:
        stats["genres"] = None

    try:
        stats["schema_version"] = conn.execute(
            "SELECT schema_version FROM pedro_environment WHERE id = 1"
        ).fetchone()[0]
    except Exception:
        stats["schema_version"] = None

    return stats


def collect_environment(db_path):
    return {
        "active_db": db_path,
        "exists": os.path.exists(db_path) if db_path else False,
        "size_bytes": os.path.getsize(db_path) if db_path and os.path.exists(db_path) else None,
        "platform": os.name,
    }


# ============================================================
# Public API
# ============================================================

def build_diagnostic_payload(db_path: str) -> dict:
    """
    Build deterministic diagnostic payload (NO timestamps).
    """

    payload = {
        "environment": collect_environment(db_path),
        "database": {},
    }

    if db_path and os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            payload["database"] = collect_db_stats(conn)
        finally:
            conn.close()

    return payload


def write_diagnostic_report(db_path: str, out_path: str) -> str:
    """
    Write a full diagnostic report with deterministic hash.
    Returns the computed hash.
    """

    payload = build_diagnostic_payload(db_path)

    # Hash BEFORE adding metadata
    state_hash = deterministic_hash(payload)

    report = dict(payload)
    report["_pedro"] = {
        "diagnostic_hash": state_hash,
        "generated_at": utcnow(),
        "format": "pedro-diagnostic-v1",
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    return state_hash