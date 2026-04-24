#!/usr/bin/env python3
"""
📚 My Bookshelves TUI — Interactive Terminal User Interface

An interactive, menu-driven terminal application for managing
the My Bookshelves library. Zero external dependencies.

Usage:
    python scripts/tui.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# Enable ANSI escape codes on Windows 10+
if sys.platform == 'win32':
    os.system('')


# ══════════════════════════════════════════════════════════
# ANSI COLORS
# ══════════════════════════════════════════════════════════

class C:
    """ANSI color constants."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background
    BG_BLUE = "\033[44m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    BG_BRIGHT_BLACK = "\033[100m"


# ══════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = Path(__file__).parent
DATA_JSON = BASE_DIR / "site" / "data.json"

# Terminal width
try:
    TERM_WIDTH = os.get_terminal_size().columns
except OSError:
    TERM_WIDTH = 80

WIDTH = min(TERM_WIDTH, 70)


# ══════════════════════════════════════════════════════════
# UI HELPERS
# ══════════════════════════════════════════════════════════

def clear() -> None:
    """Clear the terminal screen."""
    os.system('cls' if sys.platform == 'win32' else 'clear')


def hr(char: str = "─", color: str = C.BRIGHT_BLACK) -> None:
    """Print a horizontal rule."""
    print(f"{color}{char * WIDTH}{C.RESET}")


def header(title: str) -> None:
    """Print a styled header box."""
    print()
    hr("═", C.CYAN)
    padding = (WIDTH - len(title) - 4) // 2
    print(f"{C.CYAN}║{' ' * padding}{C.BOLD}{C.BRIGHT_WHITE} {title} {C.RESET}{C.CYAN}{' ' * (WIDTH - padding - len(title) - 3)}║{C.RESET}")
    hr("═", C.CYAN)


def subheader(title: str) -> None:
    """Print a subheader."""
    print(f"\n  {C.BOLD}{C.BRIGHT_CYAN}{title}{C.RESET}")
    print(f"  {C.BRIGHT_BLACK}{'─' * (WIDTH - 4)}{C.RESET}")


def menu_item(key: str, label: str, desc: str = "", color: str = C.BRIGHT_CYAN) -> None:
    """Print a menu item."""
    if desc:
        print(f"  {color}{C.BOLD}[{key}]{C.RESET}  {label}  {C.BRIGHT_BLACK}{desc}{C.RESET}")
    else:
        print(f"  {color}{C.BOLD}[{key}]{C.RESET}  {label}")


def success(msg: str) -> None:
    """Print a success message."""
    print(f"\n  {C.BRIGHT_GREEN}✅ {msg}{C.RESET}")


def error(msg: str) -> None:
    """Print an error message."""
    print(f"\n  {C.BRIGHT_RED}❌ {msg}{C.RESET}")


def warning(msg: str) -> None:
    """Print a warning message."""
    print(f"\n  {C.BRIGHT_YELLOW}⚠️  {msg}{C.RESET}")


def info(msg: str) -> None:
    """Print an info message."""
    print(f"\n  {C.BRIGHT_BLUE}ℹ️  {msg}{C.RESET}")


def prompt(msg: str = "Your choice") -> str:
    """Show an input prompt and return user input."""
    print()
    try:
        return input(f"  {C.BRIGHT_YELLOW}▸ {msg}: {C.RESET}").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def confirm(msg: str = "Are you sure?") -> bool:
    """Ask for yes/no confirmation."""
    resp = prompt(f"{msg} (y/n)")
    return resp.lower() in ("y", "yes")


def pause() -> None:
    """Wait for user to press Enter."""
    prompt("Press Enter to continue")


def load_books() -> list[dict]:
    """Load books from data.json."""
    if not DATA_JSON.exists():
        return []
    with open(DATA_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def display_title(title: str) -> str:
    """Convert underscore title to display format."""
    return title.replace("_", " ")


def run_script(script_name: str, args: list[str]) -> int:
    """Run a Python script and return exit code."""
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args
    print(f"\n  {C.DIM}Running: {' '.join(cmd)}{C.RESET}\n")
    hr()
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    hr()
    return result.returncode


# ══════════════════════════════════════════════════════════
# SCREENS
# ══════════════════════════════════════════════════════════

def screen_main_menu() -> str:
    """Display the main menu and return the user's choice."""
    clear()
    books = load_books()

    header("📚 My Bookshelves Manager")
    print()
    print(f"  {C.BRIGHT_BLACK}Library: {C.RESET}{C.BRIGHT_WHITE}{len(books)} books{C.RESET}  "
          f"{C.BRIGHT_BLACK}│  Path: {C.RESET}{C.DIM}{BASE_DIR}{C.RESET}")

    subheader("Library")
    menu_item("1", "📋 Browse Library", "View all books, categories & topics")
    menu_item("2", "🔍 Search Books", "Find books by title")

    subheader("Management")
    menu_item("3", "🗑️  Delete", "Remove books, topics, or categories")
    menu_item("4", "✏️  Update", "Edit metadata, rename topics/categories")

    subheader("Build Pipeline")
    menu_item("5", "📸 Generate Data", "Scan Books/ → create data.json + covers")
    menu_item("6", "🔤 Rename Files", "Normalize filenames to ASCII Snake_Case")
    menu_item("7", "☁️  Upload Releases", "Push books to GitHub Releases")
    menu_item("8", "📊 Update Structure Log", "Regenerate library_structure.log")

    subheader("System")
    menu_item("0", "🚪 Exit", "", C.BRIGHT_RED)

    return prompt("Select an option")


def screen_browse() -> None:
    """Browse library — show categories, topics, and books."""
    clear()
    header("📋 Browse Library")

    books = load_books()
    if not books:
        error("No books found. Run 'Generate Data' first.")
        pause()
        return

    # Build tree
    tree: dict[str, dict[str, list[dict]]] = {}
    for b in books:
        cat = b.get("category", "Unknown")
        topic = b.get("topic", "Unknown")
        tree.setdefault(cat, {}).setdefault(topic, []).append(b)

    # Category summary
    print(f"\n  {C.BRIGHT_WHITE}{len(books)} books{C.RESET} across "
          f"{C.BRIGHT_WHITE}{len(tree)} categories{C.RESET}")

    cat_list = sorted(tree.keys())
    for i, cat in enumerate(cat_list):
        cat_count = sum(len(t) for t in tree[cat].values())
        topic_count = len(tree[cat])
        print(f"\n  {C.BOLD}{C.BRIGHT_CYAN}📂 {cat}{C.RESET}  "
              f"{C.BRIGHT_BLACK}({cat_count} books, {topic_count} topics){C.RESET}")

        for topic in sorted(tree[cat].keys()):
            topic_books = tree[cat][topic]
            print(f"     {C.BRIGHT_YELLOW}📌 {topic}{C.RESET} "
                  f"{C.BRIGHT_BLACK}({len(topic_books)}){C.RESET}")
            for b in sorted(topic_books, key=lambda x: x.get("title", "")):
                title = display_title(b.get("title", "?"))
                fmt = b.get("format", "?")
                bid = b.get("id", "?")[:8]
                has_desc = "📝" if b.get("description") else "  "
                has_url = "🔗" if b.get("download_url") else "  "
                print(f"        {has_desc}{has_url} {C.WHITE}{title}{C.RESET} "
                      f"{C.BRIGHT_BLACK}[{fmt}] {bid}{C.RESET}")

    print(f"\n  {C.BRIGHT_BLACK}Legend: 📝 = has description  🔗 = has download URL{C.RESET}")
    pause()


def screen_search() -> None:
    """Search books by title."""
    clear()
    header("🔍 Search Books")

    query = prompt("Enter search term (title)")
    if not query:
        return

    books = load_books()
    q = query.lower().replace(" ", "_")
    results = [b for b in books if q in b.get("title", "").lower()]

    if not results:
        error(f"No books found matching \"{query}\"")
        pause()
        return

    print(f"\n  Found {C.BRIGHT_WHITE}{len(results)}{C.RESET} result(s):\n")

    for i, b in enumerate(results, 1):
        title = display_title(b.get("title", "?"))
        cat = b.get("category", "?")
        topic = b.get("topic", "?")
        fmt = b.get("format", "?")
        bid = b.get("id", "?")
        desc = b.get("description", "")
        desc_preview = (desc[:50] + "...") if len(desc) > 50 else desc

        print(f"  {C.BRIGHT_CYAN}{C.BOLD}{i}.{C.RESET} {C.BRIGHT_WHITE}{title}{C.RESET}")
        print(f"     {C.BRIGHT_BLACK}Category: {C.RESET}{cat}")
        print(f"     {C.BRIGHT_BLACK}Topic:    {C.RESET}{topic}")
        print(f"     {C.BRIGHT_BLACK}Format:   {C.RESET}{fmt}  {C.BRIGHT_BLACK}ID: {bid}{C.RESET}")
        if desc_preview:
            print(f"     {C.BRIGHT_BLACK}Desc:     {C.RESET}{C.DIM}{desc_preview}{C.RESET}")
        print()

    pause()


def screen_delete() -> None:
    """Interactive delete flow."""
    clear()
    header("🗑️  Delete")

    subheader("What to delete?")
    menu_item("1", "Delete a specific book", "by title")
    menu_item("2", "Delete a topic", "all books in a topic")
    menu_item("3", "Delete a category", "all books in a category")
    menu_item("0", "← Back", "", C.BRIGHT_RED)

    choice = prompt("Select")

    if choice == "1":
        title = prompt("Book title (or part of it)")
        if not title:
            return
        # Show dry-run first
        run_script("delete_books.py", ["--book", title, "--base-dir", str(BASE_DIR)])
        if confirm("Execute this deletion?"):
            also_files = confirm("Also delete physical files from Books/?")
            args = ["--book", title, "--base-dir", str(BASE_DIR), "--execute", "--yes"]
            if also_files:
                args.append("--delete-files")
            run_script("delete_books.py", args)
        pause()

    elif choice == "2":
        books = load_books()
        # Show available topics
        topics: dict[str, set[str]] = {}
        for b in books:
            cat = b.get("category", "")
            topic = b.get("topic", "")
            topics.setdefault(cat, set()).add(topic)

        print(f"\n  {C.BOLD}Available topics:{C.RESET}")
        for cat in sorted(topics.keys()):
            print(f"  {C.BRIGHT_CYAN}📂 {cat}{C.RESET}")
            for t in sorted(topics[cat]):
                print(f"     📌 {t}")

        topic = prompt("Topic name")
        category = prompt("Category name")
        if not topic or not category:
            return

        run_script("delete_books.py", ["--topic", topic, "--category", category, "--base-dir", str(BASE_DIR)])
        if confirm("Execute this deletion?"):
            run_script("delete_books.py", ["--topic", topic, "--category", category,
                                           "--base-dir", str(BASE_DIR), "--execute", "--yes"])
        pause()

    elif choice == "3":
        books = load_books()
        cats = sorted(set(b.get("category", "") for b in books))
        print(f"\n  {C.BOLD}Available categories:{C.RESET}")
        for i, cat in enumerate(cats, 1):
            count = sum(1 for b in books if b.get("category") == cat)
            print(f"  {C.BRIGHT_CYAN}[{i}]{C.RESET} {cat} ({count} books)")

        sel = prompt("Category number or name")
        if not sel:
            return
        # Resolve by number or name
        try:
            idx = int(sel) - 1
            category = cats[idx] if 0 <= idx < len(cats) else sel
        except ValueError:
            category = sel

        run_script("delete_books.py", ["--category", category, "--base-dir", str(BASE_DIR)])
        if confirm("Execute this deletion?"):
            run_script("delete_books.py", ["--category", category, "--base-dir", str(BASE_DIR),
                                           "--execute", "--yes"])
        pause()


def screen_update() -> None:
    """Interactive update flow."""
    clear()
    header("✏️  Update")

    subheader("What to update?")
    menu_item("1", "Update book description")
    menu_item("2", "Move book to another category")
    menu_item("3", "Move book to another topic")
    menu_item("4", "Rename a topic", "affects all books in it")
    menu_item("5", "Rename a category", "affects all books in it")
    menu_item("0", "← Back", "", C.BRIGHT_RED)

    choice = prompt("Select")

    if choice == "1":
        title = prompt("Book title (or part of it)")
        if not title:
            return
        desc = prompt("New description")
        if not desc:
            return
        run_script("update_books.py", ["--book", title, "--set-description", desc,
                                       "--base-dir", str(BASE_DIR)])
        if confirm("Apply this update?"):
            run_script("update_books.py", ["--book", title, "--set-description", desc,
                                           "--base-dir", str(BASE_DIR), "--execute", "--yes"])
        pause()

    elif choice == "2":
        title = prompt("Book title")
        if not title:
            return
        new_cat = prompt("New category name")
        if not new_cat:
            return
        run_script("update_books.py", ["--book", title, "--set-category", new_cat,
                                       "--base-dir", str(BASE_DIR)])
        if confirm("Apply this update?"):
            run_script("update_books.py", ["--book", title, "--set-category", new_cat,
                                           "--base-dir", str(BASE_DIR), "--execute", "--yes"])
        pause()

    elif choice == "3":
        title = prompt("Book title")
        if not title:
            return
        new_topic = prompt("New topic name")
        if not new_topic:
            return
        run_script("update_books.py", ["--book", title, "--set-topic", new_topic,
                                       "--base-dir", str(BASE_DIR)])
        if confirm("Apply this update?"):
            run_script("update_books.py", ["--book", title, "--set-topic", new_topic,
                                           "--base-dir", str(BASE_DIR), "--execute", "--yes"])
        pause()

    elif choice == "4":
        topic = prompt("Current topic name")
        category = prompt("In category")
        new_name = prompt("New topic name")
        if not all([topic, category, new_name]):
            return
        run_script("update_books.py", ["--topic", topic, "--category", category,
                                       "--rename", new_name, "--base-dir", str(BASE_DIR)])
        if confirm("Apply this rename?"):
            run_script("update_books.py", ["--topic", topic, "--category", category,
                                           "--rename", new_name, "--base-dir", str(BASE_DIR),
                                           "--execute", "--yes"])
        pause()

    elif choice == "5":
        category = prompt("Current category name")
        new_name = prompt("New category name")
        if not all([category, new_name]):
            return
        run_script("update_books.py", ["--category", category, "--rename", new_name,
                                       "--base-dir", str(BASE_DIR)])
        if confirm("Apply this rename?"):
            run_script("update_books.py", ["--category", category, "--rename", new_name,
                                           "--base-dir", str(BASE_DIR), "--execute", "--yes"])
        pause()


def screen_generate() -> None:
    """Generate data.json and covers."""
    clear()
    header("📸 Generate Data")

    warning("This scans Books/ directory and regenerates data.json + cover images.")
    warning("Existing descriptions and download_urls will be preserved.")
    print()
    menu_item("1", "Normal run", "skip existing covers")
    menu_item("2", "Force regenerate", "re-extract ALL covers")
    menu_item("0", "← Back", "", C.BRIGHT_RED)

    choice = prompt("Select")
    if choice == "1":
        run_script("generate_data.py", ["--base-dir", str(BASE_DIR)])
        pause()
    elif choice == "2":
        if confirm("Force regenerate ALL covers?"):
            run_script("generate_data.py", ["--base-dir", str(BASE_DIR), "--force"])
        pause()


def screen_rename() -> None:
    """Rename book files."""
    clear()
    header("🔤 Rename Files")

    info("Preview which files would be renamed to ASCII Snake_Case format.")
    print()

    # Run dry-run first
    run_script("rename_books.py", ["--base-dir", str(BASE_DIR)])

    if confirm("Execute the rename?"):
        run_script("rename_books.py", ["--base-dir", str(BASE_DIR), "--execute"])

    pause()


def screen_upload() -> None:
    """Upload to GitHub Releases."""
    clear()
    header("☁️  Upload to GitHub Releases")

    menu_item("1", "Dry-run", "preview what would be uploaded")
    menu_item("2", "Upload new books only")
    menu_item("3", "Force re-upload all")
    menu_item("4", "Hard reset", "delete & recreate release")
    menu_item("0", "← Back", "", C.BRIGHT_RED)

    choice = prompt("Select")
    if choice == "1":
        run_script("upload_releases.py", ["--dry-run"])
        pause()
    elif choice == "2":
        if confirm("Upload new books to GitHub Releases?"):
            run_script("upload_releases.py", [])
        pause()
    elif choice == "3":
        if confirm("Re-upload ALL books?"):
            run_script("upload_releases.py", ["--force"])
        pause()
    elif choice == "4":
        warning("This will DELETE the existing release and create a new one!")
        if confirm("Hard reset GitHub Release?"):
            run_script("upload_releases.py", ["--hard-reset"])
        pause()


def screen_structure() -> None:
    """Regenerate library_structure.log."""
    clear()
    header("📊 Update Structure Log")

    info("Regenerating library_structure.log from data.json...")
    run_script("generate_structure_log.py", ["--base-dir", str(BASE_DIR)])
    pause()


# ══════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════

def main() -> None:
    """Main TUI event loop."""
    while True:
        try:
            choice = screen_main_menu()

            if choice == "1":
                screen_browse()
            elif choice == "2":
                screen_search()
            elif choice == "3":
                screen_delete()
            elif choice == "4":
                screen_update()
            elif choice == "5":
                screen_generate()
            elif choice == "6":
                screen_rename()
            elif choice == "7":
                screen_upload()
            elif choice == "8":
                screen_structure()
            elif choice in ("0", "q", "quit", "exit"):
                clear()
                print(f"\n  {C.BRIGHT_CYAN}👋 Goodbye!{C.RESET}\n")
                break
            else:
                if choice:
                    error(f"Invalid option: \"{choice}\"")
                    pause()

        except KeyboardInterrupt:
            clear()
            print(f"\n  {C.BRIGHT_CYAN}👋 Goodbye!{C.RESET}\n")
            break


if __name__ == "__main__":
    main()
