from __future__ import annotations

from types import SimpleNamespace
import unittest

from core import snowman_band
from core import vocal_emotion
from core import vocal_timeline


class VocalEmotionTests(unittest.TestCase):
    def test_emotion_extraction_uses_lyrics_and_section_context(self) -> None:
        timeline = vocal_timeline.build_lyric_timeline(
            [
                SimpleNamespace(start_ms=100, end_ms=700, text="shine bright together", confidence=0.86),
                SimpleNamespace(start_ms=900, end_ms=1500, text="lost in cold shadow", confidence=0.8),
            ]
        )
        payload = vocal_emotion.build_vocal_emotion_timeline(
            lyric_timeline=timeline,
            song_parts=[SimpleNamespace(label="CHORUS", start_ms=0, end_ms=2000, energy=0.9)],
            vocal_peaks_ms=[120, 300, 950],
        )
        emotions = [event["emotion_type"] for event in payload["events"]]
        self.assertIn(emotions[0], {"happy", "triumphant", "energetic"})
        self.assertIn(payload["schema"], "helix.vocal_emotion.v1")
        self.assertTrue(payload["debug"]["event_count"])

    def test_face_expression_scales_lead_more_than_background(self) -> None:
        emotion = {"emotion_type": "aggressive", "intensity": 0.9, "confidence": 0.8}
        lead = vocal_emotion.face_expression_for("lead_singer", emotion, 0.6)
        bg = vocal_emotion.face_expression_for("guitarist", emotion, 0.6)
        drummer = vocal_emotion.face_expression_for("drummer", emotion, 0.6)
        self.assertGreater(lead["mouth_intensity_scale"], bg["mouth_intensity_scale"])
        self.assertGreater(bg["motion_amplitude"], drummer["motion_amplitude"] - 0.01)
        self.assertEqual(lead["palette"], "hot_red_white")

    def test_apply_emotion_to_face_cues_adds_palette_scoring_and_spatial_hints(self) -> None:
        cues, logs = vocal_emotion.apply_emotion_to_face_cues(
            [{"performer": "lead_singer", "start_ms": 100, "end_ms": 200, "intensity": 0.6, "mouth_shape": "mouth_A"}],
            {"events": [{"start_ms": 0, "end_ms": 500, "emotion_type": "happy", "intensity": 0.8, "confidence": 0.75}]},
        )
        self.assertEqual(cues[0]["emotion"]["emotion_type"], "happy")
        self.assertIn("effect_scoring_hint", cues[0])
        self.assertTrue(cues[0]["spatial_emotion_hint"]["enabled"])
        self.assertEqual(logs[0]["palette"], "warm_gold")

    def test_snowman_band_exposes_emotion_debug_and_face_controls(self) -> None:
        payload = snowman_band.build_snowman_band_plan(
            parsed_layout=SimpleNamespace(models={"NBH_RIGHT_HELIXMASCOT_CUSTOM": object()}),
            parts=[SimpleNamespace(label="CHORUS", start_ms=0, end_ms=1800, energy=0.9)],
            lyric_events=[SimpleNamespace(start_ms=100, end_ms=700, text="shine bright forever", confidence=0.88)],
            note_events=[],
            beat_ms=[0, 500, 1000, 1500],
            kicks=[],
            snares=[],
            hats=[],
            bass_peaks=[],
            vocal_peaks=[120, 320, 540],
            build_lifts=[],
            releases=[],
            chronoflow_payload={},
            multiband=SimpleNamespace(tempo_bpm=120.0),
            enable_lyrics=True,
        )
        self.assertTrue(payload["emotion"]["timeline"])
        self.assertTrue(payload["emotion"]["face_intensity_logs"])
        self.assertTrue(payload["xlights_translation"]["emotion_palette_timeline"])
        self.assertIn("emotion", payload["cues"]["lead_face_activations"][0])
        self.assertGreater(payload["debug"]["vocal_emotion_events"], 0)


if __name__ == "__main__":
    unittest.main()
