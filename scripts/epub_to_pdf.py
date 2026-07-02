#!/usr/bin/env python3
"""Convert EPUB files in Inbox to PDF files."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from lib.output import emit_json

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass
class ConversionPlan:
    """Planned EPUB to PDF conversion."""

    source: Path
    target: Path
    status: str
    message: str


@dataclass
class ConversionResult:
    """Result for one EPUB to PDF conversion."""

    source: str
    target: str
    status: str
    message: str


def import_fitz():
    """Import PyMuPDF with a clear error if it is missing."""
    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required. Install dependencies with: "
            "python -m pip install -r requirements.txt"
        ) from exc
    return fitz


def relative_path(path: Path, base_dir: Path) -> str:
    """Return a readable path, relative to base_dir when possible."""
    try:
        return path.relative_to(base_dir).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_inbox_dir(base_dir: Path, inbox_arg: str) -> Path:
    """Resolve and validate an Inbox directory under the project root."""
    inbox_dir = Path(inbox_arg)
    if not inbox_dir.is_absolute():
        inbox_dir = base_dir / inbox_dir

    inbox_dir = inbox_dir.resolve()
    try:
        inbox_dir.relative_to(base_dir)
    except ValueError as exc:
        raise ValueError(f"--inbox-dir must be inside --base-dir: {inbox_dir}") from exc

    if not inbox_dir.exists():
        raise FileNotFoundError(f"Inbox directory not found: {inbox_dir}")
    if not inbox_dir.is_dir():
        raise NotADirectoryError(f"Inbox path is not a directory: {inbox_dir}")
    return inbox_dir


def iter_epubs(inbox_dir: Path) -> list[Path]:
    """Return EPUB files directly under Inbox."""
    return sorted(path for path in inbox_dir.iterdir() if path.suffix.lower() == ".epub")


def build_plan(inbox_dir: Path, *, overwrite: bool) -> list[ConversionPlan]:
    """Build a conversion plan for EPUB files in Inbox."""
    plans: list[ConversionPlan] = []
    for source in iter_epubs(inbox_dir):
        target = source.with_suffix(".pdf")
        if target.exists() and not overwrite:
            plans.append(
                ConversionPlan(
                    source=source,
                    target=target,
                    status="skipped",
                    message="PDF already exists; use --overwrite to replace it",
                )
            )
            continue

        status = "planned"
        message = "Convert EPUB to PDF"
        if target.exists() and overwrite:
            message = "Convert EPUB to PDF and overwrite existing PDF"
        plans.append(ConversionPlan(source=source, target=target, status=status, message=message))

    return plans


def convert_epub_to_pdf(source: Path, target: Path, *, overwrite: bool) -> tuple[str, str]:
    """Convert a single EPUB to a PDF file."""
    fitz = import_fitz()
    if target.exists() and not overwrite:
        return "skipped", "PDF already exists; use --overwrite to replace it"

    temp_path = target.with_name(f".{target.stem}.converting{target.suffix}")
    if temp_path.exists():
        temp_path.unlink()

    try:
        doc = fitz.open(source)
        try:
            if doc.page_count == 0:
                return "failed", "EPUB has no renderable pages"

            pdf_bytes = doc.convert_to_pdf()
        finally:
            doc.close()

        pdf_doc = fitz.open("pdf", pdf_bytes)
        try:
            pdf_doc.save(temp_path, garbage=4, deflate=True)
        finally:
            pdf_doc.close()

        os.replace(temp_path, target)
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        return "failed", f"Conversion failed: {exc}"

    return "converted", "EPUB converted to PDF"


def execute_plan(plans: list[ConversionPlan], base_dir: Path, *, overwrite: bool) -> list[ConversionResult]:
    """Execute planned conversions and return results."""
    results: list[ConversionResult] = []
    for plan in plans:
        if plan.status == "skipped":
            results.append(
                ConversionResult(
                    source=relative_path(plan.source, base_dir),
                    target=relative_path(plan.target, base_dir),
                    status=plan.status,
                    message=plan.message,
                )
            )
            continue

        status, message = convert_epub_to_pdf(plan.source, plan.target, overwrite=overwrite)
        results.append(
            ConversionResult(
                source=relative_path(plan.source, base_dir),
                target=relative_path(plan.target, base_dir),
                status=status,
                message=message,
            )
        )
    return results


def plan_to_results(plans: list[ConversionPlan], base_dir: Path) -> list[ConversionResult]:
    """Convert dry-run plan entries to result-shaped objects."""
    return [
        ConversionResult(
            source=relative_path(plan.source, base_dir),
            target=relative_path(plan.target, base_dir),
            status=plan.status,
            message=plan.message,
        )
        for plan in plans
    ]


def print_results(results: list[ConversionResult], *, dry_run: bool) -> None:
    """Print a human-readable conversion summary."""
    print("=" * 60)
    print("My Bookshelves EPUB to PDF Converter")
    print("=" * 60)
    print(f"Mode: {'dry-run' if dry_run else 'execute'}")
    print()

    if not results:
        print("No EPUB files found.")
        return

    for result in results:
        print(f"- [{result.status}] {result.source} -> {result.target}")
        print(f"  {result.message}")

    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1

    print()
    print("Summary:")
    for status in sorted(counts):
        print(f"- {status}: {counts[status]}")

    if dry_run:
        print()
        print("No files changed. Add --execute to create PDFs.")


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", default=".", help="Project root directory")
    parser.add_argument("--inbox-dir", default="Inbox", help="Inbox directory under base-dir")
    parser.add_argument("--execute", action="store_true", help="Create PDF files")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing PDF outputs")
    parser.add_argument("--fail-fast", action="store_true", help="Stop after the first failure")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()

    try:
        inbox_dir = resolve_inbox_dir(base_dir, args.inbox_dir)
        plans = build_plan(inbox_dir, overwrite=args.overwrite)
        if args.execute:
            if args.fail_fast:
                results: list[ConversionResult] = []
                for plan in plans:
                    result = execute_plan([plan], base_dir, overwrite=args.overwrite)[0]
                    results.append(result)
                    if result.status == "failed":
                        break
            else:
                results = execute_plan(plans, base_dir, overwrite=args.overwrite)
        else:
            results = plan_to_results(plans, base_dir)
    except Exception as exc:
        if args.json:
            emit_json({"ok": False, "error": str(exc)})
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    ok = all(result.status != "failed" for result in results)

    if args.json:
        emit_json(
            {
                "ok": ok,
                "dry_run": not args.execute,
                "results": [result.__dict__ for result in results],
            }
        )
    else:
        print_results(results, dry_run=not args.execute)

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
