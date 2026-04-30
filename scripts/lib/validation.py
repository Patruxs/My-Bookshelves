"""Library validation and doctor checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .book_paths import expected_display_from_file_path
from .constants import (
    BOOK_EXTENSIONS,
    BOOKS_DIR,
    COVER_SIZE_WARNING_BYTES,
    DATA_JSON,
)
from .covers import dependency_status
from .json_io import load_books

REQUIRED_FIELDS = {
    "id",
    "title",
    "category",
    "topic",
    "file_path",
    "cover",
    "format",
    "description",
}


@dataclass
class ValidationIssue:
    """A validation issue with severity, code, and message."""

    severity: str
    code: str
    message: str
    file: str = DATA_JSON

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "file": self.file,
        }


def validate_library(base_dir: Path, *, include_dependencies: bool = True) -> dict:
    """Validate repo metadata and return a JSON-ready result."""
    base_dir = base_dir.resolve()
    issues: list[ValidationIssue] = []

    data_path = base_dir / DATA_JSON
    if not data_path.exists():
        issues.append(ValidationIssue("error", "missing_data_json", "site/data.json is missing"))
        return _result([], issues, base_dir)

    try:
        books = load_books(base_dir)
    except Exception as exc:
        issues.append(ValidationIssue("error", "invalid_json", f"Cannot read site/data.json: {exc}"))
        return _result([], issues, base_dir)

    if include_dependencies:
        for name, ok in dependency_status().items():
            if not ok:
                issues.append(ValidationIssue("error", "missing_dependency", f"{name} is not available"))

    _validate_entries(base_dir, books, issues)
    return _result(books, issues, base_dir)


def _validate_entries(base_dir: Path, books: list[dict], issues: list[ValidationIssue]) -> None:
    seen_ids: dict[str, int] = {}
    seen_paths: dict[str, int] = {}

    for index, book in enumerate(books):
        location = f"{DATA_JSON} entry {index}"
        missing = sorted(REQUIRED_FIELDS - set(book.keys()))
        if missing:
            issues.append(
                ValidationIssue("error", "missing_fields", f"Missing fields {missing}", location)
            )

        book_id = str(book.get("id", ""))
        if not book_id:
            issues.append(ValidationIssue("error", "empty_id", "Book id is empty", location))
        elif book_id in seen_ids:
            issues.append(
                ValidationIssue("error", "duplicate_id", f"Duplicate id {book_id}", location)
            )
        seen_ids[book_id] = index

        file_path = str(book.get("file_path", ""))
        if not file_path:
            issues.append(ValidationIssue("error", "empty_file_path", "file_path is empty", location))
            continue
        if file_path in seen_paths:
            issues.append(
                ValidationIssue("error", "duplicate_file_path", f"Duplicate file_path {file_path}", location)
            )
        seen_paths[file_path] = index

        _validate_path_metadata(base_dir, book, file_path, location, issues)
        _validate_cover(base_dir, book, location, issues)


def _validate_path_metadata(
    base_dir: Path,
    book: dict,
    file_path: str,
    location: str,
    issues: list[ValidationIssue],
) -> None:
    path = Path(file_path)
    parts = path.parts
    suffix = path.suffix.lower()
    if len(parts) < 4 or parts[0] != BOOKS_DIR:
        issues.append(ValidationIssue("error", "invalid_file_path", f"Invalid book path {file_path}", location))
        return
    if suffix not in BOOK_EXTENSIONS:
        issues.append(ValidationIssue("error", "unsupported_format", f"Unsupported file format {suffix}", location))

    expected_category, expected_topic = expected_display_from_file_path(file_path)
    if expected_category and book.get("category") != expected_category:
        issues.append(
            ValidationIssue(
                "error",
                "category_mismatch",
                f"category should be {expected_category!r} for {file_path}",
                location,
            )
        )
    if expected_topic and book.get("topic") != expected_topic:
        issues.append(
            ValidationIssue(
                "error",
                "topic_mismatch",
                f"topic should be {expected_topic!r} for {file_path}",
                location,
            )
        )

    for field in ("category", "topic"):
        value = str(book.get(field, ""))
        if "_" in value:
            issues.append(
                ValidationIssue("error", "display_name_uses_underscore", f"{field} uses underscores: {value}", location)
            )

    expected_format = suffix.lstrip(".")
    if book.get("format") != expected_format:
        issues.append(
            ValidationIssue("error", "format_mismatch", f"format should be {expected_format!r}", location)
        )

    local_file = base_dir / file_path
    if not local_file.exists() and not book.get("download_url"):
        issues.append(
            ValidationIssue(
                "error",
                "missing_file_and_url",
                f"{file_path} is absent locally and has no download_url",
                location,
            )
        )


def _validate_cover(base_dir: Path, book: dict, location: str, issues: list[ValidationIssue]) -> None:
    cover = str(book.get("cover", ""))
    if not cover:
        issues.append(ValidationIssue("warning", "missing_cover", "cover is empty", location))
        return
    if not cover.startswith("assets/covers/") or not cover.endswith(".webp"):
        issues.append(ValidationIssue("error", "invalid_cover_path", f"Invalid cover path {cover}", location))
        return

    cover_path = base_dir / "site" / cover
    if not cover_path.exists():
        issues.append(ValidationIssue("error", "missing_cover_file", f"Cover file missing: {cover}", location))
        return
    size = cover_path.stat().st_size
    if size > COVER_SIZE_WARNING_BYTES:
        issues.append(
            ValidationIssue("warning", "large_cover", f"Cover exceeds 80KB: {cover} ({size} bytes)", location)
        )


def _result(books: list[dict], issues: Iterable[ValidationIssue], base_dir: Path) -> dict:
    issue_list = list(issues)
    errors = [issue.as_dict() for issue in issue_list if issue.severity == "error"]
    warnings = [issue.as_dict() for issue in issue_list if issue.severity == "warning"]
    missing_urls = sum(1 for book in books if not book.get("download_url"))
    return {
        "ok": not errors,
        "summary": {
            "base_dir": base_dir.as_posix(),
            "books": len(books),
            "errors": len(errors),
            "warnings": len(warnings),
            "missing_download_urls": missing_urls,
        },
        "errors": errors,
        "warnings": warnings,
    }

