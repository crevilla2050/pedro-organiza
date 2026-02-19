# backend/doctor/doctor_types.py
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class DoctorIssue:
    code: str
    severity: str  # info | warning | error | critical
    message: str
    details: Optional[Dict[str, Any]] = None
    fix_hint: Optional[str] = None


@dataclass
class DoctorResult:
    check: str
    ok: bool
    issues: List[DoctorIssue]
    stats: Optional[Dict[str, Any]] = None
