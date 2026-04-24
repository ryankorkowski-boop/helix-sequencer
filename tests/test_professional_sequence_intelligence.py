from __future__ import annotations

import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from core import model_parser as xmp
from core import spatial_scene
from helix_composers.ac_composer import compose_ac_moment
from helix_composers.matrix_composer import compose_matrix
from helix_composers.singing_face_composer import compose_singing_face
from helix_composers.snowman_band_composer import map_drummer_parts
from helix_intent.intent_generator import generate_visual_intents
from helix_intent.visual_intent import VisualIntent
from helix_knowledge.models import TechniqueCard
from helix_knowledge.search import search_cards
from helix_knowledge.source_policy import evaluate_source_policy
from helix_knowledge.sqlite_store import TechniqueCardStore
from helix_knowledge.technique_cards import default_technique_cards
from helix_knowledge.user_notes_importer import import_user_notes
from helix_layout.anchor_points import detect_anchor_points
from helix_layout.group_optimizer import optimize_group_order
from helix_layout.layout_health import build_layout_health_report
from helix_layout.prop_roles import classify_prop_role
from helix_layout.semantic_alias_mapper import semantic_alias
from helix_layout.submodel_recommender import recommend_submodels
from helix_mapping.mapping_failure_detector import detect_mapping_failures
from helix_mapping.proxy_models import sample_proxy_model
from helix_mapping.portability_engine import LayoutMappingPlan
from helix_music.section_planner import plan_song_sections
from helix_preview.preview_generator import generate_preview_data
from helix_preview.preview_grader import grade_preview
from helix_render.render_buffer_simulator import simulate_render_buffer
from helix_render.render_style_decision import decide_render_style
from helix_spatial.lookahead_engine import detect_anticipation
from helix_spatial.spatial_fields import AttractorField, PulseField, SweepField
from helix_style.brightness_budget import brightness_budget
from helix_style.curve_envelopes import curve_envelope
from learning import feedback_loop
from core import self_improving_scoring as scoring


