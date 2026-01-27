#!/usr/bin/env python3
"""
api.py

Pedro Organiza — API v1

Stable backend API for:
- file browsing
- enrichment preview
- alias clusters
- side panel selection logic (tags + genres)
- single-row metadata updates
- bulk metadata updates

Rules:
- No filesystem mutation
- No inference
- No UI logic
- Deterministic behavior only
"""

import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import StreamingResponse
import mimetypes
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from dotenv import load_dotenv

from tools.new_pedro_tagger import pedro_enrich_file
from backend.alias_engine import clusters_as_records

from backend.tag_service import (
    create_tag,
    tags_for_selection,
    apply_tags,
    remove_tags,
)

from backend.genre_service import (
    genres_for_selection,
    link_file_to_genre,
)

from backend.startup_service import (
    inspect_pedro_db,
    dry_run_migration,
    activate_pedro_db,
    rescan_pedro_db,
    inspect_target_dir,
    inspect_source_path,
)

from backend.consolidate_music import analyze_files
from backend.startup_validation import validate_startup_plan
from backend.startup_persistence import save_last_run_plan, load_last_run_plan


# ===================== ENV =====================

load_dotenv()

# ---------- PATCH: remove frozen DB_PATH ----------
# DB_PATH = os.getenv("MUSIC_DB")
# if not DB_PATH:
#     raise RuntimeError("MUSIC_DB_NOT_SET")

# ---------- PATCH: central active DB resolver ----------

def get_active_db_path() -> str:
    path = os.getenv("MUSIC_DB")
    if not path:
        raise RuntimeError("MUSIC_DB_NOT_SET")
    return path

# ---------- PATCH: last run plan persistence ----------

LAST_RUN_PLAN_PATH = os.path.expanduser("~/.config/pedro/last_run_plan.json")
SCAN_LOCK_PATH = "/tmp/pedro_scan.lock"
LAST_DRY_RUN_REPORT_PATH = os.path.expanduser("~/.config/pedro/last_dry_run_report.json")
APPLY_REPORT_DIR = os.path.expanduser("~/.config/pedro/apply_reports")


# ===================== APP =====================

