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


if __name__ == "__main__":
    unittest.main()
