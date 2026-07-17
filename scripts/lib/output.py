"""Output helpers for human and machine-readable CLI modes."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ProgressCallback = Callable[[str], None]


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


def emit_progress(message: str, *, enabled: bool = True) -> None:
    """Print one progress line to stderr when enabled."""
    if not enabled:
        return
    print(message, file=sys.stderr, flush=True)


def make_progress_printer(*, enabled: bool) -> ProgressCallback | None:
    """Return a progress callback for execute loops, or None when disabled."""
    if not enabled:
        return None
    return lambda message: emit_progress(message, enabled=True)

