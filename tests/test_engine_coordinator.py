import unittest

from core.engine_coordinator import (
    AudioAnalysisContext,
    CallableEngineAdapter,
    ConflictStrategy,
    EngineEffectCandidate,
    EnginePolicy,
    LayoutProp,
    SectionWindow,
    build_default_coordinator,
)


def _make_context() -> AudioAnalysisContext:
    return AudioAnalysisContext(
        audio_path="audio/test_track.wav",
        duration_ms=8000,
        bpm=120.0,
        beat_grid_ms=(0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000),
        sections=(
            SectionWindow(name="intro", start_ms=0, end_ms=4000, energy=0.4),
            SectionWindow(name="chorus", start_ms=4000, end_ms=8000, energy=0.9),
        ),
    )


class TestEngineCoordinator(unittest.TestCase):
    def test_role_lane_enforcement_and_beat_snapping(self) -> None:
        ctx = _make_context()
        self.assertEqual(len(ctx.fingerprint), 64)
        self.assertEqual(ctx.section_for_ms(1200).name, "intro")
        self.assertEqual(ctx.snap_ms(980), 1000)

        props = [LayoutProp(prop_id="arch_1", prop_type="arch", max_layers=2)]
        birdsong_adapter = CallableEngineAdapter(
            "birdsong",
            lambda c, p: [
                EngineEffectCandidate(
                    engine_id="birdsong",
                    prop_id="arch_1",
                    role="base",
                    effect_type="wash",
                    start_ms=10,
                    end_ms=1990,
                ),
                EngineEffectCandidate(
                    engine_id="birdsong",
                    prop_id="arch_1",
                    role="accent",
                    effect_type="shimmer",
                    start_ms=490,
                    end_ms=1510,
                ),
            ],
        )
        coordinator = build_default_coordinator(adapters=[birdsong_adapter])
        result = coordinator.coordinate(ctx, props)

        self.assertEqual(result.report.total_candidates, 2)
        self.assertEqual(result.report.accepted_count, 1)
        self.assertEqual(result.report.rejected_count, 1)
        rejected = [d for d in result.report.decisions if not d.accepted]
        self.assertEqual(rejected[0].reason, "role_not_allowed")

        planned = result.planned_effects[0]
        self.assertEqual(planned.role, "accent")
        self.assertEqual(planned.start_ms, 500)
        self.assertEqual(planned.end_ms, 1500)

    def test_trim_ducking_on_single_layer_prop(self) -> None:
        ctx = _make_context()
        props = [LayoutProp(prop_id="tree_1", prop_type="tree", max_layers=1)]
        base_adapter = CallableEngineAdapter(
            "core_base",
            lambda c, p: [
                EngineEffectCandidate(
                    engine_id="core_base",
                    prop_id="tree_1",
                    role="base",
                    effect_type="solid_wash",
                    start_ms=0,
                    end_ms=4000,
                    score=0.5,
                )
            ],
        )
        focus_adapter = CallableEngineAdapter(
            "drum_effects",
            lambda c, p: [
                EngineEffectCandidate(
                    engine_id="drum_effects",
                    prop_id="tree_1",
                    role="focus",
                    effect_type="strobe_hit",
                    start_ms=1000,
                    end_ms=2000,
                    score=0.9,
                )
            ],
        )
        coordinator = build_default_coordinator(adapters=[base_adapter, focus_adapter])
        result = coordinator.coordinate(ctx, props)

        windows = [(e.engine_id, e.start_ms, e.end_ms, e.layer_index) for e in result.planned_effects]
        self.assertEqual(
            windows,
            [
                ("core_base", 0, 1000, 0),
                ("drum_effects", 1000, 2000, 0),
                ("core_base", 2000, 4000, 0),
            ],
        )

    def test_stack_layering_across_multi_layer_prop(self) -> None:
        ctx = _make_context()
        props = [LayoutProp(prop_id="matrix_1", prop_type="matrix", max_layers=2)]
        base_adapter = CallableEngineAdapter(
            "core_base",
            lambda c, p: [
                EngineEffectCandidate(
                    engine_id="core_base",
                    prop_id="matrix_1",
                    role="base",
                    effect_type="wash",
                    start_ms=0,
                    end_ms=2000,
                )
            ],
        )
        focus_adapter = CallableEngineAdapter(
            "matrix_intelligence",
            lambda c, p: [
                EngineEffectCandidate(
                    engine_id="matrix_intelligence",
                    prop_id="matrix_1",
                    role="focus",
                    effect_type="text_overlay",
                    start_ms=500,
                    end_ms=1500,
                )
            ],
        )
        coordinator = build_default_coordinator(adapters=[base_adapter, focus_adapter])
        result = coordinator.coordinate(ctx, props)

        self.assertEqual(len(result.planned_effects), 2)
        layers = {e.engine_id: e.layer_index for e in result.planned_effects}
        self.assertEqual(layers["matrix_intelligence"], 0)
        self.assertEqual(layers["core_base"], 1)

    def test_section_budget_and_cooldown_enforcement(self) -> None:
        ctx = _make_context()
        props = [LayoutProp(prop_id="arch_1", prop_type="arch", max_layers=3)]
        policies = {
            "custom_accent": EnginePolicy(
                engine_id="custom_accent",
                allowed_roles=("accent",),
                max_per_section=2,
                cooldown_ms=600,
                conflict_strategy=ConflictStrategy.STACK,
                fallback_strategy=ConflictStrategy.TRIM,
                snap_to_beat=False,
            )
        }
        adapter = CallableEngineAdapter(
            "custom_accent",
            lambda c, p: [
                EngineEffectCandidate("custom_accent", "arch_1", "accent", "hit", 0, 200, score=0.9),
                EngineEffectCandidate("custom_accent", "arch_1", "accent", "hit", 400, 600, score=0.8),
                EngineEffectCandidate("custom_accent", "arch_1", "accent", "hit", 1000, 1200, score=0.7),
                EngineEffectCandidate("custom_accent", "arch_1", "accent", "hit", 2000, 2200, score=0.6),
            ],
        )
        coordinator = build_default_coordinator(adapters=[adapter], policies=policies)
        result = coordinator.coordinate(ctx, props)

        self.assertEqual(len(result.planned_effects), 2)
        reasons = [d.reason for d in result.report.decisions if not d.accepted]
        self.assertIn("cooldown_active", reasons)
        self.assertIn("section_budget_exceeded", reasons)

    def test_fault_isolation_and_zero_overlaps(self) -> None:
        ctx = _make_context()
        props = [LayoutProp(prop_id="prop_1", prop_type="generic", max_layers=2)]

        def failing_engine(c: AudioAnalysisContext, p: list[LayoutProp]) -> list[EngineEffectCandidate]:
            raise RuntimeError("boom")

        broken_adapter = CallableEngineAdapter("broken_engine", failing_engine)
        base_adapter = CallableEngineAdapter(
            "core_base",
            lambda c, p: [
                EngineEffectCandidate("core_base", "prop_1", "base", "wash", 0, 3000, score=0.5),
            ],
        )
        accent_adapter = CallableEngineAdapter(
            "drum_effects",
            lambda c, p: [
                EngineEffectCandidate("drum_effects", "prop_1", "accent", "pulse", 500, 1500, score=0.8),
                EngineEffectCandidate("drum_effects", "prop_1", "focus", "flash", 1000, 2000, score=0.95),
            ],
        )
        coordinator = build_default_coordinator(adapters=[broken_adapter, base_adapter, accent_adapter])
        result = coordinator.coordinate(ctx, props)

        self.assertEqual(result.errors, {"broken_engine": "boom"})
        self.assertGreaterEqual(len(result.planned_effects), 3)
        self.assertIn("decisions", result.report.to_dict())

        by_lane: dict[tuple[str, int], list[tuple[int, int]]] = {}
        for eff in result.planned_effects:
            by_lane.setdefault((eff.prop_id, eff.layer_index), []).append((eff.start_ms, eff.end_ms))
        for lane, windows in by_lane.items():
            for i in range(len(windows) - 1):
                self.assertLessEqual(
                    windows[i][1],
                    windows[i + 1][0],
                    f"Overlap detected on {lane}: {windows[i]} vs {windows[i + 1]}",
                )


