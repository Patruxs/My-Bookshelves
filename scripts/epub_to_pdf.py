#!/usr/bin/env python3
"""Convert EPUB files in Inbox to PDF files."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

from lib.output import ProgressCallback, emit_json, make_progress_printer

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")


LETTER_WIDTH = 612.0
LETTER_HEIGHT = 792.0
PAGE_MARGIN = 54.0  # 0.75 inch - more content per page, fewer pages, faster convert
CONTENT_WIDTH = LETTER_WIDTH - (PAGE_MARGIN * 2)
CONTENT_HEIGHT = LETTER_HEIGHT - (PAGE_MARGIN * 2)
CALIBRE_FLATPAK_ID = "com.calibre_ebook.calibre"
# Lean Calibre settings: smaller type + margins -> fewer pages and faster reflow.
CALIBRE_PDF_OPTIONS = [
    "--paper-size",
    "letter",
    "--pdf-page-margin-left",
    "54.0",
    "--pdf-page-margin-right",
    "54.0",
    "--pdf-page-margin-top",
    "54.0",
    "--pdf-page-margin-bottom",
    "54.0",
    "--pdf-serif-family",
    "TeX Gyre Termes",
    "--pdf-sans-family",
    "TeX Gyre Heros",
    "--pdf-mono-family",
    "TeX Gyre Cursor",
    "--pdf-standard-font",
    "serif",
    "--pdf-default-font-size",
    "12",
    "--pdf-mono-font-size",
    "10",
    "--unit",
    "inch",
]

_UNSET = object()
_calibre_command_cache: list[str] | None | object = _UNSET


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
    """Find a working Calibre ebook-convert command (cached)."""
    global _calibre_command_cache
    if _calibre_command_cache is not _UNSET:
        return _calibre_command_cache  # type: ignore[return-value]

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
            _calibre_command_cache = command
            return command

    _calibre_command_cache = None
    return None


def clear_calibre_command_cache() -> None:
    """Reset cached Calibre command (tests / diagnostics)."""
    global _calibre_command_cache
    _calibre_command_cache = _UNSET


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


def select_epubs(inbox_dir: Path, files: list[str] | None = None) -> list[Path]:
    """Return Inbox EPUBs, optionally filtered by --file patterns."""
    epubs = iter_epubs(inbox_dir)
    if not files:
        return epubs

    selected: list[Path] = []
    for pattern in files:
        needle = pattern.strip().lower()
        if not needle:
            continue
        needle_name = Path(needle).name
        matches = [
            path
            for path in epubs
            if needle_name == path.name.lower()
            or needle_name == path.stem.lower()
            or needle in path.name.lower()
        ]
        if not matches:
            raise FileNotFoundError(f"No EPUB in Inbox matches --file {pattern!r}")
        for path in matches:
            if path not in selected:
                selected.append(path)
    return selected


def build_plan(
    inbox_dir: Path,
    *,
    overwrite: bool,
    files: list[str] | None = None,
) -> list[ConversionPlan]:
    """Build a conversion plan for EPUB files in Inbox."""
    plans: list[ConversionPlan] = []
    for source in select_epubs(inbox_dir, files):
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


def _resolve_epub_member(names: list[str], opf_path: str, href: str) -> str | None:
    """Resolve an OPF href against package members."""
    href = href.split("#", 1)[0].strip()
    if not href:
        return None
    opf_dir = Path(opf_path).parent.as_posix()
    candidates = []
    if opf_dir in {"", "."}:
        candidates.append(href)
    else:
        candidates.append(f"{opf_dir}/{href}")
    candidates.append(href)
    normalized = {name: name for name in names}
    for candidate in candidates:
        cleaned = candidate.replace("\\", "/")
        while "/./" in cleaned:
            cleaned = cleaned.replace("/./", "/")
        if cleaned in normalized:
            return cleaned
        for name in names:
            if name.endswith("/" + cleaned) or name.endswith(cleaned):
                return name
    return None


def extract_epub_cover_bytes(source: Path) -> bytes | None:
    """Extract the EPUB cover image bytes when present."""
    try:
        with zipfile.ZipFile(source) as zf:
            names = zf.namelist()
            opf_names = [name for name in names if name.lower().endswith(".opf")]
            for opf_path in opf_names:
                opf = zf.read(opf_path).decode("utf-8", errors="replace")
                cover_id_match = re.search(
                    r'name=["\']cover["\'][^>]*content=["\']([^"\']+)["\']',
                    opf,
                    flags=re.IGNORECASE,
                )
                if cover_id_match is None:
                    cover_id_match = re.search(
                        r'content=["\']([^"\']+)["\'][^>]*name=["\']cover["\']',
                        opf,
                        flags=re.IGNORECASE,
                    )
                if cover_id_match is None:
                    continue
                cover_id = re.escape(cover_id_match.group(1))
                item_match = re.search(
                    rf'id=["\']{cover_id}["\'][^>]*href=["\']([^"\']+)["\']',
                    opf,
                    flags=re.IGNORECASE,
                )
                if item_match is None:
                    item_match = re.search(
                        rf'href=["\']([^"\']+)["\'][^>]*id=["\']{cover_id}["\']',
                        opf,
                        flags=re.IGNORECASE,
                    )
                if item_match is None:
                    continue
                member = _resolve_epub_member(names, opf_path, item_match.group(1))
                if member is not None:
                    return zf.read(member)

            for name in names:
                base = Path(name).name.lower()
                if base in {"cover.jpg", "cover.jpeg", "cover.png", "cover.webp"}:
                    return zf.read(name)
    except (OSError, zipfile.BadZipFile, KeyError):
        return None
    return None


def is_cover_like_page(page) -> bool:
    """Return True when a reflowed page is essentially a cover image."""
    text = (page.get_text() or "").strip()
    if len(text) > 80:
        return False
    try:
        images = page.get_images()
    except Exception:
        images = []
    if len(images) != 1:
        return False
    try:
        blocks = page.get_text("dict").get("blocks", [])
    except Exception:
        return True
    image_blocks = [block for block in blocks if block.get("type") == 1]
    if not image_blocks:
        return True
    bbox = image_blocks[0].get("bbox")
    if not bbox or len(bbox) != 4:
        return True
    image_area = max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])
    page_area = float(page.rect.width) * float(page.rect.height)
    if page_area <= 0:
        return True
    return (image_area / page_area) >= 0.35


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
        cover_bytes = extract_epub_cover_bytes(source)

        doc = fitz.open(source)
        try:
            # Full Letter layout once - no second "content box + remount margins"
            # pass, which crushed covers into a small centered rectangle.
            doc.layout(rect=fitz.Rect(0, 0, LETTER_WIDTH, LETTER_HEIGHT))
            if doc.page_count == 0:
                return "failed", "EPUB has no renderable pages"

            pdf_bytes = doc.convert_to_pdf()
        finally:
            doc.close()

        body_doc = fitz.open("pdf", pdf_bytes)
        output_doc = fitz.open()
        try:
            if cover_bytes:
                cover_page = output_doc.new_page(width=LETTER_WIDTH, height=LETTER_HEIGHT)
                cover_page.insert_image(
                    cover_page.rect,
                    stream=cover_bytes,
                    keep_proportion=True,
                )

            start = 0
            if cover_bytes:
                # Drop leading reflow pages that duplicate the cover art.
                while start < body_doc.page_count and is_cover_like_page(body_doc[start]):
                    start += 1
                    if start >= 3:
                        break

            for page_number in range(start, body_doc.page_count):
                page = output_doc.new_page(width=LETTER_WIDTH, height=LETTER_HEIGHT)
                page.show_pdf_page(page.rect, body_doc, page_number)

            # garbage=2 is much faster than 4 on large image-heavy books.
            output_doc.save(temp_path, garbage=2, deflate=True)
        finally:
            body_doc.close()
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
    engine: str = "pymupdf",
) -> tuple[str, str]:
    """Convert a single EPUB to a PDF file."""
    if target.exists() and not overwrite:
        return "skipped", "PDF already exists; use --overwrite to replace it"

    if engine not in {"auto", "calibre", "pymupdf"}:
        return "failed", f"Unknown conversion engine: {engine}"

    # Default / auto: prefer PyMuPDF (much faster). Calibre is optional quality path.
    if engine == "calibre":
        command = find_calibre_command()
        if not command:
            return "failed", "Calibre ebook-convert was not found"
        return convert_epub_to_pdf_with_calibre(source, target, command=command)

    if engine == "auto":
        # Prefer fast local PyMuPDF; only use Calibre when PyMuPDF is missing.
        try:
            import_fitz()
        except RuntimeError:
            command = find_calibre_command()
            if command:
                return convert_epub_to_pdf_with_calibre(source, target, command=command)
            return "failed", "Neither PyMuPDF nor Calibre ebook-convert is available"
        return convert_epub_to_pdf_with_pymupdf(source, target)

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
        report(f"Converting {total} book(s) with engine={engine}...")

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
        print("Tip: convert one book faster with:")
        print('  python scripts/cli.py epub-to-pdf --base-dir . --execute --file "Book Name"')


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", default=".", help="Project root directory")
    parser.add_argument("--inbox-dir", default="Inbox", help="Inbox directory under base-dir")
    parser.add_argument("--execute", action="store_true", help="Create PDF files")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing PDF outputs")
    parser.add_argument("--fail-fast", action="store_true", help="Stop after the first failure")
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        dest="files",
        metavar="NAME",
        help="Convert only EPUBs matching this name/substring. Repeatable.",
    )
    parser.add_argument(
        "--engine",
        choices=("auto", "calibre", "pymupdf"),
        default="pymupdf",
        help="Conversion engine. pymupdf is default (fast). calibre is slower, higher reflow quality",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()

    try:
        inbox_dir = resolve_inbox_dir(base_dir, args.inbox_dir)
        plans = build_plan(inbox_dir, overwrite=args.overwrite, files=args.files or None)
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
