from __future__ import annotations

from types import SimpleNamespace
import unittest

from models.working_band_member import WORKING_MEMBER_SCHEMA
from models.working_female_singer import build_reactive_female_singer_member, build_working_female_singer


class WorkingFemaleSingerTests(unittest.TestCase):
    def test_working_female_singer_has_required_geometry_and_identity(self) -> None:
        payload = build_working_female_singer()

        self.assertEqual(payload["schema"], WORKING_MEMBER_SCHEMA)
        self.assertEqual(payload["role"], "female_singer")
        self.assertEqual(payload["geometry_role"], "singer")
        self.assertEqual(payload["display_name"], "Female Lead Singer Snowman")
        self.assertEqual(payload["status"], "working_member_slice")
        self.assertTrue(payload["validation"]["has_required_submodels"])
        self.assertTrue(payload["validation"]["has_animation_frames"])
        self.assertTrue(payload["validation"]["mouth_inside_head"])
        self.assertEqual(payload["missing_required_submodels"], [])
        self.assertEqual(payload["xlights_export_contract"]["face_definition"], "female_singer_full")

        node_counts = payload["submodel_node_counts"]
        for submodel_name in payload["required_submodels"]:
            self.assertIn(submodel_name, node_counts)
            self.assertGreater(node_counts[submodel_name], 0)

        cue_targets = {cue["submodel"] for cue in payload["default_cues"]}
        self.assertIn("mouth_A", cue_targets)
        self.assertIn("mouth_I", cue_targets)
        self.assertIn("mouth_O", cue_targets)
        self.assertIn("mic_head", cue_targets)

    def test_reactive_female_singer_uses_lyrics_for_face_cues(self) -> None:
        payload = build_reactive_female_singer_member(
            lyric_events=[SimpleNamespace(start_ms=1000, end_ms=1700, text="shine bright", confidence=0.88)],
            vocal_peaks=[1100],
            parts=[SimpleNamespace(label="CHORUS", start_ms=0, end_ms=2200, energy=0.92)],
        )

        self.assertEqual(payload["status"], "reactive_working_member_slice")
        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["validation"]["has_phoneme_cues"])
        self.assertTrue(payload["validation"]["reactive_cues_target_existing_submodels"])
        self.assertTrue(payload["reactive_debug"]["uses_lyrics"])
        self.assertFalse(payload["reactive_debug"]["uses_vocal_energy_fallback"])
        self.assertEqual(payload["reactive_debug"]["face_definition"], "female_singer_full")
        self.assertEqual(payload["reactive_debug"]["word_count"], 2)

        phoneme_cues = [cue for cue in payload["reactive_cues"] if cue["kind"] == "phoneme_face"]
        self.assertTrue(phoneme_cues)
        self.assertTrue(all(cue["performer"] == "female_singer" for cue in phoneme_cues))
        self.assertTrue(all(cue["xlights"]["face_definition"] == "female_singer_full" for cue in phoneme_cues))
        self.assertTrue(any(cue["expression"]["sparkle_accent"] for cue in phoneme_cues))
        self.assertTrue(any(cue["submodel"] == "mic_head" for cue in payload["reactive_cues"]))

    def test_reactive_female_singer_falls_back_to_vocal_energy(self) -> None:
        payload = build_reactive_female_singer_member(vocal_peaks=[500, 900])

        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["validation"]["has_phoneme_cues"])
        self.assertTrue(payload["reactive_debug"]["uses_vocal_energy_fallback"])
        self.assertEqual(payload["reactive_debug"]["timeline"]["source"], "vocal_energy_fallback")
        self.assertTrue(any(cue["submodel"] == "mouth_A" for cue in payload["reactive_cues"]))
        self.assertTrue(all(cue["performer"] == "female_singer" for cue in payload["reactive_cues"]))


if __name__ == "__main__":
    unittest.main()
