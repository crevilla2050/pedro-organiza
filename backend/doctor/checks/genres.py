from ..doctor_types import DoctorResult, DoctorIssue

def check_genre_taxonomy(conn, config):
    c = conn.cursor()

    rows = c.execute(
        "SELECT COUNT(*) FROM genres"
    ).fetchone()

    count = rows[0] if rows else 0

    if count == 0:
        return DoctorResult(
            "genres",
            False,
            [DoctorIssue(
                code="NO_GENRES_DISCOVERED",
                severity="info",
                message="No genres discovered yet",
                fix_hint="Run: pedro genres discover"
            )],
            {"count": 0}
        )

    return DoctorResult("genres", True, [], {"count": count})