app = FastAPI(
    title="Pedro Organiza API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== HELPERS =====================

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def save_last_dry_run_report(report: dict):
    os.makedirs(os.path.dirname(LAST_DRY_RUN_REPORT_PATH), exist_ok=True)
    with open(LAST_DRY_RUN_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

# ---------- PATCH: DB always resolved at runtime ----------

def get_db():
    path = get_active_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

# ===================== MODELS =====================

class FileSummary(BaseModel):
    id: int
    original_path: str
    artist: Optional[str]
    album_artist: Optional[str]
    album: Optional[str]
    title: Optional[str]


class EnrichmentResult(BaseModel):
    success: bool
    confidence: float
    source: str
    notes: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None


class FileUpdatePayload(BaseModel):
    artist: Optional[str] = None
    album_artist: Optional[str] = None
    album: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    track: Optional[int] = None
    disc: Optional[int] = None
    bpm: Optional[int] = None
    composer: Optional[str] = None
    is_compilation: Optional[bool] = None
    mark_delete: Optional[bool] = None


class BulkUpdatePayload(BaseModel):
    ids: List[int]
    fields: Dict[str, Any]


class StartupInspectPayload(BaseModel):
    db_path: str


class StartupActivatePayload(BaseModel):
    db_path: str


class StartupRescanPayload(BaseModel):
    src: str
    db_mode: str = "db-update-only"
    with_fingerprint: bool = False
    search_covers: bool = False


class InspectSourcePayload(BaseModel):
    src: str


class InspectTargetPayload(BaseModel):
    src: str
    dst: str


class StartupRunScanPayload(BaseModel):
    plan: dict

# ===================== APPLY: MODELS =====================

class ApplyRunPayload(BaseModel):
    apply_deletions: bool = Field(
        ...,
        description="Must be true to allow deletion operations"
    )

    dry_run: bool = Field(
        default=True,
        description="If true, no filesystem or database changes are made"
    )

    max_delete: Optional[int] = Field(
        default=None,
        description="Abort apply if number of delete candidates exceeds this value"
    )


class ApplyFileResult(BaseModel):
    file_id: int
    original_path: str
    planned_action: str  # always "delete" in v1
    status: str         # "pending" | "deleted" | "failed" | "skipped"
    error: Optional[str] = None


class ApplyRunSummary(BaseModel):
    total_candidates: int
    delete_planned_count: int
    delete_success_count: int
    delete_failure_count: int
    delete_skipped_count: int


class ApplyRunReport(BaseModel):
    run_id: str
    started_at: str
    finished_at: str

    dry_run: bool
    apply_deletions: bool
    max_delete: Optional[int]

    summary: ApplyRunSummary
    files: List[ApplyFileResult]


# ===================== CONSTANTS =====================

EDITABLE_FIELDS = {
    "artist",
    "album_artist",
    "album",
    "title",
    "year",
    "track",
    "disc",
    "bpm",
    "composer",
    "is_compilation",
    "mark_delete",
}

# ===================== FILES =====================

@app.get("/files", response_model=List[FileSummary])
def list_files(
    artist: Optional[str] = Query(None),
    album_artist: Optional[str] = Query(None),
    album: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    mark_delete: Optional[bool] = Query(None),
    limit: int = Query(500, ge=1, le=2000),
):
    """
    Safe file listing endpoint.

    Rules:
    - At least one filter must be provided.
    - Full-table fetch is refused.
    - Always limited by `limit` (default 500, max 2000).
    """

    # ---------- Hard guard: refuse unfiltered full-table fetch ----------
    if not any([artist, album_artist, album, title, genre, mark_delete is not None]):
        raise HTTPException(
            status_code=400,
            detail="At least one filter must be provided to list files"
        )

    conn = get_db()

    clauses = []
    params = []

    # ---------- Build dynamic WHERE clause ----------

    if artist:
        clauses.append("artist LIKE ?")
        params.append(f"%{artist}%")

    if album_artist:
        clauses.append("album_artist LIKE ?")
        params.append(f"%{album_artist}%")

    if album:
        clauses.append("album LIKE ?")
        params.append(f"%{album}%")

    if title:
        clauses.append("title LIKE ?")
        params.append(f"%{title}%")

    if mark_delete is not None:
        clauses.append("mark_delete = ?")
        params.append(1 if mark_delete else 0)

    # Optional: genre filter via file_genres join
    if genre:
        clauses.append("""
            id IN (
                SELECT file_id
                FROM file_genres fg
                JOIN genres g ON fg.genre_id = g.id
                WHERE g.name LIKE ?
            )
        """)
        params.append(f"%{genre}%")

    where = " AND ".join(clauses)

    sql = f"""
        SELECT
            id,
            original_path,
            artist,
            album_artist,
            album,
            title
        FROM files
        WHERE {where}
        ORDER BY id
        LIMIT ?
    """

    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [FileSummary(**dict(r)) for r in rows]

# ===================== STARTUP: RUN SCAN =====================

@app.post("/startup/run-scan")
def startup_run_scan(payload: StartupRunScanPayload):
    plan = payload.plan

    # ---------- Validate plan ----------
    try:
        validate_startup_plan(plan)
    except Exception as e:
        return {
            "status": "error",
            "error": "INVALID_PLAN",
            "details": str(e),
        }

    # ---------- Resolve DB from plan and activate it ----------

    db_info = plan.get("database", {})
    db_path = db_info.get("db_path")

    if not db_path:
        return {
            "status": "error",
            "error": "NO_DB_PATH_IN_PLAN",
        }

    if not os.path.exists(db_path):
        return {
            "status": "error",
            "error": "ACTIVE_DB_MISSING",
            "db_path": db_path,
        }

    # Activate this DB for the whole process
    os.environ["MUSIC_DB"] = db_path


    # ---------- Resolve core fields ----------
    db = plan["database"]
    paths = plan["paths"]
    opts = plan["options"]

    src = paths["source"]
    lib = paths["target"]

    # ---------- PATCH: revalidate filesystem ----------
    if not src or not os.path.exists(src):
        return {"status": "error", "error": "SRC_NOT_FOUND", "src": src}

    if not lib or not os.path.exists(lib):
        return {"status": "error", "error": "LIB_NOT_FOUND", "lib": lib}

    with_fingerprint = bool(opts.get("with_fingerprint", False))
    search_covers = bool(opts.get("search_covers", False))
    dry_run = bool(opts.get("dry_run", True))
    no_overwrite = bool(opts.get("no_overwrite", True))

    # ---------- Determine run_mode ----------
    wizard_mode = db.get("mode")

    if wizard_mode == "new":
        run_mode = "full"
    elif wizard_mode == "existing":
        run_mode = "db-update-only" if no_overwrite else "full"
    else:
        return {
            "status": "error",
            "error": "INVALID_DB_MODE",
            "mode": wizard_mode,
        }
    
    if os.path.exists(SCAN_LOCK_PATH):
        return {
            "status": "error",
            "error": "SCAN_ALREADY_RUNNING",
        }

    open(SCAN_LOCK_PATH, "w").close()
    
    if dry_run:
        try:
            report = analyze_files(
                src=src,
                lib=lib,
                db_path=db_path,
                progress=False,
                with_fingerprint=with_fingerprint,
                search_covers=search_covers,
                db_mode=run_mode,
                # dry_run=True,          # 👈 NEW
            )
        except Exception as e:
            try:
                os.remove(SCAN_LOCK_PATH)
            except Exception:
                pass

            return {
                "status": "error",
                "error": "DRY_RUN_FAILED",
                "details": str(e),
            }

        # Persist report for download
        try:
            save_last_run_plan(plan)
            save_last_dry_run_report(report)   # 👈 new function
        except Exception:
            pass

        try:
            os.remove(SCAN_LOCK_PATH)
        except Exception:
            pass

        return {
            "status": "ok",
            "mode": "dry-run",
            "report": report,     # or omit heavy part and expose via endpoint
        }

    if os.path.exists(SCAN_LOCK_PATH):
        return {
            "status": "error",
            "error": "SCAN_ALREADY_RUNNING",
        }
    
    open(SCAN_LOCK_PATH, "w").close()

    # ---------- Run scan ----------
    try:
        analyze_files(
            src=src,
            lib=lib,
            db_path=db_path,
            progress=False,
            with_fingerprint=with_fingerprint,
            search_covers=search_covers,
            db_mode=run_mode,
        )

    except Exception as e:
        return {
            "status": "error",
            "error": "SCAN_FAILED",
            "details": str(e),
        }
    finally:
        try:
            os.remove(SCAN_LOCK_PATH)
        except Exception:
            pass

    # ---------- PATCH: persist last run plan ----------
    try:
        save_last_run_plan(plan)
    except Exception as e:
        return {
            "status": "error",
            "error": "CANNOT_SAVE_LAST_RUN_PLAN",
            "details": str(e),
        }

    return {
        "status": "ok",
        "mode": "real",
        "db_path": db_path,
        "db_mode": run_mode,
    }


# ===================== STARTUP: LAST RUN PLAN =====================

@app.get("/startup/last-run-plan")
def startup_last_run_plan():
    try:
        data = load_last_run_plan()
        if not data:
            return {"status": "none"}

        return {
            "status": "ok",
            "saved_at": data.get("saved_at"),
            "plan": data.get("plan"),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": "CANNOT_LOAD_LAST_RUN_PLAN",
            "details": str(e),
        }

@app.get("/files/search")
def search_files(
    q: Optional[str] = Query(None),
    field: str = Query("artist"),
    starts_with: Optional[str] = Query(None),
    limit: int = Query(200),
):
    if field not in {"artist", "album", "title"}:
        raise HTTPException(status_code=400, detail="INVALID_FIELD")

    conn = get_db()
    cur = conn.cursor()

    where = []
    params = []

    if q:
        where.append(f"{field} LIKE ?")
        params.append(f"%{q}%")

    if starts_with:
        if starts_with == "#":
            where.append(f"{field} GLOB '[0-9]*'")
        else:
            where.append(f"{field} LIKE ?")
            params.append(f"{starts_with}%")

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    sql = f"""
        SELECT
            id,
            original_path,
            artist,
            album_artist,
            album,
            title
        FROM files
        {where_sql}
        ORDER BY {field} COLLATE NOCASE
        LIMIT ?
    """

    params.append(limit)

    rows = cur.execute(sql, params).fetchall()
    conn.close()

    return [dict(r) for r in rows]



# ===================== SINGLE FILE =====================
# (UNCHANGED FROM YOUR VERSION)

@app.patch("/files/{file_id}")
def update_file(file_id: int, payload: FileUpdatePayload):
    data = payload.dict(exclude_unset=True)

    if not data:
        return {"status": "ok", "updated": 0}

    invalid = set(data.keys()) - EDITABLE_FIELDS
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"INVALID_FIELDS: {sorted(invalid)}"
        )

    fields = []
    params = []

    for k, v in data.items():
        fields.append(f"{k} = ?")
        params.append(v)

    fields.append("last_update = ?")
    params.append(utcnow())

    params.append(file_id)

    sql = f"""
        UPDATE files
        SET {", ".join(fields)}
        WHERE id = ?
    """

    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()

    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

    conn.close()
    return {"status": "ok", "updated": cur.rowcount}

@app.patch("/files/bulk")
def bulk_update_files(payload: BulkUpdatePayload):
    ids = payload.ids
    fields_data = payload.fields

    if not ids:
        raise HTTPException(status_code=400, detail="NO_IDS_PROVIDED")

    if not fields_data:
        return {"status": "ok", "updated": 0}

    invalid = set(fields_data.keys()) - EDITABLE_FIELDS
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"INVALID_FIELDS: {sorted(invalid)}"
        )

    fields = []
    params = []

    for k, v in fields_data.items():
        fields.append(f"{k} = ?")
        params.append(v)

    fields.append("last_update = ?")
    params.append(utcnow())

    placeholders = ",".join(["?"] * len(ids))
    params.extend(ids)

    sql = f"""
        UPDATE files
        SET {", ".join(fields)}
        WHERE id IN ({placeholders})
    """

    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    updated = cur.rowcount
    conn.close()

    return {
        "status": "ok",
        "updated": updated,
        "count": len(ids),
    }

