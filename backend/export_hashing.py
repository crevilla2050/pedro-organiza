import json
import hashlib


def canonical_json(data) -> bytes:
    """
    Stable JSON serialization for hashing.

    Guarantees:
    - Sorted keys
    - No whitespace noise
    - UTF-8 stable encoding
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()