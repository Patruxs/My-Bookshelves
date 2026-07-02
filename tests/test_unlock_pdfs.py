import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from unlock_pdfs import read_password_file, resolve_inbox_dir  # noqa: E402


class UnlockPdfsTests(unittest.TestCase):
    def test_resolve_inbox_dir_allows_path_under_base_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            inbox = base / "Inbox"
            inbox.mkdir()

            self.assertEqual(resolve_inbox_dir(base, "Inbox"), inbox)
            self.assertEqual(resolve_inbox_dir(base, str(inbox)), inbox)

    def test_resolve_inbox_dir_rejects_path_outside_base_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            outside = base.parent / f"{base.name}_outside"
            outside.mkdir()
            try:
                with self.assertRaises(ValueError):
                    resolve_inbox_dir(base, str(outside))
            finally:
                outside.rmdir()

    def test_read_password_file_supports_env_style_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            password_file = Path(tmp) / ".env.pdf-unlock"
            password_file.write_text(
                'PDF_UNLOCK_PASSWORD="local-secret"\n',
                encoding="utf-8",
            )

            self.assertEqual(read_password_file(password_file), "local-secret")

    def test_out_of_tree_inbox_dir_returns_json_error(self) -> None:
        with tempfile.TemporaryDirectory() as base_tmp, tempfile.TemporaryDirectory() as inbox_tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "unlock_pdfs.py"),
                    "--base-dir",
                    base_tmp,
                    "--inbox-dir",
                    inbox_tmp,
                    "--json",
                ],
                capture_output=True,
                encoding="utf-8",
                check=False,
            )

        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload["ok"])
        self.assertIn("--inbox-dir must be inside --base-dir", payload["error"])


if __name__ == "__main__":
    unittest.main()