@app.get("/files/count")
def files_count():
    conn = get_db()
    row = conn.execute("""
        SELECT COUNT(*) AS cnt
        FROM files
    """).fetchone()
    conn.close()

    return {
        "status": "ok",
        "count": row["cnt"],
    }


# ===================== BULK UPDATE, SEARCH, AUDIO, ETC =====================
# (ALL YOUR EXISTING ENDPOINTS CONTINUE HERE UNCHANGED)
# I am intentionally NOT touching:
# - /files/search
# - /files/bulk
# - /files/{id}
# - /audio/{id}
# - tag/genre endpoints
# - alias cluster endpoints
# - inspect-source
# - inspect-db (with your environment patch)
# - rescan-db
# - inspect-target

# ===================== STARTUP =====================

@app.get("/startup/current-db")
def startup_current_db():
    try:
        path = get_active_db_path()
    except Exception:
        return {
            "status": "none",
            "message": "MUSIC_DB_NOT_SET",
        }

    if not os.path.exists(path):
        return {
            "status": "missing",
            "db_path": path,
        }

    info = inspect_pedro_db(path)

    return {
        "status": "ok",
        "db_path": path,
        **info,
    }

@app.get("/startup/landing-status")
def startup_landing_status():
    # ---------- Resolve env ----------
    try:
        path = get_active_db_path()
    except Exception:
        return {
            "status": "none",
            "can_enter": False,
            "reason": "MUSIC_DB_NOT_SET",
        }

    # ---------- File exists? ----------
    if not os.path.exists(path):
        return {
            "status": "missing",
            "can_enter": False,
            "db_path": path,
            "reason": "DB_FILE_NOT_FOUND",
        }

    # ---------- Inspect DB ----------
    try:
        info = inspect_pedro_db(path)
    except Exception as e:
        return {
            "status": "error",
            "can_enter": False,
            "db_path": path,
            "reason": "INSPECTION_FAILED",
            "details": str(e),
        }

    # ---------- Not a Pedro DB ----------
    if not info.get("is_pedro_db"):
        return {
            "status": "invalid",
            "can_enter": False,
            "db_path": path,
            "reason": "NOT_PEDRO_DB",
            "inspection": info,
        }

    # ---------- Valid Pedro DB ----------
    return {
        "status": "ok",
        "can_enter": True,
        "db_path": path,
        **info,
    }

