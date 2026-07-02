#!/usr/bin/env python3
"""Convert PDF files in Inbox to image-based EPUB files."""

from __future__ import annotations

import argparse
import html
import os
import sys
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from lib.output import emit_json

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass
class ConversionPlan:
    """Planned PDF to EPUB conversion."""

    source: Path
    target: Path
    status: str
    message: str


@dataclass
class ConversionResult:
    """Result for one PDF to EPUB conversion."""

    source: str
    target: str
    status: str
    message: str


@dataclass
class RenderedPage:
    """One rendered PDF page for EPUB packaging."""

    index: int
    image_name: str
    width: int
    height: int
    image_bytes: bytes


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


def iter_pdfs(inbox_dir: Path) -> list[Path]:
    """Return PDF files directly under Inbox."""
    return sorted(path for path in inbox_dir.iterdir() if path.suffix.lower() == ".pdf")


def build_plan(inbox_dir: Path, *, overwrite: bool) -> list[ConversionPlan]:
    """Build a conversion plan for PDF files in Inbox."""
    plans: list[ConversionPlan] = []
    for source in iter_pdfs(inbox_dir):
        target = source.with_suffix(".epub")
        if target.exists() and not overwrite:
            plans.append(
                ConversionPlan(
                    source=source,
                    target=target,
                    status="skipped",
                    message="EPUB already exists; use --overwrite to replace it",
                )
            )
            continue

        status = "planned"
        message = "Convert PDF to image-based EPUB"
        if target.exists() and overwrite:
            message = "Convert PDF to EPUB and overwrite existing EPUB"
        plans.append(ConversionPlan(source=source, target=target, status=status, message=message))

    return plans


def render_pdf_pages(source: Path, *, zoom: float) -> list[RenderedPage]:
    """Render PDF pages to PNG images for EPUB packaging."""
    fitz = import_fitz()
    doc = fitz.open(source)
    pages: list[RenderedPage] = []

    try:
        if doc.needs_pass:
            raise RuntimeError("PDF is password-protected; unlock it before converting")
        if doc.page_count == 0:
            raise RuntimeError("PDF has no renderable pages")

        matrix = fitz.Matrix(zoom, zoom)
        for index, page in enumerate(doc, 1):
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pages.append(
                RenderedPage(
                    index=index,
                    image_name=f"page_{index:04d}.png",
                    width=pix.width,
                    height=pix.height,
                    image_bytes=pix.tobytes("png"),
                )
            )
    finally:
        doc.close()

    return pages


def page_xhtml(page: RenderedPage, title: str) -> str:
    """Build one XHTML page containing a rendered PDF page image."""
    escaped_title = html.escape(title)
    alt = html.escape(f"{title} page {page.index}")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <title>{escaped_title} - Page {page.index}</title>
  <link rel="stylesheet" type="text/css" href="../styles/style.css"/>
</head>
<body>
  <main>
    <img src="../images/{page.image_name}" alt="{alt}" width="{page.width}" height="{page.height}"/>
  </main>
</body>
</html>
"""


def package_opf(
    title: str,
    identifier: str,
    modified: str,
    pages: list[RenderedPage],
) -> str:
    """Build EPUB package metadata."""
    escaped_title = html.escape(title)
    image_items = "\n".join(
        f'    <item id="img-{page.index}" href="images/{page.image_name}" media-type="image/png"/>'
        for page in pages
    )
    page_items = "\n".join(
        f'    <item id="page-{page.index}" href="pages/page_{page.index:04d}.xhtml" media-type="application/xhtml+xml"/>'
        for page in pages
    )
    spine_items = "\n".join(f'    <itemref idref="page-{page.index}"/>' for page in pages)

    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{identifier}</dc:identifier>
    <dc:title>{escaped_title}</dc:title>
    <dc:language>en</dc:language>
    <meta property="dcterms:modified">{modified}</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="style" href="styles/style.css" media-type="text/css"/>
{page_items}
{image_items}
  </manifest>
  <spine>
{spine_items}
  </spine>
</package>
"""


