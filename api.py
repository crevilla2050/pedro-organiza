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

# ===================== ENV =====================

load_dotenv()

DB_PATH = os.getenv("MUSIC_DB")
if not DB_PATH:
    raise RuntimeError("MUSIC_DB_NOT_SET")

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


def get_db():
    conn = sqlite3.connect(DB_PATH)
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


# ---------- Alias Clusters ----------

class AliasClusterFile(BaseModel):
    id: int
    artist: Optional[str]
    album: Optional[str]
    title: Optional[str]
    original_path: Optional[str]


class AliasCluster(BaseModel):
    cluster_id: int
    size: int
    confidence: Optional[float]
    signals: Dict[str, int]

    canonical_candidate_id: Optional[int] = None
    resolution_status: str = "unresolved"
    user_decision: Optional[Any] = None
    notes: Optional[str] = None
    cluster_tags: List[str] = Field(default_factory=list)

    files: List[AliasClusterFile] = Field(default_factory=list)


# ---------- Side Panel Payloads ----------

class SelectionPayload(BaseModel):
    entity_type: str
    entity_ids: List[int]


class TagApplyPayload(SelectionPayload):
    tag_ids: List[int]


class GenreApplyPayload(SelectionPayload):
    genre_ids: List[int]


class TagCreatePayload(BaseModel):
    name: str
    color: Optional[str] = None


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
def list_files():
    """
    List ALL files (no pagination by design).
    """
    conn = get_db()
    rows = conn.execute("""
        SELECT
            id,
            original_path,
            artist,
            album_artist,
            album,
            title
        FROM files
        ORDER BY id
    """).fetchall()
    conn.close()

    return [FileSummary(**dict(r)) for r in rows]


@app.get("/files/search", response_model=List[FileSummary])
def search_files(
    q: Optional[str] = Query(None),
    field: str = Query("artist", pattern="^(artist|album|title)$"),
    starts_with: Optional[str] = Query(None),
    sort: Optional[str] = Query(
        None,
        description="Comma separated sort fields, e.g. artist:asc,album:asc,title:asc"
    ),
    max_results: Optional[int] = Query(None, ge=1),
):
    conn = get_db()

    where_clauses = []
    params = []

    # =========================
    # TEXT SEARCH
    # =========================
    if q and not starts_with:
        q = q.strip()
        column = field

        if "*" in q or "?" in q:
            pattern = q.replace("*", "%").replace("?", "_")
            where_clauses.append(
                f"{column} IS NOT NULL AND LOWER({column}) LIKE LOWER(?)"
            )
            params.append(pattern)
        else:
            where_clauses.append(
                f"{column} IS NOT NULL AND LOWER({column}) = LOWER(?)"
            )
            params.append(q)

    # =========================
    # ALPHABET FILTER
    # =========================
    if starts_with:
        if starts_with == "#":
            where_clauses.append(
                f"{field} IS NOT NULL AND {field} GLOB '[^A-Za-z]*'"
            )
        else:
            where_clauses.append(
                f"{field} IS NOT NULL AND LOWER({field}) LIKE LOWER(?)"
            )
            params.append(f"{starts_with}%")

    where_sql = (
        "WHERE " + " AND ".join(where_clauses)
        if where_clauses else ""
    )

    # =========================
    # SORTING
    # =========================
    order_sql = ""
    if sort:
        order_parts = []
        for part in sort.split(","):
            try:
                col, direction = part.split(":")
            except ValueError:
                continue

            if col not in ("artist", "album", "title"):
                continue

            dir_sql = "DESC" if direction.lower() == "desc" else "ASC"
            order_parts.append(f"{col} COLLATE NOCASE {dir_sql}")

        if order_parts:
            order_sql = "ORDER BY " + ", ".join(order_parts)

    # =========================
    # LIMIT
    # =========================
    limit_sql = ""
    if max_results:
        limit_sql = "LIMIT ?"
        params.append(max_results)

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
        {order_sql}
        {limit_sql}
    """

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [FileSummary(**dict(r)) for r in rows]


# ===================== SINGLE FILE =====================

@app.get("/files/{file_id}", response_model=FileSummary)
def get_file(file_id: int):
    conn = get_db()
    row = conn.execute(
        """
        SELECT
            id,
            original_path,
            artist,
            album_artist,
            album,
            title
        FROM files
        WHERE id = ?
        """,
        (file_id,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

    return FileSummary(**dict(row))


@app.patch("/files/bulk")
def bulk_update_files(payload: BulkUpdatePayload):
    if not payload.ids:
        return {"status": "noop", "updated_fields": []}

    updates = {
        k: v for k, v in payload.fields.items()
        if k in EDITABLE_FIELDS and v is not None
    }

    if not updates:
        return {"status": "noop", "updated_fields": []}

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    id_placeholders = ",".join("?" for _ in payload.ids)

    params = list(updates.values()) + payload.ids

    conn = get_db()
    conn.execute(
        f"""
        UPDATE files
        SET {set_clause}
        WHERE id IN ({id_placeholders})
        """,
        params,
    )
    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "updated_fields": list(updates.keys()),
        "updated_ids": payload.ids,
    }


@app.patch("/files/{file_id}")
def update_file(file_id: int, payload: FileUpdatePayload):
    updates = payload.dict(exclude_unset=True)

    if not updates:
        return {"status": "noop", "updated_fields": []}

    invalid = [k for k in updates if k not in EDITABLE_FIELDS]
    if invalid:
        raise HTTPException(status_code=400, detail="INVALID_FIELDS")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    params = list(updates.values()) + [file_id]

    conn = get_db()
    conn.execute(f"UPDATE files SET {set_clause} WHERE id = ?", params)
    conn.commit()

    row = conn.execute(
        """
        SELECT
            id,
            original_path,
            artist,
            album_artist,
            album,
            title
        FROM files
        WHERE id = ?
        """,
        (file_id,),
    ).fetchone()
    conn.close()

    return {
        "status": "ok",
        "updated_fields": list(updates.keys()),
        "file": dict(row) if row else None,
    }


# ===================== AUDIO STREAMING =====================

@app.get("/audio/{file_id}")
def stream_audio(file_id: int, request: Request):
    conn = get_db()
    row = conn.execute(
        "SELECT original_path FROM files WHERE id = ?",
        (file_id,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

    path = row["original_path"]

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="FILE_MISSING")

    file_size = os.path.getsize(path)
    range_header = request.headers.get("range")

    content_type, _ = mimetypes.guess_type(path)
    content_type = content_type or "audio/mpeg"

    def open_file(start=0, end=None):
        with open(path, "rb") as f:
            f.seek(start)
            remaining = (end - start + 1) if end else file_size - start
            while remaining > 0:
                chunk = f.read(min(8192, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    if range_header:
        units, range_spec = range_header.split("=")
        start_str, end_str = range_spec.split("-")

        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Type": content_type,
        }

        return StreamingResponse(
            open_file(start, end),
            status_code=206,
            headers=headers,
            media_type=content_type,
        )

    headers = {
        "Content-Length": str(file_size),
        "Accept-Ranges": "bytes",
        "Content-Type": content_type,
    }

    return StreamingResponse(
        open_file(),
        headers=headers,
        media_type=content_type,
    )


# ===================== END =====================
