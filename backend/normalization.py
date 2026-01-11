import re
import unicodedata
from typing import Optional

# ============================================================
# Normalization v0 — core rules
# ============================================================
NORMALIZATION_VERSION = "v0"

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

# Minimal transliteration map (v0 only)
TRANSLITERATION_MAP = {
    "ð": "d",
    "Ð": "d",
}

RE_PUNCTUATION = re.compile(r"[\"'.,:;!?()\[\]{}]")
RE_SEPARATORS = re.compile(r"[-_/]")
RE_WHITESPACE = re.compile(r"\s+")
RE_DIGITS_ONLY = re.compile(r"^\d+$")


def normalize_text(value: Optional[str]) -> str:
    """
    Base normalization function (v0).

    Conservative, deterministic, lossy-but-predictable.
    Produces ASCII, lowercase, whitespace-normalized output.
    """

    if not value:
        return ""

    # ---- Unicode normalization ----
    text = unicodedata.normalize("NFKD", value)

    # Remove combining marks
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Apply minimal transliteration
    for src, dst in TRANSLITERATION_MAP.items():
        text = text.replace(src, dst)

    # Drop remaining non-ASCII
    text = text.encode("ascii", "ignore").decode("ascii")

    # ---- Lowercase ----
    text = text.lower()

    # ---- Punctuation & separators ----
    text = RE_PUNCTUATION.sub(" ", text)
    text = RE_SEPARATORS.sub(" ", text)

    # ---- Whitespace ----
    text = RE_WHITESPACE.sub(" ", text).strip()
    if not text:
        return ""

    tokens = text.split(" ")

    has_numeric_token = any(RE_DIGITS_ONLY.match(t) for t in tokens)

    # ---- Token filtering ----
    words = []
    for token in tokens:
        if RE_DIGITS_ONLY.match(token):
            continue
        if has_numeric_token and token in NOISE_TOKENS:
            continue
        words.append(token)

    return " ".join(words)


# ============================================================
# Field-specific wrappers (v0)
# ============================================================

def normalize_artist(value: Optional[str]) -> str:
    return normalize_text(value)


def normalize_album_artist(value: Optional[str]) -> str:
    return normalize_text(value)


def normalize_album(value: Optional[str]) -> str:
    return normalize_text(value)


def normalize_title(value: Optional[str]) -> str:
    return normalize_text(value)


def normalize_genre_token(value: Optional[str]) -> str:
    return normalize_text(value)
