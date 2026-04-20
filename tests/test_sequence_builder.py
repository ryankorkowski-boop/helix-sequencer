from __future__ import annotations

import unittest

from core import effect_engine
from core import engine_profiles
from core import sequence_builder


class SequenceBuilderTests(unittest.TestCase):
    def test_available_profiles_only_exposes_master(self) -> None:
        profiles = sequence_builder.available_profiles()
        self.assertEqual([profile.profile_id for profile in profiles], ["master"])

    def test_master_profile_tracks_active_style_version(self) -> None:
        profile = engine_profiles.resolve_profile("master")
        self.assertEqual(profile.version, effect_engine.ACTIVE_STYLE_VERSION)
        self.assertFalse(profile.legacy)

    def test_legacy_version_can_still_resolve_explicitly(self) -> None:
        profile = engine_profiles.resolve_profile("v27.3")
        self.assertEqual(profile.version, "v27.3")

    def test_effect_engine_parser_exposes_one_click_flags(self) -> None:
        args = effect_engine.parse_args(
            effect_engine.ACTIVE_STYLE,
            ["--variants", "4", "--auto-shortlist", "--learn-from-my-xsqs"],
        )
        self.assertTrue(args.polish_enabled)
        self.assertEqual(args.variant_count, 4)
        self.assertTrue(args.auto_shortlist)
        self.assertTrue(args.learn_from_my_xsqs)


if __name__ == "__main__":
    unittest.main()
