import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from epub_to_pdf import (  # noqa: E402
    CALIBRE_PDF_OPTIONS,
    LETTER_HEIGHT,
    LETTER_WIDTH,
    ConversionPlan,
    build_plan,
    convert_epub_to_pdf,
    execute_plan,
    extract_epub_cover_bytes,
    resolve_inbox_dir,
    select_epubs,
)


class FakeRect:
    def __init__(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


class FakeEpubDocument:
    page_count = 2
    layout_rect: FakeRect | None = None

    def layout(self, *, rect: FakeRect) -> None:
        self.layout_rect = rect

    def convert_to_pdf(self) -> bytes:
        if self.layout_rect is None:
            raise AssertionError("EPUB document was not laid out before conversion")
        self.layout_rect_used = self.layout_rect
        return b"fake-pdf-bytes"

    def close(self) -> None:
        pass


class FakeBodyPage:
    def __init__(self) -> None:
        self.rect = FakeRect(0, 0, LETTER_WIDTH, LETTER_HEIGHT)

    def get_text(self, *args: object, **_: object):
        if args and args[0] == "dict":
            return {
                "blocks": [
                    {
                        "type": 0,
                        "lines": [{"spans": [{"text": "Chapter body text for testing"}]}],
                    }
                ]
            }
        return "Chapter body text for testing " * 3

    def get_images(self):
        return []


class FakeConvertedPdfDocument:
    page_count = 2

    def __getitem__(self, index: int) -> FakeBodyPage:
        if index < 0 or index >= self.page_count:
            raise IndexError(index)
        return FakeBodyPage()

    def close(self) -> None:
        pass


class FakeOutputPage:
    def __init__(self) -> None:
        self.rect = FakeRect(0, 0, LETTER_WIDTH, LETTER_HEIGHT)
        self.show_calls: list[tuple[FakeRect, object, int]] = []
        self.insert_image_calls: list[tuple[FakeRect, bytes | None]] = []

    def show_pdf_page(self, rect: FakeRect, pdf_doc: object, page_number: int) -> None:
        self.show_calls.append((rect, pdf_doc, page_number))

    def insert_image(self, rect: FakeRect, stream: bytes | None = None, **_: object) -> None:
        self.insert_image_calls.append((rect, stream))


class FakeOutputPdfDocument:
    def __init__(self) -> None:
        self.pages: list[FakeOutputPage] = []

    def new_page(self, *, width: float, height: float) -> FakeOutputPage:
        if (width, height) != (LETTER_WIDTH, LETTER_HEIGHT):
            raise AssertionError(f"Unexpected output page size: {(width, height)!r}")
        page = FakeOutputPage()
        self.pages.append(page)
        return page

    def save(self, path: Path, **_: object) -> None:
        # Without an EPUB cover, all body pages are remounted full-bleed.
        if len(self.pages) != FakeConvertedPdfDocument.page_count:
            raise AssertionError(f"Unexpected page count: {len(self.pages)!r}")
        for page in self.pages:
            if not page.show_calls:
                raise AssertionError("Output page has no placed content")
            rect = page.show_calls[0][0]
            if rect.as_tuple() != (0.0, 0.0, LETTER_WIDTH, LETTER_HEIGHT):
                raise AssertionError(f"Unexpected content placement: {rect.as_tuple()!r}")
        path.write_bytes(b"%PDF-fake")

    def close(self) -> None:
        pass


class FakeFitz:
    Rect = FakeRect

    def open(self, *args: object):
        if len(args) == 0:
            return FakeOutputPdfDocument()
        if len(args) == 1:
            doc = FakeEpubDocument()
            self.epub_doc = doc
            return doc
        if len(args) == 2 and args[0] == "pdf":
            return FakeConvertedPdfDocument()
        raise AssertionError(f"Unexpected fitz.open arguments: {args!r}")


class EpubToPdfTests(unittest.TestCase):
    def test_build_plan_detects_epubs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "Inbox"
            inbox.mkdir()
            (inbox / "Acing the System Design Interview.epub").write_bytes(b"fake")

            plan = build_plan(inbox, overwrite=False)

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].target.name, "Acing the System Design Interview.pdf")
        self.assertEqual(plan[0].status, "planned")

    def test_select_epubs_filters_by_substring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "Inbox"
            inbox.mkdir()
            (inbox / "React Quickly, Second Edition.epub").write_bytes(b"fake")
            (inbox / "Other Book.epub").write_bytes(b"fake")

            selected = select_epubs(inbox, ["React Quickly"])

        self.assertEqual([path.name for path in selected], ["React Quickly, Second Edition.epub"])

    def test_build_plan_honors_file_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "Inbox"
            inbox.mkdir()
            (inbox / "React Quickly, Second Edition.epub").write_bytes(b"fake")
            (inbox / "Other Book.epub").write_bytes(b"fake")

            plan = build_plan(inbox, overwrite=False, files=["React Quickly"])

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].source.name, "React Quickly, Second Edition.epub")

    def test_build_plan_skips_existing_pdf_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "Inbox"
            inbox.mkdir()
            (inbox / "Book.epub").write_bytes(b"fake")
            (inbox / "Book.pdf").write_bytes(b"%PDF")

            plan = build_plan(inbox, overwrite=False)

        self.assertEqual(plan[0].status, "skipped")

    def test_resolve_inbox_dir_rejects_path_outside_base_dir(self) -> None:
        with tempfile.TemporaryDirectory() as base_tmp, tempfile.TemporaryDirectory() as inbox_tmp:
            with self.assertRaises(ValueError):
                resolve_inbox_dir(Path(base_tmp).resolve(), inbox_tmp)

    def test_json_dry_run_reports_planned_epub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            inbox = base / "Inbox"
            inbox.mkdir()
            (inbox / "Book.epub").write_bytes(b"fake")

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "epub_to_pdf.py"),
                    "--base-dir",
                    str(base),
                    "--json",
                ],
                capture_output=True,
                encoding="utf-8",
                check=False,
            )

        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["results"][0]["status"], "planned")
        self.assertEqual(payload["results"][0]["target"], "Inbox/Book.pdf")

    def test_convert_epub_to_pdf_uses_pymupdf_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Book.epub"
            target = Path(tmp) / "Book.pdf"
            source.write_bytes(b"fake epub")

            fake_fitz = FakeFitz()
            with patch("epub_to_pdf.import_fitz", return_value=fake_fitz):
                status, message = convert_epub_to_pdf(source, target, overwrite=False)

            self.assertEqual(status, "converted")
            self.assertEqual(message, "EPUB converted to PDF with PyMuPDF")
            self.assertEqual(target.read_bytes(), b"%PDF-fake")

    def test_convert_epub_to_pdf_uses_calibre_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Book.epub"
            target = Path(tmp) / "Book.pdf"
            source.write_bytes(b"fake epub")

            def fake_run(cmd: list[str], **_: object):
                self.assertEqual(cmd[:3], ["ebook-convert", str(source), str(target.with_name(".Book.converting.pdf"))])
                self.assertEqual(cmd[3:], CALIBRE_PDF_OPTIONS)
                target.with_name(".Book.converting.pdf").write_bytes(b"%PDF-calibre")
                return subprocess.CompletedProcess(cmd, 0, "", "")

            with (
                patch("epub_to_pdf.find_calibre_command", return_value=["ebook-convert"]),
                patch("epub_to_pdf.subprocess.run", side_effect=fake_run),
            ):
                status, message = convert_epub_to_pdf(
                    source,
                    target,
                    overwrite=False,
                    engine="calibre",
                )

            self.assertEqual(status, "converted")
            self.assertEqual(message, "EPUB converted to PDF with Calibre")
            self.assertEqual(target.read_bytes(), b"%PDF-calibre")

    def test_convert_epub_to_pdf_fallback_writes_letter_pdf_with_pymupdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Book.epub"
            target = Path(tmp) / "Book.pdf"
            source.write_bytes(b"fake epub")

            fake_fitz = FakeFitz()
            with patch("epub_to_pdf.import_fitz", return_value=fake_fitz):
                status, message = convert_epub_to_pdf(
                    source,
                    target,
                    overwrite=False,
                    engine="pymupdf",
                )

            self.assertEqual(status, "converted")
            self.assertEqual(message, "EPUB converted to PDF with PyMuPDF")
            self.assertEqual(target.read_bytes(), b"%PDF-fake")
            self.assertEqual(
                fake_fitz.epub_doc.layout_rect_used.as_tuple(),
                (0, 0, LETTER_WIDTH, LETTER_HEIGHT),
            )

    def test_extract_epub_cover_bytes_reads_opf_cover(self) -> None:
        import io
        import zipfile

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Book.epub"
            cover = b"\xff\xd8\xffcover-bytes"
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                zf.writestr(
                    "OEBPS/content.opf",
                    """<?xml version="1.0"?>
<package>
  <metadata>
    <meta name="cover" content="cover"/>
  </metadata>
  <manifest>
    <item id="cover" href="cover.jpeg" media-type="image/jpeg"/>
  </manifest>
</package>
""",
                )
                zf.writestr("OEBPS/cover.jpeg", cover)
            source.write_bytes(buf.getvalue())

            extracted = extract_epub_cover_bytes(source)

        self.assertEqual(extracted, cover)

    def test_real_epub_conversion_outputs_letter_pages(self) -> None:
        import fitz  # type: ignore[import-not-found]

        source = ROOT / "Inbox" / "Acing the System Design Interview.epub"
        if not source.exists():
            self.skipTest("sample Inbox EPUB is not available")

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "Acing the System Design Interview.pdf"

            status, message = convert_epub_to_pdf(
                source,
                target,
                overwrite=False,
                engine="pymupdf",
            )

            self.assertEqual(status, "converted")
            self.assertEqual(message, "EPUB converted to PDF with PyMuPDF")
            doc = fitz.open(target)
            try:
                self.assertGreater(doc.page_count, 0)
                page_sizes = {
                    tuple(round(value, 2) for value in page.rect)
                    for page in doc
                }
                self.assertEqual(page_sizes, {(0.0, 0.0, LETTER_WIDTH, LETTER_HEIGHT)})
            finally:
                doc.close()

    def test_execute_plan_emits_book_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            inbox = base / "Inbox"
            inbox.mkdir()
            source_one = inbox / "Book_One.epub"
            source_two = inbox / "Book_Two.epub"
            target_one = inbox / "Book_One.pdf"
            target_two = inbox / "Book_Two.pdf"
            source_one.write_bytes(b"fake")
            source_two.write_bytes(b"fake")
            target_two.write_bytes(b"%PDF")

            plans = [
                ConversionPlan(
                    source=source_one,
                    target=target_one,
                    status="planned",
                    message="Convert EPUB to PDF",
                ),
                ConversionPlan(
                    source=source_two,
                    target=target_two,
                    status="skipped",
                    message="PDF already exists; use --overwrite to replace it",
                ),
            ]
            messages: list[str] = []

            with patch(
                "epub_to_pdf.convert_epub_to_pdf",
                return_value=("converted", "ok"),
            ) as convert_mock:
                results = execute_plan(
                    plans,
                    base,
                    overwrite=False,
                    engine="auto",
                    progress=messages.append,
                )

            convert_mock.assert_called_once()
            self.assertEqual([result.status for result in results], ["converted", "skipped"])
            self.assertEqual(messages[0], "Converting 2 book(s) with engine=auto...")
            self.assertEqual(messages[1], "[1/2] converting Book_One.epub -> Book_One.pdf")
            self.assertEqual(messages[2], "[1/2] done: converted - ok")
            self.assertIn("[2/2] skip Book_Two.epub", messages[3])
            self.assertEqual(messages[-1], "Done.")

    def test_execute_plan_fail_fast_stops_with_correct_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            inbox = base / "Inbox"
            inbox.mkdir()
            plans = []
            for name in ("One", "Two", "Three"):
                source = inbox / f"{name}.epub"
                target = inbox / f"{name}.pdf"
                source.write_bytes(b"fake")
                plans.append(
                    ConversionPlan(
                        source=source,
                        target=target,
                        status="planned",
                        message="Convert EPUB to PDF",
                    )
                )

            messages: list[str] = []
            with patch(
                "epub_to_pdf.convert_epub_to_pdf",
                return_value=("failed", "boom"),
            ) as convert_mock:
                results = execute_plan(
                    plans,
                    base,
                    overwrite=False,
                    engine="auto",
                    fail_fast=True,
                    progress=messages.append,
                )

            convert_mock.assert_called_once()
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, "failed")
            self.assertIn("[1/3] converting One.epub -> One.pdf", messages)
            self.assertIn("[1/3] done: failed - boom", messages)
            self.assertTrue(all("[2/3]" not in line for line in messages))
            self.assertEqual(messages[-1], "Done.")


if __name__ == "__main__":
    unittest.main()
