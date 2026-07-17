#!/usr/bin/env python3
"""Convert EPUB files in Inbox to PDF files."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from lib.output import ProgressCallback, emit_json, make_progress_printer

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")


LETTER_WIDTH = 612.0
LETTER_HEIGHT = 792.0
PAGE_MARGIN = 72.0
CONTENT_WIDTH = LETTER_WIDTH - (PAGE_MARGIN * 2)
CONTENT_HEIGHT = LETTER_HEIGHT - (PAGE_MARGIN * 2)
CALIBRE_FLATPAK_ID = "com.calibre_ebook.calibre"
CALIBRE_PDF_OPTIONS = [
    "--paper-size",
    "letter",
    "--pdf-page-margin-left",
    "72.0",
    "--pdf-page-margin-right",
    "72.0",
    "--pdf-page-margin-top",
    "72.0",
    "--pdf-page-margin-bottom",
    "72.0",
    "--pdf-serif-family",
    "TeX Gyre Termes",
    "--pdf-sans-family",
    "TeX Gyre Heros",
    "--pdf-mono-family",
    "TeX Gyre Cursor",
    "--pdf-standard-font",
    "serif",
    "--pdf-default-font-size",
    "20",
    "--pdf-mono-font-size",
    "16",
    "--unit",
    "inch",
]


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


def calibre_command_candidates() -> list[list[str]]:
    """Return possible Calibre ebook-convert command prefixes."""
    candidates: list[list[str]] = []
    if shutil.which("ebook-convert"):
        candidates.append(["ebook-convert"])
    if shutil.which("flatpak"):
        candidates.append(["flatpak", "run", "--command=ebook-convert", CALIBRE_FLATPAK_ID])
    return candidates


def find_calibre_command() -> list[str] | None:
    """Find a working Calibre ebook-convert command."""
    for command in calibre_command_candidates():
        try:
            result = subprocess.run(
                [*command, "--version"],
                capture_output=True,
                encoding="utf-8",
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0:
            return command
    return None


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


def letter_rects(fitz) -> tuple[object, object]:
    """Return full Letter page and inner content rectangles."""
    page_rect = fitz.Rect(0, 0, LETTER_WIDTH, LETTER_HEIGHT)
    content_rect = fitz.Rect(
        PAGE_MARGIN,
        PAGE_MARGIN,
        LETTER_WIDTH - PAGE_MARGIN,
        LETTER_HEIGHT - PAGE_MARGIN,
    )
    return page_rect, content_rect


def command_error_tail(result: subprocess.CompletedProcess[str]) -> str:
    """Return the useful tail of a failed command."""
    output = "\n".join(part for part in (result.stderr, result.stdout) if part)
    lines = output.strip().splitlines()
    if not lines:
        return f"exit code {result.returncode}"
    return "\n".join(lines[-8:])


def convert_epub_to_pdf_with_calibre(
    source: Path,
    target: Path,
    *,
    command: list[str],
) -> tuple[str, str]:
    """Convert one EPUB to PDF using Calibre ebook-convert."""
    temp_path = target.with_name(f".{target.stem}.converting{target.suffix}")
    if temp_path.exists():
        temp_path.unlink()

    result = subprocess.run(
        [*command, str(source), str(temp_path), *CALIBRE_PDF_OPTIONS],
        cwd=str(target.parent),
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        if temp_path.exists():
            temp_path.unlink()
        return "failed", f"Calibre conversion failed: {command_error_tail(result)}"
    if not temp_path.exists():
        return "failed", "Calibre conversion did not create a PDF"

    os.replace(temp_path, target)
    return "converted", "EPUB converted to PDF with Calibre"


def convert_epub_to_pdf_with_pymupdf(source: Path, target: Path) -> tuple[str, str]:
    """Convert a single EPUB to a Letter-sized PDF using PyMuPDF."""
    fitz = import_fitz()
    temp_path = target.with_name(f".{target.stem}.converting{target.suffix}")
    if temp_path.exists():
        temp_path.unlink()

    try:
        doc = fitz.open(source)
        try:
            doc.layout(rect=fitz.Rect(0, 0, CONTENT_WIDTH, CONTENT_HEIGHT))
            if doc.page_count == 0:
                return "failed", "EPUB has no renderable pages"

            pdf_bytes = doc.convert_to_pdf()
        finally:
            doc.close()

        pdf_doc = fitz.open("pdf", pdf_bytes)
        output_doc = fitz.open()
        try:
            _, content_rect = letter_rects(fitz)
            for page_number in range(pdf_doc.page_count):
                page = output_doc.new_page(width=LETTER_WIDTH, height=LETTER_HEIGHT)
                page.show_pdf_page(content_rect, pdf_doc, page_number)

            output_doc.save(temp_path, garbage=4, deflate=True)
        finally:
            pdf_doc.close()
            output_doc.close()

        os.replace(temp_path, target)
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        return "failed", f"PyMuPDF conversion failed: {exc}"

    return "converted", "EPUB converted to PDF with PyMuPDF"


def convert_epub_to_pdf(
    source: Path,
    target: Path,
    *,
    overwrite: bool,
    engine: str = "auto",
) -> tuple[str, str]:
    """Convert a single EPUB to a PDF file."""
    if target.exists() and not overwrite:
        return "skipped", "PDF already exists; use --overwrite to replace it"

    if engine not in {"auto", "calibre", "pymupdf"}:
        return "failed", f"Unknown conversion engine: {engine}"

    if engine in {"auto", "calibre"}:
        command = find_calibre_command()
        if command:
            return convert_epub_to_pdf_with_calibre(source, target, command=command)
        if engine == "calibre":
            return "failed", "Calibre ebook-convert was not found"

    return convert_epub_to_pdf_with_pymupdf(source, target)


def execute_plan(
    plans: list[ConversionPlan],
    base_dir: Path,
    *,
    overwrite: bool,
    engine: str,
    fail_fast: bool = False,
    progress: ProgressCallback | None = None,
) -> list[ConversionResult]:
    """Execute planned conversions and return results."""
    report = progress or (lambda _message: None)
    total = len(plans)
    if total:
        report(f"Converting {total} book(s)...")

    results: list[ConversionResult] = []
    for index, plan in enumerate(plans, 1):
        prefix = f"[{index}/{total}]"
        source_name = plan.source.name
        target_name = plan.target.name

        if plan.status == "skipped":
            report(f"{prefix} skip {source_name} - {plan.message}")
            results.append(
                ConversionResult(
                    source=relative_path(plan.source, base_dir),
                    target=relative_path(plan.target, base_dir),
                    status=plan.status,
                    message=plan.message,
                )
            )
            continue

        report(f"{prefix} converting {source_name} -> {target_name}")
        status, message = convert_epub_to_pdf(
            plan.source,
            plan.target,
            overwrite=overwrite,
            engine=engine,
        )
        report(f"{prefix} done: {status} - {message}")
        results.append(
            ConversionResult(
                source=relative_path(plan.source, base_dir),
                target=relative_path(plan.target, base_dir),
                status=status,
                message=message,
            )
        )
        if fail_fast and status == "failed":
            break

    if total:
        report("Done.")
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
    parser.add_argument(
        "--engine",
        choices=("auto", "calibre", "pymupdf"),
        default="auto",
        help="Conversion engine. auto prefers Calibre and falls back to PyMuPDF",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()

    try:
        inbox_dir = resolve_inbox_dir(base_dir, args.inbox_dir)
        plans = build_plan(inbox_dir, overwrite=args.overwrite)
        if args.execute:
            progress = make_progress_printer(enabled=not args.json)
            results = execute_plan(
                plans,
                base_dir,
                overwrite=args.overwrite,
                engine=args.engine,
                fail_fast=args.fail_fast,
                progress=progress,
            )
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
