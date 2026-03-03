#!/usr/bin/env python3
"""
📚 My Bookshelves — Smart Incremental Sync (Agent 4: DevOps)

Cơ chế Đồng bộ hóa Thông minh: CHỈ upload sách MỚI lên GitHub Releases,
không re-upload toàn bộ thư viện. Dùng data.json làm Single Source of Truth.

Workflow:
  1. Quét Books/ tìm tất cả PDF/EPUB
  2. Đọc data.json → lọc ra file đã có download_url (đã uploaded)
  3. Diff → danh sách file MỚI cần upload
  4. Tạo cover WebP cho file mới (nếu chưa có)
  5. Upload CHỈ file mới lên Release cố định (storage-v1)
  6. Append metadata vào data.json + cập nhật download_url
  7. Commit data.json + covers → done

Usage:
    python scripts/upload_releases.py                     # Sync mới
    python scripts/upload_releases.py --tag storage-v1    # Custom tag
    python scripts/upload_releases.py --dry-run            # Xem trước
    python scripts/upload_releases.py --force              # Re-upload tất cả

Requirements:
    - GitHub CLI (gh) installed & authenticated
    - PyMuPDF (fitz), Pillow, ebooklib (optional, for cover extraction)
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


# ══════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════

BOOKS_DIR = "Books"
DATA_JSON = "site/data.json"
COVER_DIR = "site/assets/covers"
COVER_WEB_PATH = "assets/covers"
BOOK_EXTENSIONS = {".pdf", ".epub"}
DEFAULT_TAG = "storage-v1"
COVER_WIDTH = 250
COVER_QUALITY = 60
CATEGORY_PATTERN = re.compile(r"^(\d+)_(.+)$")


# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════

def sanitize_filename(name: str) -> str:
    """Create a safe filename from a book title."""
    name = re.sub(r"[^\w\s\-.]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:100]


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
    return hashlib.md5(file_path.encode("utf-8")).hexdigest()[:12]


def fmt_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    mb = size_bytes / (1024 * 1024)
    if mb >= 1:
        return f"{mb:.1f} MB"
    return f"{size_bytes / 1024:.0f} KB"


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
    import ebooklib
    from ebooklib import epub
    HAS_EBOOKLIB = True
except ImportError:
    HAS_EBOOKLIB = False


def extract_cover(file_path: Path, output_path: Path) -> bool:
    """Extract cover from PDF/EPUB → WebP (250px, q60)."""
    ext = file_path.suffix.lower()

    if ext == ".pdf" and HAS_PYMUPDF:
        try:
            doc = fitz.open(str(file_path))
            if doc.page_count == 0:
                doc.close()
                return False
            page = doc[0]
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom then downscale
            pix = page.get_pixmap(matrix=mat, alpha=False)
            if HAS_PILLOW:
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                if img.width > COVER_WIDTH:
                    ratio = COVER_WIDTH / img.width
                    img = img.resize((COVER_WIDTH, int(img.height * ratio)), Image.LANCZOS)
                img.save(str(output_path), "WEBP", quality=COVER_QUALITY, method=6)
            else:
                pix.save(str(output_path))
            doc.close()
            return True
        except Exception as e:
            print(f"    ⚠️  Cover error: {e}")
            return False

    elif ext == ".epub" and HAS_EBOOKLIB:
        try:
            book = epub.read_epub(str(file_path), options={"ignore_ncx": True})
            cover_data = None
            # Method 1: cover metadata
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_COVER:
                    cover_data = item.get_content()
                    break
            # Method 2: image with 'cover' in name
            if not cover_data:
                for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                    if "cover" in item.get_name().lower():
                        cover_data = item.get_content()
                        break
            # Method 3: first image
            if not cover_data:
                for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                    cover_data = item.get_content()
                    break

            if cover_data and HAS_PILLOW:
                from io import BytesIO
                img = Image.open(BytesIO(cover_data))
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                if img.width > COVER_WIDTH:
                    ratio = COVER_WIDTH / img.width
                    img = img.resize((COVER_WIDTH, int(img.height * ratio)), Image.LANCZOS)
                img.save(str(output_path), "WEBP", quality=COVER_QUALITY, method=6)
                return True
        except Exception as e:
            print(f"    ⚠️  Cover error: {e}")
            return False

    return False


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
         "--notes", "Persistent storage for book files (PDF/EPUB). Managed by upload_releases.py.",
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
    """Get actual download URL from GitHub API after upload.
    
    GitHub may rename/sanitize filenames (strip Unicode, etc.),
    so we query the API to get the real browser_download_url.
    Falls back to constructed URL if API query fails.
    """
    try:
        result = subprocess.run(
            ["gh", "release", "view", tag, "--json", "assets",
             "-q", f'.assets[] | select(.name | test("{re.escape(Path(filename).stem[:10])}")) | .browserDownloadUrl'],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            # May return multiple lines if partial match; find best match
            urls = result.stdout.strip().splitlines()
            ext = Path(filename).suffix.lower()
            for url in urls:
                if url.lower().endswith(ext):
                    return url
            return urls[0]  # fallback to first match
    except Exception:
        pass
    # Fallback: construct URL (may not work for Unicode filenames)
    safe_name = filename.replace(" ", ".")
    return f"https://github.com/{owner}/{repo}/releases/download/{tag}/{safe_name}"


# ══════════════════════════════════════════════════════════
# CORE: SMART INCREMENTAL SYNC
# ══════════════════════════════════════════════════════════

def scan_local_books(base_dir: Path) -> list[dict]:
    """Scan Books/ directory, return list of book metadata."""
    books_root = base_dir / BOOKS_DIR
    if not books_root.exists():
        print(f"❌ Books directory not found: {books_root}")
        return []

    books = []
    for cat_folder in sorted(books_root.iterdir()):
        if not cat_folder.is_dir() or not CATEGORY_PATTERN.match(cat_folder.name):
            continue

        category_name = parse_category_name(cat_folder.name)

        for root, dirs, files in os.walk(cat_folder):
            root_path = Path(root)
            rel_to_cat = root_path.relative_to(cat_folder)
            parts = rel_to_cat.parts
            topic_name = parse_topic_name(parts[0]) if parts else category_name

            for filename in sorted(files):
                file_path = root_path / filename
                if file_path.suffix.lower() not in BOOK_EXTENSIONS:
                    continue

                rel_path = file_path.relative_to(base_dir).as_posix()
                books.append({
                    "abs_path": file_path,
                    "rel_path": rel_path,
                    "filename": filename,
                    "title": file_path.stem,
                    "category": category_name,
                    "topic": topic_name,
                    "format": file_path.suffix.lower()[1:],
                    "size": file_path.stat().st_size,
                })
    return books


def load_data_json(base_dir: Path) -> list[dict]:
    """Load existing data.json."""
    data_path = base_dir / DATA_JSON
    if not data_path.exists():
        return []
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_data_json(base_dir: Path, data: list[dict]) -> None:
    """Save data.json (preserve formatting)."""
    data_path = base_dir / DATA_JSON
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    os.chdir(base_dir)
    tag = args.tag

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
        print(f"\n✅ Everything is in sync! Nothing to upload.")
        return

    print(f"\n   📤 Total to upload: {len(all_to_upload)} files ({fmt_size(upload_size)})")
    for b in all_to_upload:
        status = "NEW" if b in new_books else "RE-UPLOAD"
        print(f"      [{status}] {b['filename']} ({fmt_size(b['size'])})")

    # ── Step 4: Create covers for new books ──
    if new_books:
        print(f"\n{'─' * 60}")
        print(f"🖼️  Step 4: Creating covers for {len(new_books)} new books...")
        cover_map = create_covers_for_new(base_dir, new_books)
    else:
        cover_map = {}

    if args.dry_run:
        print(f"\n{'═' * 60}")
        print(f"🔍 DRY RUN — No files uploaded.")
        print(f"   Would upload {len(all_to_upload)} files ({fmt_size(upload_size)})")
        print(f"   Would add {len(new_books)} new entries to data.json")
        print(f"{'═' * 60}")
        return

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


if __name__ == "__main__":
    main()