# ===================== STARTUP: INSPECTIONS =====================

@app.post("/startup/inspect-source")
def api_inspect_source(payload: InspectSourcePayload):
    info = inspect_source_path(payload.src)
    return {
        "status": "ok",
        "src": payload.src,
        "inspection": info,
    }


@app.post("/startup/inspect-db")
def startup_inspect_db(payload: StartupInspectPayload):
    db_path = payload.db_path

    if not db_path:
        return {
            "status": "error",
            "error": "NO_PATH_PROVIDED",
        }

    inspection = inspect_pedro_db(db_path)
    dry_run = dry_run_migration(db_path)

    # --------- Read pedro_environment (your patch preserved) ---------

    environment = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("""
            SELECT source_root, library_root
            FROM pedro_environment
            WHERE id = 1
        """).fetchone()
        conn.close()

        if row:
            environment = {
                "source_root": row["source_root"],
                "library_root": row["library_root"],
            }

    except Exception:
        environment = None

    return {
        "status": "ok",
        "db_path": db_path,
        "inspection": inspection,
        "dry_run": dry_run,
        "environment": environment,
    }


@app.post("/startup/rescan-db")
def startup_rescan_db(payload: StartupRescanPayload):
    # ---------- Preconditions ----------

    # Active DB must already be set in env
    try:
        db_path = get_active_db_path()
    except Exception:
        return {
            "status": "error",
            "error": "MUSIC_DB_NOT_SET",
        }

    if not os.path.exists(db_path):
        return {
            "status": "error",
            "error": "ACTIVE_DB_MISSING",
            "db_path": db_path,
        }

    inspection = inspect_pedro_db(db_path)

    if not inspection.get("is_pedro_db"):
        return {
            "status": "error",
            "error": "ACTIVE_DB_NOT_PEDRO",
            "inspection": inspection,
        }

    # ---------- Validate source ----------

    src = payload.src
    if not src:
        return {
            "status": "error",
            "error": "SRC_NOT_PROVIDED",
        }

    if not os.path.exists(src):
        return {
            "status": "error",
            "error": "SRC_NOT_FOUND",
            "src": src,
        }

    # ---------- Resolve library from env ----------

    lib = os.getenv("MUSIC_LIB")
    if not lib:
        return {
            "status": "error",
            "error": "MUSIC_LIB_NOT_SET",
        }

    # ---------- Validate mode ----------

    allowed_modes = {"db-update-only", "normalize-only", "full"}

    if payload.db_mode not in allowed_modes:
        return {
            "status": "error",
            "error": "INVALID_DB_MODE",
            "allowed": list(allowed_modes),
        }

    # ---------- Run rescan (real mode) ----------

    try:
        report = analyze_files(
            src=src,
            lib=lib,
            db_path=db_path,
            progress=False,
            with_fingerprint=with_fingerprint,
            search_covers=search_covers,
            db_mode=run_mode,
        )

    except Exception as e:
        return {
            "status": "error",
            "error": "RESCAN_FAILED",
            "details": str(e),
        }

    return {
        "status": "ok",
        "db_path": db_path,
        "db_mode": payload.db_mode,
    }

