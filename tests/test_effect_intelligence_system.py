from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from core import cinematic_planner, effect_layering_engine, signature_style, spatial_choreography, spatial_mapping_engine, spatial_scene, style_engine
from core.sequence_context import SequenceContext


class EffectIntelligenceSystemTests(unittest.TestCase):
    def _write_layout(self, models: list[dict[str, str]]) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = ET.Element("xrgb")
        models_root = ET.SubElement(root, "models")
        for attrs in models:
            ET.SubElement(models_root, "model", attrs)
        layout_path = Path(tempdir.name) / "xlights_rgbeffects.xml"
        ET.ElementTree(root).write(layout_path, encoding="utf-8", xml_declaration=True)
        return layout_path

    def _scene(self) -> spatial_scene.SpatialScene:
        return spatial_scene.load_scene(
            self._write_layout(
                [
                    {
                        "name": "Mega Tree",
                        "DisplayAs": "Tree Flat",
                        "WorldPosX": "0",
                        "WorldPosY": "0",
                        "WorldPosZ": "0",
                        "X2": "0",
                        "Y2": "80",
                        "Z2": "0",
                        "NumStrings": "8",
                        "NodesPerString": "20",
                        "StringType": "RGB Nodes",
                    },
                    {
                        "name": "Front Arch",
                        "DisplayAs": "Arches",
                        "WorldPosX": "100",
                        "WorldPosY": "0",
                        "WorldPosZ": "0",
                        "X2": "50",
                        "Y2": "0",
                        "Z2": "0",
                        "StringType": "RGB Nodes",
                    },
                    {
                        "name": "Main Matrix",
                        "DisplayAs": "Horiz Matrix",
                        "WorldPosX": "200",
                        "WorldPosY": "20",
                        "WorldPosZ": "40",
                        "CustomWidth": "24",
                        "CustomHeight": "12",
                        "StringType": "RGB Nodes",
                    },
                    {
                        "name": "Singer Face",
                        "DisplayAs": "Custom",
                        "WorldPosX": "300",
                        "WorldPosY": "30",
                        "WorldPosZ": "20",
                        "CustomWidth": "12",
                        "CustomHeight": "12",
                        "StringType": "RGB Nodes",
                    },
                    {
                        "name": "AC Gate",
                        "DisplayAs": "Channel Block",
                        "WorldPosX": "400",
                        "WorldPosY": "0",
                        "WorldPosZ": "10",
                        "NumChannels": "1",
                        "StringType": "Single Color Red",
                    },
                ]
            )
        )

    def test_style_detection_override_and_blend_write_context_debug(self) -> None:
        context = SequenceContext(
            audio_features={
                "tempo_bpm": 128,
                "instrumentation": ["synth", "drum_machine"],
                "rhythm_patterns": ["four_on_floor"],
                "percussive_ratio": 0.8,
            }
        )

        detected = style_engine.resolve_style(context)
        blended = style_engine.resolve_style(context, blends={"edm": 0.75, "ambient": 0.25})

        self.assertEqual(detected.detected_style, "edm")
        self.assertEqual(context.style_profile["name"], "edm+ambient")
        self.assertGreater(blended.profile.effect_density, style_engine.STYLE_PROFILES["ambient"].effect_density)
        self.assertIn("style_engine", context.debug)

    def test_spatial_mapping_normalizes_and_adapts_each_model_type(self) -> None:
        scene = self._scene()
        context = SequenceContext(style_profile=style_engine.STYLE_PROFILES["edm"].to_dict())
        plan = spatial_mapping_engine.build_mapping_plan(
            scene,
            points=[
                (0, 0, 0, 0.7),
                (125, 0, 0, 0.8),
                (210, 35, 40, 0.9),
                (300, 35, 20, 0.6),
                (400, 0, 10, 0.75),
            ],
            trajectories=[
                {"name": "rise", "points": [(0.0, 0.0, 0.0, 0.5), (0.5, 1.0, 0.4, 0.8)], "start_ms": 1000, "end_ms": 1600}
            ],
            energy_fields=[{"center": (0.5, 0.5, 0.2, 1.0), "radius": 0.4, "strength": 0.8, "start_ms": 2000, "end_ms": 2400}],
            context=context,
        )

        effects_by_type = {effect.model_type: effect for effect in plan.effects}
        self.assertIn("tree", effects_by_type)
        self.assertIn("arch", effects_by_type)
        self.assertIn("matrix", effects_by_type)
        self.assertIn("face", effects_by_type)
        self.assertIn("ac", effects_by_type)
        self.assertIn("Spirals", {effect.effect for effect in plan.effects if effect.model_type == "tree"})
        self.assertEqual(effects_by_type["arch"].effect, "Wave")
        self.assertIn(effects_by_type["matrix"].effect, {"Shader", "Pictures"})
        self.assertTrue(plan.coverage_visualization["grid"])
        self.assertEqual(context.spatial_features["layout_capability"], scene.capability)

    def test_spatial_mapping_falls_back_when_requested_model_type_is_missing(self) -> None:
        scene = spatial_scene.load_scene(
            self._write_layout(
                [
                    {
                        "name": "Only Matrix",
                        "DisplayAs": "Horiz Matrix",
                        "WorldPosX": "0",
                        "WorldPosY": "0",
                        "WorldPosZ": "0",
                        "CustomWidth": "20",
                        "CustomHeight": "10",
                        "StringType": "RGB Nodes",
                    }
                ]
            )
        )

        plan = spatial_mapping_engine.build_mapping_plan(scene, points=[(0.2, 0.5, 0.0, 0.5), (0.8, 0.5, 0.0, 0.5)])

        self.assertEqual(len(plan.effects), 2)
        self.assertTrue(plan.fallback_logs)
        self.assertTrue(all(effect.model == "Only Matrix" for effect in plan.effects))

    def test_spatial_choreography_builds_cross_prop_dialogue_and_depth_strategy(self) -> None:
        scene = spatial_scene.load_scene(
            self._write_layout(
                [
                    {"name": "Singer Face", "DisplayAs": "Custom", "WorldPosX": "0", "WorldPosY": "0", "CustomWidth": "8", "CustomHeight": "8", "StringType": "RGB Nodes"},
                    {"name": "Floor Piano Notes", "DisplayAs": "Single Line", "WorldPosX": "40", "WorldPosY": "0", "X2": "120", "Y2": "0", "StringType": "RGB Nodes"},
                    {"name": "Front Arches", "DisplayAs": "Arches", "WorldPosX": "80", "WorldPosY": "0", "X2": "80", "Y2": "0", "StringType": "RGB Nodes"},
                    {"name": "Mega Tree", "DisplayAs": "Tree Flat", "WorldPosX": "160", "WorldPosY": "20", "X2": "0", "Y2": "90", "StringType": "RGB Nodes"},
                    {"name": "Roofline", "DisplayAs": "Single Line", "WorldPosX": "0", "WorldPosY": "120", "X2": "220", "Y2": "0", "StringType": "RGB Nodes"},
                ]
            )
        )
        scenes = [
            {"scene_id": "scene_01_verse", "section_label": "verse", "start_ms": 0, "end_ms": 1000, "energy": 0.42, "palette": {"name": "lantern_mix"}},
            {"scene_id": "scene_02_buildup", "section_label": "buildup", "start_ms": 1000, "end_ms": 2200, "energy": 0.64, "palette": {"name": "aurora_mix"}},
            {"scene_id": "scene_03_drop", "section_label": "drop", "start_ms": 2200, "end_ms": 3200, "energy": 0.92, "palette": {"name": "golden_impact"}},
        ]
        band_sync_payload = {
            "performer_focus": [
                {"start_ms": 0, "end_ms": 1000, "primary_focus": "singer"},
                {"start_ms": 1000, "end_ms": 2200, "primary_focus": "environment"},
                {"start_ms": 2200, "end_ms": 3200, "primary_focus": "drummer"},
            ]
        }

        plan = spatial_choreography.build_spatial_choreography_plan(
            scenes,
            layout=scene,
            band_sync_payload=band_sync_payload,
        )
        payload = plan.to_dict()
        families = {family.name: family for family in plan.prop_families}

        self.assertEqual(payload["schema"], "helix.spatial_choreography.v1")
        self.assertTrue(all(families[name].available for name in spatial_choreography.PROP_FAMILIES))
        self.assertEqual(len(plan.dialogue_cues), 3)
        self.assertEqual(plan.dialogue_cues[0].source_family, "band")
        self.assertEqual(plan.dialogue_cues[1].target_family, "arches")
        self.assertEqual(plan.dialogue_cues[2].target_family, "megatree")
        self.assertIn("near", plan.dialogue_cues[2].depth_path)
        self.assertIn("far", plan.dialogue_cues[2].depth_path)
        self.assertIn("impact", {entry.name for entry in plan.motion_grammar})
        self.assertIn("megatree", payload["depth_strategy"]["far"])

    def test_signature_style_builds_key_palettes_and_show_profile_without_phase_11_layer(self) -> None:
        scenes = [
            {"scene_id": "scene_01_intro", "section_label": "intro", "start_ms": 0, "end_ms": 1000, "energy": 0.2},
            {"scene_id": "scene_02_chorus", "section_label": "chorus", "start_ms": 1000, "end_ms": 2400, "energy": 0.86},
            {"scene_id": "scene_03_breakdown", "section_label": "breakdown", "start_ms": 2400, "end_ms": 3400, "energy": 0.28},
            {"scene_id": "scene_04_drop", "section_label": "drop", "start_ms": 3400, "end_ms": 4400, "energy": 0.94},
        ]

        plan = signature_style.build_signature_style_plan(
            scenes,
            song_key="G",
            runtime_tuning={"max_layers_per_prop": 3, "palette_mode": "workspace_match"},
            workspace_history={"palette_pool": ["#123456,#abcdef,#fedcba"]},
            genre_hint="edm",
            mood_hint="energetic",
        )
        payload = plan.to_dict()

        self.assertEqual(payload["schema"], "helix.signature_style.v1")
        self.assertEqual(plan.song_key, "G")
        self.assertEqual(plan.key_palette, signature_style.KEY_PALETTES["G"])
        self.assertEqual(plan.show_profile.brand_palette, ("#123456", "#abcdef", "#fedcba"))
        self.assertEqual(plan.show_profile.pacing_style, "bold_payoff_cycles")
        self.assertLessEqual(plan.show_profile.complexity_ceiling, 5)
        self.assertEqual(len(plan.section_palettes), len(scenes))
        self.assertEqual(plan.section_palettes[1].treatment, "signature_bright")
        self.assertEqual(plan.section_palettes[3].treatment, "impact_flash_guarded")
        self.assertEqual(len(plan.section_dynamics), len(scenes))
        self.assertEqual(plan.section_dynamics[1].decay_curve, "fast_attack_controlled_release")
        self.assertTrue(all(0.0 < dynamic.brightness_modulation < 0.1 for dynamic in plan.section_dynamics))
        self.assertNotIn("humanization", payload)
        self.assertTrue(payload["consistency_rules"])

    def test_cinematic_planner_merges_scene_spatial_and_signature_metadata(self) -> None:
        scene_plan = {
            "scenes": [
                {
                    "scene_id": "scene_01_chorus",
                    "section_label": "chorus",
                    "start_ms": 1000,
                    "end_ms": 2400,
                    "energy": 0.86,
                    "primary_focal_element": "hook_signature",
                    "supporting_layer": "bass_and_harmony_support",
                    "motion_layer": "cascade",
                    "background_ambience": "restrained_wash",
                    "palette": {"primary": "#ffd166", "secondary": "#ef476f", "accent": "#06d6a0"},
                }
            ],
            "transitions": [
                {
                    "start_ms": 850,
                    "end_ms": 1100,
                    "from_scene_id": "scene_00_buildup",
                    "to_scene_id": "scene_01_chorus",
                    "transition_type": "swell_crossfade",
                    "palette_shift": "aurora_to_signature",
                    "energy_delta": 0.42,
                }
            ],
        }
        spatial_payload = {
            "prop_families": [
                {"name": "band", "depth_layer": "near"},
                {"name": "roofline", "depth_layer": "far"},
            ],
            "dialogue_cues": [
                {
                    "scene_id": "scene_01_chorus",
                    "source_family": "band",
                    "target_family": "roofline",
                    "motion": "bloom",
                    "intensity": 0.84,
                }
            ],
            "depth_strategy": {"intensity_scale": {"near": 0.9, "mid": 1.0, "far": 0.82}},
        }
        signature_payload = {
            "section_palettes": [
                {
                    "scene_id": "scene_01_chorus",
                    "colors": ["#ffd166", "#06d6a0", "#ffffff"],
                    "treatment": "signature_bright",
                }
            ],
            "humanization": [
                {
                    "scene_id": "scene_01_chorus",
                    "timing_offset_ms": -9,
                    "brightness_modulation": 0.04,
                    "decay_curve": "fast_attack_controlled_release",
                }
            ],
            "show_profile": {"complexity_ceiling": 3, "motion_intensity_bias": 0.82},
        }

        plan = cinematic_planner.build_cinematic_plan(
            scene_plan,
            spatial_choreography=spatial_payload,
            signature_style=signature_payload,
        )
        payload = plan.to_dict()

        self.assertEqual(payload["schema"], "helix.cinematic_planner.v1")
        self.assertEqual(len(plan.cues), 3)
        self.assertEqual(plan.cues[0].hierarchy_role, "primary")
        self.assertEqual(plan.cues[0].prop_family, "roofline")
        self.assertEqual(plan.cues[0].depth_layer, "far")
        self.assertEqual(plan.cues[0].motion, "bloom")
        self.assertEqual(plan.cues[0].palette, ("#ffd166", "#06d6a0", "#ffffff"))
        self.assertEqual(plan.cues[0].start_ms, 991)
        self.assertEqual(plan.cues[0].decay_curve, "fast_attack_controlled_release")
        self.assertEqual(len(plan.transitions), 1)
        self.assertGreater(plan.transitions[0].intensity, 0.5)
        self.assertEqual(payload["debug_summary"]["role_counts"]["primary"], 1)

    def test_effect_layering_composes_overflow_and_updates_scoring_feedback(self) -> None:
        context = SequenceContext(
            energy_level=0.9,
            dominant_elements=["vocals"],
            band_state={"primary_focus": "singer"},
            emotion_state={"emotion_type": "energetic"},
            style_profile=style_engine.STYLE_PROFILES["pop"].to_dict(),
            scoring_feedback={"clutter_ratio": 0.28, "visual_coherence": 0.7},
        )
        candidates = [
            {"model": "Main Matrix", "effect": "Pictures", "start_ms": 0, "end_ms": 500, "layer": "base", "intensity": 0.6, "source": "harmony"},
            {"model": "Main Matrix", "effect": "Wave", "start_ms": 100, "end_ms": 550, "layer": "motion", "intensity": 0.7, "source": "drums"},
            {"model": "Main Matrix", "effect": "On", "start_ms": 140, "end_ms": 300, "layer": "accent", "intensity": 0.95, "source": "vocals"},
            {"model": "Main Matrix", "effect": "Shader", "start_ms": 160, "end_ms": 520, "layer": "texture", "intensity": 0.8, "source": "spatial"},
        ]

        plan = effect_layering_engine.build_layering_plan(candidates, context=context, max_layers=2)

        self.assertLessEqual(len([effect for effect in plan.layered_effects if effect.model == "Main Matrix"]), 2)
        self.assertGreaterEqual(plan.debug_summary["composited_layer_count"], 1)
        self.assertIn("layered_effect_count", context.scoring_feedback)
        self.assertIn("effect_layering_engine", context.debug)

    def test_effect_layering_enforces_one_primary_focal_element(self) -> None:
        candidates = [
            {"model": "Main Matrix", "effect": "On", "start_ms": 0, "end_ms": 500, "layer": "accent", "intensity": 0.65, "source": "drums"},
            {"model": "Main Matrix", "effect": "Shader", "start_ms": 100, "end_ms": 450, "layer": "focus", "intensity": 0.95, "source": "vocals"},
            {"model": "Main Matrix", "effect": "Wave", "start_ms": 120, "end_ms": 520, "layer": "motion", "intensity": 0.7, "source": "motion"},
            {"model": "Main Matrix", "effect": "Pictures", "start_ms": 0, "end_ms": 520, "layer": "base", "intensity": 0.5, "source": "ambience"},
        ]

        plan = effect_layering_engine.build_layering_plan(candidates, max_layers=4)
        primary = [effect for effect in plan.layered_effects if effect.model == "Main Matrix" and effect.layer_role in {"focus", "accent"}]

        self.assertEqual(len(primary), 1)
        self.assertEqual(primary[0].effect, "Shader")
        self.assertEqual(plan.debug_summary["hierarchy_promoted_count"], 1)


if __name__ == "__main__":
    unittest.main()
