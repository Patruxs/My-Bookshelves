#!/usr/bin/env python3
"""Validate the My Bookshelves repo and automation environment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.output import emit_json
from lib.validation import validate_library

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")


def print_human(result: dict, *, strict: bool) -> None:
    """Print a concise human-readable doctor report."""
    summary = result["summary"]
    print("=" * 60)
    print("My Bookshelves Doctor")
    print("=" * 60)
    print(f"Base dir: {summary['base_dir']}")
    print(f"Books: {summary['books']}")
    print(f"Errors: {summary['errors']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Missing download_url: {summary['missing_download_urls']}")
    print(f"Mode: {'strict' if strict else 'advisory'}")

    for section in ("errors", "warnings"):
        items = result[section]
        if not items:
            continue
        print()
        print(section.upper())
        for item in items:
            print(f"- [{item['code']}] {item['message']} ({item['file']})")

    print()
    print("Status:", "OK" if result["ok"] else "FAILED")


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", default=".", help="Project root directory")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on validation errors")
    args = parser.parse_args()

    result = validate_library(Path(args.base_dir), include_dependencies=True)
    if args.json:
        emit_json(result)
    else:
        print_human(result, strict=args.strict)

    if args.strict and not result["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