def nav_xhtml(title: str, pages: list[RenderedPage]) -> str:
    """Build EPUB navigation document."""
    escaped_title = html.escape(title)
    links = "\n".join(
        f'      <li><a href="pages/page_{page.index:04d}.xhtml">Page {page.index}</a></li>'
        for page in pages
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head>
  <title>{escaped_title}</title>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>{escaped_title}</h1>
    <ol>
{links}
    </ol>
  </nav>
</body>
</html>
"""


def stylesheet() -> str:
    """Build compact CSS for page-image EPUB output."""
    return """html, body {
  margin: 0;
  padding: 0;
  background: #ffffff;
}

main {
  margin: 0;
  padding: 0;
  text-align: center;
}

img {
  display: block;
  width: 100%;
  height: auto;
  margin: 0 auto;
}
"""


def write_epub(target: Path, title: str, pages: list[RenderedPage]) -> None:
    """Write an EPUB 3 archive."""
    identifier = f"urn:uuid:{uuid.uuid4()}"
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with zipfile.ZipFile(target, "w") as epub:
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        epub.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        epub.writestr("OEBPS/package.opf", package_opf(title, identifier, modified, pages))
        epub.writestr("OEBPS/nav.xhtml", nav_xhtml(title, pages))
        epub.writestr("OEBPS/styles/style.css", stylesheet())
        for page in pages:
            epub.writestr(f"OEBPS/pages/page_{page.index:04d}.xhtml", page_xhtml(page, title))
            epub.writestr(f"OEBPS/images/{page.image_name}", page.image_bytes)


def convert_pdf_to_epub(
    source: Path,
    target: Path,
    *,
    overwrite: bool,
    zoom: float,
) -> tuple[str, str]:
    """Convert a single PDF to an image-based EPUB file."""
    if target.exists() and not overwrite:
        return "skipped", "EPUB already exists; use --overwrite to replace it"
    if zoom <= 0:
        return "failed", "--zoom must be greater than 0"

    temp_path = target.with_name(f".{target.stem}.converting{target.suffix}")
    if temp_path.exists():
        temp_path.unlink()

    try:
        pages = render_pdf_pages(source, zoom=zoom)
        write_epub(temp_path, source.stem, pages)
        os.replace(temp_path, target)
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        return "failed", f"Conversion failed: {exc}"

    return "converted", "PDF converted to image-based EPUB"


def execute_plan(
    plans: list[ConversionPlan],
    base_dir: Path,
    *,
    overwrite: bool,
    zoom: float,
) -> list[ConversionResult]:
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

        status, message = convert_pdf_to_epub(
            plan.source,
            plan.target,
            overwrite=overwrite,
            zoom=zoom,
        )
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
    print("My Bookshelves PDF to EPUB Converter")
    print("=" * 60)
    print(f"Mode: {'dry-run' if dry_run else 'execute'}")
    print()

    if not results:
        print("No PDF files found.")
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
        print("No files changed. Add --execute to create EPUBs.")


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", default=".", help="Project root directory")
    parser.add_argument("--inbox-dir", default="Inbox", help="Inbox directory under base-dir")
    parser.add_argument("--execute", action="store_true", help="Create EPUB files")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing EPUB outputs")
    parser.add_argument("--fail-fast", action="store_true", help="Stop after the first failure")
    parser.add_argument("--zoom", type=float, default=1.5, help="PDF render zoom for page images")
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
                    result = execute_plan(
                        [plan],
                        base_dir,
                        overwrite=args.overwrite,
                        zoom=args.zoom,
                    )[0]
                    results.append(result)
                    if result.status == "failed":
                        break
            else:
                results = execute_plan(
                    plans,
                    base_dir,
                    overwrite=args.overwrite,
                    zoom=args.zoom,
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
