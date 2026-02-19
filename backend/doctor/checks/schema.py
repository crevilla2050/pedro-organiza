"""
Doctor check: Schema integrity

Validates:
- pedro_environment exists
- schema version matches expected target
"""

from backend.db_migrations import (
    get_schema_version,
    TARGET_SCHEMA_VERSION,
)
from ..doctor_types import DoctorResult, DoctorIssue


def check_schema_version(conn, config=None):
    if config is None:
        config = {}
    """
    Validate schema version against code target.
    """

    try:
        current = get_schema_version(conn)
    except Exception as e:
        issues = [
            DoctorIssue(
                code="SCHEMA_UNREADABLE",
                severity="fail",
                message="Unable to read schema version",
                fix_hint="Database may be corrupted. Try restoring from backup.",
                details=str(e),
            )
        ]
        return DoctorResult(
            "schema_version",
            False,
            issues,
            {"error": str(e)},
        )

    expected = TARGET_SCHEMA_VERSION

    # ----------------------------------------
    # OK
    # ----------------------------------------
    if current == expected:
        return DoctorResult(
            "schema_version",
            True,
            [],
            {
                "status": "ok",
                "version": current,
                "target": expected,
            },
        )

    # ----------------------------------------
    # OUTDATED
    # ----------------------------------------
    if current < expected:
        issues = [
            DoctorIssue(
                code="SCHEMA_OUTDATED",
                severity="warn",
                message=f"Schema version {current}, expected {expected}",
                fix_hint="Run: pedro migrate",
                autofix_tier="safe",
            )
        ]

        return DoctorResult(
            "schema_version",
            False,
            issues,
            {
                "current": current,
                "expected": expected,
                "upgrade_required": True,
            },
        )

    # ----------------------------------------
    # FUTURE SCHEMA (rare but important)
    # ----------------------------------------
    issues = [
        DoctorIssue(
            code="SCHEMA_NEWER_THAN_CODE",
            severity="fail",
            message=f"Database schema {current} is newer than this Pedro build ({expected})",
            fix_hint="Upgrade Pedro to a newer version",
        )
    ]

    return DoctorResult(
        "schema_version",
        False,
        issues,
        {
            "current": current,
            "expected": expected,
            "downgrade_detected": True,
        },
    )

from ..registry import register_check
register_check("schema", check_schema_version)
# EOF
