import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GenerateDataTests(unittest.TestCase):
    def test_generate_preserves_metadata_and_removes_stale_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            book = base / "Books/1_Test_Category/Test_Topic/Fake_Book.pdf"
            book.parent.mkdir(parents=True)
            book.write_bytes(b"%PDF-1.4 fake")
            data_path = base / "site/data.json"
            data_path.parent.mkdir(parents=True)
            data_path.write_text(
                json.dumps([
                    {
                        "id": "old",
                        "title": "Fake_Book",
                        "category": "Test Category",
                        "topic": "Test Topic",
                        "file_path": "Books/1_Test_Category/Test_Topic/Fake_Book.pdf",
                        "cover": "",
                        "format": "pdf",
                        "description": "Existing description",
                        "download_url": "https://example.com/Fake_Book.pdf",
                    },
                    {
                        "id": "stale",
                        "title": "Old_Book",
                        "category": "Test Category",
                        "topic": "Test Topic",
                        "file_path": "Books/1_Test_Category/Test_Topic/Old_Book.pdf",
                        "cover": "",
                        "format": "pdf",
                        "description": "Stale",
                        "download_url": "https://example.com/Old_Book.pdf",
                    },
                ]),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/generate_data.py"),
                    "--base-dir",
                    str(base),
                    "--json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["description"], "Existing description")
            self.assertEqual(data[0]["download_url"], "https://example.com/Fake_Book.pdf")


if __name__ == "__main__":
    unittest.main()

