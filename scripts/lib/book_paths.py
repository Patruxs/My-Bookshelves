"""Path and metadata helpers for book files."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .constants import BOOK_EXTENSIONS, BOOKS_DIR, CATEGORY_PATTERN


def sanitize_filename(name: str) -> str:
    """Create the canonical cover filename stem for a book title."""
    safe = re.sub(r"[^\w\s\-.]", "", name)
    safe = re.sub(r"\s+", "_", safe.strip())
    return safe[:100]


def parse_category_name(folder_name: str) -> str:
    """Convert `1_Computer_Science` to `Computer Science`."""
    match = CATEGORY_PATTERN.match(folder_name)
    if match:
        return match.group(2).replace("_", " ")
    return folder_name.replace("_", " ")


def parse_topic_name(folder_name: str) -> str:
    """Convert `Data_Structures` to `Data Structures`."""
    return folder_name.replace("_", " ")


def display_to_folder_name(display_name: str) -> str:
    """Convert a display name to the folder-style name."""
    return display_name.replace(" ", "_")


def display_topic_from_parts(parts: tuple[str, ...]) -> str:
    """Convert topic/subtopic folder parts to a display topic."""
    return "/".join(parse_topic_name(part) for part in parts)


def generate_book_id(file_path: str) -> str:
    """Generate a stable 12-character ID from a relative book path."""
    return hashlib.md5(file_path.encode("utf-8")).hexdigest()[:12]


def is_book_file(path: Path) -> bool:
    """Return True when a path is a supported book file."""
    return path.is_file() and path.suffix.lower() in BOOK_EXTENSIONS


def metadata_from_book_path(base_dir: Path, file_path: Path) -> dict[str, object]:
    """Build canonical metadata from a physical book file path."""
    rel_path = file_path.relative_to(base_dir).as_posix()
    parts = Path(rel_path).parts
    if len(parts) < 4 or parts[0] != BOOKS_DIR:
        raise ValueError(f"Unsupported book path: {rel_path}")

    category = parse_category_name(parts[1])
    topic_parts = tuple(parts[2:-1])
    topic = display_topic_from_parts(topic_parts) if topic_parts else category

    return {
        "abs_path": file_path,
        "rel_path": rel_path,
        "filename": file_path.name,
        "title": file_path.stem,
        "category": category,
        "topic": topic,
        "format": file_path.suffix.lower()[1:],
        "size": file_path.stat().st_size,
    }


def expected_display_from_file_path(file_path: str) -> tuple[str | None, str | None]:
    """Return expected `(category, topic)` display values from `file_path`."""
    parts = Path(file_path).parts
    if len(parts) < 4 or parts[0] != BOOKS_DIR:
        return None, None

    category = parse_category_name(parts[1])
    topic_parts = tuple(parts[2:-1])
    topic = display_topic_from_parts(topic_parts) if topic_parts else category
    return category, topic


def format_size(size_bytes: int) -> str:
    """Format bytes for human-readable output."""
    mb = size_bytes / (1024 * 1024)
    if mb >= 1:
        return f"{mb:.1f} MB"
    return f"{size_bytes / 1024:.0f} KB"

