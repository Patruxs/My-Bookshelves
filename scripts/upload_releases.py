#!/usr/bin/env python3
"""
📚 My Bookshelves — GitHub Releases Uploader (Agent 4: DevOps)

Uploads book files (PDF/EPUB) to GitHub Releases to avoid bloating the git repo.
Then updates data.json with the GitHub Releases download URLs.

This is the KEY STRATEGY to store unlimited books on GitHub:
  - Git repo tracks only code + tiny .webp covers (~2MB total)
  - Books (PDF/EPUB) are attached to GitHub Releases (no repo size impact)
  - data.json points download links to Release asset URLs

Requirements:
  - GitHub CLI (`gh`) must be installed and authenticated
  - Install: https://cli.github.com/

Usage:
    python scripts/upload_releases.py                    # Upload all books
    python scripts/upload_releases.py --tag v2025.03     # Custom release tag
    python scripts/upload_releases.py --dry-run           # Preview without uploading
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


# ── Configuration ──
BOOKS_DIR = 'Books'
DATA_JSON = 'site/data.json'
BOOK_EXTENSIONS = {'.pdf', '.epub'}


def get_repo_info():
    """Get GitHub repo owner/name from git remote."""
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True, text=True, check=True
        )
        url = result.stdout.strip()
        # Parse: https://github.com/owner/repo.git or git@github.com:owner/repo.git
        if 'github.com' in url:
            parts = url.rstrip('.git').split('github.com')[-1]
            parts = parts.lstrip(':').lstrip('/')
            owner, repo = parts.split('/')
            return owner, repo
    except Exception:
        pass
    return None, None


def check_gh_cli():
    """Check if GitHub CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ['gh', 'auth', 'status'],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_existing_release(tag):
    """Check if a release with the given tag already exists."""
    result = subprocess.run(
        ['gh', 'release', 'view', tag],
        capture_output=True, text=True
    )
    return result.returncode == 0


def create_release(tag, title):
    """Create a new GitHub Release."""
    result = subprocess.run(
        ['gh', 'release', 'create', tag,
         '--title', title,
         '--notes', f'📚 Book library assets uploaded on {datetime.now().strftime("%Y-%m-%d %H:%M")}',
         '--latest'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ❌ Failed to create release: {result.stderr}")
        return False
    return True


def upload_asset(tag, file_path):
    """Upload a file as a release asset. Overwrites if exists."""
    result = subprocess.run(
        ['gh', 'release', 'upload', tag, str(file_path), '--clobber'],
        capture_output=True, text=True
    )
    return result.returncode == 0


def get_release_asset_url(tag, filename, owner, repo):
    """Construct the download URL for a release asset."""
    # GitHub Releases asset URL format
    safe_name = filename.replace(' ', '.')
    return f"https://github.com/{owner}/{repo}/releases/download/{tag}/{safe_name}"


def scan_books(base_dir):
    """Scan for all book files."""
    books_root = Path(base_dir) / BOOKS_DIR
    if not books_root.exists():
        print(f"❌ Books directory not found: {books_root}")
        return []

    books = []
    for root, dirs, files in os.walk(books_root):
        for filename in sorted(files):
            file_path = Path(root) / filename
            if file_path.suffix.lower() in BOOK_EXTENSIONS:
                rel_path = file_path.relative_to(base_dir).as_posix()
                books.append({
                    'path': str(file_path),
                    'rel_path': rel_path,
                    'filename': filename,
                    'size_mb': file_path.stat().st_size / (1024 * 1024)
                })
    return books


def update_data_json(base_dir, url_map):
    """Update data.json with GitHub Releases download URLs."""
    data_path = Path(base_dir) / DATA_JSON
    if not data_path.exists():
        print(f"❌ data.json not found: {data_path}")
        return 0

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated = 0
    for book in data:
        file_path = book.get('file_path', '')
        if file_path in url_map:
            book['download_url'] = url_map[file_path]
            updated += 1

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return updated


def main():
    parser = argparse.ArgumentParser(description='Upload books to GitHub Releases')
    parser.add_argument('--base-dir', default='.', help='Project root directory')
    parser.add_argument('--tag', default=None, help='Release tag (default: auto-generated)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without uploading')
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    os.chdir(base_dir)

    print("=" * 60)
    print("📚 My Bookshelves — GitHub Releases Uploader")
    print("=" * 60)

    # Check prerequisites
    if not args.dry_run:
        if not check_gh_cli():
            print("\n❌ GitHub CLI (gh) is not installed or not authenticated.")
            print("   Install: https://cli.github.com/")
            print("   Auth:    gh auth login")
            sys.exit(1)
        print("✅ GitHub CLI authenticated")

    owner, repo = get_repo_info()
    if owner and repo:
        print(f"📦 Repository: {owner}/{repo}")
    else:
        print("⚠️  Could not detect GitHub repo info")
        if not args.dry_run:
            sys.exit(1)

    # Generate release tag
    tag = args.tag or f"books-{datetime.now().strftime('%Y%m%d')}"
    print(f"🏷️  Release tag: {tag}")

    # Scan books
    books = scan_books(str(base_dir))
    if not books:
        print("\n⚠️  No books found to upload.")
        return

    total_size = sum(b['size_mb'] for b in books)
    print(f"\n📊 Found {len(books)} books ({total_size:.1f} MB total)")
    print("-" * 60)

    for b in books:
        print(f"  📖 {b['filename']} ({b['size_mb']:.1f} MB)")

    if args.dry_run:
        print(f"\n🔍 DRY RUN — No files uploaded.")
        print(f"   Would create release '{tag}' with {len(books)} assets")
        return

    # Create Release if not exists
    print(f"\n🚀 Creating release '{tag}'...")
    if not get_existing_release(tag):
        if not create_release(tag, f"📚 Library Books ({datetime.now().strftime('%Y-%m-%d')})"):
            sys.exit(1)
        print("  ✅ Release created")
    else:
        print("  ⏭️  Release already exists, will update assets")

    # Upload books
    print(f"\n📤 Uploading {len(books)} files...")
    url_map = {}
    uploaded = 0
    failed = 0

    for b in books:
        print(f"  📤 {b['filename']}...", end=' ', flush=True)
        if upload_asset(tag, b['path']):
            url = get_release_asset_url(tag, b['filename'], owner, repo)
            url_map[b['rel_path']] = url
            uploaded += 1
            print("✅")
        else:
            failed += 1
            print("❌")

    # Update data.json
    if url_map:
        print(f"\n📝 Updating data.json...")
        count = update_data_json(str(base_dir), url_map)
        print(f"  ✅ Updated {count} download URLs")

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Upload Summary:")
    print(f"   ✅ Uploaded: {uploaded}/{len(books)}")
    if failed:
        print(f"   ❌ Failed: {failed}")
    print(f"   💾 Total size: {total_size:.1f} MB")
    print(f"   🏷️  Release: {tag}")
    print(f"   🔗 URL pattern: https://github.com/{owner}/{repo}/releases/download/{tag}/[filename]")
    print("=" * 60)


if __name__ == '__main__':
    main()
