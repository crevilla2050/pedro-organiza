import re
import unicodedata
from typing import Optional

NOISE_TOKENS = {
    "remaster",
    "remastered",
    "mono",
    "stereo",
    "version",
    "edit",
    "mix",
    "deluxe",
    "expanded",
    "anniversary",
    "edition",
}

# Minimal transliteration map (v0)
TRANSLITERATION_MAP = {
    "ð": "d",
    "Ð": "d",
}

RE_PUNCTUATION = re.compile(r"[\"'.,:;!?()\[\]{}]")
RE_SEPARATORS = re.compile(r"[-_/]")
RE_WHITESPACE = re.compile(r"\s+")
RE_DIGITS_ONLY = re.compile(r"^\d+$")


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""

    # ---- Stage 1: Unicode normalization ----
    text = unicodedata.normalize("NFKD", value)

    # Remove combining marks
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Apply minimal transliteration
    for src, dst in TRANSLITERATION_MAP.items():
        text = text.replace(src, dst)

    # Remove remaining non-ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")

    # ---- Stage 2: lowercase ----
    text = text.lower()

    # ---- Stage 3: punctuation & separators ----
    text = RE_PUNCTUATION.sub(" ", text)
    text = RE_SEPARATORS.sub(" ", text)

    # ---- Stage 4: whitespace normalization ----
    text = RE_WHITESPACE.sub(" ", text).strip()
    if not text:
        return ""

    tokens = text.split(" ")

    # Detect presence of numeric qualifiers (years, editions)
    has_numeric_token = any(RE_DIGITS_ONLY.match(t) for t in tokens)

    # ---- Stage 5: token filtering ----
    words = []
    for token in tokens:
        # Drop pure numbers
        if RE_DIGITS_ONLY.match(token):
            continue

        # Drop noise tokens only if numeric context exists
        if has_numeric_token and token in NOISE_TOKENS:
            continue

        words.append(token)

    # ---- Final canonical spacing ----
    normalized = " ".join(words)
    normalized = RE_WHITESPACE.sub(" ", normalized).strip()

    return normalized

# ============================================================
# Field-specific normalization wrappers (v0)
# ============================================================

def normalize_artist(value: Optional[str]) -> str:
    """
    Normalize artist names for comparison and grouping.

    v0 behavior:
    - Delegates directly to normalize_text()
    - No aliasing
    - No reordering ("Beatles, The")
    - No article stripping ("the")

    Future versions may add artist-specific rules.
    """
    return normalize_text(value)


def normalize_album_artist(value: Optional[str]) -> str:
    """
    Normalize album artist names.

    v0 behavior:
    - Same as artist normalization
    - Kept separate for semantic clarity
    """
    return normalize_text(value)


def normalize_album(value: Optional[str]) -> str:
    """
    Normalize album titles.

    v0 behavior:
    - Same base normalization as titles
    - Conservative by design
    """
    return normalize_text(value)


def normalize_title(value: Optional[str]) -> str:
    """
    Normalize track titles.

    v0 behavior:
    - Same base normalization as albums
    - Featured artists and subtitles preserved
    """
    return normalize_text(value)


def normalize_genre_token(value: Optional[str]) -> str:
    """
    Normalize a single genre token.

    v0 behavior:
    - Uses base normalization
    - Token-level normalization only
    """
    return normalize_text(value)

