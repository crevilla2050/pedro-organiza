from ..doctor_types import DoctorResult, DoctorIssue

def check_alias_views(conn, config):
    c = conn.cursor()
    rows = c.execute(
        "SELECT name FROM sqlite_master WHERE type='view'"
    ).fetchall()

    views = {r[0] for r in rows}

    if "alias_pairs_sha256" in views:
        return DoctorResult("alias_views", True, [])

    return DoctorResult(
        "alias_views",
        False,
        [DoctorIssue(
            code="ALIAS_VIEWS_MISSING",
            severity="warning",
            message="Alias views not created yet",
            fix_hint="They will be created automatically on demand"
        )]
    )
