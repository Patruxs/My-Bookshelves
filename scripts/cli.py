#!/usr/bin/env python3
"""
📚 My Bookshelves CLI — Unified Command Line Interface

Single entry point for all library management operations.
Designed for both humans and AI agents.

Usage:
    python scripts/cli.py <command> [options]
    book <command> [options]

Commands:
    list            List all books, topics, and categories
    doctor          Validate repo health and dependencies
    validate        Validate repo health and dependencies
    codex-sync      Regenerate the .codex adapter from .agents
    smoke           Smoke check static site contracts
    unlock-pdfs     Remove password encryption from PDFs in Inbox
    delete          Delete books, topics, or categories
    update          Update book metadata, rename topics/categories
    generate        Generate data.json and cover images
    rename          Normalize book filenames to ASCII Snake_Case
    upload          Upload books to GitHub Releases
    structure       Regenerate library_structure.log

Examples:
    book doctor
    book docter
    book unlock-pdfs --execute
    book tui
    python scripts/cli.py list
    python scripts/cli.py delete --book "Title"
    python scripts/cli.py delete --book "Title" --execute
    python scripts/cli.py update --book "Title" --set-description "New desc" --execute
    python scripts/cli.py update --topic "Old" --category "Cat" --rename "New" --execute
    python scripts/cli.py generate
    python scripts/cli.py rename
    python scripts/cli.py upload --dry-run
    python scripts/cli.py doctor --base-dir . --strict
    python scripts/cli.py smoke --base-dir .
    python scripts/cli.py codex-sync --base-dir .
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
    "doctor": {
        "script": "doctor.py",
        "inject_args": [],
        "desc": "Validate repo health and dependencies",
    },
    "validate": {
        "script": "doctor.py",
        "inject_args": [],
        "desc": "Validate repo health and dependencies",
    },
    "codex-sync": {
        "script": "sync_codex.py",
        "inject_args": [],
        "desc": "Regenerate the .codex adapter from .agents",
    },
    "smoke": {
        "script": "smoke_site.py",
        "inject_args": [],
        "desc": "Smoke check static site contracts",
    },
    "unlock-pdfs": {
        "script": "unlock_pdfs.py",
        "inject_args": [],
        "desc": "Remove password encryption from PDFs in Inbox",
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
    "tui": {
        "script": "tui.py",
        "inject_args": [],
        "desc": "Open the interactive terminal UI",
    },
}

ALIASES = {
    "docter": "doctor",
    "doc": "doctor",
    "check": "doctor",
    "unlock": "unlock-pdfs",
    "unlock-pdf": "unlock-pdfs",
    "pdf-unlock": "unlock-pdfs",
}


def print_help() -> None:
    """Print CLI help with all available commands."""
    print("=" * 60)
    print("📚 My Bookshelves CLI")
    print("=" * 60)
    print()
    print("Usage: python scripts/cli.py <command> [options]")
    print("       book <command> [options]")
    print()
    print("Commands:")
    for name, info in COMMANDS.items():
        print(f"  {name:<14} {info['desc']}")
    print()
    print("Examples:")
    print("  book doctor")
    print("  book docter")
    print("  book unlock-pdfs --execute")
    print("  book tui")
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
    print("  python scripts/cli.py doctor --base-dir . --strict")
    print("  python scripts/cli.py smoke --base-dir .")
    print("  python scripts/cli.py smoke --base-dir . --check-download-urls")
    print("  python scripts/cli.py smoke --base-dir . --allow-missing-download-url")
    print("  python scripts/cli.py unlock-pdfs --base-dir .")
    print("  python scripts/cli.py unlock-pdfs --base-dir . --execute")
    print("  python scripts/cli.py validate --base-dir . --json")
    print("  python scripts/cli.py structure --base-dir .")
    print("  python scripts/cli.py codex-sync --base-dir .")
    print()


def normalize_command(command: str) -> str:
    """Resolve friendly aliases and common typos to canonical commands."""
    return ALIASES.get(command, command)


def main() -> None:
    """Main entry point — dispatch to the appropriate script."""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)

    command = normalize_command(sys.argv[1])

    if command not in COMMANDS:
        print(f"❌ Unknown command: \"{command}\"")
        print(f"   Available: {', '.join(COMMANDS.keys())}")
        print(f"   Aliases: {', '.join(sorted(ALIASES.keys()))}")
        print(f"   Run: book --help")
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
