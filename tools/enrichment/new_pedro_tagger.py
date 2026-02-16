"""
new_pedro_tagger.py

Pedro tag enrichment engine.

Responsibilities:
- Suggest metadata (artist / album / title / album_artist / compilation)
- Never overwrite existing confirmed data
- Provide confidence + source attribution
- Fallback to SOURCE PATH inference when all else fails
- Suggest album art (never embed, never mutate filesystem)

This module provides a conservative, advisory-only tagging assistant
called "Pedro". It reads embedded metadata, accepts optional context
hints, and falls back to safe heuristics based on source paths. Any
suggestions include a confidence score and a `source` field so callers
can decide whether to apply the suggestion.

Usage (example):
    from tools import new_pedro_tagger
    suggestion = new_pedro_tagger.pedro_enrich_file('/path/to/track.mp3')

Important: functions in this module do not modify audio files.
They return dictionaries describing suggested tags and album-art
metadata; another part of the system is responsible for applying
changes after user confirmation.
"""

import os
import re
import unicodedata
import hashlib
import mimetypes
from typing import Optional, Dict, List

from mutagen import File as MutagenFile

# -------------------------------
# Constants
# -------------------------------

# Keywords commonly used in album-art filenames. Used to detect
# high-confidence 'sibling' cover images placed alongside audio files.
# The list is intentionally small and conservative to reduce false
# positives when scanning arbitrary directories.
COVER_KEYWORDS = [
    "cover",
    "folder",
    "front",
    "albumart",
    "album_art",
    "albumartSmall",
    "artwork",    
]

# Supported image file extensions for sibling image detection. These
# are common formats used for album art; the set is restrictive so
# the code ignores unrelated files (e.g., text or archive files).
SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


# -------------------------------
# Utilities
# -------------------------------

