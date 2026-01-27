# backend/export_schema.py

from pydantic import BaseModel
from typing import List, Optional, Literal, Any
from datetime import datetime

class ExportFilter(BaseModel):
    field: str
    op: Literal["=", "!=", "in", "not_in", ">", ">=", "<", "<=", "like"]
    value: Any


class ExportQuery(BaseModel):
    filters: List[ExportFilter] = []

    exclude_marked_delete: bool = True
    only_resolved_aliases: bool = True
    exclude_compilations: bool = False


class ExportSource(BaseModel):
    db_path: str
    selection_mode: Literal["query"] = "query"
    query: ExportQuery


class LayoutPart(BaseModel):
    type: Literal["field", "sep"]
    value: str


class ExportLayout(BaseModel):
    directory_layout: List[str]
    filename_layout: List[LayoutPart]

    separate_compilations: bool = True
    sanitize: bool = True
    max_filename_length: int = 120


class ExportTarget(BaseModel):
    root: str
    allow_override: bool = True
    create_missing_dirs: bool = True


class ExportOptions(BaseModel):
    incremental: bool = True
    delete_orphans: bool = False

    conflict_policy: Literal["skip", "overwrite", "rename"] = "skip"
    on_error: Literal["continue", "stop"] = "continue"

    preserve_timestamps: bool = True
    follow_symlinks: bool = False

    log_level: Literal["quiet", "normal", "verbose"] = "normal"


class PostProcessing(BaseModel):
    rewrite_tags: bool = False
    normalize_unicode: bool = True
    strip_comments: bool = False


class ExportPreset(BaseModel):
    preset_version: int = 1

    id: str
    name: str
    description: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    source: ExportSource
    layout: ExportLayout
    target: ExportTarget
    export_options: ExportOptions
    post_processing: PostProcessing
