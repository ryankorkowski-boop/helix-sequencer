"""Regression tests for musical showcase media eligibility."""
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "verify_xlights_showcase_media",
    Path(__file__).resolve().parents[1] / "tools" / "verify_xlights_showcase_media.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

def sequence(media="", kind="Animation"):
    return (f"<xsequence><head><sequenceType>{kind}</sequenceType>"
            f"<sequenceDuration>24.000</sequenceDuration><mediaFile>{media}</mediaFile>"
            "</head></xsequence>")

class ShowcaseMediaTests(unittest.TestCase):
    def test_animation_without_media_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "show.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("Snowman_Band_Showcase.xsq", sequence())
            report = MODULE.audit_archive(archive)
            self.assertFalse(report["musical_showcase_eligible"])
            self.assertEqual(report["sequences"][0]["media_file"], "")

    def test_audio_link_is_not_enough_for_animation(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "show.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("test.xsq", sequence("song.mp3"))
            self.assertFalse(MODULE.audit_archive(archive)["musical_showcase_eligible"])

    def test_media_bound_musical_sequence_is_candidate_only(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "show.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("test.xsq", sequence("song.mp3", "Media"))
            self.assertTrue(MODULE.audit_archive(archive)["musical_showcase_eligible"])

if __name__ == "__main__":
    unittest.main()
