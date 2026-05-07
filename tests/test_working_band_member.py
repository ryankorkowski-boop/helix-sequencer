from __future__ import annotations

from types import SimpleNamespace
import unittest

from models.working_band_member import WORKING_MEMBER_SCHEMA, build_reactive_bassist_member, build_working_bassist


class WorkingBandMemberTests(unittest.TestCase):
    def test_working_bassist_has_required_geometry_and_animation(self) -> None:
        payload = build_working_bassist()

        self.assertEqual(payload["schema"], WORKING_MEMBER_SCHEMA)
        self.assertEqual(payload["role"], "bassist")
        self.assertEqual(payload["status"], "working_member_slice")
        self.assertTrue(payload["validation"]["has_required_submodels"])
        self.assertTrue(payload["validation"]["has_animation_frames"])
        self.assertTrue(payload["validation"]["mouth_inside_head"])
        self.assertEqual(payload["missing_required_submodels"], [])

        node_counts = payload["submodel_node_counts"]
        for submodel_name in payload["required_submodels"]:
            self.assertIn(submodel_name, node_counts)
            self.assertGreater(node_counts[submodel_name], 0)

        cue_targets = {cue["submodel"] for cue in payload["default_cues"]}
        self.assertIn("pluck_zone", cue_targets)
        self.assertIn("neck_zone", cue_targets)
        self.assertIn("bass_body", cue_targets)

    def test_working_bassist_export_contract_names_smoke_test_targets(self) -> None:
        payload = build_working_bassist()
        contract = payload["xlights_export_contract"]

        self.assertEqual(contract["target_model_type"], "custom_model_with_submodels")
        self.assertEqual(contract["node_order"], "row_major_top_left_1_based")
        self.assertIn("pluck_zone", contract["must_export_submodels"])
        self.assertIn("band_body_core", contract["must_export_submodels"])
        self.assertIn("neck_zone", contract["first_sequence_smoke_test"])

    def test_reactive_bassist_uses_bass_peaks_and_low_note_sustains(self) -> None:
        payload = build_reactive_bassist_member(
            bass_peaks=[240, 740],
            note_events=[SimpleNamespace(start_ms=200, end_ms=900, notes=[(43, 0.8), (55, 0.4)])],
            beat_ms=[0, 500, 1000],
            parts=[SimpleNamespace(label="CHORUS", start_ms=0, end_ms=1200)],
            band_sync_payload={
                "performer_focus": [{"start_ms": 0, "end_ms": 1200, "primary_focus": "bassist"}],
                "energy_distributions": [{"start_ms": 0, "end_ms": 1200, "allocations": {"bassist": 0.8}}],
            },
        )

        self.assertEqual(payload["status"], "reactive_working_member_slice")
        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["validation"]["reactive_cues_target_existing_submodels"])
        self.assertTrue(payload["reactive_debug"]["uses_bass_peaks"])
        self.assertTrue(payload["reactive_debug"]["uses_low_note_sustains"])
        self.assertTrue(payload["reactive_debug"]["band_sync_applied"])

        targets = {cue["submodel"] for cue in payload["reactive_cues"]}
        self.assertIn("pluck_zone", targets)
        self.assertIn("bass_body", targets)
        self.assertTrue(any(cue.get("string_index") for cue in payload["reactive_cues"]))
        self.assertTrue(any(cue.get("expression", {}).get("low_frequency_emphasis") for cue in payload["reactive_cues"]))

    def test_reactive_bassist_falls_back_to_beat_when_audio_inputs_missing(self) -> None:
        payload = build_reactive_bassist_member(beat_ms=[0, 500, 1000, 1500])

        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["reactive_debug"]["uses_beat_fallback"])
        self.assertEqual(payload["reactive_debug"]["detection"]["fallback_mode"], "beat")
        self.assertTrue(all(cue["submodel"] == "pluck_zone" for cue in payload["reactive_cues"]))


if __name__ == "__main__":
    unittest.main()
