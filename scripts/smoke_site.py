"""Smoke checks for the static My Bookshelves site.

This script intentionally uses only the Python standard library so it can run
before JavaScript tooling exists. It validates the contracts most likely to
break during frontend refactors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_BOOK_FIELDS = {
    "id",
    "title",
    "category",
    "topic",
    "file_path",
    "cover",
    "format",
}


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def load_json(path: Path, failures: list[str]) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - smoke output matters here.
        fail(f"{path}: could not parse JSON: {exc}", failures)
        return []

    if not isinstance(payload, list):
        fail(f"{path}: expected a top-level list", failures)
        return []

    books: list[dict[str, object]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            fail(f"{path}: item {index} is not an object", failures)
            continue
        books.append(item)
    return books


def display_name_from_folder(folder_name: str) -> str:
    """Convert a disk folder segment to its data.json display name."""
    return re.sub(r"^\d+_", "", folder_name).replace("_", " ").strip()


def expected_metadata_from_file_path(file_path: str) -> tuple[str, str] | None:
    parts = Path(file_path).parts
    if len(parts) < 4 or parts[0] != "Books":
        return None

    category = display_name_from_folder(parts[1])
    topic = "/".join(display_name_from_folder(part) for part in parts[2:-1])
    return category, topic


def validate_books(
    site_dir: Path,
    books: list[dict[str, object]],
    failures: list[str],
    allow_missing_download_url: bool,
) -> None:
    seen_ids: set[str] = set()
    for index, book in enumerate(books):
        label = str(book.get("title") or f"book #{index}")
        missing = sorted(field for field in REQUIRED_BOOK_FIELDS if not book.get(field))
        if missing:
            fail(f"{label}: missing required fields: {', '.join(missing)}", failures)

        book_id = str(book.get("id") or "")
        if book_id in seen_ids:
            fail(f"{label}: duplicate id {book_id}", failures)
        if book_id:
            seen_ids.add(book_id)

        category = str(book.get("category") or "")
        topic = str(book.get("topic") or "")
        if "_" in category:
            fail(f"{label}: category must use display spaces, got {category!r}", failures)
        if "_" in topic:
            fail(f"{label}: topic must use display spaces, got {topic!r}", failures)

        file_path = str(book.get("file_path") or "")
        expected_metadata = expected_metadata_from_file_path(file_path)
        if expected_metadata is None:
            fail(f"{label}: file_path must be under Books/<Category>/<Topic>/, got {file_path!r}", failures)
        else:
            expected_category, expected_topic = expected_metadata
            if category != expected_category:
                fail(
                    f"{label}: category {category!r} does not match file_path folder {expected_category!r}",
                    failures,
                )
            if topic != expected_topic:
                fail(
                    f"{label}: topic {topic!r} does not match file_path folder {expected_topic!r}",
                    failures,
                )

        cover = str(book.get("cover") or "")
        if cover and not re.fullmatch(r"assets/covers/[-\w.%/]+\.webp", cover, re.IGNORECASE):
            fail(f"{label}: cover must be a local WebP under assets/covers, got {cover!r}", failures)
        elif cover and not (site_dir / cover).exists():
            fail(f"{label}: cover file does not exist: {cover}", failures)

        download_url = str(book.get("download_url") or "")
        if not download_url and not allow_missing_download_url:
            fail(f"{label}: missing download_url", failures)
        elif download_url:
            parsed = urlparse(download_url)
            if parsed.scheme not in {"http", "https"}:
                fail(f"{label}: download_url must be http(s), got {download_url!r}", failures)


def validate_html(site_dir: Path, failures: list[str]) -> None:
    index_path = site_dir / "index.html"
    try:
        html = index_path.read_text(encoding="utf-8")
    except Exception as exc:
        fail(f"{index_path}: could not read HTML: {exc}", failures)
        return

    app_scripts = re.findall(r'<script[^>]+type=["\']module["\'][^>]+src=["\']([^"\']+)["\']', html)
    if not any(src.split("?")[0] == "./app.js" for src in app_scripts):
        fail("site/index.html: expected module script loading ./app.js", failures)

    required_ids = [
        "home-view",
        "detail-view",
        "grid",
        "skeleton",
        "search",
        "pagination",
        "filter-panel",
        "sb-tree",
        "toast",
    ]
    for element_id in required_ids:
        if f'id="{element_id}"' not in html:
            fail(f"site/index.html: missing #{element_id}", failures)


def validate_js_imports(site_dir: Path, failures: list[str]) -> None:
    js_files = [site_dir / "app.js", *sorted((site_dir / "js").glob("**/*.js"))]
    import_pattern = re.compile(r'import\s+(?:[^"\']+\s+from\s+)?["\'](\.{1,2}/[^"\']+)["\']')

    for js_file in js_files:
        if not js_file.exists():
            continue
        text = js_file.read_text(encoding="utf-8")
        for import_path in import_pattern.findall(text):
            target = (js_file.parent / import_path.split("?", 1)[0]).resolve()
            if not target.exists():
                fail(f"{js_file.relative_to(site_dir.parent)}: missing import {import_path}", failures)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke check the static site.")
    parser.add_argument("--base-dir", default=".", help="Repository root")
    parser.add_argument(
        "--allow-missing-download-url",
        action="store_true",
        help="Allow new generated books before the upload step has filled download_url",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    site_dir = base_dir / "site"
    failures: list[str] = []

    books = load_json(site_dir / "data.json", failures)
    validate_books(site_dir, books, failures, args.allow_missing_download_url)
    validate_html(site_dir, failures)
    validate_js_imports(site_dir, failures)

    if failures:
        print("Smoke checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Smoke checks passed: {len(books)} books, static site contracts OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
