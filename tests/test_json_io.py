import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.json_io import load_json, write_json_atomic  # noqa: E402


class JsonIoTests(unittest.TestCase):
    def test_atomic_write_creates_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.json"
            path.write_text(json.dumps([{"old": True}]), encoding="utf-8")

            backup = write_json_atomic(path, [{"new": True}], backup=True)

            self.assertIsNotNone(backup)
            self.assertTrue(backup.exists())
            self.assertEqual(load_json(path), [{"new": True}])
            self.assertEqual(load_json(backup), [{"old": True}])

    def test_missing_json_returns_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_json(Path(tmp) / "missing.json", default=[]), [])


if __name__ == "__main__":
    unittest.main()