class ProfessionalSequenceIntelligenceTests(unittest.TestCase):
    def _model(self, name: str, display_as: str, *, string_type: str = "RGB Nodes", total_pixels: int = 120) -> xmp.Model:
        return xmp.Model(
            name=name,
            display_as=display_as,
            type=display_as.lower(),
            strings=12,
            nodes_per_string=max(1, total_pixels // 12),
            total_pixels=total_pixels,
            start_channel=None,
            coordinates=(0.0, 0.0, 0.0),
            end_coordinates=(10.0, 20.0, 0.0),
            orientation="horizontal",
            wiring=None,
            string_type=string_type,
            color_family="rgb" if "RGB" in string_type else "white",
        )

    def _layout_path(self) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = ET.Element("xrgb")
        models = ET.SubElement(root, "models")
        ET.SubElement(models, "model", {
            "name": "Mega Tree",
            "DisplayAs": "Tree Flat",
            "WorldPosX": "0",
            "WorldPosY": "0",
            "WorldPosZ": "0",
            "X2": "0",
            "Y2": "80",
            "Z2": "0",
            "NumStrings": "12",
            "NodesPerString": "30",
            "StringType": "RGB Nodes",
        })
        ET.SubElement(models, "model", {
            "name": "Main Matrix",
            "DisplayAs": "Horiz Matrix",
            "WorldPosX": "100",
            "WorldPosY": "20",
            "WorldPosZ": "0",
            "CustomWidth": "24",
            "CustomHeight": "12",
            "StringType": "RGB Nodes",
        })
        ET.SubElement(models, "model", {
            "name": "Snowman Face",
            "DisplayAs": "Custom",
            "WorldPosX": "200",
            "WorldPosY": "10",
            "WorldPosZ": "0",
            "CustomWidth": "12",
            "CustomHeight": "12",
            "StringType": "RGB Nodes",
        })
        groups = ET.SubElement(root, "modelGroups")
        ET.SubElement(groups, "modelGroup", {"name": "Whole House", "models": "Mega Tree,Main Matrix,Snowman Face", "centrex": "100", "centrey": "25"})
        path = Path(tempdir.name) / "layout.xml"
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
        return path

    def _learning_payload(self) -> dict:
        return {
            "label": "attempt_a",
            "version": "v27.3",
            "duration_seconds": 40.0,
            "style_profile": {"name": "edm", "effect_density": 0.82},
            "runtime_tuning": {"palette_mode": "template", "layering_mode": "smart_layer"},
            "advanced_audio": {"tempo_bpm": 128.0, "genre_hint": "edm", "mood_hint": "energetic"},
            "placements": {"chorus_hook": 12, "motion_sweep": 8, "matrix_shader": 4},
            "effect_layering": {"layered_effects": [{"model": "Matrix", "effect": "Shader", "layer_role": "base", "blend_mode": "Normal", "intensity": 0.7}]},
            "spatial_mapping": {"mapping_logs": [{"source": "point", "mapped_category": "matrix", "effect": "Shader"}], "coverage_visualization": {"coverage_by_type": {"matrix": 4}}},
            "quality": {
                "score": 92.0,
                "coverage_ratio": 0.82,
                "dominant_family_ratio": 0.28,
                "component_scores": {"density": 88.0, "structure": 92.0, "validation": 94.0, "coverage": 90.0, "family_diversity": 86.0, "dominance": 90.0},
            },
            "audit": {"final": {"score": 92.0, "musical_coherence": 91.0, "intensity_balance": 89.0, "section_coverage": 0.84, "clutter_ratio": 0.05, "section_scores": [{"label": "CHORUS", "start_ms": 0, "end_ms": 1000, "energy": 0.9, "score": 91.0, "coverage_ratio": 0.84, "density": 0.82}]}},
            "watermark": {"version": scoring.HELIX_WATERMARK_POLICY_VERSION, "signature": "ok"},
        }

    def test_technique_card_creation(self) -> None:
        card = default_technique_cards()[0]
        self.assertIsInstance(card, TechniqueCard)
        self.assertEqual(card.source_type, "HELIX_GENERATED_EXPERIMENTS")

    def test_blocked_source_policy(self) -> None:
        decision = evaluate_source_policy("PAID_SEQUENCES", "blocked")
        self.assertFalse(decision.allowed)

    def test_user_authored_notes_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "notes.md"
            path.write_text("Center Out Motion\nUse center anchors.\n\nAC Restraint\nAvoid micro flicker.", encoding="utf-8")
            cards = import_user_notes(path)
            self.assertEqual(len(cards), 2)

    def test_layout_health_report(self) -> None:
        report = build_layout_health_report(self._layout_path())
        self.assertIn("recommendations", report.to_dict())

    def test_prop_role_classification(self) -> None:
        roles = classify_prop_role(self._model("Main Matrix", "matrix"))
        self.assertIn("matrix", roles)

    def test_group_order_optimization(self) -> None:
        scene = spatial_scene.load_scene(self._layout_path())
        ordered = optimize_group_order(["Mega Tree", "Main Matrix", "Snowman Face"], scene, "left_to_right")
        self.assertEqual(ordered[0], "Mega Tree")

    def test_anchor_detection(self) -> None:
        anchors = detect_anchor_points(spatial_scene.load_scene(self._layout_path()))
        self.assertIn("center", anchors)

    def test_submodel_recommendation(self) -> None:
        recs = recommend_submodels(self._model("Mega Tree", "tree"))
        self.assertIn("spiral_lane", recs)

    def test_render_style_decision(self) -> None:
        intent = VisualIntent("id", 0.0, 1.0, "sweep", "section_change", "left_to_right", ["arches"], "medium", "dramatic", "warm", "budgeted", "kick", "per_preview", 0.8)
        plan = decide_render_style(intent, {"visual_readability": 0.8, "render_cost": 0.2}, is_ac=False)
        self.assertIn(plan.render_style, {"per_preview", "per_model_per_preview"})

    def test_render_buffer_scoring(self) -> None:
        sim = simulate_render_buffer(self._model("Main Matrix", "matrix", total_pixels=288))
        self.assertGreater(sim["visual_readability"], 0.0)

    def test_spatial_pulse_sampling(self) -> None:
        value = PulseField((0.0, 0.0, 0.0), 1.0, 1.0).sample((0.2, 0.0, 0.0))
        self.assertGreater(value, 0.0)

    def test_sweep_field_sampling(self) -> None:
        value = SweepField((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.2).sample((0.5, 0.0, 0.0))
        self.assertGreater(value, 0.0)

    def test_attractor_field_proximity(self) -> None:
        near = AttractorField((0.0, 0.0, 0.0), 1.0).sample((0.1, 0.0, 0.0))
        far = AttractorField((0.0, 0.0, 0.0), 1.0).sample((2.0, 0.0, 0.0))
        self.assertGreater(near, far)

    def test_lookahead_anticipation_detection(self) -> None:
        result = detect_anticipation([{"time": 2.0, "type": "drop_hit"}], 1.0, 1.5)
        self.assertTrue(result["anticipation"])

    def test_section_planner_density_budgets(self) -> None:
        sections = plan_song_sections(120.0, "fast")
        chorus = next(section for section in sections if section.name == "chorus")
        self.assertGreater(chorus.density_budget, 0.8)

    def test_brightness_budget_behavior(self) -> None:
        verse = brightness_budget("verse")
        chorus = brightness_budget("chorus")
        self.assertLess(verse["max_total_brightness"], chorus["max_total_brightness"])

    def test_curve_envelope_generation(self) -> None:
        curve = curve_envelope("kick")
        self.assertGreater(len(curve), 2)

    def test_ac_vs_pixel_composer_selection(self) -> None:
        ac = compose_ac_moment("pulse")
        matrix = compose_matrix("waveform", density_budget=0.7)
        self.assertEqual(ac["composer"], "ac")
        self.assertEqual(matrix["composer"], "matrix")

    def test_matrix_composer_low_density_fallback(self) -> None:
        result = compose_matrix("lyric", density_budget=0.2)
        self.assertEqual(result["mode"], "low_density_fallback")

    def test_singing_face_fallback_when_lyrics_missing(self) -> None:
        result = compose_singing_face(has_lyrics=False)
        self.assertEqual(result["mode"], "fallback_vowel_energy")

    def test_snowman_drummer_kick_snare_tom_mapping(self) -> None:
        mapping = map_drummer_parts({"kick_events": [], "snare_events": [], "tom_events": []})
        self.assertEqual(mapping["kick_events"], "kick")
        self.assertEqual(mapping["snare_events"], "snare")
        self.assertEqual(mapping["tom_events"], "tom")

    def test_semantic_alias_matching(self) -> None:
        self.assertEqual(semantic_alias("starburst"), "star")

    def test_mapping_failure_detection(self) -> None:
        failures = detect_mapping_failures(source_density=0.9, target_density=0.3, has_submodel=False, is_ac=True, requires_pixels=True)
        self.assertIn("density_mismatch", failures)
        self.assertIn("AC_pixel_mismatch", failures)

    def test_proxy_model_sampling(self) -> None:
        proxy = sample_proxy_model("virtual_whole_house_matrix", ["A", "B", "C"])
        self.assertEqual(proxy["proxy"], "virtual_whole_house_matrix")

    def test_preview_grading(self) -> None:
        preview = generate_preview_data(layout_name="helixville", intents=[{"id": "a"}, {"id": "b"}], seconds=20)
        grade = grade_preview(preview)
        self.assertIn("preview_grade", grade)

    def test_learning_memory_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = feedback_loop.update_learning_from_sequence(
                memory_path=Path(tmp) / "memory.json",
                payload=self._learning_payload(),
                expected_score=0.72,
            )
            self.assertTrue(result["stored"])

    def test_sqlite_store_and_search(self) -> None:
        fd, raw_path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        path = Path(raw_path)
        def _cleanup_sqlite() -> None:
            try:
                if path.exists():
                    path.unlink()
            except PermissionError:
                pass

        self.addCleanup(_cleanup_sqlite)
        store = TechniqueCardStore(path)
        cards = default_technique_cards()
        store.save_cards(cards)
        loaded = store.load_cards()
        found = search_cards(loaded, "chorus center")
        self.assertTrue(found)

    def test_portability_engine_plan(self) -> None:
        plan = LayoutMappingPlan(
            song_analysis={"tempo": 128},
            visual_intents=[item.to_dict() for item in generate_visual_intents([section.to_dict() for section in plan_song_sections(60.0)])[:2]],
            layout_mapping={"layout": "helixville"},
            render_style_plan=[{"render_style": "per_preview"}],
            effect_export_plan={"debug_sidecar": "helix_export_debug.json"},
        )
        self.assertIn("song_analysis", plan.to_dict())


if __name__ == "__main__":
    unittest.main()
