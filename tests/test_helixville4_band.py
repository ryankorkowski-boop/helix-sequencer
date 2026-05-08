from __future__ import annotations

import json
import unittest

from models.helixville4_band import (
    HELIXVILLE4_BAND_MEMBERS,
    band_member_by_id,
    build_helixville4_band_member_catalog,
)


class Helixville4BandTests(unittest.TestCase):
    def test_band_catalog_is_json_ready_and_has_expected_schema(self) -> None:
        catalog = build_helixville4_band_member_catalog()
        decoded = json.loads(json.dumps(catalog, sort_keys=True))

        self.assertEqual(decoded["schema"], "helixville4.band_members.v1")
        self.assertEqual(decoded["stage_id"], "snowman_band_stage")
        self.assertEqual(decoded["scope"], "layout_and_sequencing_metadata")
        self.assertEqual(len(decoded["members"]), 5)
        self.assertTrue(decoded["implementation_boundary"]["layout_metadata"])
        self.assertFalse(decoded["implementation_boundary"]["layout_xml_generation"])
        self.assertFalse(decoded["implementation_boundary"]["sequencing_behavior"])
        self.assertFalse(decoded["implementation_boundary"]["audio_analysis"])
        self.assertFalse(decoded["implementation_boundary"]["animation_runtime"])

    def test_required_snowman_band_members_exist(self) -> None:
        ids = {member.member_id for member in HELIXVILLE4_BAND_MEMBERS}

        self.assertEqual(
            ids,
            {
                "snowman_bassist",
                "snowman_guitarist",
                "snowman_drummer",
                "snowman_singer",
                "snowman_singer_female",
            },
        )

    def test_member_specs_include_models_roles_lanes_and_stage_positions(self) -> None:
        for member in HELIXVILLE4_BAND_MEMBERS:
            self.assertTrue(member.display_name)
            self.assertTrue(member.primary_role)
            self.assertTrue(member.instrument)
            self.assertTrue(member.model_prefix.startswith("HX_SNOWMAN_"))
            self.assertEqual(member.body_model, f"{member.model_prefix}_BODY")
            self.assertEqual(member.instrument_model, f"{member.model_prefix}_INSTRUMENT")
            self.assertTrue(member.sequencing_lane.startswith("lane_"))
            self.assertGreaterEqual(len(member.timing_tracks), 3)
            self.assertGreaterEqual(len(member.animation_cues), 4)
            self.assertGreater(member.priority, 0)
            self.assertLess(member.stage_position.y_ft, 0.0)

    def test_vocalists_are_phoneme_capable_and_have_lyric_tracks(self) -> None:
        vocalists = [member for member in HELIXVILLE4_BAND_MEMBERS if member.phoneme_capable]

        self.assertEqual({member.member_id for member in vocalists}, {"snowman_singer", "snowman_singer_female"})
        for member in vocalists:
            self.assertIn("lyrics", member.timing_tracks)
            self.assertIn("phonemes", member.timing_tracks)
            self.assertIn("mouth_phoneme", member.animation_cues)

    def test_catalog_groups_split_vocals_and_instruments(self) -> None:
        catalog = build_helixville4_band_member_catalog()

        self.assertEqual(len(catalog["groups"]["HX_SNOWMAN_BAND"]), 5)
        self.assertEqual(
            set(catalog["groups"]["HX_SNOWMAN_VOCALS"]),
            {"HX_SNOWMAN_SINGER", "HX_SNOWMAN_SINGER_FEMALE"},
        )
        self.assertEqual(
            set(catalog["groups"]["HX_SNOWMAN_INSTRUMENTS"]),
            {"HX_SNOWMAN_BASSIST", "HX_SNOWMAN_GUITARIST", "HX_SNOWMAN_DRUMMER"},
        )
        self.assertEqual(
            set(catalog["phoneme_models"]),
            {"HX_SNOWMAN_SINGER_BODY", "HX_SNOWMAN_SINGER_FEMALE_BODY"},
        )

    def test_member_lookup_normalizes_common_user_input(self) -> None:
        self.assertEqual(band_member_by_id("snowman-bassist").instrument, "bass")
        self.assertEqual(band_member_by_id("Snowman Singer Female").primary_role, "harmony_vocal")
        with self.assertRaisesRegex(KeyError, "Unknown Helixville4 band member"):
            band_member_by_id("kazoo goblin")


if __name__ == "__main__":
    unittest.main()
