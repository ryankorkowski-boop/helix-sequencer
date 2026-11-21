import tempfile
import unittest
from pathlib import Path
from tools.build_shared_approval_analysis import create, verify


class SharedAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source = root / "song.wav"
        self.source.write_bytes(b"original audio")
        self.stems = root / "stems"
        self.stems.mkdir()
        for role in ("drums", "bass", "other", "vocals"):
            (self.stems / (role + ".wav")).write_bytes(role.encode())
        self.manifest = root / "shared.json"

    def build(self):
        return create(self.source, self.stems, self.manifest, "a" * 40)

    def test_source_and_stems_verified(self):
        self.build()
        self.assertEqual(verify(self.source, self.stems, self.manifest)["source_audio_name"], "song.wav")

    def test_rejects_changed_stem(self):
        self.build()
        (self.stems / "vocals.wav").write_bytes(b"mutated")
        with self.assertRaisesRegex(ValueError, "stem provenance"):
            verify(self.source, self.stems, self.manifest)

    def test_rejects_changed_source(self):
        self.build()
        self.source.write_bytes(b"mutated")
        with self.assertRaisesRegex(ValueError, "integrity"):
            verify(self.source, self.stems, self.manifest)

    def test_rejects_missing_stem(self):
        (self.stems / "bass.wav").unlink()
        with self.assertRaisesRegex(ValueError, "Exactly one"):
            self.build()


if __name__ == "__main__":
    unittest.main()
