from __future__ import annotations

from types import SimpleNamespace
import unittest

from models.working_floor_piano import FLOOR_PIANO_SCHEMA, build_reactive_floor_piano, build_working_floor_piano


class WorkingFloorPianoTests(unittest.TestCase):
    def test_working_floor_piano_has_24_key_structure(self) -> None:
        payload = build_working_floor_piano()

        self.assertEqual(payload["schema"], FLOOR_PIANO_SCHEMA)
        self.assertEqual(payload["role"], "floor_piano")
        self.assertEqual(payload["status"], "working_stage_prop_slice")
        self.assertEqual(payload["key_count"], 24)
        self.assertTrue(payload["validation"]["has_required_submodels"])
        self.assertTrue(payload["validation"]["has_animation_frames"])
        self.assertTrue(payload["validation"]["has_24_keys"])
        self.assertEqual(payload["missing_required_submodels"], [])

        for idx in range(1, 25):
            self.assertIn(f"HX_FLOOR_PIANO_KEY_{idx:02d}", payload["available_submodels"])
        self.assertIn("HX_FLOOR_PIANO_KEY_GROUP", payload["available_submodels"])

    def test_reactive_floor_piano_maps_note_events_to_keys(self) -> None:
        payload = build_reactive_floor_piano(
            note_events=[SimpleNamespace(start_ms=100, end_ms=420, notes=[(36, 0.8), (60, 0.7), (84, 0.9)])]
        )

        self.assertEqual(payload["status"], "reactive_working_stage_prop_slice")
        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["validation"]["reactive_cues_target_existing_submodels"])
        self.assertTrue(payload["reactive_debug"]["uses_note_events"])

        targets = {cue["submodel"] for cue in payload["reactive_cues"]}
        self.assertIn("HX_FLOOR_PIANO_KEY_01", targets)
        self.assertIn("HX_FLOOR_PIANO_KEY_12", targets)
        self.assertIn("HX_FLOOR_PIANO_KEY_24", targets)

    def test_reactive_floor_piano_uses_drummer_player_piano_hooks(self) -> None:
        payload = build_reactive_floor_piano(
            drum_cues=[
                {
                    "start_ms": 500,
                    "kind": "kick",
                    "velocity": 0.9,
                    "confidence": 0.8,
                    "visual_effect": {"player_piano_hook": {"enabled": True, "velocity": 0.9}},
                },
                {
                    "start_ms": 1000,
                    "kind": "snare",
                    "velocity": 0.7,
                    "confidence": 0.72,
                    "visual_effect": {"player_piano_hook": {"enabled": True, "velocity": 0.7}},
                },
            ]
        )

        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["reactive_debug"]["uses_player_piano_hooks"])
        targets = {cue["submodel"] for cue in payload["reactive_cues"]}
        self.assertIn("HX_FLOOR_PIANO_KEY_01", targets)
        self.assertIn("HX_FLOOR_PIANO_KEY_09", targets)
        self.assertTrue(all(cue["source"] == "player_piano_hook" for cue in payload["reactive_cues"]))

    def test_reactive_floor_piano_uses_beat_fallback_and_phrase_sweep(self) -> None:
        payload = build_reactive_floor_piano(beat_ms=[0, 500, 1000, 1500, 2000], phrase_hits=[750])

        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["reactive_debug"]["uses_beat_fallback"])
        self.assertTrue(payload["reactive_debug"]["uses_phrase_hits"])
        self.assertTrue(payload["validation"]["reactive_cues_target_existing_submodels"])
        targets = {cue["submodel"] for cue in payload["reactive_cues"]}
        self.assertIn("HX_FLOOR_PIANO_KEY_GROUP", targets)
        self.assertTrue(any(cue["source"] == "beat_fallback" for cue in payload["reactive_cues"]))
        self.assertTrue(any(cue["source"] == "phrase_hit" for cue in payload["reactive_cues"]))


if __name__ == "__main__":
    unittest.main()
