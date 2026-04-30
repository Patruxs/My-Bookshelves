"""Book filesystem scanner shared by generation and upload scripts."""

from __future__ import annotations

import os
from pathlib import Path

from .book_paths import is_book_file, metadata_from_book_path
from .constants import BOOKS_DIR, CATEGORY_PATTERN


def scan_book_files(base_dir: Path) -> list[dict]:
    """Scan `Books/` and return canonical metadata for supported book files."""
    books_root = base_dir / BOOKS_DIR
    if not books_root.exists():
        return []

    books: list[dict] = []
    for cat_folder in sorted(books_root.iterdir()):
        if not cat_folder.is_dir() or not CATEGORY_PATTERN.match(cat_folder.name):
            continue

        for root, _dirs, files in os.walk(cat_folder):
            root_path = Path(root)
            for filename in sorted(files, key=_book_sort_key):
                file_path = root_path / filename
                if is_book_file(file_path):
                    books.append(metadata_from_book_path(base_dir, file_path))
    return books


def _book_sort_key(name: str) -> tuple[str, int]:
    path = Path(name)
    ext_priority = {".pdf": 0, ".epub": 1, ".docx": 2}
    return path.stem, ext_priority.get(path.suffix.lower(), 3)

