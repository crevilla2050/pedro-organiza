#!/usr/bin/env python3
"""
api.py

Pedro Organiza — API v1

Stable backend API for:
- file browsing
- enrichment preview
- alias clusters
- side panel selection logic (tags + genres)

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

class SortKey(BaseModel):
    field: str
    direction: str  # "asc" | "desc"

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


def build_order_by(sort_param: Optional[str]) -> str:
    """
    Build a robust ORDER BY clause from a sort string like:
    artist:asc,album:desc
    """

    if not sort_param:
        return "ORDER BY artist COLLATE NOCASE ASC"

    VALID_FIELDS = {
        "artist",
        "album",
        "title",
        "year",
        "track",
        "disc",
    }

    clauses = []

    for part in sort_param.split(","):
        try:
            field, direction = part.split(":")
        except ValueError:
            continue

        field = field.strip()
        direction = direction.strip().upper()

        if field not in VALID_FIELDS:
            continue

        if direction not in ("ASC", "DESC"):
            direction = "ASC"

        # NULLs last, case-insensitive
        clauses.append(f"{field} IS NULL")
        clauses.append(f"{field} COLLATE NOCASE {direction}")

    if not clauses:
        return "ORDER BY artist COLLATE NOCASE ASC"

    return "ORDER BY " + ", ".join(clauses)


@app.get("/files/search", response_model=List[FileSummary])
def search_files(
    q: Optional[str] = Query(None),
    field: str = Query("artist", regex="^(artist|album|title)$"),

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
    # TEXT SEARCH (q)
    # =========================
    if q and not starts_with:
        q = q.strip()

        column = field

        # Wildcards support (* and ?)
        if "*" in q or "?" in q:
            pattern = (
                q.replace("*", "%")
                 .replace("?", "_")
            )

            where_clauses.append(
                f"{column} IS NOT NULL AND LOWER({column}) LIKE LOWER(?)"
            )
            params.append(pattern)

        else:
            # STRICT equality by default
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
            col, direction = part.split(":")
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
    """
    Fetch a single file by ID.
    Used for row refresh, playback sync, and post-write updates.
    """

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

    # ---------- RANGE REQUEST (CRITICAL FOR BROWSERS) ----------
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

    # ---------- FULL FILE FALLBACK ----------
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

# ====================== AUDIO HEADERS CHECK =====================

@app.head("/audio/{file_id}")
def head_audio(file_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT original_path FROM files WHERE id = ?",
        (file_id,),
    ).fetchone()
    conn.close()

    if not row or not os.path.exists(row["original_path"]):
        raise HTTPException(status_code=404)

    return {}


# ===================== FILE ENRICHMENT =====================

@app.post("/files/{file_id}/enrich", response_model=EnrichmentResult)
def enrich_file(file_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM files WHERE id = ?",
        (file_id,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

    result = pedro_enrich_file(
        source_path=row["original_path"],
        artist_hint=row["artist"],
        title_hint=row["title"],
        album_artist_hint=row["album_artist"],
        is_compilation_hint=row["is_compilation"],
    )

    return EnrichmentResult(
        success=result.get("success", False),
        confidence=result.get("confidence", 0.0),
        source=result.get("source", "unknown"),
        notes=result.get("notes"),
        tags=result.get("tags"),
    )

# ===================== ALIAS CLUSTERS =====================

@app.get("/aliases/clusters", response_model=List[AliasCluster])
def list_alias_clusters(
    min_size: int = Query(2, ge=2),
):
    conn = get_db()
    clusters = clusters_as_records(conn, min_size=min_size)
    conn.close()

    return [
        {
            "cluster_id": idx,
            "size": cluster["size"],
            "confidence": cluster.get("confidence"),
            "signals": cluster.get("signals", {}),
            "canonical_candidate_id": None,
            "resolution_status": "unresolved",
            "user_decision": None,
            "notes": None,
            "cluster_tags": [],
            "files": cluster["files"],
        }
        for idx, cluster in enumerate(clusters, start=1)
    ]

# ===================== SIDE PANEL: TAGS =====================

@app.get("/side-panel/tags")
def side_panel_tags(
    entity_type: str = Query(...),
    entity_ids: str = Query(""),
):
    ids = [int(x) for x in entity_ids.split(",") if x.strip()]
    conn = get_db()
    try:
        return tags_for_selection(
            conn,
            entity_type=entity_type,
            entity_ids=ids,
        )
    finally:
        conn.close()


@app.post("/side-panel/tags/apply")
def side_panel_tags_apply(payload: TagApplyPayload):
    conn = get_db()
    try:
        apply_tags(
            conn,
            entity_type=payload.entity_type,
            entity_ids=payload.entity_ids,
            tag_ids=payload.tag_ids,
        )
    finally:
        conn.close()

    return {"key": "TAGS_APPLIED"}


@app.post("/side-panel/tags/remove")
def side_panel_tags_remove(payload: TagApplyPayload):
    conn = get_db()
    try:
        remove_tags(
            conn,
            entity_type=payload.entity_type,
            entity_ids=payload.entity_ids,
            tag_ids=payload.tag_ids,
        )
    finally:
        conn.close()

    return {"key": "TAGS_REMOVED"}


@app.post("/side-panel/tags/create")
def side_panel_tags_create(payload: TagCreatePayload):
    conn = get_db()
    try:
        tag = create_tag(conn, payload.name, payload.color)
    finally:
        conn.close()

    return {"key": "TAG_CREATED", "tag": tag}

# ===================== SIDE PANEL: GENRES =====================

@app.get("/side-panel/genres")
def side_panel_genres(
    entity_type: str = Query("file"),
    entity_ids: str = Query(""),
):
    ids = [int(x) for x in entity_ids.split(",") if x.strip()]
    conn = get_db()
    try:
        if entity_type != "file":
            raise HTTPException(status_code=400, detail="UNSUPPORTED_ENTITY_FOR_GENRES")

        return genres_for_selection(conn, ids)
    finally:
        conn.close()


@app.post("/side-panel/genres/apply")
def side_panel_genres_apply(payload: GenreApplyPayload):
    conn = get_db()
    try:
        if payload.entity_type != "file":
            raise HTTPException(status_code=400, detail="UNSUPPORTED_ENTITY_FOR_GENRES")

        # Link each file to each genre
        for gid in payload.genre_ids:
            for fid in payload.entity_ids:
                link_file_to_genre(conn, fid, gid, source="tag", confidence=1.0, apply=True)
        conn.commit()
    finally:
        conn.close()

    return {"key": "GENRES_APPLIED"}


@app.post("/side-panel/genres/remove")
def side_panel_genres_remove(payload: GenreApplyPayload):
    conn = get_db()
    try:
        if payload.entity_type != "file":
            raise HTTPException(status_code=400, detail="UNSUPPORTED_ENTITY_FOR_GENRES")

        if not payload.entity_ids or not payload.genre_ids:
            return

        conn.execute(
            f"""
            DELETE FROM file_genres
            WHERE file_id IN ({','.join('?' for _ in payload.entity_ids)})
              AND genre_id IN ({','.join('?' for _ in payload.genre_ids)})
            """,
            (*payload.entity_ids, *payload.genre_ids),
        )
        conn.commit()
    finally:
        conn.close()

    return {"key": "GENRES_REMOVED"}

# ===================== END =====================
