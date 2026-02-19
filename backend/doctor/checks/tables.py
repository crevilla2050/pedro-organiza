"""
Doctor check: Core table integrity

Validates presence of essential Pedro tables.
"""

from ..doctor_types import DoctorResult, DoctorIssue

REQUIRED_TABLES = [
    "files",
    "actions",
    "genres",
    "file_genres",
    "genre_mappings",
]


def check_core_tables(conn, config=None):
    if config is None:
        config = {}
    """
    Ensure required tables exist in the SQLite schema.
    """

    try:
        c = conn.cursor()
        rows = c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    except Exception as e:
        issues = [
            DoctorIssue(
                code="TABLES_UNREADABLE",
                severity="fail",
                message="Unable to read database schema",
                fix_hint="Database may be corrupted. Try restoring from backup.",
                details=str(e),
            )
        ]
        return DoctorResult(
            "core_tables",
            False,
            issues,
            {"error": str(e)},
        )

    existing = {r[0] for r in rows}
    missing = [t for t in REQUIRED_TABLES if t not in existing]

    # ----------------------------------------
    # OK
    # ----------------------------------------
    if not missing:
        return DoctorResult(
            "core_tables",
            True,
            [],
            {
                "required": REQUIRED_TABLES,
                "present_count": len(existing),
            },
        )

    # ----------------------------------------
    # Missing tables
    # ----------------------------------------
    issues = [
        DoctorIssue(
            code="MISSING_TABLE",
            severity="fail",
            message=f"Missing table: {t}",
            fix_hint="Run: pedro migrate",
            autofix_tier="safe",
            details={"table": t},
        )
        for t in missing
    ]

    return DoctorResult(
        "core_tables",
        False,
        issues,
        {
            "missing_tables": missing,
            "required_tables": REQUIRED_TABLES,
        },
    )

from ..registry import register_check
register_check("tables", check_core_tables)
# EOF