import sys
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import tui  # noqa: E402


class TuiTests(unittest.TestCase):
    def test_unlock_pdfs_screen_runs_dry_run_then_execute(self) -> None:
        calls: list[tuple[str, list[str]]] = []

        def fake_run_script(script_name: str, args: list[str]) -> int:
            calls.append((script_name, args))
            return 0

        with (
            redirect_stdout(StringIO()),
            patch.object(tui, "clear"),
            patch.object(tui, "run_script", side_effect=fake_run_script),
            patch.object(tui, "confirm", return_value=True),
            patch.object(tui, "pause"),
        ):
            tui.screen_unlock_pdfs()

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], "unlock_pdfs.py")
        self.assertNotIn("--execute", calls[0][1])
        self.assertEqual(calls[1][0], "unlock_pdfs.py")
        self.assertIn("--execute", calls[1][1])

    def test_epub_to_pdf_screen_runs_dry_run_then_execute(self) -> None:
        calls: list[tuple[str, list[str]]] = []

        def fake_run_script(script_name: str, args: list[str]) -> int:
            calls.append((script_name, args))
            return 0

        with (
            redirect_stdout(StringIO()),
            patch.object(tui, "clear"),
            patch.object(tui, "run_script", side_effect=fake_run_script),
            patch.object(tui, "confirm", side_effect=[True, False]),
            patch.object(tui, "pause"),
        ):
            tui.screen_epub_to_pdf()

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], "epub_to_pdf.py")
        self.assertNotIn("--execute", calls[0][1])
        self.assertEqual(calls[1][0], "epub_to_pdf.py")
        self.assertIn("--execute", calls[1][1])
        self.assertNotIn("--overwrite", calls[1][1])

    def test_pdf_to_epub_screen_runs_dry_run_then_execute(self) -> None:
        calls: list[tuple[str, list[str]]] = []

        def fake_run_script(script_name: str, args: list[str]) -> int:
            calls.append((script_name, args))
            return 0

        with (
            redirect_stdout(StringIO()),
            patch.object(tui, "clear"),
            patch.object(tui, "run_script", side_effect=fake_run_script),
            patch.object(tui, "confirm", side_effect=[True, False]),
            patch.object(tui, "pause"),
        ):
            tui.screen_pdf_to_epub()

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], "pdf_to_epub.py")
        self.assertNotIn("--execute", calls[0][1])
        self.assertEqual(calls[1][0], "pdf_to_epub.py")
        self.assertIn("--execute", calls[1][1])
        self.assertNotIn("--overwrite", calls[1][1])


if __name__ == "__main__":
    unittest.main()
