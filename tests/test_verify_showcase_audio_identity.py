"""Tests for exact-byte audio provenance before native footage reuse."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "verify_showcase_audio_identity",
    Path(__file__).resolve().parents[1] / "tools" / "verify_showcase_audio_identity.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class AudioIdentityTests(unittest.TestCase):
    def test_exact_source_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "music.mp3"
            path.write_bytes(b"original music")
            digest = hashlib.sha256(b"original music").hexdigest()
            self.assertTrue(MODULE.verify(path, digest)["passed"])

    def test_same_name_different_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "music.mp3"
            path.write_bytes(b"alternate export")
            digest = hashlib.sha256(b"original music").hexdigest()
            result = MODULE.verify(path, digest)
            self.assertFalse(result["passed"])
            self.assertIn("reuse prohibited", result["reason"])

    def test_missing_file_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = MODULE.verify(Path(directory) / "missing.mp3", "a" * 64)
            self.assertFalse(result["passed"])

    def test_invalid_hash_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.verify("unused", "not-a-hash")

if __name__ == "__main__":
    unittest.main()
