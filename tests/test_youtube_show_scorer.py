from __future__ import annotations

import unittest

from core import youtube_show_scorer as scorer


def focused_payload() -> dict:
    return {
        "sections": [
            {
                "label": "intro",
                "focal_target": "faces",
                "active_props": ["faces", "rooflines"],
                "layers": ["background", "focal"],
                "colors": ["blue", "white"],
                "motion": "left_to_right",
                "brightness": 0.22,
                "density": 0.18,
                "has_rest": True,
                "prop_roles": {"faces": "vocals", "rooflines": "structure"},
            },
            {
                "label": "verse 1",
                "focal_target": "faces",
                "active_props": ["faces", "rooflines", "mini_trees"],
                "layers": ["background", "motion", "focal"],
                "colors": ["blue", "white", "gold"],
                "motion": "call_response",
                "brightness": 0.38,
                "density": 0.35,
                "prop_roles": {"faces": "vocals", "rooflines": "structure", "mini_trees": "beat"},
            },
            {
                "label": "chorus 1",
                "focal_target": "mega_tree",
                "active_props": ["mega_tree", "arches", "rooflines"],
                "layers": ["background", "motion", "focal"],
                "colors": ["red", "green", "white"],
                "motion": "center_outward",
                "brightness": 0.62,
                "density": 0.58,
                "prop_roles": {"mega_tree": "hero", "arches": "travel", "rooflines": "structure"},
            },
            {
                "label": "finale",
                "focal_target": "full_house",
                "active_props": ["full_house", "mega_tree", "arches", "rooflines"],
                "layers": ["background", "motion", "accent"],
                "colors": ["red", "green", "white", "gold"],
                "motion": "wave_handoff",
                "brightness": 0.88,
                "density": 0.82,
                "prop_roles": {"full_house": "payoff", "mega_tree": "hero", "arches": "travel"},
            },
        ]
    }


class YoutubeShowScorerTests(unittest.TestCase):
    def test_focused_output_scores_higher_than_cluttered_output(self) -> None:
        focused = focused_payload()
        cluttered = {
            "sections": [
                {
                    "label": "verse",
                    "active_props": ["faces", "mega_tree", "matrix", "arches", "rooflines", "windows", "floods", "mini_trees"],
                    "layers": ["base", "texture", "motion", "accent", "focus", "sparkle"],
                    "colors": ["red", "green", "blue", "white", "gold", "purple", "rainbow"],
                    "motion": "random",
                    "brightness": 0.92,
                    "density": 0.95,
                }
            ]
        }

        self.assertGreater(scorer.score_youtube_show(focused)["final_score"], scorer.score_youtube_show(cluttered)["final_score"])

    def test_darkness_rest_usage_improves_score(self) -> None:
        with_rests = focused_payload()
        no_rests = focused_payload()
        for section in no_rests["sections"]:
            section["has_rest"] = False
            section["brightness"] = 0.78
            section["density"] = 0.78

        self.assertGreater(
            scorer.score_youtube_show(with_rests)["darkness_usage"],
            scorer.score_youtube_show(no_rests)["darkness_usage"],
        )

    def test_excessive_simultaneous_layers_are_penalized(self) -> None:
        controlled = focused_payload()
        excessive = focused_payload()
        excessive["sections"][1]["layers"] = ["base", "texture", "motion", "accent", "focus", "sparkle"]

        self.assertGreater(
            scorer.score_youtube_show(controlled)["layer_control"],
            scorer.score_youtube_show(excessive)["layer_control"],
        )
        self.assertGreater(
            scorer.score_youtube_show(excessive)["clutter_penalty"],
            scorer.score_youtube_show(controlled)["clutter_penalty"],
        )

    def test_controlled_color_palette_scores_higher_than_rainbow_spam(self) -> None:
        controlled = focused_payload()
        rainbow = focused_payload()
        for section in rainbow["sections"]:
            section["colors"] = ["red", "orange", "yellow", "green", "blue", "purple", "rainbow", "random"]

        self.assertGreater(
            scorer.score_youtube_show(controlled)["color_discipline"],
            scorer.score_youtube_show(rainbow)["color_discipline"],
        )

    def test_chorus_finale_escalation_improves_score(self) -> None:
        escalating = focused_payload()
        flat = focused_payload()
        for section in flat["sections"]:
            section["brightness"] = 0.45
            section["density"] = 0.45

        self.assertGreater(
            scorer.score_youtube_show(escalating)["escalation"],
            scorer.score_youtube_show(flat)["escalation"],
        )

    def test_final_score_is_bounded_from_zero_to_one_hundred(self) -> None:
        for payload in (
            {},
            focused_payload(),
            {"sections": [{"label": "chaos", "layers": list(range(40)), "colors": list(range(40)), "active_props": list(range(40))}]},
        ):
            score = scorer.score_youtube_show(payload)["final_score"]
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 100.0)


if __name__ == "__main__":
    unittest.main()
