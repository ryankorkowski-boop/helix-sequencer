from __future__ import annotations

import unittest

from export.stage_pack_manifest_export import build_demo_stage_pack_export_manifest
from models.working_double_helix import (
    WORKING_DOUBLE_HELIX_SCHEMA,
    build_reactive_double_helix_from_manifest,
    build_working_double_helix,
)


class WorkingDoubleHelixTests(unittest.TestCase):
    def test_working_double_helix_has_geometry_and_required_zones(self) -> None:
        payload = build_working_double_helix()

        self.assertEqual(payload["schema"], WORKING_DOUBLE_HELIX_SCHEMA)
        self.assertEqual(payload["model_id"], "HELIXIA_GIANT_DOUBLE_HELIX")
        self.assertEqual(payload["status"], "working_centerpiece_slice")
        self.assertTrue(payload["validation"]["has_geometry"])
        self.assertTrue(payload["validation"]["has_required_submodels"])
        self.assertTrue(payload["validation"]["has_audio_in_zone"])
        self.assertTrue(payload["validation"]["has_lights_out_zone"])
        self.assertIn("HELIXIA_DNA_STRAND_A", payload["required_submodels"])
        self.assertIn("HELIXIA_DNA_STRAND_B", payload["required_submodels"])
        self.assertIn("HELIXIA_DNA_RUNGS", payload["required_submodels"])

    def test_reactive_double_helix_maps_stage_pack_manifest_to_helix_regions(self) -> None:
        manifest = build_demo_stage_pack_export_manifest()
        payload = build_reactive_double_helix_from_manifest(manifest)

        self.assertEqual(payload["status"], "reactive_centerpiece_slice")
        self.assertTrue(payload["validation"]["has_reactive_cues"])
        self.assertTrue(payload["validation"]["reactive_cues_target_existing_submodels"])
        self.assertTrue(payload["validation"]["has_stage_pack_source_rows"])
        self.assertTrue(payload["validation"]["has_audio_in_and_lights_out"])
        self.assertEqual(payload["reactive_debug"]["source_row_count"], manifest["row_count"])
        self.assertTrue(payload["reactive_debug"]["uses_singers"])
        self.assertTrue(payload["reactive_debug"]["uses_guitar"])
        self.assertTrue(payload["reactive_debug"]["uses_bass"])
        self.assertTrue(payload["reactive_debug"]["uses_drums"])
        self.assertTrue(payload["reactive_debug"]["uses_floor_piano"])
        self.assertTrue(payload["reactive_debug"]["has_audio_in_cue"])
        self.assertTrue(payload["reactive_debug"]["has_lights_out_cue"])

        targets = {cue["submodel"] for cue in payload["reactive_cues"]}
        self.assertIn("HELIXIA_DNA_TOP_INPUT", targets)
        self.assertIn("HELIXIA_DNA_BOTTOM_OUTPUT", targets)
        self.assertIn("HELIXIA_DNA_CORE", targets)
        self.assertIn("HELIXIA_DNA_STRAND_A", targets)
        self.assertIn("HELIXIA_DNA_STRAND_B", targets)
        self.assertIn("HELIXIA_DNA_RUNGS", targets)
        self.assertIn("HELIXIA_DNA_RUNG_EVEN", targets)

    def test_reactive_double_helix_preserves_xlights_metadata(self) -> None:
        manifest = build_demo_stage_pack_export_manifest()
        payload = build_reactive_double_helix_from_manifest(manifest)

        self.assertTrue(all("xlights" in cue for cue in payload["reactive_cues"]))
        self.assertTrue(any(cue["xlights"]["effect"] == "Sparkle" for cue in payload["reactive_cues"]))
        self.assertTrue(any(cue["xlights"]["effect"] == "Bars" for cue in payload["reactive_cues"]))
        self.assertTrue(any(cue["xlights"]["effect"] == "Chase" for cue in payload["reactive_cues"]))
        self.assertTrue(any(cue["source"] == "audio_in" for cue in payload["reactive_cues"]))
        self.assertTrue(any(cue["source"] == "lights_out" for cue in payload["reactive_cues"]))


if __name__ == "__main__":
    unittest.main()
