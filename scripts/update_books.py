#!/usr/bin/env python3
"""
📚 My Bookshelves — Book Updater

Update book metadata, rename topics, or rename categories in the library.
Modifies entries in data.json, and optionally moves physical files/folders.

Usage:
    # Update a book's description
    python scripts/update_books.py --book "Title" --set-description "New desc"

    # Move a book to a different category
    python scripts/update_books.py --book "Title" --set-category "New Category"

    # Move a book to a different topic
    python scripts/update_books.py --book "Title" --set-topic "New Topic"

    # Rename a topic (all books in it)
    python scripts/update_books.py --topic "Old Topic" --category "Cat" --rename "New Topic"

    # Rename a category (all books in it)
    python scripts/update_books.py --category "Old Category" --rename "New Category"

    # Preview mode (default — no changes made)
    python scripts/update_books.py --book "Title" --set-topic "New"

    # Execute update
    python scripts/update_books.py --book "Title" --set-topic "New" --execute

    # List all books/topics/categories
    python scripts/update_books.py --list
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding
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
    """Load books from data.json."""
    data_path = base_dir / DATA_JSON
    if not data_path.exists():
        print(f"❌ data.json not found at: {data_path}")
        sys.exit(1)
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(base_dir: Path, books: list[dict]) -> None:
    """Save books to data.json."""
    data_path = base_dir / DATA_JSON
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════
# LISTING
# ══════════════════════════════════════════════════════════

def list_library(base_dir: Path) -> None:
    """Print all categories, topics, and book counts."""
    books = load_data(base_dir)
    tree: dict[str, dict[str, list[str]]] = {}
    for b in books:
        cat = b.get("category", "Unknown")
        topic = b.get("topic", "Unknown")
        title = b.get("title", "Unknown")
        tree.setdefault(cat, {}).setdefault(topic, []).append(title)

    print(f"\n📚 Library Overview ({len(books)} books total)\n")
    print("=" * 60)
    for cat in sorted(tree.keys()):
        cat_count = sum(len(t) for t in tree[cat].values())
        print(f"\n📂 {cat} ({cat_count} books)")
        for topic in sorted(tree[cat].keys()):
            titles = tree[cat][topic]
            print(f"   📌 {topic} ({len(titles)} books)")
            for title in sorted(titles):
                print(f"      • {title.replace('_', ' ')}")
    print(f"\n{'=' * 60}")


# ══════════════════════════════════════════════════════════
# BOOK SELECTION
# ══════════════════════════════════════════════════════════

def find_books_by_title(books: list[dict], query: str) -> list[dict]:
    """Find books matching a title (case-insensitive, partial match)."""
    q = query.lower().replace(" ", "_")
    return [b for b in books if q in b.get("title", "").lower()]


def find_books_by_id(books: list[dict], book_id: str) -> list[dict]:
    """Find a book by exact ID."""
    return [b for b in books if b.get("id", "") == book_id]


def find_books_by_topic(books: list[dict], topic: str, category: str) -> list[dict]:
    """Find all books in a specific topic within a category."""
    return [
        b for b in books
        if b.get("topic", "").lower() == topic.lower()
        and b.get("category", "").lower() == category.lower()
    ]


def find_books_by_category(books: list[dict], category: str) -> list[dict]:
    """Find all books in a specific category."""
    return [b for b in books if b.get("category", "").lower() == category.lower()]


# ══════════════════════════════════════════════════════════
# UPDATE LOGIC
# ══════════════════════════════════════════════════════════

def preview_book_updates(targets: list[dict], field: str, new_value: str) -> None:
    """Display preview of what will change for each book."""
    print(f"\n📝 Changes to be applied ({len(targets)} book(s)):\n")
    for b in targets:
        title = b.get("title", "?").replace("_", " ")
        old_value = b.get(field, "")
        if field == "description":
            old_preview = (old_value[:60] + "...") if len(old_value) > 60 else old_value
            new_preview = (new_value[:60] + "...") if len(new_value) > 60 else new_value
            print(f"  📖 {title}")
            print(f"     {field}: \"{old_preview}\"")
            print(f"          → \"{new_preview}\"")
        else:
            print(f"  📖 {title}")
            print(f"     {field}: \"{old_value}\" → \"{new_value}\"")
        print()


def apply_book_updates(books: list[dict], target_ids: set[str],
                       field: str, new_value: str) -> int:
    """Apply field updates to matching books in the full list.

    Args:
        books: Full book list (modified in-place).
        target_ids: IDs of books to update.
        field: Field name to update.
        new_value: New value for the field.

    Returns:
        Number of books updated.
    """
    updated = 0
    for b in books:
        if b.get("id") in target_ids:
            b[field] = new_value
            updated += 1
    return updated


def update_file_paths(books: list[dict], target_ids: set[str],
                      old_category: str, new_category: str,
                      old_topic: str, new_topic: str) -> int:
    """Update file_path fields when category/topic changes.

    Replaces the category folder name and/or topic folder name in file_path.

    Args:
        books: Full book list (modified in-place).
        target_ids: IDs of books to update.
        old_category/new_category: Category folder names.
        old_topic/new_topic: Topic folder names.

    Returns:
        Number of paths updated.
    """
    updated = 0
    for b in books:
        if b.get("id") not in target_ids:
            continue
        fp = b.get("file_path", "")
        if not fp:
            continue

        parts = Path(fp).parts
        # Expected: ('Books', 'N_Category', 'Topic', [...], 'file.ext')
        if len(parts) < 4:
            continue

        new_parts = list(parts)
        changed = False

        # Update category folder (index 1)
        if old_category and new_category and parts[1] != new_category:
            # Find the matching category folder
            cat_display = parts[1].split("_", 1)
            if len(cat_display) >= 2:
                # Keep the numeric prefix, replace the name
                prefix = cat_display[0]
                new_cat_folder = f"{prefix}_{new_category.replace(' ', '_')}"
                new_parts[1] = new_cat_folder
                changed = True

        # Update topic folder (index 2)
        if old_topic and new_topic:
            new_topic_folder = new_topic.replace(" ", "_")
            new_parts[2] = new_topic_folder
            changed = True

        if changed:
            b["file_path"] = "/".join(new_parts)
            updated += 1

    return updated


def update_structure_log(base_dir: Path) -> None:
    """Regenerate library_structure.log."""
    script = base_dir / "scripts" / "generate_structure_log.py"
    if not script.exists():
        print("  ⚠️  generate_structure_log.py not found, skipping")
        return
    try:
        subprocess.run(
            [sys.executable, str(script), "--base-dir", str(base_dir)],
            check=True, capture_output=True, text=True,
        )
        print("  ✅ Updated library_structure.log")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Failed to update log: {e}")


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="📚 My Bookshelves — Update books, topics, or categories"
    )

    # Selection
    parser.add_argument("--book", default=None,
                        help="Select book(s) by title (partial match)")
    parser.add_argument("--book-id", default=None,
                        help="Select a book by exact ID")
    parser.add_argument("--topic", default=None,
                        help="Select ALL books in this topic (requires --category)")
    parser.add_argument("--category", default=None,
                        help="Select ALL books in this category")

    # Update actions
    parser.add_argument("--set-description", default=None,
                        help="Set new description for selected book(s)")
    parser.add_argument("--set-category", default=None,
                        help="Move selected book(s) to a new category")
    parser.add_argument("--set-topic", default=None,
                        help="Move selected book(s) to a new topic")
    parser.add_argument("--rename", default=None,
                        help="Rename a topic or category (use with --topic or --category)")

    # Execution control
    parser.add_argument("--execute", action="store_true",
                        help="Actually perform updates (default: dry-run)")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt")

    # Utility
    parser.add_argument("--list", action="store_true",
                        help="List all categories, topics, and books")
    parser.add_argument("--base-dir", default=".",
                        help="Project root directory (default: .)")

    args = parser.parse_args()
    base_dir = Path(args.base_dir).resolve()
    is_dry_run = not args.execute

    print("=" * 60)
    print("📚 My Bookshelves — Book Updater")
    print("=" * 60)
    print(f"📂 Base directory: {base_dir}")

    # ── List mode ──
    if args.list:
        list_library(base_dir)
        return

    # ── Validate ──
    has_selection = args.book or args.book_id or args.topic or args.category
    has_action = args.set_description or args.set_category or args.set_topic or args.rename

    if not has_selection:
        print("\n❌ No selection. Use --book, --book-id, --topic, or --category.")
        print("   Use --list to see all available books.\n")
        parser.print_help()
        sys.exit(1)

    if not has_action:
        print("\n❌ No update action. Use --set-description, --set-category,")
        print("   --set-topic, or --rename.\n")
        parser.print_help()
        sys.exit(1)

    if args.topic and not args.category and not args.rename:
        print("\n❌ --topic requires --category to disambiguate.")
        sys.exit(1)

    print(f"🔧 Mode: {'🚀 EXECUTE' if not is_dry_run else '👀 DRY-RUN (preview only)'}")

    # ── Load data ──
    books = load_data(base_dir)
    print(f"\n📖 Loaded {len(books)} books from data.json")

    # ── RENAME topic/category (bulk rename) ──
    if args.rename:
        if args.topic and args.category:
            # Rename a topic
            targets = find_books_by_topic(books, args.topic, args.category)
            if not targets:
                print(f"\n❌ No books in topic \"{args.topic}\" / category \"{args.category}\"")
                sys.exit(1)

            print(f"\n🔄 Rename topic: \"{args.topic}\" → \"{args.rename}\"")
            print(f"   In category: \"{args.category}\"")
            preview_book_updates(targets, "topic", args.rename)

            if is_dry_run:
                print("─" * 60)
                print("ℹ️  DRY-RUN. No changes made. Add --execute to apply.")
                return

            if not args.yes:
                r = input(f"\n   Rename topic for {len(targets)} book(s)? (yes/no): ").strip().lower()
                if r not in ("yes", "y"):
                    print("\n❌ Cancelled.")
                    return

            target_ids = {b["id"] for b in targets}
            updated = apply_book_updates(books, target_ids, "topic", args.rename)
            update_file_paths(books, target_ids, "", "", args.topic, args.rename)
            save_data(base_dir, books)
            print(f"\n✅ Renamed topic for {updated} book(s)")
            print("\n📋 Updating library_structure.log...")
            update_structure_log(base_dir)
            print(f"\n{'═' * 60}")
            print(f"📌 Next: git add -A && git commit -m 'Rename topic' && git push")
            print(f"{'═' * 60}")
            return

        elif args.category and not args.topic:
            # Rename a category
            targets = find_books_by_category(books, args.category)
            if not targets:
                print(f"\n❌ No books in category \"{args.category}\"")
                sys.exit(1)

            print(f"\n🔄 Rename category: \"{args.category}\" → \"{args.rename}\"")
            preview_book_updates(targets, "category", args.rename)

            if is_dry_run:
                print("─" * 60)
                print("ℹ️  DRY-RUN. No changes made. Add --execute to apply.")
                return

            if not args.yes:
                r = input(f"\n   Rename category for {len(targets)} book(s)? (yes/no): ").strip().lower()
                if r not in ("yes", "y"):
                    print("\n❌ Cancelled.")
                    return

            target_ids = {b["id"] for b in targets}
            updated = apply_book_updates(books, target_ids, "category", args.rename)
            save_data(base_dir, books)
            print(f"\n✅ Renamed category for {updated} book(s)")
            print("\n📋 Updating library_structure.log...")
            update_structure_log(base_dir)
            print(f"\n{'═' * 60}")
            print(f"📌 Next: git add -A && git commit -m 'Rename category' && git push")
            print(f"{'═' * 60}")
            return

        else:
            print("\n❌ --rename requires --topic+--category or --category alone.")
            sys.exit(1)

    # ── BOOK-LEVEL UPDATES ──
    targets: list[dict] = []

    if args.book_id:
        targets = find_books_by_id(books, args.book_id)
        if not targets:
            print(f"\n❌ No book with ID: {args.book_id}")
            sys.exit(1)
        print(f"🔍 Found {len(targets)} book(s) with ID: {args.book_id}")

    elif args.book:
        targets = find_books_by_title(books, args.book)
        if not targets:
            print(f"\n❌ No book matching: \"{args.book}\"")
            sys.exit(1)
        print(f"🔍 Found {len(targets)} book(s) matching: \"{args.book}\"")

    elif args.topic and args.category:
        targets = find_books_by_topic(books, args.topic, args.category)
        if not targets:
            print(f"\n❌ No books in topic \"{args.topic}\" / \"{args.category}\"")
            sys.exit(1)
        print(f"🔍 Found {len(targets)} book(s) in topic \"{args.topic}\"")

    elif args.category:
        targets = find_books_by_category(books, args.category)
        if not targets:
            print(f"\n❌ No books in category: \"{args.category}\"")
            sys.exit(1)
        print(f"🔍 Found {len(targets)} book(s) in category \"{args.category}\"")

    # Collect all updates to apply
    updates: list[tuple[str, str]] = []
    if args.set_description is not None:
        updates.append(("description", args.set_description))
    if args.set_category is not None:
        updates.append(("category", args.set_category))
    if args.set_topic is not None:
        updates.append(("topic", args.set_topic))

    # Preview
    for field, value in updates:
        preview_book_updates(targets, field, value)

    if is_dry_run:
        print("─" * 60)
        print("ℹ️  DRY-RUN. No changes made. Add --execute to apply.")
        return

    # Confirm
    if not args.yes:
        fields_str = ", ".join(f for f, _ in updates)
        r = input(f"\n   Update {fields_str} for {len(targets)} book(s)? (yes/no): ").strip().lower()
        if r not in ("yes", "y"):
            print("\n❌ Cancelled.")
            return

    # Apply
    print(f"\n{'─' * 60}")
    print("🚀 Applying updates...\n")

    target_ids = {b["id"] for b in targets}
    total_updated = 0

    for field, value in updates:
        count = apply_book_updates(books, target_ids, field, value)
        print(f"  ✅ Updated {field} for {count} book(s)")
        total_updated += count

    # Update file_path if category or topic changed
    if args.set_category or args.set_topic:
        old_cat = targets[0].get("category", "") if not args.set_category else args.category or ""
        new_cat = args.set_category or ""
        old_topic = args.topic or ""
        new_topic = args.set_topic or ""
        if new_cat or new_topic:
            paths = update_file_paths(books, target_ids, old_cat, new_cat, old_topic, new_topic)
            if paths:
                print(f"  ✅ Updated {paths} file path(s)")

    save_data(base_dir, books)
    print(f"\n📝 Saved data.json ({len(books)} books)")

    print("\n📋 Updating library_structure.log...")
    update_structure_log(base_dir)

    print(f"\n{'═' * 60}")
    print(f"📊 Summary: Updated {total_updated} field(s) across {len(targets)} book(s)")
    print(f"\n📌 Next: git add -A && git commit -m 'Update books' && git push")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    main()
