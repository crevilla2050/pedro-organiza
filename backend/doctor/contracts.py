# backend/doctor/contracts.py

from dataclasses import dataclass, field
from typing import Literal, Any, Dict

Severity = Literal["INFO", "WARN", "FAIL"]
Tier = Literal["NONE", "SAFE", "DESTRUCTIVE"]


@dataclass
class DoctorCheckResult:
    id: str
    severity: Severity
    message: str
    autofix_available: bool = False
    autofix_tier: Tier = "NONE"
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "severity": self.severity,
            "message": self.message,
            "autofix_available": self.autofix_available,
            "autofix_tier": self.autofix_tier,
            "data": self.data,
        }
