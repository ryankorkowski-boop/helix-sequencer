from __future__ import annotations

from types import SimpleNamespace
import unittest

from audio.drum_classification import DrumEvent
from models.working_stage_pack import STAGE_PACK_SCHEMA, build_reactive_snowman_stage_pack, build_working_snowman_stage_pack


def _event(ms: int, drum_type: str, velocity: float = 0.8, confidence: float = 0.72) -> DrumEvent:
    return DrumEvent(ms / 1000.0, velocity, confidence, {"test": 1.0}, 1, drum_type, "test")


class WorkingStagePackTests(unittest.TestCase):
    def test_working_stage_pack_aggregates_members_and_floor_piano(self) -> None:
        payload = build_working_snowman_stage_pack()

        self.assertEqual(payload["schema"], STAGE_PACK_SCHEMA)
        self.assertEqual(payload["status"], "working_stage_pack_slice")
        self.assertTrue(payload["validation"]["all_members_have_required_submodels"])
        self.assertTrue(payload["validation"]["all_members_have_animation_frames"])
        self.assertTrue(payload["validation"]["all_stage_props_have_required_submodels"])
        self.assertEqual(
            set(payload["band_members"]),
            {"bassist", "guitarist", "singer", "female_singer", "drummer"},
        )
        self.assertEqual(set(payload["stage_props"]), {"floor_piano"})

    def test_reactive_stage_pack_feeds_drummer_hooks_into_floor_piano(self) -> None:
        payload = build_reactive_snowman_stage_pack(
            lyric_events=[SimpleNamespace(start_ms=100, end_ms=520, text="bright snow", confidence=0.84)],
            female_lyric_events=[SimpleNamespace(start_ms=560, end_ms=920, text="shine now", confidence=0.82)],
            vocal_peaks=[120, 320],
            female_vocal_peaks=[600, 760],
            note_events=[
                SimpleNamespace(start_ms=100, end_ms=260, notes=[(60, 0.7), (64, 0.8), (67, 0.6)]),
                SimpleNamespace(start_ms=300, end_ms=900, notes=[(43, 0.8), (55, 0.4)]),
            ],
            bass_peaks=[320, 760],
            guitar_onsets=[100, 500],
            beat_ms=[0, 250, 500, 750, 1000],
            parts=[SimpleNamespace(label="CHORUS", start_ms=0, end_ms=1200, energy=0.9)],
            drum_event_streams={
                "kick_events": [_event(250, "kick", 0.9, 0.86)],
                "snare_events": [_event(500, "snare", 0.7, 0.78)],
                "hihat_events": [_event(750, "hihat", 0.45, 0.62)],
                "cymbal_events": [_event(1000, "cymbal", 0.8, 0.74)],
                "tom_events": [],
                "drum_bus_events": [],
            },
            phrase_hits=[0, 1000],
            band_sync_payload={
                "performer_focus": [{"start_ms": 0, "end_ms": 1200, "primary_focus": "guitarist"}],
                "energy_distributions": [
                    {"start_ms": 0, "end_ms": 1200, "allocations": {"guitarist": 0.75, "bassist": 0.65}}
                ],
            },
        )

        self.assertEqual(payload["schema"], STAGE_PACK_SCHEMA)
        self.assertEqual(payload["status"], "reactive_working_stage_pack_slice")
        self.assertTrue(payload["validation"]["all_members_have_reactive_cues"])
        self.assertTrue(payload["validation"]["all_member_reactive_cues_target_existing_submodels"])
        self.assertTrue(payload["validation"]["all_stage_props_have_reactive_cues"])
        self.assertTrue(payload["validation"]["all_stage_prop_cues_target_existing_submodels"])
        self.assertTrue(payload["validation"]["drummer_feeds_floor_piano"])
        self.assertTrue(payload["integration"]["drummer_feeds_floor_piano"])
        self.assertIn("player_piano_hook", payload["integration"]["floor_piano_sources"])

        floor_piano = payload["stage_props"]["floor_piano"]
        floor_sources = {cue["source"] for cue in floor_piano["reactive_cues"]}
        self.assertIn("player_piano_hook", floor_sources)
        self.assertIn("note_events", floor_sources)
        self.assertIn("phrase_hit", floor_sources)
        self.assertTrue(any(cue["submodel"] == "HX_FLOOR_PIANO_KEY_01" for cue in floor_piano["reactive_cues"]))


if __name__ == "__main__":
    unittest.main()