def normalize(s: Optional[str]) -> str:
    """
    Normalize text for comparison and display.

    Why: Tag data can come from many sources with different unicode
    normalization forms and combining characters (accents). Normalizing
    makes downstream comparisons and storage deterministic without
    changing the semantic content of the tags.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip()


def clean_token(s: str) -> str:
    """
    Lightweight token cleaner used to produce readable artist/album
    segments from filenames or path components.

    Why: Filesystem names often use underscores, repeated whitespace,
    or other separators. This helper standardizes those tokens so
    inferred tags look sensible to users and downstream logic.
    """
    s = normalize(s)
    s = re.sub(r'[_]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def filename_to_title(filename: str) -> str:
    """
    Derive a reasonable track title from a filename.

    Why: Many filenames begin with track numbers or use separators
    that are not part of the human-readable title. This function
    strips common numeric prefixes and cleans the remainder so the
    inferred `title` is useful when embedded tags are missing.
    """
    name = os.path.splitext(os.path.basename(filename))[0]
    name = re.sub(r'^\d+\s*[-._]\s*', '', name)
    return clean_token(name)


def sha256_bytes(data: bytes) -> str:
    """
    Return a SHA-256 hex digest for a bytes object.

    Why: We use a compact content hash to identify identical images
    or to create stable IDs for images suggested as album art. Hashes
    are stored instead of raw bytes to keep diagnostic storage small.
    """
    return hashlib.sha256(data).hexdigest()




# -------------------------------
# Embedded metadata extraction
# -------------------------------

def extract_existing_tags(path: str) -> Dict[str, Optional[str]]:
    """
    Read embedded tags from an audio file using Mutagen.

    Why: Embedded metadata is the highest-confidence source for tags.
    This function returns a small set of commonly used fields plus a
    boolean `is_compilation` when the file's raw tags indicate a
    compilation. The code keeps a defensive try/except because files
    can be malformed or unsupported; in that case we return an empty
    dict and allow lower-confidence inference to proceed.
    """
    try:
        # `easy=True` yields the human-friendly keys (e.g. 'artist',
        # 'album') with lists of values. `easy=False` returns the raw
        # backend object which can contain format-specific flags used
        # to detect compilations on MP4/iTunes files.
        audio_easy = MutagenFile(path, easy=True)
        audio_raw = MutagenFile(path, easy=False)

        if not audio_easy:
            # Mutagen couldn't parse the file or it is unsupported.
            return {}

        album_artist = audio_easy.get("albumartist", [None])[0]
        is_compilation = False

        # Detect compilation flags across different container/tag types.
        if audio_raw and hasattr(audio_raw, "tags"):
            for key in audio_raw.tags.keys():
                if str(key).lower() in ("tcmp", "compilation", "cpil"):
                    is_compilation = True
                    break

        # Return a compact mapping of the common fields we care about.
        return {
            "artist": audio_easy.get("artist", [None])[0],
            "album": audio_easy.get("album", [None])[0],
            "title": audio_easy.get("title", [None])[0],
            "album_artist": album_artist,
            "is_compilation": is_compilation,
        }

    except Exception:
        # Be defensive: if tag parsing fails, downstream heuristics will
        # still attempt to propose reasonable suggestions.
        return {}


# -------------------------------
# SOURCE PATH inference
# -------------------------------

def infer_tags_from_source_path(path: str) -> Dict[str, str]:
    """
    Conservative heuristic:
        Artist / Album / Track.ext
    """
    parts: List[str] = []
    p = os.path.normpath(path)

    while True:
        p, tail = os.path.split(p)
        if tail:
            parts.append(tail)
        else:
            break

    parts = list(reversed(parts))
    inferred = {}

    # We interpret path segments conservatively: when the tree depth
    # suggests `.../Artist/Album/Track`, we use those parts. This avoids
    # aggressive guessing when files are stored in arbitrary nested
    # folders.
    if len(parts) >= 3:
        inferred["artist"] = clean_token(parts[-3])
        inferred["album"] = clean_token(parts[-2])
        inferred["title"] = filename_to_title(parts[-1])

    elif len(parts) == 2:
        inferred["album"] = clean_token(parts[-2])
        inferred["title"] = filename_to_title(parts[-1])

    elif len(parts) == 1:
        inferred["title"] = filename_to_title(parts[-1])

    return {k: v for k, v in inferred.items() if v}


# -------------------------------
# Album art helpers
# -------------------------------

def _find_sibling_cover(source_paths: List[str]):
    """
    Look for sibling cover images near source audio files.
    Highest confidence signal.
    """
    checked_dirs = set()

    for path in source_paths:
        directory = os.path.dirname(path)
        if directory in checked_dirs:
            continue

        checked_dirs.add(directory)

        try:
            for fname in os.listdir(directory):
                fname_l = fname.lower()
                ext = os.path.splitext(fname_l)[1]

                # Only consider files with supported image extensions and
                # conservative filename matches (e.g. 'cover.jpg',
                # 'folder.png'). This helps avoid false positives like
                # artwork thumbnails or unrelated images.
                if ext not in SUPPORTED_IMAGE_EXTS:
                    continue

                if not any(k in fname_l for k in COVER_KEYWORDS):
                    continue

                img_path = os.path.join(directory, fname)
                with open(img_path, "rb") as f:
                    data = f.read()

                # Guess mime type for downstream consumers; default to a
                # generic binary mime if detection fails.
                mime, _ = mimetypes.guess_type(img_path)
                mime = mime or "application/octet-stream"

                # Return on first reasonable match: sibling images are a
                # very strong signal and we prefer the first located file
                # to keep behavior deterministic.
                return {
                    "image_bytes": data,
                    "image_hash": sha256_bytes(data),
                    "mime": mime,
                    "source": "sibling",
                    "confidence": 0.98,
                    "notes": {
                        "key": "ALBUM_ART_SIBLING_FOUND",
                        "params": {"filename": fname}
                    },
                }

        except Exception:
            continue

    return None


# -------------------------------
# Pedro: album art suggestion
# -------------------------------

def pedro_suggest_album_art(
    album_artist: Optional[str],
    album: Optional[str],
    is_compilation: bool,
    source_paths: List[str],
) -> Dict:
    """
    Suggest album art.
    Advisory only. No embedding. No mutation.
    """

    # 1️⃣ sibling image (highest confidence)
    sibling = _find_sibling_cover(source_paths)
    if sibling:
        return {
            "success": True,
            "status": "found",
            **sibling,
        }

    # 2️⃣ network sources (hooks only for now)
    # Placeholder branch: network fetches / online lookups are intentionally
    # unimplemented in this module — callers may extend or replace this
    # behaviour with a richer provider if desired.
    if album and (album_artist or is_compilation):
        return {
            "success": False,
            "status": "missing",
            "source": "network_placeholder",
            "confidence": 0.0,
            "image_bytes": None,
            "image_hash": None,
            "mime": None,
            "notes": {
                "key": "ALBUM_ART_NETWORK_NOT_IMPLEMENTED"
            },
        }

    # 3️⃣ nothing found
    return {
        "success": False,
        "status": "missing",
        "source": "none",
        "confidence": 0.0,
        "image_bytes": None,
        "image_hash": None,
        "mime": None,
        "notes": {
            "key": "ALBUM_ART_NOT_FOUND"
        },
    }


# -------------------------------
# Pedro: file enrichment
# -------------------------------

def pedro_enrich_file(
    source_path: str,
    artist_hint: Optional[str] = None,
    title_hint: Optional[str] = None,
    album_artist_hint: Optional[str] = None,
    is_compilation_hint: Optional[bool] = None,
) -> Dict:
    """
    Suggest tags for a single file.
    """

    # Priority 1: embedded tags (highest confidence). If useful fields
    # exist in the file metadata, return them immediately so callers can
    # surface them to users without performing further inference.
    existing = extract_existing_tags(source_path)
    tags = {}

    if existing:
        for k in ("artist", "album", "title", "album_artist"):
            if existing.get(k):
                tags[k] = normalize(existing[k])

        if existing.get("is_compilation"):
            tags["is_compilation"] = True

        if tags:
            return {
                "success": True,
                "tags": tags,
                "confidence": 0.95,
                "source": "file_metadata",
                "notes": {
                    "key": "TAGGER_EXISTING_METADATA"
                },
            }

    # Priority 2: explicit context hints provided by the caller. These are
    # treated as medium-confidence signals because they usually originate
    # from user input or UI state.
    if any(v is not None for v in (artist_hint, title_hint, album_artist_hint, is_compilation_hint)):
        if artist_hint:
            tags["artist"] = normalize(artist_hint)
        if title_hint:
            tags["title"] = normalize(title_hint)
        if album_artist_hint:
            tags["album_artist"] = normalize(album_artist_hint)
        if is_compilation_hint is not None:
            tags["is_compilation"] = bool(is_compilation_hint)

        return {
            "success": True,
            "tags": tags,
            "confidence": 0.60,
            "source": "context_hints",
            "notes": {
                "key": "TAGGER_CONTEXT_HINTS"
            },
        }

    # Priority 3: conservative source-path inference when no higher
    # confidence data is available.
    inferred = infer_tags_from_source_path(source_path)
    if inferred:
        return {
            "success": True,
            "tags": inferred,
            "confidence": 0.45,
            "source": "source_path_inference",
            "notes": {
                "key": "TAGGER_SOURCE_PATH_INFERENCE"
            },
        }

    return {
        "success": False,
        "tags": {},
        "confidence": 0.0,
        "source": "none",
        "notes": {
            "key": "TAGGER_NO_METADATA"
        },

    }


# -------------------------------
# Pedro: cluster enrichment
# -------------------------------

def pedro_enrich_cluster(
    album_artist: Optional[str],
    album: Optional[str],
    is_compilation: bool,
    source_paths: List[str],
) -> Dict:
    """
    Album-level enrichment (currently album art only).
    """

    art = pedro_suggest_album_art(
        album_artist=album_artist,
        album=album,
        is_compilation=bool(is_compilation),
        source_paths=source_paths,
    )

    return {
        "success": art.get("success", False),
        "album_artist": album_artist,
        "album": album,
        "is_compilation": is_compilation,
        "art": art,
    }
