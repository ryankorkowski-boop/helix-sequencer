from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core import audio_intelligence
from core import effect_engine


class AudioToolsetVariantTests(unittest.TestCase):
    def test_v29_variants_have_distinct_known_audio_toolsets(self) -> None:
        variants = [effect_engine.VARIANTS[f"v29.{idx}"] for idx in range(1, 10)]
        toolsets = [variant.audio_intelligence_toolset for variant in variants]

        self.assertEqual(len(set(toolsets)), len(toolsets))
        self.assertTrue(set(toolsets).issubset(effect_engine.AUDIO_INTELLIGENCE_TOOLSETS))
        self.assertNotIn("modern", toolsets)

    def test_toolset_preset_applies_runtime_switches(self) -> None:
        tuning = effect_engine.RuntimeTuning(audio_intelligence_toolset="legacy_audio_routes")

        patched = effect_engine.apply_audio_intelligence_toolset(tuning)

        self.assertEqual(patched.audio_intelligence_toolset, "legacy_audio_routes")
        self.assertTrue(patched.pixel_reactive)
        self.assertFalse(patched.matrix_intelligence)
        self.assertEqual(patched.audio_reactive_profile, "showcase")
        self.assertGreater(patched.audio_reactive_intensity, 1.0)

    def test_hardkor_toolset_uses_hardkor_runtime_path(self) -> None:
        tuning = effect_engine.RuntimeTuning(audio_intelligence_toolset="legacy_hardkor")

        patched = effect_engine.apply_audio_intelligence_toolset(tuning)

        self.assertTrue(patched.hardkor_enabled)
        self.assertEqual(patched.hardkor_profile, "ac256")

    def test_cached_local_stems_reuses_complete_fallback_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            audio = folder / "LightsOutTheme.mp3"
            audio.write_bytes(b"fake audio")
            for stem in ("vocals", "drums", "bass", "other"):
                (folder / f"LightsOutTheme.{stem}.wav").write_bytes(b"cached stem")

            cached = audio_intelligence._cached_local_stems(audio, folder)

        self.assertIsNotNone(cached)
        self.assertEqual(set(cached or {}), {"vocals", "drums", "bass", "other"})


if __name__ == "__main__":
    unittest.main()
