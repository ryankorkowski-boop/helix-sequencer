"""Regression coverage for fail-closed showcase recovery inventory."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "audit_showcase_artifacts",
    Path(__file__).resolve().parents[1] / "tools" / "audit_showcase_artifacts.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class ArtifactAuditTests(unittest.TestCase):
    def test_matching_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "clip.mp4").write_bytes(b"native footage")
            expected = hashlib.sha256(b"native footage").hexdigest()
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps([{"path": "clip.mp4", "sha256": expected}]))
            self.assertEqual(MODULE.audit(root, manifest)["verified"], 1)

    def test_missing_artifact_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps([{"path": "missing.mp4", "sha256": "a" * 64}]))
            self.assertFalse(MODULE.audit(root, manifest)["passed"])

    def test_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "clip.mp4").write_bytes(b"wrong")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps([{"path": "clip.mp4", "sha256": "a" * 64}]))
            self.assertFalse(MODULE.audit(root, manifest)["passed"])

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps([{"path": "../escape.mp4", "sha256": "a" * 64}]))
            self.assertFalse(MODULE.audit(root, manifest)["passed"])

    def test_non_object_record_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps([None, "invalid", 5]))
            result = MODULE.audit(root, manifest)
            self.assertFalse(result["passed"])
            self.assertEqual(result["total"], 3)

    def test_empty_inventory_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text("[]")
            self.assertFalse(MODULE.audit(root, manifest)["passed"])

if __name__ == "__main__":
    unittest.main()
