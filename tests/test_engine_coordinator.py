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


if __name__ == "__main__":
    unittest.main()
