import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/fetch-sources.py"


class SourceVerification(unittest.TestCase):
    def fetch(self, root, expected):
        lock = root / "lock.json"
        lock.write_text(json.dumps({"example": {"version": "1", "archive": "source.bin",
                                                "url": (root / "upstream").as_uri(), "sha256": expected}}))
        return subprocess.run([sys.executable, str(SCRIPT), "--lock", str(lock),
                               "--output", str(root / "cache"), "example"], capture_output=True, text=True)

    def test_valid_download_and_offline_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "upstream").write_bytes(b"verified source")
            digest = hashlib.sha256(b"verified source").hexdigest()
            self.assertEqual(self.fetch(root, digest).returncode, 0)
            (root / "upstream").unlink()
            self.assertEqual(self.fetch(root, digest).returncode, 0)
            self.assertEqual((root / "cache/source.bin").read_bytes(), b"verified source")

    def test_corrupt_cached_source_is_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "upstream").write_bytes(b"verified source")
            (root / "cache").mkdir()
            (root / "cache/source.bin").write_bytes(b"corrupt")
            self.assertEqual(self.fetch(root, hashlib.sha256(b"verified source").hexdigest()).returncode, 0)
            self.assertEqual((root / "cache/source.bin").read_bytes(), b"verified source")

    def test_mismatched_download_is_never_installed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "upstream").write_bytes(b"unexpected data")
            result = self.fetch(root, "0" * 64)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("checksum mismatch", result.stderr)
            self.assertEqual(list((root / "cache").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
