# backend/doctor/registry.py

from typing import Callable, Dict, List
import sqlite3
from .contracts import DoctorCheckResult

DoctorCheckFn = Callable[[sqlite3.Connection], DoctorCheckResult]

_REGISTRY: Dict[str, DoctorCheckFn] = {}


def register_check(name: str, fn: DoctorCheckFn):
    _REGISTRY[name] = fn


def get_check(name: str) -> DoctorCheckFn:
    return _REGISTRY[name]


def list_checks() -> List[str]:
    return sorted(_REGISTRY.keys())


def run_checks(conn, checks: List[str]) -> List[DoctorCheckResult]:
    results = []
    for name in checks:
        fn = _REGISTRY.get(name)
        if not fn:
            continue
        results.append(fn(conn))
    return results

# -------------------------------------------------
# Check groups (execution profiles)
# -------------------------------------------------

QUICK_CHECKS = [
    "schema",
    "tables",
    "lockfile",
]

FULL_CHECKS = [
    # start with quick checks
    *QUICK_CHECKS,

    # future:
    # "filesystem",
    # "dependencies",
    # "aliases",
    # "genres",
]