class TestShowMasteringAndAdapters(unittest.TestCase):
    def test_negative_space_restraint(self) -> None:
        from core.engine_coordinator import CoordinationResult, ArbitrationReport, PlannedEffect
        from core.show_mastering import ProShowMaster, ShowMasteringConfig

        ctx = AudioAnalysisContext(
            duration_ms=8000,
            bpm=120.0,
            sections=(
                SectionWindow("intro", 0, 4000, energy=0.25),
                SectionWindow("chorus", 4000, 8000, energy=0.90),
            ),
        )
        props = [
            LayoutProp("hero_tree", "mega_tree", max_layers=2, tags=("hero",)),
            LayoutProp("arch_1", "arch", max_layers=1),
            LayoutProp("arch_2", "arch", max_layers=1),
            LayoutProp("mini_1", "mini_tree", max_layers=1),
        ]
        planned = (
            PlannedEffect("drum_effects", "hero_tree", "focus", "spiral", 0, 4000, score=0.95, priority=5, section_name="intro"),
            PlannedEffect("core_base", "arch_1", "base", "wash", 0, 4000, score=0.5, priority=1, section_name="intro"),
            PlannedEffect("core_base", "arch_2", "base", "wash", 0, 4000, score=0.4, priority=1, section_name="intro"),
            PlannedEffect("core_base", "mini_1", "base", "wash", 0, 4000, score=0.3, priority=1, section_name="intro"),
            PlannedEffect("drum_effects", "hero_tree", "focus", "spiral", 4000, 8000, score=0.95, priority=5, section_name="chorus"),
            PlannedEffect("core_base", "arch_1", "base", "wash", 4000, 8000, score=0.6, priority=1, section_name="chorus"),
            PlannedEffect("core_base", "arch_2", "base", "wash", 4000, 8000, score=0.5, priority=1, section_name="chorus"),
            PlannedEffect("core_base", "mini_1", "base", "wash", 4000, 8000, score=0.4, priority=1, section_name="chorus"),
        )
        result = CoordinationResult(planned_effects=planned, report=ArbitrationReport())
        mastered = ProShowMaster(ShowMasteringConfig(enforce_negative_space=True)).master_plan(result, ctx, props)

        intro_props = {e.prop_id for e in mastered.planned_effects if e.section_name == "intro"}
        chorus_props = {e.prop_id for e in mastered.planned_effects if e.section_name == "chorus"}
        self.assertEqual(intro_props, {"hero_tree"})
        self.assertGreaterEqual(len(chorus_props), 3)

    def test_unified_palette_locking_and_character_exemption(self) -> None:
        from core.engine_coordinator import CoordinationResult, ArbitrationReport, PlannedEffect
        from core.show_mastering import DEFAULT_PALETTES, ProShowMaster, ShowMasteringConfig

        ctx = AudioAnalysisContext(
            duration_ms=4000,
            bpm=150.0,
            sections=(SectionWindow("chorus", 0, 4000, energy=0.9),),
        )
        props = [
            LayoutProp("tree_1", "mega_tree"),
            LayoutProp("arch_1", "arch"),
            LayoutProp("snowman_1", "snowman", tags=("character",)),
        ]
        planned = (
            PlannedEffect("core_base", "tree_1", "base", "wash", 0, 4000, section_name="chorus", params={"colors": ["#111111"]}),
            PlannedEffect("drum_effects", "arch_1", "accent", "pulse", 0, 4000, section_name="chorus", params={"colors": ["#222222"]}),
            PlannedEffect("snowman_band", "snowman_1", "motion", "sing", 0, 4000, section_name="chorus", params={"colors": ["#FFFFFF"]}),
        )
        result = CoordinationResult(planned_effects=planned, report=ArbitrationReport())
        cfg = ShowMasteringConfig(palette_name="winter_aurora", enforce_negative_space=False), lock_palette=True
        mastered = ProShowMaster(cfg).master_plan(result, ctx, props)

        expected_primary = DEFAULT_PALETTES["winter_aurora"].primary
        by_prop = {e.prop_id: e for e in mastered.planned_effects}
        self.assertEqual(by_prop["tree_1"].params["primary_color"], expected_primary)
        self.assertEqual(by_prop["arch_1"].params["primary_color"], expected_primary)
        self.assertEqual(by_prop["tree_1"].params["colors"], by_prop["arch_1"].params["colors"])
        self.assertEqual(by_prop["snowman_1"].params["colors"], ["#FFFFFF"])
        self.assertEqual(by_prop["tree_1"].params["bpm_speed_scale"], 1.25)
        self.assertEqual(by_prop["tree_1"].params["fade_in_ms"], 150)

    def test_pre_drop_anticipation_breath_carving(self) -> None:
        from core.engine_coordinator import CoordinationResult, ArbitrationReport, PlannedEffect
        from core.show_mastering import ProShowMaster, ShowMasteringConfig

        ctx = AudioAnalysisContext(
            duration_ms=8000,
            bpm=120.0,
            sections=(
                SectionWindow("verse", 0, 4000, energy=0.45),
                SectionWindow("chorus", 4000, 8000, energy=0.95),
            ),
        )
        props = [LayoutProp("tree_1", "mega_tree", max_layers=2)]
        planned = (
            PlannedEffect("core_base", "tree_1", "base", "wash", 0, 4000, section_name="verse"),
            PlannedEffect("drum_effects", "tree_1", "focus", "flash", 3000, 4000, layer_index=1, section_name="verse"),
        )
        result = CoordinationResult(planned_effects=planned, report=ArbitrationReport())
        cfg = ShowMasteringConfig(anticipation_breath_ms=100, enforce_negative_space=False)
        mastered = ProShowMaster(cfg).master_plan(result, ctx, props)

        base_eff = [e for e in mastered.planned_effects if e.role == "base"][0]
        focus_eff = [e for e in mastered.planned_effects if e.role == "focus"][0]
        self.assertEqual(base_eff.end_ms, 3900)
        self.assertEqual(focus_eff.end_ms, 4000)

    def test_chorus_motif_continuity_bonus(self) -> None:
        from core.show_mastering import ProShowMaster, ShowMasteringConfig

        ctx = AudioAnalysisContext(
            duration_ms=12000,
            bpm=120.0,
            sections=(
                SectionWindow("chorus", 0, 4000, energy=0.9),
                SectionWindow("verse", 4000, 8000, energy=0.45),
                SectionWindow("chorus", 8000, 12000, energy=0.9),
            ),
        )
        candidates = [
            EngineEffectCandidate("drum_effects", "tree_1", "focus", "spiral_burst", 0, 4000, score=0.90),
            EngineEffectCandidate("drum_effects", "tree_1", "focus", "spiral_chase", 8000, 12000, score=0.70),
            EngineEffectCandidate("drum_effects", "tree_1", "accent", "bars_pulse", 8000, 12000, score=0.75),
        ]
        boosted = ProShowMaster(ShowMasteringConfig(motif_bonus=0.15)).apply_motif_continuity(candidates, ctx)
        chase = [c for c in boosted if c.effect_type == "spiral_chase"][0]
        bars = [c for c in boosted if c.effect_type == "bars_pulse"][0]
        self.assertAlmostEqual(chase.score, 0.85, places=5)
        self.assertTrue(chase.metadata.get("motif_callback"))
        self.assertEqual(bars.score, 0.75)

    def test_adapter_registration_and_graceful_fallback(self) -> None:
        from core.engine_adapters import DrumEffectsAdapter, DEFAULT_ADAPTER_CLASSES
        from core.sequence_builder import coordinate_sub_engines, create_engine_coordinator

        coordinator = create_engine_coordinator(register_defaults=True)
        for cls in DEFAULT_ADAPTER_CLASSES:
            self.assertIn(cls.engine_id, coordinator._adapters)

        ctx = AudioAnalysisContext(
            duration_ms=4000,
            bpm=120.0,
            sections=(SectionWindow("chorus", 0, 4000, energy=0.9),),
        )
        props = [LayoutProp("tree_1", "mega_tree")]

        disabled = DrumEffectsAdapter(enabled=False, target_callable=lambda c, p: [{"prop_id": "tree_1", "start_ms": 0, "end_ms": 1000}])
        self.assertEqual(disabled.generate_candidates(ctx, props), [])

        bad_sig = DrumEffectsAdapter(target_callable=lambda only_one: [])
        self.assertEqual(bad_sig.generate_candidates(ctx, props), [])

        dict_adapter = DrumEffectsAdapter(
            target_callable=lambda c, p: [
                {"prop_id": "tree_1", "role": "invalid_lane", "effect_type": "hit", "start_ms": 0, "end_ms": 1000, "score": 0.9}
            ]
        )
        normalized = dict_adapter.generate_candidates(ctx, props)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0].role, "accent")

        result = coordinate_sub_engines(ctx, props, adapters=[dict_adapter])
        self.assertEqual(len(result.planned_effects), 1)
        self.assertIn("palette_name", result.planned_effects[0].params)

    def test_show_mastering_default_vibrant_all_props_and_soft_hierarchy(self) -> None:
        master = ProShowMaster(ShowMasteringConfig())
        ctx = AudioAnalysisContext(duration_ms=4000, bpm=120.0, sections=(SectionWindow("verse", 0, 4000, energy=0.45),))
        props = [LayoutProp("tree_1", "mega_tree"), LayoutProp("arch_1", "arch"), LayoutProp("house_1", "matrix"), LayoutProp("roof_1", "roofline")]
        planned = [
            PlannedEffect("tree_1", "tree", 0, 4000, "focus", "spiral", 1, {"color": "#FF00AA", "palette_name": "neon"}),
            PlannedEffect("arch_1", "arch", 0, 4000, "accent", "chase", 0, {"color": "#00FF88", "palette_name": "emerald"}),
            PlannedEffect("house_1", "matrix", 0, 4000, "base", "wash", 0, {"color": "#3366FF", "palette_name": "ocean"}),
            PlannedEffect("roof_1", "roofline", 0, 4000, "texture", "twinkle", 0, {"color": "#FFFF00", "palette_name": "gold"}),
        ]
        result = CoordinationResult(planned_effects=planned, report=ArbitrationReport(4, 4, 0, 0, 0, {}))
        mastered = master.master_plan(result, ctx, props)
        by_prop = {e.prop_id: e for e in mastered.planned_effects}
        self.assertEqual(set(by_prop.keys()), {"tree_1", "arch_1", "house_1", "roof_1"})
        for e in planned:
            self.assertEqual(by_prop[e.prop_id].params["color"], e.params["color"])
        self.assertGreater(by_prop["tree_1"].params["brightness_scale"], by_prop["house_1"].params["brightness_scale"])
        self.assertGreater(by_prop["arch_1"].params["brightness_scale"], by_prop["house_1"].params["brightness_scale"])
        self.assertGreater(by_prop["tree_1"].params["brightness_scale"], by_prop["roof_1"].params["brightness_scale"])
        self.assertGreater(by_prop["arch_1"].params["brightness_scale"], by_prop["roof_1"].params["brightness_scale"])
        self.assertGreater(by_prop["roof_1"].params["brightness_scale"], 0.0)
        self.assertEqual(len({(e.prop_id, e.layer_index) for e in mastered.planned_effects}), len(mastered.planned_effects))
            
        
if __name__ == "__main__":
    unittest.main()
