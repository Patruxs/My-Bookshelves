import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from epub_to_pdf import build_plan, convert_epub_to_pdf, resolve_inbox_dir  # noqa: E402


class FakeEpubDocument:
    page_count = 2

    def convert_to_pdf(self) -> bytes:
        return b"fake-pdf-bytes"

    def close(self) -> None:
        pass


class FakePdfDocument:
    def save(self, path: Path, **_: object) -> None:
        path.write_bytes(b"%PDF-fake")

    def close(self) -> None:
        pass


class FakeFitz:
    def open(self, *args: object):
        if len(args) == 1:
            return FakeEpubDocument()
        if len(args) == 2 and args[0] == "pdf":
            return FakePdfDocument()
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

    def test_convert_epub_to_pdf_writes_pdf_with_existing_dependency_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Book.epub"
            target = Path(tmp) / "Book.pdf"
            source.write_bytes(b"fake epub")

            with patch("epub_to_pdf.import_fitz", return_value=FakeFitz()):
                status, message = convert_epub_to_pdf(source, target, overwrite=False)

            self.assertEqual(status, "converted")
            self.assertEqual(message, "EPUB converted to PDF")
            self.assertEqual(target.read_bytes(), b"%PDF-fake")


if __name__ == "__main__":
    unittest.main()
