import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pdf_to_epub import (  # noqa: E402
    ConversionPlan,
    build_plan,
    convert_pdf_to_epub,
    execute_plan,
    render_pdf_pages,
    resolve_inbox_dir,
    should_report_page,
)


class PdfToEpubTests(unittest.TestCase):
    def test_build_plan_detects_pdfs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "Inbox"
            inbox.mkdir()
            (inbox / "Book.pdf").write_bytes(b"%PDF")

            plan = build_plan(inbox, overwrite=False)

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].target.name, "Book.epub")
        self.assertEqual(plan[0].status, "planned")

    def test_build_plan_skips_existing_epub_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "Inbox"
            inbox.mkdir()
            (inbox / "Book.pdf").write_bytes(b"%PDF")
            (inbox / "Book.epub").write_bytes(b"epub")

            plan = build_plan(inbox, overwrite=False)

        self.assertEqual(plan[0].status, "skipped")

    def test_resolve_inbox_dir_rejects_path_outside_base_dir(self) -> None:
        with tempfile.TemporaryDirectory() as base_tmp, tempfile.TemporaryDirectory() as inbox_tmp:
            with self.assertRaises(ValueError):
                resolve_inbox_dir(Path(base_tmp).resolve(), inbox_tmp)

    def test_json_dry_run_reports_planned_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            inbox = base / "Inbox"
            inbox.mkdir()
            (inbox / "Book.pdf").write_bytes(b"%PDF")

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "pdf_to_epub.py"),
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
        self.assertEqual(payload["results"][0]["target"], "Inbox/Book.epub")

    def test_convert_pdf_to_epub_writes_valid_epub_zip(self) -> None:
        import fitz  # type: ignore[import-not-found]

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Book.pdf"
            target = Path(tmp) / "Book.epub"
            doc = fitz.open()
            page = doc.new_page(width=120, height=160)
            page.insert_text((20, 40), "Hello EPUB")
            doc.save(source)
            doc.close()

            status, message = convert_pdf_to_epub(source, target, overwrite=False, zoom=0.5)

            self.assertEqual(status, "converted")
            self.assertEqual(message, "PDF converted to image-based EPUB")
            with zipfile.ZipFile(target) as epub:
                names = set(epub.namelist())
                self.assertEqual(epub.read("mimetype"), b"application/epub+zip")
                package = epub.read("OEBPS/package.opf").decode("utf-8")
                self.assertIn("META-INF/container.xml", names)
                self.assertIn("OEBPS/package.opf", names)
                self.assertIn("OEBPS/nav.xhtml", names)
                self.assertIn("OEBPS/pages/page_0001.xhtml", names)
                self.assertIn("OEBPS/images/page_0001.png", names)
                self.assertIn('version="3.0"', package)
                self.assertIn('property="dcterms:modified"', package)

    def test_execute_plan_emits_book_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            inbox = base / "Inbox"
            inbox.mkdir()
            source_one = inbox / "Book_One.pdf"
            source_two = inbox / "Book_Two.pdf"
            target_one = inbox / "Book_One.epub"
            target_two = inbox / "Book_Two.epub"
            source_one.write_bytes(b"%PDF")
            source_two.write_bytes(b"%PDF")
            target_two.write_bytes(b"epub")

            plans = [
                ConversionPlan(
                    source=source_one,
                    target=target_one,
                    status="planned",
                    message="Convert PDF to image-based EPUB",
                ),
                ConversionPlan(
                    source=source_two,
                    target=target_two,
                    status="skipped",
                    message="EPUB already exists; use --overwrite to replace it",
                ),
            ]
            messages: list[str] = []

            with patch(
                "pdf_to_epub.convert_pdf_to_epub",
                return_value=("converted", "ok"),
            ) as convert_mock:
                results = execute_plan(
                    plans,
                    base,
                    overwrite=False,
                    zoom=1.5,
                    progress=messages.append,
                )

            convert_mock.assert_called_once()
            self.assertEqual([result.status for result in results], ["converted", "skipped"])
            self.assertEqual(messages[0], "Converting 2 book(s)...")
            self.assertEqual(messages[1], "[1/2] converting Book_One.pdf -> Book_One.epub")
            self.assertEqual(messages[2], "[1/2] done: converted - ok")
            self.assertIn("[2/2] skip Book_Two.pdf", messages[3])
            self.assertEqual(messages[-1], "Done.")

    def test_render_pdf_pages_calls_on_page(self) -> None:
        import fitz  # type: ignore[import-not-found]

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Book.pdf"
            doc = fitz.open()
            for text in ("Page one", "Page two"):
                page = doc.new_page(width=120, height=160)
                page.insert_text((20, 40), text)
            doc.save(source)
            doc.close()

            calls: list[tuple[int, int]] = []
            pages = render_pdf_pages(source, zoom=0.5, on_page=lambda cur, tot: calls.append((cur, tot)))

            self.assertEqual(len(pages), 2)
            self.assertEqual(calls, [(1, 2), (2, 2)])

    def test_should_report_page_throttles_updates(self) -> None:
        self.assertTrue(should_report_page(1, 1))
        self.assertTrue(should_report_page(1, 20))
        self.assertTrue(should_report_page(20, 20))
        self.assertTrue(should_report_page(10, 20))
        self.assertFalse(should_report_page(3, 20))
        self.assertTrue(should_report_page(1, 100))
        self.assertTrue(should_report_page(100, 100))
        self.assertTrue(should_report_page(50, 100))
        self.assertFalse(should_report_page(3, 100))


if __name__ == "__main__":
    unittest.main()
