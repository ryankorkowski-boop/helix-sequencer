from __future__ import annotations

import json
import unittest

from models.helixville4_band_assets import (
    HELIXVILLE4_BAND_ASSETS,
    band_asset_by_member,
    build_helixville4_band_asset_catalog,
    svg_for_band_asset,
)


class Helixville4BandAssetsTests(unittest.TestCase):
    def test_asset_catalog_is_json_ready_and_covers_all_performers(self) -> None:
        catalog = build_helixville4_band_asset_catalog()
        decoded = json.loads(json.dumps(catalog, sort_keys=True))
        member_ids = {asset["member_id"] for asset in decoded["assets"]}

        self.assertEqual(decoded["schema"], "helixville4.band_assets.v1")
        self.assertEqual(decoded["scope"], "background_svg_and_white_outline_maps")
        self.assertEqual(decoded["asset_count"], 5)
        self.assertEqual(
            member_ids,
            {
                "snowman_singer",
                "snowman_singer_female",
                "snowman_guitarist",
                "snowman_bassist",
                "snowman_drummer",
            },
        )

    def test_every_asset_has_outline_segments_and_submodel_order(self) -> None:
        for asset in HELIXVILLE4_BAND_ASSETS:
            self.assertEqual(asset.width_px, 420)
            self.assertEqual(asset.height_px, 620)
            self.assertEqual(asset.view, "front")
            self.assertGreaterEqual(len(asset.outline_segments), 10)
            self.assertGreaterEqual(len(asset.submodel_order), 8)
            self.assertTrue(all(segment.submodel.startswith(asset.model_prefix) for segment in asset.outline_segments))
            self.assertEqual(tuple(dict.fromkeys(segment.submodel for segment in asset.outline_segments)), asset.submodel_order)

    def test_vocal_assets_include_mouth_phoneme_submodels(self) -> None:
        singer = band_asset_by_member("snowman_singer")
        harmony = band_asset_by_member("snowman singer female")

        self.assertIn("HX_SNOWMAN_SINGER_MOUTH_PHONEME", singer.submodel_order)
        self.assertIn("HX_SNOWMAN_SINGER_FEMALE_MOUTH_PHONEME", harmony.submodel_order)
        self.assertIn("HX_SNOWMAN_SINGER_FEMALE_CALL_RESPONSE", harmony.submodel_order)

    def test_guitar_and_bass_assets_include_instrument_articulation_submodels(self) -> None:
        guitar = band_asset_by_member("snowman_guitarist")
        bass = band_asset_by_member("snowman_bassist")

        self.assertIn("HX_SNOWMAN_GUITARIST_GUITAR_BODY", guitar.submodel_order)
        self.assertIn("HX_SNOWMAN_GUITARIST_GUITAR_NECK", guitar.submodel_order)
        self.assertIn("HX_SNOWMAN_GUITARIST_STRUM_ZONE", guitar.submodel_order)
        self.assertIn("HX_SNOWMAN_BASSIST_BASS_BODY", bass.submodel_order)
        self.assertIn("HX_SNOWMAN_BASSIST_BASS_NECK", bass.submodel_order)
        self.assertIn("HX_SNOWMAN_BASSIST_PLUCK_ZONE", bass.submodel_order)

    def test_drummer_asset_includes_drum_targets_and_arm_motion(self) -> None:
        drummer = band_asset_by_member("snowman-drummer")

        for submodel in (
            "HX_SNOWMAN_DRUMMER_LEFT_ARM",
            "HX_SNOWMAN_DRUMMER_RIGHT_ARM",
            "HX_SNOWMAN_DRUMMER_STICKS",
            "HX_SNOWMAN_DRUMMER_KICK",
            "HX_SNOWMAN_DRUMMER_SNARE",
            "HX_SNOWMAN_DRUMMER_TOM",
            "HX_SNOWMAN_DRUMMER_HI_HAT",
            "HX_SNOWMAN_DRUMMER_CYMBALS",
        ):
            self.assertIn(submodel, drummer.submodel_order)

    def test_svg_output_contains_background_grid_and_data_submodels(self) -> None:
        asset = band_asset_by_member("snowman_guitarist")
        svg = svg_for_band_asset(asset)

        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("Rock Guitar Snowman", svg)
        self.assertIn("data-submodel=\"HX_SNOWMAN_GUITARIST_GUITAR_BODY\"", svg)
        self.assertIn("<rect width=\"100%\" height=\"100%\"", svg)
        self.assertIn("</svg>", svg)

    def test_unknown_asset_lookup_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(KeyError, "Unknown Helixville4 band asset"):
            band_asset_by_member("accordion yeti")


if __name__ == "__main__":
    unittest.main()
