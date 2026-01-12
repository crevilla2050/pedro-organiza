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
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from tools.new_pedro_tagger import pedro_enrich_file
from backend.alias_engine import clusters_as_records

from backend.tag_service import (
    list_tags,
    create_tag,
    tags_for_selection,
    apply_tags,
    remove_tags,
)

from backend.genre_service import (
    genres_for_selection,
    apply_genres,
    remove_genres,
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
    tags: Optional[dict] = None


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
    cluster_tags: List[str] = []

    files: List[AliasClusterFile]


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
        return genres_for_selection(
            conn,
            entity_type=entity_type,
            entity_ids=ids,
        )
    finally:
        conn.close()


@app.post("/side-panel/genres/apply")
def side_panel_genres_apply(payload: GenreApplyPayload):
    conn = get_db()
    try:
        apply_genres(
            conn,
            entity_type=payload.entity_type,
            entity_ids=payload.entity_ids,
            genre_ids=payload.genre_ids,
        )
    finally:
        conn.close()

    return {"key": "GENRES_APPLIED"}


@app.post("/side-panel/genres/remove")
def side_panel_genres_remove(payload: GenreApplyPayload):
    conn = get_db()
    try:
        remove_genres(
            conn,
            entity_type=payload.entity_type,
            entity_ids=payload.entity_ids,
            genre_ids=payload.genre_ids,
        )
    finally:
        conn.close()

    return {"key": "GENRES_REMOVED"}

# ===================== END =====================
