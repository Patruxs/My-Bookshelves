import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UploadDryRunTests(unittest.TestCase):
    def test_upload_dry_run_does_not_create_covers_or_mutate_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            book = base / "Books/1_Test_Category/Test_Topic/Fake_Book.pdf"
            book.parent.mkdir(parents=True)
            book.write_bytes(b"%PDF-1.4 fake")
            data_path = base / "site/data.json"
            data_path.parent.mkdir(parents=True)
            data_path.write_text("[]", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/upload_releases.py"),
                    "--base-dir",
                    str(base),
                    "--dry-run",
                    "--json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(data_path.read_text(encoding="utf-8")), [])
            self.assertFalse((base / "site/assets/covers/Fake_Book.webp").exists())


if __name__ == "__main__":
    unittest.main()
