#!/usr/bin/env python3
"""
📚 My Bookshelves — Smart Incremental Sync (Agent 4: DevOps)

Smart Incremental Sync: upload ONLY NEW books to GitHub Releases,
without re-uploading the entire library. Uses data.json as the single source of truth.

Workflow:
  1. Scan Books/ for all PDF/EPUB/DOCX files
  2. Read data.json → filter files that already have download_url (already uploaded)
  3. Diff → list NEW files that need upload
  4. Create WebP covers for new files (if missing)
  5. Upload ONLY new files to the fixed release (storage-v1)
  6. Append metadata to data.json + update download_url
  7. Commit data.json + covers → done

Usage:
    python scripts/upload_releases.py                     # Sync new files
    python scripts/upload_releases.py --tag storage-v1    # Custom tag
    python scripts/upload_releases.py --dry-run            # Preview
    python scripts/upload_releases.py --force              # Re-upload everything

Requirements:
    - GitHub CLI (gh) installed & authenticated
    - PyMuPDF (fitz), Pillow, python-docx
"""

import os
import sys
import json
import hashlib
import subprocess
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from lib.book_paths import format_size as shared_fmt_size
from lib.book_paths import generate_book_id as shared_generate_book_id
from lib.book_paths import sanitize_filename as shared_sanitize_filename
from lib.constants import COVER_QUALITY as SHARED_COVER_QUALITY
from lib.constants import COVER_WIDTH as SHARED_COVER_WIDTH
from lib.covers import extract_cover as extract_shared_cover
from lib.json_io import load_books, save_books
from lib.output import emit_json
from lib.scanner import scan_book_files

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


# ══════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════

BOOKS_DIR = "Books"
DATA_JSON = "site/data.json"
COVER_DIR = "site/assets/covers"
COVER_WEB_PATH = "assets/covers"
BOOK_EXTENSIONS = {".pdf", ".epub", ".docx"}
DEFAULT_TAG = "storage-v1"
COVER_WIDTH = SHARED_COVER_WIDTH
COVER_QUALITY = SHARED_COVER_QUALITY
CATEGORY_PATTERN = re.compile(r"^(\d+)_(.+)$")


# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════

def sanitize_filename(name: str) -> str:
    """Create a safe filename from a book title."""
    return shared_sanitize_filename(name)


def parse_category_name(folder_name: str) -> str:
    """'1_Computer_Science_Fundamentals' → 'Computer Science Fundamentals'"""
    match = CATEGORY_PATTERN.match(folder_name)
    if match:
        return match.group(2).replace("_", " ")
    return folder_name.replace("_", " ")


def parse_topic_name(folder_name: str) -> str:
    """'Data_Structures_and_Algorithms' → 'Data Structures and Algorithms'"""
    return folder_name.replace("_", " ")


def generate_book_id(file_path: str) -> str:
    """Generate unique ID: MD5 hash (12 chars) of file_path."""
    return shared_generate_book_id(file_path)


def fmt_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    return shared_fmt_size(size_bytes)


# ══════════════════════════════════════════════════════════
# COVER EXTRACTION (reuse logic from generate_data.py)
# ══════════════════════════════════════════════════════════

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    from docx import Document as DocxDocument
    HAS_PYTHON_DOCX = True
except ImportError:
    HAS_PYTHON_DOCX = False


def extract_cover(file_path: Path, output_path: Path) -> bool:
    """Extract a WebP cover using the canonical 600px/q85 policy."""
    ok = extract_shared_cover(file_path, output_path)
    if not ok:
        print(f"    ⚠️  Cover unavailable for {file_path.name}")
    return ok


# ══════════════════════════════════════════════════════════
# GITHUB CLI HELPERS
# ══════════════════════════════════════════════════════════

