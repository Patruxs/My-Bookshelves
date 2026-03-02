#!/usr/bin/env python3
"""
📚 My Bookshelves — Auto-Organizer Utility

Công cụ hỗ trợ cho Antigravity AI Agent để quét Inbox và di chuyển file.
Script này KHÔNG gọi API bên ngoài — Agent sẽ trực tiếp phân loại sách.

Cách dùng (bởi Agent hoặc user):
    # Liệt kê file trong Inbox
    python auto_organize.py --list

    # Di chuyển 1 file cụ thể (Agent gọi sau khi phân loại)
    python auto_organize.py --move "filename.pdf" --to "1_Computer_Science/Programming_Languages/Java"

    # Hiển thị cấu trúc thư viện
    python auto_organize.py --structure
"""

import os
import sys
import json
import shutil
import re
import argparse
from pathlib import Path
from datetime import datetime


# ── Configuration ──
PROJECT_ROOT = Path(__file__).parent.parent
SKILL_DIR = PROJECT_ROOT / '.agents' / 'skills' / 'auto-organize'
CONFIG_FILE = SKILL_DIR / 'config' / 'settings.json'

DEFAULT_CONFIG = {
    "inbox_dir": "Inbox",
    "book_extensions": [".pdf", ".epub"],
    "log_file": "auto_organize.log",
}

CATEGORY_PATTERN = re.compile(r'^(\d+)_(.+)$')
BOOKS_DIR = 'Books'


def load_config() -> dict:
    """Load configuration from skill config file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CONFIG


def log_action(message: str, base_dir: str, config: dict):
    """Log an action to file and console."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)

    log_file = config.get('log_file', 'auto_organize.log')
    log_path = Path(base_dir) / log_file
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')


# ───────────────────────────────────────────────────────────────────────────
# COMMANDS
# ───────────────────────────────────────────────────────────────────────────

def cmd_list(base_dir: str, config: dict):
    """List all book files in Inbox."""
    base = Path(base_dir).resolve()
    inbox_name = config.get('inbox_dir', 'Inbox')
    inbox = base / inbox_name
    extensions = set(config.get('book_extensions', ['.pdf', '.epub']))

    if not inbox.exists():
        inbox.mkdir(parents=True)
        print(f"📁 Created Inbox folder: {inbox}")
        print("   Drop your PDF/EPUB files here!")
        return

    files = [f for f in inbox.iterdir()
             if f.is_file() and f.suffix.lower() in extensions]

    if not files:
        print("📭 Inbox is empty.")
        return

    print(f"📬 Found {len(files)} book(s) in {inbox_name}/:\n")
    for i, f in enumerate(sorted(files), 1):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {i}. {f.name} ({size_mb:.1f} MB) [{f.suffix.upper()[1:]}]")


def cmd_structure(base_dir: str):
    """Display current library folder structure."""
    base = Path(base_dir).resolve()
    books_root = base / BOOKS_DIR

    print("📚 Library Structure:\n")
    if not books_root.exists():
        print(f"⚠️  Books directory not found: {books_root}")
        return
    for cat_folder in sorted(books_root.iterdir()):
        if not cat_folder.is_dir():
            continue
        match = CATEGORY_PATTERN.match(cat_folder.name)
        if not match:
            continue

        cat_readable = match.group(2).replace('_', ' ')
        # Count books in this category
        book_count = sum(1 for _ in cat_folder.rglob('*')
                        if _.is_file() and _.suffix.lower() in {'.pdf', '.epub'})
        print(f"📂 {cat_folder.name} ({cat_readable}) — {book_count} books")

        for sub in sorted(cat_folder.iterdir()):
            if sub.is_dir():
                sub_count = sum(1 for _ in sub.rglob('*')
                               if _.is_file() and _.suffix.lower() in {'.pdf', '.epub'})
                print(f"   ├── {sub.name} ({sub_count})")

                for subsub in sorted(sub.iterdir()):
                    if subsub.is_dir():
                        subsub_count = sum(1 for _ in subsub.rglob('*')
                                          if _.is_file() and _.suffix.lower() in {'.pdf', '.epub'})
                        print(f"   │   └── {subsub.name} ({subsub_count})")
    print()


def cmd_move(base_dir: str, filename: str, target: str, config: dict):
    """Move a specific file from Inbox to target folder."""
    base = Path(base_dir).resolve()
    inbox_name = config.get('inbox_dir', 'Inbox')
    inbox = base / inbox_name

    source = inbox / filename
    if not source.exists():
        print(f"❌ File not found: {source}")
        sys.exit(1)

    target_dir = base / BOOKS_DIR / target
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / filename

    # Handle name conflicts
    if target_path.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 1
        while target_path.exists():
            target_path = target_dir / f"{stem} ({counter}){suffix}"
            counter += 1

    shutil.move(str(source), str(target_path))
    rel_target = target_path.relative_to(base)

    print(f"✅ Moved: {filename}")
    print(f"   → {rel_target}")
    log_action(f"MOVED: {filename} → {rel_target}", base_dir, config)


def cmd_structure_json(base_dir: str):
    """Output library structure as JSON (for Agent consumption)."""
    base = Path(base_dir).resolve()
    books_root = base / BOOKS_DIR
    structure = {}

    if not books_root.exists():
        return structure
    for cat_folder in sorted(books_root.iterdir()):
        if not cat_folder.is_dir():
            continue
        match = CATEGORY_PATTERN.match(cat_folder.name)
        if not match:
            continue

        topics = []
        for sub in sorted(cat_folder.iterdir()):
            if sub.is_dir():
                subtopics = [ss.name for ss in sorted(sub.iterdir()) if ss.is_dir()]
                topics.append({
                    'name': sub.name,
                    'subtopics': subtopics
                })

        structure[cat_folder.name] = topics

    print(json.dumps(structure, ensure_ascii=False, indent=2))


# ───────────────────────────────────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='📚 Auto-Organizer Utility for My Bookshelves',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  --list               List files in Inbox/
  --structure          Show library folder structure
  --structure-json     Output structure as JSON
  --move FILE --to DIR Move a file from Inbox to target folder

Examples:
  python auto_organize.py --list
  python auto_organize.py --structure
  python auto_organize.py --move "Clean Code.pdf" --to "2_Software_Engineering_Disciplines/Software_Architecture_and_Design"
        """
    )
    parser.add_argument('--base-dir', default='..', help='Base directory of the library (default: parent directory)')
    parser.add_argument('--list', action='store_true', help='List files in Inbox')
    parser.add_argument('--structure', action='store_true', help='Show library structure')
    parser.add_argument('--structure-json', action='store_true', help='Output structure as JSON')
    parser.add_argument('--move', type=str, help='Filename to move from Inbox')
    parser.add_argument('--to', type=str, help='Target folder path (relative to base)')
    args = parser.parse_args()

    config = load_config()

    if args.list:
        cmd_list(args.base_dir, config)
    elif args.structure:
        cmd_structure(args.base_dir)
    elif args.structure_json:
        cmd_structure_json(args.base_dir)
    elif args.move:
        if not args.to:
            print("❌ --to is required when using --move")
            sys.exit(1)
        cmd_move(args.base_dir, args.move, args.to, config)
    else:
        # Default: show list
        cmd_list(args.base_dir, config)


if __name__ == '__main__':
    main()
