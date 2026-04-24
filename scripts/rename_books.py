#!/usr/bin/env python3
"""
📚 My Bookshelves — Book File Renamer

Normalizes ALL book filenames to ASCII-safe, underscore-separated format.
Removes Vietnamese diacritics and replaces special characters.

Algorithm (Slugify):
  1. Remove Vietnamese diacritics (đ→d, ă→a, ứ→u, etc.)
  2. Replace spaces, dots, hyphens, plus, brackets → underscore
  3. Remove remaining non-alphanumeric chars (except underscore)
  4. Collapse consecutive underscores → single underscore
  5. Trim leading/trailing underscores

Examples:
  'Kiến trúc ứng dụng web.epub'     → 'Kien_truc_ung_dung_web.epub'
  'Ch05a_Mo.hinh.hoa.quy.trinh.pdf' → 'Ch05a_Mo_hinh_hoa_quy_trinh.pdf'
  'Go With Domain.pdf'              → 'Go_With_Domain.pdf'
  'Head First Java 2nd Edition.pdf' → 'Head_First_Java_2nd_Edition.pdf'

Usage:
    python scripts/rename_books.py --base-dir .              # Dry-run (preview)
    python scripts/rename_books.py --base-dir . --execute     # Actually rename
"""

import os
import re
import sys
import json
import argparse
import unicodedata
from pathlib import Path

# Fix Windows console encoding for Vietnamese/Unicode output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


# ══════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════

BOOK_EXTENSIONS = {".pdf", ".epub", ".docx"}
DATA_JSON = "site/data.json"
SCAN_DIRS = ["Books", "Inbox"]


# ══════════════════════════════════════════════════════════
# CORE: FILENAME NORMALIZATION
# ══════════════════════════════════════════════════════════

def remove_diacritics(text: str) -> str:
    """Remove Vietnamese diacritics using Unicode NFD decomposition.

    Handles đ/Đ specially since they don't decompose via NFD.
    All other Vietnamese chars (ă, â, ê, ô, ơ, ư + tone marks)
    are decomposed into base letter + combining marks, then marks are stripped.

    Args:
        text: Input string with possible Vietnamese diacritics.

    Returns:
        String with all diacritics removed.
    """
    # đ/Đ are special: NFD doesn't decompose them
    text = text.replace('đ', 'd').replace('Đ', 'D')
    # NFD decomposition splits accented chars into base + combining marks
    nfkd = unicodedata.normalize('NFD', text)
    # Strip all combining marks (category 'Mn' = Mark, Nonspacing)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


def slugify_filename(filename: str) -> str:
    """Convert a filename to ASCII-safe, underscore-separated format.

    Args:
        filename: Original filename (e.g. "Kiến trúc ứng dụng web.epub").

    Returns:
        Normalized filename (e.g. "Kien_truc_ung_dung_web.epub").
    """
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower()

    # Step 1: Remove Vietnamese diacritics
    stem = remove_diacritics(stem)

    # Step 2: Replace special characters with underscore
    # Covers: spaces, dots, hyphens, plus, brackets, and other punctuation
    stem = re.sub(r'[\s.\-+\(\)\[\],;:!?@#$%^&*={}|\\/<>\'"~`]', '_', stem)

    # Step 3: Remove any remaining non-alphanumeric chars (except underscore)
    stem = re.sub(r'[^a-zA-Z0-9_]', '_', stem)

    # Step 4: Collapse multiple consecutive underscores
    stem = re.sub(r'_+', '_', stem)

    # Step 5: Trim leading/trailing underscores
    stem = stem.strip('_')

    if not stem:
        return filename  # Safety: don't create empty filenames

    return f"{stem}{ext}"


# ══════════════════════════════════════════════════════════
# SCAN & PLAN
# ══════════════════════════════════════════════════════════