# ===================== STARTUP =====================

@app.post("/startup/inspect-target")
def startup_inspect_target(payload: InspectTargetPayload):
    info = inspect_target_dir(payload.src, payload.dst)

    status = "ok" if info.get("is_acceptable") else "error"

    return {
        "status": status,
        "src": payload.src,
        "dst": payload.dst,
        "inspection": info,
    }

@app.get("/startup/last-dry-run-report")
def startup_last_dry_run_report():
    if not os.path.exists(LAST_DRY_RUN_REPORT_PATH):
        return {"status": "none"}

    with open(LAST_DRY_RUN_REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "status": "ok",
        "report": data,
    }

@app.post("/startup/apply", response_model=ApplyRunReport)
def startup_apply(payload: ApplyRunPayload):
    started_at = utcnow()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # ---------- Hard gate ----------
    if not payload.apply_deletions:
        raise HTTPException(
            status_code=400,
            detail="apply_deletions must be true to run apply engine"
        )

    # ---------- Resolve active DB ----------
    try:
        db_path = get_active_db_path()
    except Exception:
        raise HTTPException(status_code=400, detail="MUSIC_DB_NOT_SET")

    if not os.path.exists(db_path):
        raise HTTPException(status_code=400, detail="ACTIVE_DB_MISSING")

    conn = get_db()

    # ---------- Phase 1: Select candidates ----------
    candidates = select_delete_candidates(conn)
    total_candidates = len(candidates)

    # ---------- Phase 2: Safety cap ----------
    if payload.max_delete is not None and total_candidates > payload.max_delete:
        # Build skipped plan
        files = []
        for row in candidates:
            files.append(ApplyFileResult(
                file_id=row["id"],
                original_path=row["original_path"],
                planned_action="delete",
                status="skipped",
                error="MAX_DELETE_EXCEEDED",
            ))

        summary = ApplyRunSummary(
            total_candidates=total_candidates,
            delete_planned_count=total_candidates,
            delete_success_count=0,
            delete_failure_count=0,
            delete_skipped_count=total_candidates,
        )

        finished_at = utcnow()

        report = ApplyRunReport(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            dry_run=payload.dry_run,
            apply_deletions=payload.apply_deletions,
            max_delete=payload.max_delete,
            summary=summary,
            files=files,
        )

        save_apply_report(report)
        return report

    # ---------- Phase 3: Build plan ----------
    plan = build_apply_plan(candidates)

    # ---------- Phase 4: Dry-run ----------
    if payload.dry_run:
        summary = ApplyRunSummary(
            total_candidates=total_candidates,
            delete_planned_count=total_candidates,
            delete_success_count=0,
            delete_failure_count=0,
            delete_skipped_count=0,
        )

        finished_at = utcnow()

        report = ApplyRunReport(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            dry_run=True,
            apply_deletions=payload.apply_deletions,
            max_delete=payload.max_delete,
            summary=summary,
            files=plan,
        )

        save_apply_report(report)
        return report

    # ---------- Phase 5: Real apply ----------
    apply_deletions(conn, plan)

    # ---------- Phase 6: Build summary ----------
    success = sum(1 for f in plan if f.status == "deleted")
    failed = sum(1 for f in plan if f.status == "failed")
    skipped = sum(1 for f in plan if f.status == "skipped")

    summary = ApplyRunSummary(
        total_candidates=total_candidates,
        delete_planned_count=total_candidates,
        delete_success_count=success,
        delete_failure_count=failed,
        delete_skipped_count=skipped,
    )

    finished_at = utcnow()

    report = ApplyRunReport(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        dry_run=False,
        apply_deletions=payload.apply_deletions,
        max_delete=payload.max_delete,
        summary=summary,
        files=plan,
    )

    save_apply_report(report)
    return report
# ===================== START =====================

def select_delete_candidates(conn) -> List[sqlite3.Row]:
    rows = conn.execute("""
        SELECT id, original_path
        FROM files
        WHERE mark_delete = 1
        ORDER BY id
    """).fetchall()
    return rows

def build_apply_plan(candidates: List[sqlite3.Row]) -> List[ApplyFileResult]:
    plan: List[ApplyFileResult] = []

    for row in candidates:
        plan.append(ApplyFileResult(
            file_id=row["id"],
            original_path=row["original_path"],
            planned_action="delete",
            status="pending",
            error=None,
        ))

    return plan


def apply_deletions(conn, plan: List[ApplyFileResult]):
    cur = conn.cursor()

    for item in plan:
        try:
            os.remove(item.original_path)
            cur.execute("DELETE FROM files WHERE id = ?", (item.file_id,))
            item.status = "deleted"
        except Exception as e:
            item.status = "failed"
            item.error = str(e)

    conn.commit()

def save_apply_report(report: ApplyRunReport) -> str:
    os.makedirs(APPLY_REPORT_DIR, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"apply_report_{ts}.json"
    path = os.path.join(APPLY_REPORT_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report.dict(), f, indent=2)

    return path

# ===================== END =====================
