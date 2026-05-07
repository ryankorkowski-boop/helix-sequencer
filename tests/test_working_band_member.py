from __future__ import annotations

from types import SimpleNamespace
import unittest

from models.working_band_member import (
    WORKING_MEMBER_SCHEMA,
    build_reactive_bassist_member,
    build_reactive_guitarist_member,
    build_working_bassist,
    build_working_guitarist,
)


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

    def test_working_guitarist_has_required_geometry_and_animation(self) -> None:
        payload = build_working_guitarist()

        self.assertEqual(payload["schema"], WORKING_MEMBER_SCHEMA)
        self.assertEqual(payload["role"], "guitarist")
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
        self.assertIn("strum_zone", cue_targets)
        self.assertIn("fret_zone", cue_targets)
        self.assertIn("guitar_body", cue_targets)

    def test_working_guitarist_export_contract_names_smoke_test_targets(self) -> None:
        payload = build_working_guitarist()
        contract = payload["xlights_export_contract"]

        self.assertEqual(contract["target_model_type"], "custom_model_with_submodels")
        self.assertEqual(contract["node_order"], "row_major_top_left_1_based")
        self.assertIn("strum_zone", contract["must_export_submodels"])
        self.assertIn("fret_zone", contract["must_export_submodels"])
        self.assertIn("guitar_body", contract["first_sequence_smoke_test"])

    def test_reactive_guitarist_uses_note_events_for_strum_fret_and_sustain(self) -> None:
        payload = build_reactive_guitarist_member(
            note_events=[
                SimpleNamespace(start_ms=100, end_ms=260, notes=[(60, 0.7), (64, 0.8), (67, 0.6)]),
                SimpleNamespace(start_ms=500, end_ms=1200, notes=[(69, 0.9)]),
            ],
            beat_ms=[0, 500, 1000],
            parts=[SimpleNamespace(label="CHORUS", start_ms=0, end_ms=1500)],
            band_sync_payload={
                "performer_focus": [{"start_ms": 0, "end_ms": 1500, "primary_focus": "guitarist"}],
                "energy_distributions": [{"start_ms": 0, "end_ms": 1500, "allocations": {"guitarist": 0.85}}],
            },
        )

        self.assertEqual(payload["status"], "reactive_working_member_slice")
        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["validation"]["reactive_cues_target_existing_submodels"])
        self.assertTrue(payload["reactive_debug"]["uses_note_events"])
        self.assertTrue(payload["reactive_debug"]["band_sync_applied"])

        targets = {cue["submodel"] for cue in payload["reactive_cues"]}
        self.assertIn("strum_zone", targets)
        self.assertIn("guitar_body", targets)
        self.assertIn("fret_zone", targets)
        self.assertIn("strum", payload["reactive_debug"]["event_types"])
        self.assertIn("sustained_note", payload["reactive_debug"]["event_types"])
        self.assertTrue(any(cue.get("neck_position") for cue in payload["reactive_cues"]))
        self.assertTrue(any(cue.get("spatial_impulse", {}).get("enabled") for cue in payload["reactive_cues"]))

    def test_reactive_guitarist_falls_back_to_rhythm_when_note_events_missing(self) -> None:
        payload = build_reactive_guitarist_member(onset_ms=[0, 500, 1000], beat_ms=[0, 500, 1000, 1500])

        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["reactive_debug"]["uses_rhythm_fallback"])
        self.assertEqual(payload["reactive_debug"]["detection"]["fallback_mode"], "rhythm_energy")
        self.assertTrue(all(cue["submodel"] == "strum_zone" for cue in payload["reactive_cues"]))


if __name__ == "__main__":
    unittest.main()
