import os
import sqlite3
import json
import hashlib
from datetime import datetime, timezone

from backend.db_migrations import get_code_schema_version


# ============================================================
# Core Doctor Report
# ============================================================

def run_doctor(db_path):
    report = {
        "db_exists": False,
        "is_pedro_db": False,
        "schema_version": None,
        "code_schema_version": get_code_schema_version(),
        "schema_outdated": False,
        "writable": False,
        "tables_ok": False,
    }

    if not db_path or not os.path.exists(db_path):
        return report

    report["db_exists"] = True

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Check pedro_environment existence
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE name='pedro_environment'"
        ).fetchone()

        if not row:
            return report

        report["is_pedro_db"] = True

        schema = conn.execute(
            "SELECT schema_version FROM pedro_environment WHERE id=1"
        ).fetchone()["schema_version"]

        report["schema_version"] = schema
        report["schema_outdated"] = schema < report["code_schema_version"]

        # Writable check (simple, safe)
        try:
            conn.execute("SELECT 1")
            report["writable"] = True
        except Exception:
            report["writable"] = False

        # Basic table presence
        required_tables = ["files", "actions", "genres"]
        ok = True
        for t in required_tables:
            if not conn.execute(
                "SELECT name FROM sqlite_master WHERE name=?", (t,)
            ).fetchone():
                ok = False
        report["tables_ok"] = ok

    finally:
        conn.close()

    return report


# ============================================================
# Diagnostics Export
# ============================================================

def _utcnow():
    return datetime.now(timezone.utc).isoformat()


def _deterministic_hash(data_dict):
    """
    Create a deterministic SHA256 hash of the report.
    Stable ordering ensures reproducibility.
    """
    payload = json.dumps(data_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_diagnostic_report(db_path, output_path):
    """
    Runs doctor and writes a full diagnostic JSON file.

    Returns:
        deterministic_hash (str)
    """

    doctor_report = run_doctor(db_path)

    full_report = {
        "generated_at": _utcnow(),
        "db_path": os.path.abspath(db_path) if db_path else None,
        "doctor": doctor_report,
        "platform": {
            "os": os.name,
        },
    }

    diag_hash = _deterministic_hash(full_report)
    full_report["deterministic_hash"] = diag_hash

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    return diag_hash