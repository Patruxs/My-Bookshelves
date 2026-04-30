"""Output helpers for human and machine-readable CLI modes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def to_jsonable(value: Any) -> Any:
    """Convert common script values into JSON-serializable data."""
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    return value


def emit_json(data: Any) -> None:
    """Print a stable JSON payload."""
    print(json.dumps(to_jsonable(data), ensure_ascii=False, indent=2))

