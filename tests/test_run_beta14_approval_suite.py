import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.run_beta14_approval_suite import ROLES, run_suite


class Beta14SuiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.audio = self.root / "audio.wav"
        self.audio.write_bytes(b"owner original")
        self.stems = self.root / "stems"
        self.stems.mkdir()
        for role in ("drums", "bass", "other", "vocals"):
            (self.stems / (role + ".wav")).write_bytes(role.encode())
        self.output = self.root / "output"
        self.commands = {role: ["renderer", role] for role in ROLES}

    def runner(self, command, check, env):
        self.assertTrue(check)
        role = env["HELIX_APPROVAL_ROLE"]
        self.assertEqual(command[1], role)
        movie = Path(env["HELIX_APPROVAL_OUTPUT"], "preview.mp4")
        movie.write_bytes(b"synthetic test bytes" * 100)
        Path(env["HELIX_APPROVAL_OUTPUT"], "receipt.json").write_text(json.dumps({
            "role": role, "source_audio_sha256": env["HELIX_APPROVAL_SOURCE_SHA256"],
            "analysis_sha256": env["HELIX_APPROVAL_ANALYSIS_SHA256"],
            "source_commit": "a" * 40,
            "native_verified": True, "mp4_verified": True, "owner_approved": False,
            "mp4": {"path": "preview.mp4", "sha256": hashlib.sha256(movie.read_bytes()).hexdigest()}
        }))

    def test_all_three_use_same_analysis(self):
        result = run_suite(self.audio, self.stems, self.output, "a" * 40,
                           self.commands, runner=self.runner)
        self.assertEqual(result["status"], "AWAITING_OWNER_APPROVAL")
        self.assertTrue((self.output / "approval_suite_receipt.json").exists())

    def test_rejects_missing_renderer(self):
        with self.assertRaisesRegex(ValueError, "Three real renderer"):
            run_suite(self.audio, self.stems, self.output, "a" * 40,
                      {"16-panel": ["renderer"]}, runner=self.runner)

    def test_rejects_missing_video_bytes(self):
        def no_video(command, check, env):
            self.runner(command, check, env)
            Path(env["HELIX_APPROVAL_OUTPUT"], "preview.mp4").unlink()
        with self.assertRaisesRegex(ValueError, "MP4 missing"):
            run_suite(self.audio, self.stems, self.output, "a" * 40,
                      self.commands, runner=no_video)

    def test_rejects_false_source_receipt(self):
        def incorrect(command, check, env):
            self.runner(command, check, env)
            p = Path(env["HELIX_APPROVAL_OUTPUT"], "receipt.json")
            row = json.loads(p.read_text())
            row["analysis_sha256"] = "f" * 64
            p.write_text(json.dumps(row))
        with self.assertRaisesRegex(ValueError, "shared analysis_sha256"):
            run_suite(self.audio, self.stems, self.output, "a" * 40,
                      self.commands, runner=incorrect)


if __name__ == "__main__":
    unittest.main()
