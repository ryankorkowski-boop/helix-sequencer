"""Verify ZIP evidence is not mistaken for source-verified musical showcases."""
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "verify_native_proof_archive",
    Path(__file__).resolve().parents[1] / "tools" / "verify_native_proof_archive.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class NativeProofArchiveTests(unittest.TestCase):
    def test_diagnostic_video_not_counted_as_showcase(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "native.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("Physical_Drummer_Diagnostic/Native_Physical_Channel_Diagnostic.mp4", b"fixture")
                z.writestr("Final_Band_Output_Diagnostic/verification.json",
                           json.dumps({"source": "authored fixture; not original-song transcription"}))
            report = MODULE.inspect(archive)
            self.assertTrue(report["valid_zip"])
            self.assertEqual(report["showcase_mp4s_verified"], 0)
            self.assertEqual(len(report["mp4s_present"]), 1)

    def test_bad_zip_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "broken.zip"
            archive.write_bytes(b"not a zip")
            with self.assertRaises(zipfile.BadZipFile):
                MODULE.inspect(archive)

if __name__ == "__main__":
    unittest.main()
