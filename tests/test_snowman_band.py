from __future__ import annotations

import unittest
from types import SimpleNamespace

from core import snowman_band


class SnowmanBandTests(unittest.TestCase):
    def test_preferred_face_routing_prioritizes_helix_mascot(self) -> None:
        routing = snowman_band.preferred_face_routing(
            [
                "NBH_RIGHT_SINGING_FACE_01_PANEL",
                "NBH_RIGHT_SINGING_FACE_02_PANEL",
                "NBH_RIGHT_HELIXMASCOT_CUSTOM",
                "NBH_LEFT_MATRIX_01",
            ]
        )
        self.assertEqual(routing["preferred_lead"], "NBH_RIGHT_HELIXMASCOT_CUSTOM")
        self.assertTrue(routing["lead_cycle"])
        self.assertEqual(routing["lead_cycle"][0], "NBH_RIGHT_HELIXMASCOT_CUSTOM")
        self.assertIn("NBH_LEFT_MATRIX_01", routing["lyric_surfaces"])

    def test_build_snowman_band_plan_creates_performer_cues(self) -> None:
        parsed_layout = SimpleNamespace(
            models={
                "NBH_RIGHT_HELIXMASCOT_CUSTOM": object(),
                "NBH_RIGHT_SINGING_FACE_01_PANEL": object(),
            }
        )
        parts = [
            SimpleNamespace(label="VERSE", start_ms=0, end_ms=1200),
            SimpleNamespace(label="CHORUS", start_ms=1200, end_ms=2600),
        ]
        lyric_events = [SimpleNamespace(start_ms=1300, end_ms=1500, text="hello world")]
        note_events = [
            SimpleNamespace(start_ms=220, end_ms=420, notes=[(43, 0.8), (55, 0.3)]),
            SimpleNamespace(start_ms=1320, end_ms=1560, notes=[(50, 0.5), (67, 0.9)]),
        ]
        payload = snowman_band.build_snowman_band_plan(
            parsed_layout=parsed_layout,
            parts=parts,
            lyric_events=lyric_events,
            note_events=note_events,
            beat_ms=[0, 500, 1000, 1500, 2000],
            kicks=[500, 1500],
            snares=[750, 1750],
            hats=[250, 1000, 1800],
            bass_peaks=[260, 1480],
            vocal_peaks=[1360],
            build_lifts=[1180],
            releases=[1600],
            chronoflow_payload={"debug": {"event_count": 12}},
            multiband=SimpleNamespace(tempo_bpm=128.0),
            enable_lyrics=True,
        )

        self.assertTrue(payload["enabled"])
        self.assertEqual(payload["face_routing"]["preferred_lead"], "NBH_RIGHT_HELIXMASCOT_CUSTOM")
        self.assertTrue(payload["cues"]["lead_singer"])
        self.assertTrue(payload["cues"]["bassist"])
        self.assertTrue(payload["cues"]["guitarist"])
        self.assertTrue(payload["cues"]["drummer"])
        self.assertIn("kick", payload["kit"]["components"])
        self.assertEqual(payload["debug"]["chronoflow_event_count"], 12)

    def test_build_timing_track_labels_core_performers(self) -> None:
        payload = {
            "cues": {
                "lead_singer": [{"start_ms": 100, "end_ms": 180, "viseme": "AH"}],
                "bassist": [{"start_ms": 200, "end_ms": 320, "string_index": 3}],
                "guitarist": [{"start_ms": 250, "end_ms": 380, "neck_position": 2}],
                "drummer": [{"start_ms": 300, "end_ms": 360, "kind": "snare"}],
                "background_vocals": [{"start_ms": 400, "end_ms": 520, "performer": "guitarist"}],
            }
        }
        track = snowman_band.build_timing_track(payload)
        labels = [label for label, _, _ in track]
        self.assertEqual(labels[:5], ["vox:AH", "bass:s3", "gtr:n2", "drm:snare", "bgv:gtr"])


if __name__ == "__main__":
    unittest.main()
