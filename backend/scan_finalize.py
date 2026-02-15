"""
Pedro Organiza — Scan Finalization Layer

Central place for post-scan logic:
- Drift marking
- Future telemetry
- Scan statistics
"""

from backend.drift_service import mark_library_drift
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc).isoformat()


def finalize_scan(conn, library_id: int, scan_started_at: str):
    """
    Called once per completed scan.
    """

    drift_count = 0

    if library_id:
        drift_count = mark_library_drift(conn, library_id, scan_started_at)

    return {
        "drifted": drift_count,
    }