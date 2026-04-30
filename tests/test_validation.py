import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.validation import validate_library  # noqa: E402


class ValidationTests(unittest.TestCase):
    def test_detects_topic_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cover = base / "site/assets/covers/Book.webp"
            cover.parent.mkdir(parents=True)
            cover.write_bytes(b"RIFFxxxxWEBP")
            data = [{
                "id": "abc",
                "title": "Book",
                "category": "Computer Science Fundamentals",
                "topic": "Programming Languages",
                "file_path": "Books/1_Computer_Science_Fundamentals/Programming_Languages/Java/Book.pdf",
                "cover": "assets/covers/Book.webp",
                "format": "pdf",
                "description": "",
                "download_url": "https://example.com/Book.pdf",
            }]
            data_path = base / "site/data.json"
            data_path.write_text(json.dumps(data), encoding="utf-8")

            result = validate_library(base, include_dependencies=False)

        codes = {issue["code"] for issue in result["errors"]}
        self.assertIn("topic_mismatch", codes)
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()

