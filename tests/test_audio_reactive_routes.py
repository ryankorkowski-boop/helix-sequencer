from __future__ import annotations

import unittest

from core import audio_reactive_effect_catalog
from core import audio_trigger_routes


class AudioReactiveRouteTests(unittest.TestCase):
    def test_catalog_selects_conflict_safe_effects(self) -> None:
        effects = audio_reactive_effect_catalog.choose_effects_for_frame(
            {
                "energy_smooth": 0.55,
                "low": 0.2,
                "mid": 0.2,
                "high": 0.1,
                "onset": 0.4,
            },
            is_downbeat=True,
            max_effects=4,
        )

        names = {str(effect["name"]) for effect in effects}
        self.assertIn("downbeat_flash", names)
        self.assertIn("build_ramp", names)
        self.assertNotIn("drop_burst", names)

    def test_trigger_routes_build_deterministic_actions(self) -> None:
        timeline = [
            {"time_ms": 0, "downbeat": True, "energy_smooth": 0.5, "low": 0.19, "mid": 0.13, "high": 0.02, "onset": 0.3},
            {"time_ms": 500, "downbeat": False, "energy_smooth": 0.1, "low": 0.02, "mid": 0.02, "high": 0.09, "onset": 0.02},
            {"time_ms": 1000, "downbeat": False, "energy_smooth": 0.3, "low": 0.18, "mid": 0.02, "high": 0.02, "onset": 0.02},
        ]

        actions = audio_trigger_routes.build_audio_reactive_actions(timeline)
        effect_names = [str(action["effect"]) for action in actions]

        self.assertIn("downbeat_flash", effect_names)
        self.assertIn("treble_sparkle", effect_names)
        self.assertIn("bass_pulse", effect_names)
        self.assertEqual(actions, audio_trigger_routes.build_audio_reactive_actions(timeline))

        summary = audio_trigger_routes.build_audio_reactive_summary(actions)
        self.assertEqual(summary["action_count"], len(actions))
        self.assertIn("catalog", summary)

    def test_profile_routes_shape_density_and_priorities(self) -> None:
        subtle = {route.effect: route for route in audio_trigger_routes.routes_for_profile("subtle")}
        showcase = {route.effect: route for route in audio_trigger_routes.routes_for_profile("showcase")}

        self.assertGreater(subtle["drop_burst"].threshold, showcase["drop_burst"].threshold)
        self.assertGreater(subtle["bass_pulse"].min_gap_ms, showcase["bass_pulse"].min_gap_ms)
        self.assertGreater(showcase["build_ramp"].priority, subtle["build_ramp"].priority)

    def test_showcase_profile_builds_more_actions_than_subtle(self) -> None:
        timeline = [
            {
                "time_ms": idx * 250,
                "downbeat": idx % 8 == 0,
                "energy_smooth": 0.45,
                "low": 0.17,
                "mid": 0.13,
                "high": 0.09,
                "onset": 0.3,
            }
            for idx in range(24)
        ]

        subtle = audio_trigger_routes.build_audio_reactive_actions(
            timeline,
            routes=audio_trigger_routes.routes_for_profile("subtle"),
        )
        showcase = audio_trigger_routes.build_audio_reactive_actions(
            timeline,
            routes=audio_trigger_routes.routes_for_profile("showcase"),
        )

        self.assertGreater(len(showcase), len(subtle))


if __name__ == "__main__":
    unittest.main()