def check_gh_cli() -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_repo_info() -> tuple[Optional[str], Optional[str]]:
    """Get (owner, repo) from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True
        )
        url = result.stdout.strip()
        if "github.com" in url:
            parts = url.rstrip(".git").split("github.com")[-1]
            parts = parts.lstrip(":").lstrip("/")
            owner, repo = parts.split("/")
            return owner, repo
    except Exception:
        pass
    return None, None


def get_existing_assets(tag: str) -> set[str]:
    """Get set of filenames already uploaded to a release."""
    try:
        result = subprocess.run(
            ["gh", "release", "view", tag, "--json", "assets", "-q", ".assets[].name"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return set(result.stdout.strip().splitlines())
    except Exception:
        pass
    return set()


def ensure_release(tag: str) -> bool:
    """Create release if it doesn't exist."""
    check = subprocess.run(
        ["gh", "release", "view", tag],
        capture_output=True, text=True
    )
    if check.returncode == 0:
        return True

    result = subprocess.run(
        ["gh", "release", "create", tag,
         "--title", f"📚 Library Storage ({tag})",
         "--notes", "Persistent storage for book files (PDF/EPUB/DOCX). Managed by upload_releases.py.",
         "--latest"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def upload_asset(tag: str, file_path: str) -> bool:
    """Upload a single file to release. --clobber overwrites if exists."""
    result = subprocess.run(
        ["gh", "release", "upload", tag, file_path, "--clobber"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def get_asset_url(tag: str, filename: str, owner: str, repo: str) -> str:
    """Construct GitHub Releases download URL.

    Filenames MUST be ASCII-safe with underscores only (no spaces, no Unicode).
    Run `rename_books.py --execute` before uploading to ensure this.
    """
    return f"https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}"


# ══════════════════════════════════════════════════════════
# CORE: SMART INCREMENTAL SYNC
# ══════════════════════════════════════════════════════════

def scan_local_books(base_dir: Path) -> list[dict]:
    """Scan Books/ directory, return list of book metadata."""
    books_root = base_dir / BOOKS_DIR
    if not books_root.exists():
        print(f"❌ Books directory not found: {books_root}")
        return []
    return scan_book_files(base_dir)


def load_data_json(base_dir: Path) -> list[dict]:
    """Load existing data.json."""
    try:
        return load_books(base_dir)
    except (json.JSONDecodeError, IOError, ValueError):
        return []


def save_data_json(base_dir: Path, data: list[dict]) -> None:
    """Save data.json (preserve formatting)."""
    save_books(base_dir, data, backup=True)


def compute_diff(local_books: list[dict], existing_data: list[dict], force: bool = False) -> tuple[list[dict], list[dict]]:
    """
    Compare local books vs data.json to find:
      - new_books: files on disk but NOT in data.json
      - need_upload: files in data.json but missing download_url

    Returns: (new_books, need_upload)
    """
    # Index existing entries by file_path
    existing_map = {entry["file_path"]: entry for entry in existing_data}

    new_books = []
    need_upload = []

    for book in local_books:
        rel_path = book["rel_path"]

        if rel_path not in existing_map:
            # Completely new file — not in data.json
            new_books.append(book)
        elif force:
            # Force mode — re-upload everything
            need_upload.append(book)
        elif not existing_map[rel_path].get("download_url"):
            # In data.json but missing download URL
            need_upload.append(book)

    return new_books, need_upload


def create_covers_for_new(base_dir: Path, new_books: list[dict]) -> dict[str, str]:
    """Extract WebP covers for new books. Returns {rel_path: cover_web_path}."""
    covers_dir = base_dir / COVER_DIR
    covers_dir.mkdir(parents=True, exist_ok=True)

    cover_map = {}
    for book in new_books:
        cover_filename = sanitize_filename(book["title"]) + ".webp"
        cover_path = covers_dir / cover_filename
        cover_web = f"{COVER_WEB_PATH}/{cover_filename}"

        if cover_path.exists():
            print(f"    ⏭️  Cover exists: {cover_filename}")
            cover_map[book["rel_path"]] = cover_web
            continue

        print(f"    🖼️  Extracting: {cover_filename}...", end=" ", flush=True)
        if extract_cover(book["abs_path"], cover_path):
            cover_map[book["rel_path"]] = cover_web
            size = cover_path.stat().st_size
            print(f"✅ ({fmt_size(size)})")
        else:
            print("❌ (no cover)")
            cover_map[book["rel_path"]] = ""

    return cover_map


# ══════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="📚 Smart Incremental Sync — Upload only NEW books to GitHub Releases"
    )
    parser.add_argument("--base-dir", default=".", help="Project root directory")
    parser.add_argument("--tag", default=DEFAULT_TAG, help=f"Release tag (default: {DEFAULT_TAG})")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without uploading")
    parser.add_argument("--force", action="store_true", help="Re-upload ALL books (ignore existing)")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON summary")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip hard-reset confirmation prompt")
    parser.add_argument("--hard-reset", action="store_true",
                        help="DELETE existing release entirely, recreate, and re-upload ALL files")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    os.chdir(base_dir)
    tag = args.tag

    # ── Hard Reset Mode ──
    if args.hard_reset:
        print("\n" + "⚠️" * 20)
        print("  HARD RESET MODE: This will DELETE the entire release")
        print("  and re-upload ALL books from scratch.")
        print("⚠️" * 20 + "\n")

        if not args.dry_run:
            if not args.yes:
                response = input("Type yes to continue hard reset: ").strip().lower()
                if response not in ("yes", "y"):
                    print("❌ Cancelled.")
                    return
            if not check_gh_cli():
                print("❌ GitHub CLI (gh) not installed or not authenticated.")
                sys.exit(1)

            # Step 1: Delete existing release
            print(f"🗑️  Deleting release '{tag}'...")
            result = subprocess.run(
                ["gh", "release", "delete", tag, "--yes", "--cleanup-tag"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("   ✅ Release deleted")
            else:
                print(f"   ⚠️  Delete result: {result.stderr.strip() or 'release may not exist'}")

            # Step 2: Clear all download_urls in data.json
            print("📝 Clearing all download_urls in data.json...")
            data = load_data_json(base_dir)
            for entry in data:
                entry["download_url"] = ""
            save_data_json(base_dir, data)
            print(f"   ✅ Cleared {len(data)} entries")

            # Step 3: Recreate release
            print(f"🚀 Recreating release '{tag}'...")
            if ensure_release(tag):
                print("   ✅ Release created")
            else:
                print("   ❌ Failed to create release")
                sys.exit(1)

        # Force-upload everything
        args.force = True

    # ── Header ──
    print("=" * 60)
    print("📚 My Bookshelves — Smart Incremental Sync")
    print("=" * 60)

    # ── Prerequisites ──
    if not args.dry_run:
        if not check_gh_cli():
            print("\n❌ GitHub CLI (gh) not installed or not authenticated.")
            print("   Install: https://cli.github.com/")
            print("   Auth:    gh auth login")
            sys.exit(1)
        print("✅ GitHub CLI authenticated")

    owner, repo = get_repo_info()
    if owner and repo:
        print(f"📦 Repository: {owner}/{repo}")
    else:
        print("⚠️  Could not detect repo info")
        if not args.dry_run:
            sys.exit(1)

    print(f"🏷️  Release tag: {tag}")

    # ── Step 1: Scan local books ──
    print(f"\n{'─' * 60}")
    print("📂 Step 1: Scanning local books...")
    local_books = scan_local_books(base_dir)
    total_size = sum(b["size"] for b in local_books)
    print(f"   Found {len(local_books)} books ({fmt_size(total_size)})")

    if not local_books:
        print("⚠️  No books found. Nothing to do.")
        return

    # ── Step 2: Load data.json ──
    print(f"\n{'─' * 60}")
    print("📋 Step 2: Loading data.json...")
    existing_data = load_data_json(base_dir)
    already_uploaded = sum(1 for e in existing_data if e.get("download_url"))
    print(f"   {len(existing_data)} entries, {already_uploaded} already uploaded")

    # ── Step 3: Compute diff ──
    print(f"\n{'─' * 60}")
    print("🔍 Step 3: Computing diff...")
    new_books, need_upload = compute_diff(local_books, existing_data, force=args.force)

    all_to_upload = new_books + need_upload
    upload_size = sum(b["size"] for b in all_to_upload)

    print(f"   📗 New books (not in data.json): {len(new_books)}")
    print(f"   📙 Missing download_url:         {len(need_upload)}")
    print(f"   📕 Already synced (skip):         {len(local_books) - len(all_to_upload)}")

    if not all_to_upload:
        if args.json:
            emit_json({
                "ok": True,
                "dry_run": args.dry_run,
                "tag": tag,
                "local_books": len(local_books),
                "new_books": 0,
                "need_upload": 0,
                "would_upload": 0,
                "upload_size_bytes": 0,
                "files": [],
            })
        print(f"\n✅ Everything is in sync! Nothing to upload.")
        return

    print(f"\n   📤 Total to upload: {len(all_to_upload)} files ({fmt_size(upload_size)})")
    for b in all_to_upload:
        status = "NEW" if b in new_books else "RE-UPLOAD"
        print(f"      [{status}] {b['filename']} ({fmt_size(b['size'])})")

    if args.dry_run:
        summary = {
            "ok": True,
            "dry_run": True,
            "tag": tag,
            "local_books": len(local_books),
            "new_books": len(new_books),
            "need_upload": len(need_upload),
            "would_upload": len(all_to_upload),
            "upload_size_bytes": upload_size,
            "files": all_to_upload,
        }
        if args.json:
            emit_json(summary)
        print(f"\n{'═' * 60}")
        print(f"🔍 DRY RUN — No files uploaded.")
        print("   No covers or data files were written.")
        print(f"   Would upload {len(all_to_upload)} files ({fmt_size(upload_size)})")
        print(f"   Would add {len(new_books)} new entries to data.json")
        print(f"{'═' * 60}")
        return

    # ── Step 4: Create covers for new books ──
    if new_books:
        print(f"\n{'─' * 60}")
        print(f"🖼️  Step 4: Creating covers for {len(new_books)} new books...")
        cover_map = create_covers_for_new(base_dir, new_books)
    else:
        cover_map = {}

    # ── Step 5: Ensure release exists ──
    print(f"\n{'─' * 60}")
    print(f"🚀 Step 5: Ensuring release '{tag}' exists...")
    if not ensure_release(tag):
        print("❌ Failed to create/verify release")
        sys.exit(1)
    print("   ✅ Release ready")

    # ── Step 6: Upload only new/missing files ──
    print(f"\n{'─' * 60}")
    print(f"📤 Step 6: Uploading {len(all_to_upload)} files...")
    url_map = {}
    uploaded = 0
    failed = 0

    for book in all_to_upload:
        print(f"   📤 {book['filename']} ({fmt_size(book['size'])})...", end=" ", flush=True)
        if upload_asset(tag, str(book["abs_path"])):
            url = get_asset_url(tag, book["filename"], owner, repo)
            url_map[book["rel_path"]] = url
            uploaded += 1
            print("✅")
        else:
            failed += 1
            print("❌")

    # ── Step 7: Update data.json ──
    print(f"\n{'─' * 60}")
    print("📝 Step 7: Updating data.json...")

    # Reload data.json (fresh)
    data = load_data_json(base_dir)
    existing_paths = {entry["file_path"] for entry in data}

    # Append NEW book entries
    new_count = 0
    for book in new_books:
        if book["rel_path"] not in existing_paths:
            entry = {
                "id": generate_book_id(book["rel_path"]),
                "title": book["title"],
                "category": book["category"],
                "topic": book["topic"],
                "file_path": book["rel_path"],
                "cover": cover_map.get(book["rel_path"], ""),
                "format": book["format"],
                "description": "",
                "download_url": url_map.get(book["rel_path"], ""),
            }
            data.append(entry)
            new_count += 1

    # Update download_url for existing entries (re-upload / missing)
    url_updated = 0
    for entry in data:
        fp = entry.get("file_path", "")
        if fp in url_map:
            entry["download_url"] = url_map[fp]
            url_updated += 1

    save_data_json(base_dir, data)
    print(f"   ✅ Appended {new_count} new entries")
    print(f"   ✅ Updated {url_updated} download URLs")

    # ── Summary ──
    print(f"\n{'═' * 60}")
    print("📊 Sync Summary:")
    print(f"   ✅ Uploaded:  {uploaded}/{len(all_to_upload)} files")
    if failed:
        print(f"   ❌ Failed:    {failed}")
    print(f"   📗 New added: {new_count} entries to data.json")
    print(f"   💾 Data sent: {fmt_size(upload_size)}")
    print(f"   ⏭️  Skipped:   {len(local_books) - len(all_to_upload)} (already synced)")
    print(f"   🏷️  Release:   {tag}")
    print(f"\n   Next step: git add site/data.json site/assets/covers/ && git commit && git push")
    print(f"{'═' * 60}")

    if args.json:
        emit_json({
            "ok": failed == 0,
            "dry_run": False,
            "tag": tag,
            "uploaded": uploaded,
            "failed": failed,
            "new_entries": new_count,
            "download_urls_updated": url_updated,
            "skipped": len(local_books) - len(all_to_upload),
        })

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
