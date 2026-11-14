"""A disk cache of JSON values under `backend/cache/`, keyed by the SHA-256 of the joined key parts."""

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from app.config import BACKEND_DIR

CACHE_DIR = BACKEND_DIR / "cache"
"""The directory holding one JSON file per cached value."""


def get_path(parts: list[str]) -> Path:
    """Returns the cache file path for the given key parts."""
    digest = hashlib.sha256("\x1f".join(parts).encode()).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def get(parts: list[str]) -> Any | None:
    """Returns the cached value for the key parts, or `None` when nothing is cached."""
    try:
        return json.loads(get_path(parts).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def set(parts: list[str], value: Any) -> None:
    """Stores a JSON-serializable value under the key parts, replacing the file atomically."""
    CACHE_DIR.mkdir(exist_ok=True)
    path = get_path(parts)
    temporary_path = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    temporary_path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    temporary_path.replace(path)
