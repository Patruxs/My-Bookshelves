import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pdf_to_epub import build_plan, convert_pdf_to_epub, resolve_inbox_dir  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
