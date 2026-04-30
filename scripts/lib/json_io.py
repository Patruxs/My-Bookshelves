"""JSON loading and atomic write helpers."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .constants import DATA_JSON


def load_json(path: Path, default: Any | None = None) -> Any:
    """Load JSON from a path, returning `default` when the file is absent."""
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_books(base_dir: Path) -> list[dict]:
    """Load `site/data.json` from the project root."""
    data = load_json(base_dir / DATA_JSON, default=[])
    if not isinstance(data, list):
        raise ValueError("site/data.json must contain a JSON array")
    return data


def write_json_atomic(path: Path, data: Any, *, backup: bool = True) -> Path | None:
    """Write JSON atomically and optionally keep a timestamped backup."""
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = None

    if backup and path.exists():
        backup_dir = path.parent / ".backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = backup_dir / f"{path.name}.{stamp}.bak"
        shutil.copy2(path, backup_path)

    tmp_path = path.with_name(f".{path.name}.tmp")
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp_path, path)
    return backup_path


def save_books(base_dir: Path, books: list[dict], *, backup: bool = True) -> Path | None:
    """Atomically save `site/data.json`."""
    return write_json_atomic(base_dir / DATA_JSON, books, backup=backup)

