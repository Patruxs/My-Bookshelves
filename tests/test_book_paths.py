import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.book_paths import (  # noqa: E402
    expected_display_from_file_path,
    generate_book_id,
    metadata_from_book_path,
)


class BookPathTests(unittest.TestCase):
    def test_nested_topic_display_name(self) -> None:
        file_path = "Books/1_Computer_Science_Fundamentals/Programming_Languages/Java/Head_First_Java.pdf"

        category, topic = expected_display_from_file_path(file_path)

        self.assertEqual(category, "Computer Science Fundamentals")
        self.assertEqual(topic, "Programming Languages/Java")

    def test_metadata_from_book_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            book = base / "Books/2_Software_Engineering/DevOps/Continuous_Delivery.pdf"
            book.parent.mkdir(parents=True)
            book.write_bytes(b"%PDF-1.4")

            metadata = metadata_from_book_path(base, book)

        self.assertEqual(metadata["rel_path"], "Books/2_Software_Engineering/DevOps/Continuous_Delivery.pdf")
        self.assertEqual(metadata["category"], "Software Engineering")
        self.assertEqual(metadata["topic"], "DevOps")
        self.assertEqual(metadata["format"], "pdf")

    def test_book_id_is_stable(self) -> None:
        path = "Books/1_Cat/Topic/File.pdf"
        self.assertEqual(generate_book_id(path), generate_book_id(path))
        self.assertEqual(len(generate_book_id(path)), 12)


if __name__ == "__main__":
    unittest.main()

