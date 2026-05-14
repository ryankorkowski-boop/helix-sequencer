from __future__ import annotations

import unittest
from types import SimpleNamespace

from core import contrast_engine, energy_model, motif_fingerprinting, scene_engine, song_structure


class MusicalIntelligenceTests(unittest.TestCase):
    def test_energy_model_builds_per_beat_energy_ramps_and_accents(self) -> None:
        audio = SimpleNamespace(
            dur_s=2.0,
            times_s=[0.0, 0.5, 1.0, 1.5, 2.0],
            rms01=[0.1, 0.2, 0.75, 0.9, 0.25],
        )
        multiband = SimpleNamespace(
            frame_times_s=[0.0, 0.5, 1.0, 1.5, 2.0],
            spectral_flux01=[0.05, 0.2, 0.8, 0.85, 0.15],
            chroma_stability01=[0.8, 0.72, 0.35, 0.28, 0.74],
            spectral_flux_marks=[1000, 1500],
            descriptor_summary={"chroma_stability_mean": 0.52},
        )

        curve = energy_model.build_energy_curve(
            audio=audio,
            beat_ms=[0, 500, 1000, 1500, 2000],
            onset_ms=[1000, 1500],
            multiband=multiband,
            percussion_ms=[1000, 1500],
        )

        self.assertEqual(len(curve.points), 5)
        self.assertGreater(curve.sample(1500), curve.sample(500))
        self.assertTrue(curve.macro_ramps)
        self.assertTrue(curve.micro_accents)
        self.assertIn("beat_energy", curve.to_dict())

    def test_song_structure_classifies_canonical_sections(self) -> None:
        audio = SimpleNamespace(dur_s=8.0, times_s=[idx for idx in range(9)], rms01=[0.1, 0.2, 0.34, 0.54, 0.9, 0.82, 0.42, 0.25, 0.12])
        sections = [
            SimpleNamespace(label="INTRO", start_ms=0, end_ms=1500, energy=0.1),
            SimpleNamespace(label="", start_ms=1500, end_ms=3000, energy=0.3),
            SimpleNamespace(label="BUILD", start_ms=3000, end_ms=4500, energy=0.6),
            SimpleNamespace(label="DROP", start_ms=4500, end_ms=6500, energy=0.9),
            SimpleNamespace(label="OUTRO", start_ms=6500, end_ms=8000, energy=0.2),
        ]

        timeline = song_structure.detect_song_structure(
            audio=audio,
            beat_ms=[idx * 500 for idx in range(17)],
            onset_ms=[3000, 4500, 5000],
            sections=sections,
        )

        labels = [section.label for section in timeline.sections]
        self.assertIn("intro", labels)
        self.assertIn("buildup", labels)
        self.assertIn("drop", labels)
        self.assertIn("outro", labels)
        self.assertTrue(set(labels).issubset(set(song_structure.CANONICAL_SECTION_LABELS)))

    def test_motif_fingerprinting_detects_repeated_hook(self) -> None:
        events = [
            SimpleNamespace(start_ms=0, end_ms=180, notes=[(60, 0.8), (64, 0.7)], part="VERSE", section="verse"),
            SimpleNamespace(start_ms=1000, end_ms=1180, notes=[(62, 0.9), (66, 0.7)], part="CHORUS", section="chorus"),
            SimpleNamespace(start_ms=2000, end_ms=2180, notes=[(67, 0.6), (71, 0.6)], part="CHORUS", section="chorus"),
            SimpleNamespace(start_ms=3000, end_ms=3180, notes=[(60, 0.8), (67, 0.7)], part="BRIDGE", section="bridge"),
        ]

        report = motif_fingerprinting.build_motif_report(events)

        self.assertEqual(report["motif_count"], 1)
        hook = report["hooks"][0]
        self.assertGreaterEqual(hook["repeat_count"], 3)
        self.assertGreater(hook["hook_score"], 0.5)

    def test_contrast_engine_alternates_visual_pressure(self) -> None:
        sections = [
            SimpleNamespace(label="intro", start_ms=0, end_ms=1000, energy=0.2),
            SimpleNamespace(label="chorus", start_ms=1000, end_ms=2000, energy=0.78),
            SimpleNamespace(label="breakdown", start_ms=2000, end_ms=3000, energy=0.28),
            SimpleNamespace(label="drop", start_ms=3000, end_ms=4000, energy=0.9),
        ]

        plan = contrast_engine.build_contrast_plan(sections)
        densities = [decision.density for decision in plan.decisions]
        brightness = [decision.brightness for decision in plan.decisions]

        self.assertIn("sparse", densities)
        self.assertIn("dense", densities)
        self.assertIn("bright", brightness)
        self.assertEqual(plan.to_dict()["schema"], "helix.contrast_engine.v1")

    def test_scene_engine_builds_scenes_transitions_and_palette_evolution(self) -> None:
        sections = [
            SimpleNamespace(label="intro", start_ms=0, end_ms=1000, energy=0.2),
            SimpleNamespace(label="buildup", start_ms=1000, end_ms=2200, energy=0.58),
            SimpleNamespace(label="drop", start_ms=2200, end_ms=3400, energy=0.9),
            SimpleNamespace(label="outro", start_ms=3400, end_ms=4400, energy=0.22),
        ]
        contrast_plan = contrast_engine.build_contrast_plan(sections)
        motif_report = {
            "hooks": [
                {
                    "fingerprint": {"key": "rise:0,4:2,2"},
                    "occurrences": [{"start_ms": 2250, "end_ms": 2350}],
                }
            ]
        }

        plan = scene_engine.build_scene_plan(
            sections,
            contrast_plan=contrast_plan,
            motif_report=motif_report,
        )
        payload = plan.to_dict()

        self.assertEqual(payload["schema"], "helix.scene_engine.v1")
        self.assertEqual(len(plan.scenes), 4)
        self.assertEqual(len(plan.transitions), 3)
        self.assertEqual(plan.scenes[2].scene_mode, "impact_release")
        self.assertEqual(plan.scenes[2].primary_focal_element, "percussion_impact")
        self.assertIn("rise:0,4:2,2", plan.scenes[2].motif_keys)
        self.assertTrue(any(item.transition_type in {"blackout_impact", "swell_crossfade"} for item in plan.transitions))
        self.assertEqual(len(payload["palette_evolution"]), 4)


if __name__ == "__main__":
    unittest.main()
