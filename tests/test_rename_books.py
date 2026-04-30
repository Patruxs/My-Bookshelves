import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rename_books import scan_and_plan, slugify_filename  # noqa: E402


class RenameBooksTests(unittest.TestCase):
    def test_slugify_vietnamese_filename(self) -> None:
        self.assertEqual(
            slugify_filename("Kiến trúc ứng dụng web.epub"),
            "Kien_truc_ung_dung_web.epub",
        )

    def test_scan_and_plan_detects_needed_rename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            inbox = base / "Inbox"
            inbox.mkdir()
            (inbox / "Go With Domain.pdf").write_bytes(b"%PDF-1.4")

            plan = scan_and_plan(base)

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["new_name"], "Go_With_Domain.pdf")


if __name__ == "__main__":
    unittest.main()

