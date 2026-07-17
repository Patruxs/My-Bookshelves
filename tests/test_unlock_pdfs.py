import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from unlock_pdfs import (  # noqa: E402
    read_password_file,
    resolve_inbox_dir,
    resolve_password,
)


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

    def test_read_password_file_allows_spaces_around_equals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            password_file = Path(tmp) / ".env"
            password_file.write_text(
                "PDF_UNLOCK_PASSWORD = spaced-secret\n",
                encoding="utf-8",
            )

            self.assertEqual(read_password_file(password_file), "spaced-secret")

    def test_resolve_password_reads_project_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            (base / ".env").write_text(
                "PDF_UNLOCK_PASSWORD=from-dotenv\n",
                encoding="utf-8",
            )
            env = {
                key: value
                for key, value in os.environ.items()
                if key not in ("PDF_UNLOCK_PASSWORD", "PDF_PASSWORD")
            }
            with mock.patch.dict(os.environ, env, clear=True):
                password, source = resolve_password(base, None, prompt=False)

            self.assertEqual(password, "from-dotenv")
            self.assertTrue(source.endswith(".env"))

    def test_resolve_password_prefers_dedicated_unlock_file_over_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            (base / ".env.pdf-unlock").write_text(
                "PDF_UNLOCK_PASSWORD=from-unlock-file\n",
                encoding="utf-8",
            )
            (base / ".env").write_text(
                "PDF_UNLOCK_PASSWORD=from-dotenv\n",
                encoding="utf-8",
            )
            env = {
                key: value
                for key, value in os.environ.items()
                if key not in ("PDF_UNLOCK_PASSWORD", "PDF_PASSWORD")
            }
            with mock.patch.dict(os.environ, env, clear=True):
                password, source = resolve_password(base, None, prompt=False)

            self.assertEqual(password, "from-unlock-file")
            self.assertTrue(source.endswith(".env.pdf-unlock"))

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
