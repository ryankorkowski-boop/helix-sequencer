import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_shared_approval_source import verify


class SharedApprovalSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rows = [
            dict(role=role, source_audio_sha256="a"*64, analysis_sha256="b"*64,
                 source_commit="c"*40, native_verified=True, mp4_verified=True,
                 owner_approved=False)
            for role in ("16-panel", "12-layout", "six-snowman-band")
        ]

    def check(self):
        paths = []
        for index, row in enumerate(self.rows):
            path = self.root / f"{index}.json"
            path.write_text(json.dumps(row))
            paths.append(path)
        return verify(paths)

    def test_accepts_one_analysis_pass(self):
        self.assertEqual(self.check()["status"], "AWAITING_OWNER_APPROVAL")

    def test_rejects_different_source(self):
        self.rows[1]["source_audio_sha256"] = "d"*64
        with self.assertRaisesRegex(ValueError, "source_audio_sha256"):
            self.check()

    def test_rejects_different_analysis(self):
        self.rows[2]["analysis_sha256"] = "d"*64
        with self.assertRaisesRegex(ValueError, "analysis_sha256"):
            self.check()

    def test_rejects_unverified_video(self):
        self.rows[0]["mp4_verified"] = False
        with self.assertRaisesRegex(ValueError, "Unverified"):
            self.check()

    def test_rejects_duplicate_role(self):
        self.rows[2]["role"] = "12-layout"
        with self.assertRaisesRegex(ValueError, "role"):
            self.check()


if __name__ == "__main__":
    unittest.main()
