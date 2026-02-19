import os
from ..doctor_types import DoctorResult, DoctorIssue

def check_roots_exist(conn, config):
    issues = []

    for key in ("source_root", "library_root"):
        path = config.get(key)
        if path and not os.path.exists(path):
            issues.append(
                DoctorIssue(
                    code="MISSING_PATH",
                    severity="error",
                    message=f"{key} does not exist",
                    details={"path": path},
                )
            )

    return DoctorResult("filesystem_roots", len(issues) == 0, issues)
