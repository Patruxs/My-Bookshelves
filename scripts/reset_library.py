#!/usr/bin/env python3
"""
📚 My Bookshelves — Reset Library Utility

This script is used during the initial setup to clear out the original author's
sample data (metadata, covers, and logs) so the user can start with a fresh library.

Usage:
    python scripts/reset_library.py [--force]
"""

import argparse
import json
import shutil
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_JSON = BASE_DIR / "site" / "data.json"
COVERS_DIR = BASE_DIR / "site" / "assets" / "covers"
LOG_FILE = BASE_DIR / "library_structure.log"
BOOKS_DIR = BASE_DIR / "Books"
INBOX_DIR = BASE_DIR / "Inbox"

def reset_library():
    print("🧹 Cleaning up sample data for a fresh start...")

    # 1. Reset data.json
    if DATA_JSON.exists():
        with open(DATA_JSON, "w", encoding="utf-8") as f:
            json.dump([], f)
        print("   ✅ Reset site/data.json to empty")

    # 2. Clear covers
    if COVERS_DIR.exists():
        count = 0
        for item in COVERS_DIR.iterdir():
            if item.is_file() and item.suffix.lower() in [".webp", ".jpg", ".png"]:
                item.unlink()
                count += 1
        print(f"   ✅ Removed {count} cover image(s)")

    # 3. Delete log file
    if LOG_FILE.exists():
        LOG_FILE.unlink()
        print("   ✅ Removed library_structure.log")

    # 4. Ensure Books and Inbox exist but don't delete them completely 
    # (just in case the user has already put something in them)
    if not BOOKS_DIR.exists():
        BOOKS_DIR.mkdir()
    if not INBOX_DIR.exists():
        INBOX_DIR.mkdir()

    print("\n✨ Library has been successfully reset. You are ready to add your own books!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset the library data.")
    parser.add_argument("--force", action="store_true", help="Force reset without confirmation")
    args = parser.parse_args()
    
    # In setup we usually force, but if run manually, we might want confirmation
    if not args.force:
        confirm = input("⚠️  This will delete all current book metadata and covers. Are you sure? (y/n): ")
        if confirm.lower() not in ('y', 'yes'):
            print("Operation cancelled.")
            exit(0)

    reset_library()