def scan_and_plan(base_dir: Path) -> list[dict]:
    """Scan directories and create a rename plan.

    Only includes files that NEED renaming (old name != new name).

    Args:
        base_dir: Project root directory.

    Returns:
        List of dicts with old_path, new_path, old_name, new_name, old_rel, new_rel.
    """
    plan = []

    for scan_dir_name in SCAN_DIRS:
        scan_dir = base_dir / scan_dir_name
        if not scan_dir.exists():
            continue

        for root, dirs, files in os.walk(scan_dir):
            root_path = Path(root)
            for filename in sorted(files):
                file_path = root_path / filename
                if file_path.suffix.lower() not in BOOK_EXTENSIONS:
                    continue

                new_name = slugify_filename(filename)

                if new_name != filename:
                    new_path = root_path / new_name
                    plan.append({
                        "old_path": file_path,
                        "new_path": new_path,
                        "old_name": filename,
                        "new_name": new_name,
                        "old_rel": file_path.relative_to(base_dir).as_posix(),
                        "new_rel": new_path.relative_to(base_dir).as_posix(),
                    })

    return plan


# ══════════════════════════════════════════════════════════
# DATA.JSON UPDATE
# ══════════════════════════════════════════════════════════

def update_data_json(base_dir: Path, renamed_items: list[dict]) -> int:
    """Update file_path in data.json for successfully renamed files.

    Also clears download_url since old URLs are now invalid
    (files will be re-uploaded with new names via --hard-reset).

    Args:
        base_dir: Project root directory.
        renamed_items: List of successfully renamed items.

    Returns:
        Number of entries updated.
    """
    data_path = base_dir / DATA_JSON
    if not data_path.exists():
        print("   ⚠️  data.json not found, skipping update")
        return 0

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build mapping: old_rel → new_rel
    path_map = {item["old_rel"]: item["new_rel"] for item in renamed_items}

    updated = 0
    for entry in data:
        old_fp = entry.get("file_path", "")
        if old_fp in path_map:
            entry["file_path"] = path_map[old_fp]
            # Clear download_url — will be re-set after upload_releases.py --hard-reset
            entry["download_url"] = ""
            updated += 1

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return updated


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="📚 Normalize book filenames to ASCII-safe, underscore-separated format"
    )
    parser.add_argument("--base-dir", default=".", help="Project root directory")
    parser.add_argument("--execute", action="store_true",
                        help="Actually rename files (default: dry-run preview)")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()

    print("=" * 60)
    print("📚 My Bookshelves — Book File Renamer")
    print("=" * 60)
    print(f"📂 Base directory: {base_dir}")
    print(f"🔧 Mode: {'🚀 EXECUTE' if args.execute else '👀 DRY-RUN (preview only)'}\n")

    # ── Scan and plan ──
    plan = scan_and_plan(base_dir)

    if not plan:
        print("✅ All filenames are already normalized! Nothing to rename.")
        return

    # ── Show plan ──
    print(f"📋 Found {len(plan)} files to rename:\n")
    for i, item in enumerate(plan, 1):
        print(f"  {i:2d}. ❌ {item['old_name']}")
        print(f"      ✅ {item['new_name']}")
        print()

    if not args.execute:
        print("─" * 60)
        print("ℹ️  DRY-RUN mode. No files were renamed.")
        print("   To execute, add --execute flag:")
        print(f"   python scripts/rename_books.py --base-dir . --execute")
        return

    # ── Execute renames ──
    print("─" * 60)
    print("🚀 Executing renames...\n")

    renamed_items = []
    errors = 0

    for item in plan:
        try:
            # Check for filename conflicts
            if item["new_path"].exists():
                print(f"  ⚠️  SKIP (target exists): {item['old_name']}")
                errors += 1
                continue

            item["old_path"].rename(item["new_path"])
            print(f"  ✅ {item['old_name']} → {item['new_name']}")
            renamed_items.append(item)
        except Exception as e:
            print(f"  ❌ {item['old_name']}: {e}")
            errors += 1

    # ── Update data.json ──
    print(f"\n{'─' * 60}")
    print("📝 Updating data.json...")
    updated = update_data_json(base_dir, renamed_items)
    print(f"   ✅ Updated {updated} entries (file_path + cleared download_url)")

    # ── Summary ──
    print(f"\n{'═' * 60}")
    print(f"📊 Summary:")
    print(f"   ✅ Renamed:  {len(renamed_items)} files")
    if errors:
        print(f"   ⚠️  Skipped:  {errors}")
    print(f"   📝 Updated:  {updated} data.json entries")
    print(f"\n   📌 Next steps (migration):")
    print(f"   1. python scripts/generate_data.py --base-dir .      # Regenerate covers + data")
    print(f"   2. python scripts/upload_releases.py --hard-reset     # Delete old release, re-upload all")
    print(f"   3. git add -A && git commit && git push               # Deploy")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    main()
