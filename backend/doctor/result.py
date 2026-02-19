class DoctorCheckResult:
    id: str
    severity: Literal["PASS", "WARN", "FAIL"]
    message: str

class DoctorRunResult:
    scope: str
    results: List[DoctorCheckResult]
    summary: Dict[str, int]
