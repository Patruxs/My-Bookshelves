#!/usr/bin/env python3
"""
📚 My Bookshelves — Book Deleter

Delete books, topics, or entire categories from the library.
Removes entries from data.json, deletes cover images, and optionally
removes physical book files and empty directories.

Usage:
    # Delete a single book by title or ID
    python scripts/delete_books.py --book "Leetcode_Pattern_Recognition_Guide"
    python scripts/delete_books.py --book-id "932e4b18bff6"

    # Delete all books in a topic (requires --category to disambiguate)
    python scripts/delete_books.py --topic "Data Structures and Algorithms" --category "Computer Science Fundamentals"

    # Delete all books in a category
    python scripts/delete_books.py --category "Personal Development and Skills"

    # Preview mode (default — no changes made)
    python scripts/delete_books.py --book "..." --dry-run

    # Execute deletion (requires explicit flag)
    python scripts/delete_books.py --book "..." --execute

    # Skip confirmation prompt
    python scripts/delete_books.py --book "..." --execute --yes

    # Also delete physical book files from Books/ directory
    python scripts/delete_books.py --book "..." --execute --delete-files

    # List all categories and topics
    python scripts/delete_books.py --list
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding for Vietnamese/Unicode output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


# ══════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════

DATA_JSON = "site/data.json"
COVERS_DIR = "site/assets/covers"
BOOKS_DIR = "Books"


# ══════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════

def load_data(base_dir: Path) -> list[dict]:
    """Load books from data.json.

    Args:
        base_dir: Project root directory.

    Returns:
        List of book entries.
    """
    data_path = base_dir / DATA_JSON
    if not data_path.exists():
        print(f"❌ data.json not found at: {data_path}")
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(base_dir: Path, books: list[dict]) -> None:
    """Save books to data.json.

    Args:
        base_dir: Project root directory.
        books: List of book entries to save.
    """
    data_path = base_dir / DATA_JSON
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════
# LISTING
# ══════════════════════════════════════════════════════════

def list_library(base_dir: Path) -> None:
    """Print all categories, topics, and book counts.

    Args:
        base_dir: Project root directory.
    """
    books = load_data(base_dir)

    # Build tree
    tree: dict[str, dict[str, list[str]]] = {}
    for b in books:
        cat = b.get("category", "Unknown")
        topic = b.get("topic", "Unknown")
        title = b.get("title", "Unknown")
        if cat not in tree:
            tree[cat] = {}
        if topic not in tree[cat]:
            tree[cat][topic] = []
        tree[cat][topic].append(title)

    print(f"\n📚 Library Overview ({len(books)} books total)\n")
    print("=" * 60)

    for cat in sorted(tree.keys()):
        cat_count = sum(len(titles) for titles in tree[cat].values())
        print(f"\n📂 {cat} ({cat_count} books)")

        for topic in sorted(tree[cat].keys()):
            titles = tree[cat][topic]
            print(f"   📌 {topic} ({len(titles)} books)")
            for title in sorted(titles):
                display_title = title.replace("_", " ")
                print(f"      • {display_title}")

    print(f"\n{'=' * 60}")


# ══════════════════════════════════════════════════════════
# BOOK SELECTION
# ══════════════════════════════════════════════════════════

def find_books_by_title(books: list[dict], title_query: str) -> list[dict]:
    """Find books matching a title query (case-insensitive, partial match).

    Args:
        books: All book entries.
        title_query: Title to search for.

    Returns:
        List of matching books.
    """
    query = title_query.lower().replace(" ", "_")
    return [b for b in books if query in b.get("title", "").lower()]


def find_books_by_id(books: list[dict], book_id: str) -> list[dict]:
    """Find books matching a specific ID.

    Args:
        books: All book entries.
        book_id: Book ID to match.

    Returns:
        List of matching books (should be 0 or 1).
    """
    return [b for b in books if b.get("id", "") == book_id]


def find_books_by_topic(books: list[dict], topic: str, category: str) -> list[dict]:
    """Find all books in a specific topic within a category.

    Args:
        books: All book entries.
        topic: Topic name.
        category: Category name.

    Returns:
        List of matching books.
    """
    return [
        b for b in books
        if b.get("topic", "").lower() == topic.lower()
        and b.get("category", "").lower() == category.lower()
    ]


def find_books_by_category(books: list[dict], category: str) -> list[dict]:
    """Find all books in a specific category.

    Args:
        books: All book entries.
        category: Category name.

    Returns:
        List of matching books.
    """
    return [
        b for b in books
        if b.get("category", "").lower() == category.lower()
    ]


# ══════════════════════════════════════════════════════════
# DELETION LOGIC
# ══════════════════════════════════════════════════════════

def display_books_to_delete(books_to_delete: list[dict]) -> None:
    """Display the list of books that will be deleted.

    Args:
        books_to_delete: Books selected for deletion.
    """
    print(f"\n🗑️  Books to be deleted ({len(books_to_delete)}):\n")

    # Group by category/topic for readability
    grouped: dict[str, dict[str, list[dict]]] = {}
    for b in books_to_delete:
        cat = b.get("category", "Unknown")
        topic = b.get("topic", "Unknown")
        if cat not in grouped:
            grouped[cat] = {}
        if topic not in grouped[cat]:
            grouped[cat][topic] = []
        grouped[cat][topic].append(b)

    for cat in sorted(grouped.keys()):
        print(f"  📂 {cat}")
        for topic in sorted(grouped[cat].keys()):
            print(f"     📌 {topic}")
            for b in grouped[cat][topic]:
                title = b.get("title", "Unknown").replace("_", " ")
                fmt = b.get("format", "?")
                book_id = b.get("id", "?")
                print(f"        🗑️  {title} [{fmt}] (id: {book_id})")
        print()


def delete_cover_images(base_dir: Path, books_to_delete: list[dict],
                        dry_run: bool = True) -> int:
    """Delete cover image files for the specified books.

    Args:
        base_dir: Project root directory.
        books_to_delete: Books whose covers should be deleted.
        dry_run: If True, only preview — don't actually delete.

    Returns:
        Number of cover files deleted (or would be deleted).
    """
    covers_dir = base_dir / COVERS_DIR
    deleted = 0

    # Collect unique cover paths
    cover_paths: set[str] = set()
    for b in books_to_delete:
        cover = b.get("cover", "")
        if cover:
            cover_paths.add(cover)

    for cover_rel in sorted(cover_paths):
        # cover_rel is like "assets/covers/Title.webp"
        cover_path = base_dir / "site" / cover_rel
        if cover_path.exists():
            if dry_run:
                print(f"  🖼️  Would delete cover: {cover_path.name}")
            else:
                cover_path.unlink()
                print(f"  🖼️  Deleted cover: {cover_path.name}")
            deleted += 1

    return deleted


def delete_book_files(base_dir: Path, books_to_delete: list[dict],
                      dry_run: bool = True) -> int:
    """Delete physical book files (PDF/EPUB/DOCX) from Books/ directory.

    Args:
        base_dir: Project root directory.
        books_to_delete: Books whose files should be deleted.
        dry_run: If True, only preview — don't actually delete.

    Returns:
        Number of book files deleted (or would be deleted).
    """
    deleted = 0

    for b in books_to_delete:
        file_path = base_dir / b.get("file_path", "")
        if file_path.exists():
            if dry_run:
                print(f"  📄 Would delete file: {file_path.relative_to(base_dir)}")
            else:
                file_path.unlink()
                print(f"  📄 Deleted file: {file_path.relative_to(base_dir)}")
            deleted += 1
        else:
            # File doesn't exist locally (might be on Releases only)
            pass

    return deleted


def cleanup_empty_dirs(base_dir: Path, dry_run: bool = True) -> int:
    """Remove empty directories in the Books/ folder (bottom-up).

    Args:
        base_dir: Project root directory.
        dry_run: If True, only preview — don't actually delete.

    Returns:
        Number of directories removed (or would be removed).
    """
    books_root = base_dir / BOOKS_DIR
    if not books_root.exists():
        return 0

    removed = 0
    # Walk bottom-up to find empty dirs
    for dirpath in sorted(books_root.rglob("*"), reverse=True):
        if dirpath.is_dir() and not any(dirpath.iterdir()):
            if dry_run:
                print(f"  📁 Would remove empty dir: {dirpath.relative_to(base_dir)}")
            else:
                dirpath.rmdir()
                print(f"  📁 Removed empty dir: {dirpath.relative_to(base_dir)}")
            removed += 1

    return removed


def update_structure_log(base_dir: Path) -> None:
    """Regenerate library_structure.log by calling generate_structure_log.py.

    Args:
        base_dir: Project root directory.
    """
    script = base_dir / "scripts" / "generate_structure_log.py"
    if not script.exists():
        print("  ⚠️  generate_structure_log.py not found, skipping log update")
        return

    try:
        subprocess.run(
            [sys.executable, str(script), "--base-dir", str(base_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        print("  ✅ Updated library_structure.log")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Failed to update library_structure.log: {e}")


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="📚 My Bookshelves — Delete books, topics, or categories"
    )

    # Selection modes (mutually exclusive-ish)
    parser.add_argument(
        "--book", default=None,
        help="Delete book(s) matching this title (partial match, case-insensitive)"
    )
    parser.add_argument(
        "--book-id", default=None,
        help="Delete a book by its exact ID"
    )
    parser.add_argument(
        "--topic", default=None,
        help="Delete ALL books in this topic (requires --category)"
    )
    parser.add_argument(
        "--category", default=None,
        help="Delete ALL books in this category (or scope --topic to a category)"
    )

    # Execution control
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually perform deletion (default: dry-run preview)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview only — no changes made (this is the default)"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--delete-files", action="store_true",
        help="Also delete physical book files from Books/ directory"
    )

    # Utility
    parser.add_argument(
        "--list", action="store_true",
        help="List all categories, topics, and books"
    )
    parser.add_argument(
        "--base-dir", default=".",
        help="Project root directory (default: current directory)"
    )

    args = parser.parse_args()
    base_dir = Path(args.base_dir).resolve()

    # Determine if dry-run (default unless --execute is specified)
    is_dry_run = not args.execute

    print("=" * 60)
    print("📚 My Bookshelves — Book Deleter")
    print("=" * 60)
    print(f"📂 Base directory: {base_dir}")

    # ── List mode ──
    if args.list:
        list_library(base_dir)
        return

    # ── Validate arguments ──
    if not args.book and not args.book_id and not args.topic and not args.category:
        print("\n❌ No selection specified. Use --book, --book-id, --topic, or --category.")
        print("   Use --list to see all available books.\n")
        parser.print_help()
        sys.exit(1)

    if args.topic and not args.category:
        print("\n❌ --topic requires --category to disambiguate topics with the same name.")
        print("   Use --list to see all categories and topics.\n")
        sys.exit(1)

    print(f"🔧 Mode: {'🚀 EXECUTE' if not is_dry_run else '👀 DRY-RUN (preview only)'}")
    if args.delete_files:
        print("📄 Physical files: WILL BE DELETED")
    else:
        print("📄 Physical files: kept (only data.json + covers affected)")

    # ── Load data ──
    books = load_data(base_dir)
    print(f"\n📖 Loaded {len(books)} books from data.json")

    # ── Find books to delete ──
    books_to_delete: list[dict] = []

    if args.book_id:
        books_to_delete = find_books_by_id(books, args.book_id)
        if not books_to_delete:
            print(f"\n❌ No book found with ID: {args.book_id}")
            sys.exit(1)
        print(f"🔍 Found {len(books_to_delete)} book(s) with ID: {args.book_id}")

    elif args.book:
        books_to_delete = find_books_by_title(books, args.book)
        if not books_to_delete:
            print(f"\n❌ No book found matching title: \"{args.book}\"")
            print("   Use --list to see all available books.")
            sys.exit(1)
        print(f"🔍 Found {len(books_to_delete)} book(s) matching: \"{args.book}\"")

    elif args.topic and args.category:
        books_to_delete = find_books_by_topic(books, args.topic, args.category)
        if not books_to_delete:
            print(f"\n❌ No books found in topic \"{args.topic}\" of category \"{args.category}\"")
            print("   Use --list to see all categories and topics.")
            sys.exit(1)
        print(f"🔍 Found {len(books_to_delete)} book(s) in topic \"{args.topic}\"")

    elif args.category and not args.topic:
        books_to_delete = find_books_by_category(books, args.category)
        if not books_to_delete:
            print(f"\n❌ No books found in category: \"{args.category}\"")
            print("   Use --list to see all categories.")
            sys.exit(1)
        print(f"🔍 Found {len(books_to_delete)} book(s) in category \"{args.category}\"")

    # ── Display books to delete ──
    display_books_to_delete(books_to_delete)

    # ── Dry-run: stop here ──
    if is_dry_run:
        print("─" * 60)
        print("ℹ️  DRY-RUN mode. No changes were made.")
        print("   To execute, add --execute flag:")
        print(f"   python scripts/delete_books.py {' '.join(sys.argv[1:])} --execute")
        return

    # ── Confirmation ──
    if not args.yes:
        print("─" * 60)
        print(f"⚠️  This will permanently delete {len(books_to_delete)} book(s) from data.json")
        if args.delete_files:
            print("   AND their physical files from the Books/ directory!")
        response = input("\n   Are you sure? (yes/no): ").strip().lower()
        if response not in ("yes", "y"):
            print("\n❌ Cancelled. No changes made.")
            return

    # ── Execute deletion ──
    print(f"\n{'─' * 60}")
    print("🚀 Executing deletion...\n")

    # 1. Delete cover images
    print("📸 Deleting cover images...")
    covers_deleted = delete_cover_images(base_dir, books_to_delete, dry_run=False)

    # 2. Delete physical book files (if requested)
    files_deleted = 0
    if args.delete_files:
        print("\n📄 Deleting physical book files...")
        files_deleted = delete_book_files(base_dir, books_to_delete, dry_run=False)

    # 3. Remove entries from data.json
    print("\n📝 Updating data.json...")
    ids_to_delete = {b["id"] for b in books_to_delete}
    remaining_books = [b for b in books if b["id"] not in ids_to_delete]
    save_data(base_dir, remaining_books)
    print(f"   ✅ Removed {len(books_to_delete)} entries ({len(remaining_books)} books remaining)")

    # 4. Cleanup empty directories
    if args.delete_files:
        print("\n📁 Cleaning up empty directories...")
        dirs_removed = cleanup_empty_dirs(base_dir, dry_run=False)
    else:
        dirs_removed = 0

    # 5. Update library_structure.log
    print("\n📋 Updating library_structure.log...")
    update_structure_log(base_dir)

    # ── Summary ──
    print(f"\n{'═' * 60}")
    print("📊 Summary:")
    print(f"   🗑️  Books removed:    {len(books_to_delete)}")
    print(f"   🖼️  Covers deleted:   {covers_deleted}")
    if args.delete_files:
        print(f"   📄 Files deleted:    {files_deleted}")
        print(f"   📁 Dirs removed:     {dirs_removed}")
    print(f"   📖 Books remaining:  {len(remaining_books)}")
    print(f"\n   📌 Next steps:")
    print(f"   1. git add -A && git commit -m 'Remove books' && git push")
    if args.delete_files:
        print(f"   2. Files on GitHub Releases are NOT deleted (do manually if needed)")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    main()
