from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.core_sandbox import CoreFlags, run_core_sandbox


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "tests" / "snapshots" / "core_sandbox_snapshot.json"
AUDIO_INTELLIGENCE_SNAPSHOT_PATH = ROOT / "tests" / "snapshots" / "core_audio_intelligence_snapshot.json"


class CoreSandboxTests(unittest.TestCase):
    def _audio_path(self) -> Path:
        return ROOT / "2.wav"

    def _skip_if_no_audio(self) -> None:
        if not self._audio_path().exists():
            self.skipTest("2.wav not found; sandbox regression harness requires fixed audio input")

    def _canonical_modules(self, payload: dict) -> dict:
        return json.loads(json.dumps(payload["modules"]))

    def test_core_sandbox_is_deterministic_for_fixed_audio(self) -> None:
        self._skip_if_no_audio()
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            result1 = run_core_sandbox(
                audio_path=self._audio_path(),
                output_dir=Path(tmp1),
                flags=CoreFlags(),
                preview_frames=False,
            )
            result2 = run_core_sandbox(
                audio_path=self._audio_path(),
                output_dir=Path(tmp2),
                flags=CoreFlags(),
                preview_frames=False,
            )
        self.assertEqual(self._canonical_modules(result1), self._canonical_modules(result2))

    def test_core_sandbox_exposes_required_artifacts(self) -> None:
        self._skip_if_no_audio()
        with tempfile.TemporaryDirectory() as tmp:
            result = run_core_sandbox(
                audio_path=self._audio_path(),
                output_dir=Path(tmp),
                flags=CoreFlags(),
                preview_frames=False,
            )
        modules = result["modules"]
        for module_name in ("effect_engine", "self_improving_scoring", "spatial_mapping_engine", "audio_intelligence"):
            self.assertIn(module_name, modules)
            payload = modules[module_name]
            self.assertIn(payload["status"], {"ok", "missing", "disabled"})
            self.assertIn("effect_timeline", payload)
            self.assertIn("intensity_map", payload)
            self.assertIn("color_distribution", payload)
            self.assertIn("spatial_coordinates", payload)

    def test_core_sandbox_feature_flags_disable_modules(self) -> None:
        self._skip_if_no_audio()
        flags = CoreFlags(
            effect_engine=False,
            self_improving_scoring=True,
            spatial_mapping_engine=False,
            audio_intelligence=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_core_sandbox(
                audio_path=self._audio_path(),
                output_dir=Path(tmp),
                flags=flags,
                preview_frames=False,
            )
        self.assertEqual(result["modules"]["effect_engine"]["status"], "disabled")
        self.assertEqual(result["modules"]["spatial_mapping_engine"]["status"], "disabled")

    def test_core_sandbox_matches_snapshot(self) -> None:
        self._skip_if_no_audio()
        if not SNAPSHOT_PATH.exists():
            self.skipTest("Sandbox snapshot file missing")
        expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_core_sandbox(
                audio_path=self._audio_path(),
                output_dir=Path(tmp),
                flags=CoreFlags(),
                preview_frames=False,
            )
        self.assertEqual(self._canonical_modules(result), expected["modules"])

    def test_audio_intelligence_isolated_snapshot(self) -> None:
        self._skip_if_no_audio()
        if not AUDIO_INTELLIGENCE_SNAPSHOT_PATH.exists():
            self.skipTest("Audio intelligence snapshot file missing")
        expected = json.loads(AUDIO_INTELLIGENCE_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_core_sandbox(
                audio_path=self._audio_path(),
                output_dir=Path(tmp),
                flags=CoreFlags(
                    effect_engine=False,
                    self_improving_scoring=False,
                    spatial_mapping_engine=False,
                    audio_intelligence=True,
                ),
                preview_frames=False,
            )
        actual = json.loads(json.dumps(result["modules"]["audio_intelligence"]))
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
