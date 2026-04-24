#!/usr/bin/env python3
"""
📚 My Bookshelves CLI — Unified Command Line Interface

Single entry point for all library management operations.
Designed for both humans and AI agents.

Usage:
    python scripts/cli.py <command> [options]

Commands:
    list            List all books, topics, and categories
    delete          Delete books, topics, or categories
    update          Update book metadata, rename topics/categories
    generate        Generate data.json and cover images
    rename          Normalize book filenames to ASCII Snake_Case
    upload          Upload books to GitHub Releases
    structure       Regenerate library_structure.log

Examples:
    python scripts/cli.py list
    python scripts/cli.py delete --book "Title"
    python scripts/cli.py delete --book "Title" --execute
    python scripts/cli.py update --book "Title" --set-description "New desc" --execute
    python scripts/cli.py update --topic "Old" --category "Cat" --rename "New" --execute
    python scripts/cli.py generate
    python scripts/cli.py rename
    python scripts/cli.py upload --dry-run
"""

import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


SCRIPTS_DIR = Path(__file__).parent

# ── Command → Script mapping ──
COMMANDS = {
    "list": {
        "script": "delete_books.py",
        "inject_args": ["--list"],
        "desc": "List all books, topics, and categories",
    },
    "delete": {
        "script": "delete_books.py",
        "inject_args": [],
        "desc": "Delete books, topics, or categories",
    },
    "update": {
        "script": "update_books.py",
        "inject_args": [],
        "desc": "Update book metadata, rename topics/categories",
    },
    "generate": {
        "script": "generate_data.py",
        "inject_args": [],
        "desc": "Generate data.json and cover images from Books/",
    },
    "rename": {
        "script": "rename_books.py",
        "inject_args": [],
        "desc": "Normalize book filenames to ASCII Snake_Case",
    },
    "upload": {
        "script": "upload_releases.py",
        "inject_args": [],
        "desc": "Upload books to GitHub Releases",
    },
    "structure": {
        "script": "generate_structure_log.py",
        "inject_args": [],
        "desc": "Regenerate library_structure.log",
    },
}


def print_help() -> None:
    """Print CLI help with all available commands."""
    print("=" * 60)
    print("📚 My Bookshelves CLI")
    print("=" * 60)
    print()
    print("Usage: python scripts/cli.py <command> [options]")
    print()
    print("Commands:")
    for name, info in COMMANDS.items():
        print(f"  {name:<14} {info['desc']}")
    print()
    print("Examples:")
    print("  python scripts/cli.py list")
    print("  python scripts/cli.py delete --book \"Title\"")
    print("  python scripts/cli.py delete --book \"Title\" --execute")
    print("  python scripts/cli.py delete --topic \"Topic\" --category \"Cat\" --execute")
    print("  python scripts/cli.py delete --category \"Cat\" --execute")
    print("  python scripts/cli.py update --book \"Title\" --set-description \"Desc\" --execute")
    print("  python scripts/cli.py update --book \"Title\" --set-category \"Cat\" --execute")
    print("  python scripts/cli.py update --book \"Title\" --set-topic \"Topic\" --execute")
    print("  python scripts/cli.py update --topic \"Old\" --category \"Cat\" --rename \"New\" --execute")
    print("  python scripts/cli.py update --category \"Old\" --rename \"New\" --execute")
    print("  python scripts/cli.py generate --base-dir .")
    print("  python scripts/cli.py rename --base-dir . --execute")
    print("  python scripts/cli.py upload --dry-run")
    print("  python scripts/cli.py structure --base-dir .")
    print()


def main() -> None:
    """Main entry point — dispatch to the appropriate script."""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)

    command = sys.argv[1]

    if command not in COMMANDS:
        print(f"❌ Unknown command: \"{command}\"")
        print(f"   Available: {', '.join(COMMANDS.keys())}")
        print(f"   Run: python scripts/cli.py --help")
        sys.exit(1)

    info = COMMANDS[command]
    script_path = SCRIPTS_DIR / info["script"]

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        sys.exit(1)

    # Build command: python <script> [injected_args] [user_args]
    extra_args = sys.argv[2:]  # Everything after the command name
    cmd = [sys.executable, str(script_path)] + info["inject_args"] + extra_args

    # Run the script, passing through stdin/stdout/stderr
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
