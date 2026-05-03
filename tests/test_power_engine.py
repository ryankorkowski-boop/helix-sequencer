from __future__ import annotations

import unittest

from core.power_engine import CircuitMeta, FrameInput, FramePropState, PropPowerMeta, analyze_power, estimate_prop_watts


class PowerEngineTests(unittest.TestCase):
    def test_estimate_prop_watts_formula(self) -> None:
        prop = PropPowerMeta(
            prop_id="megatree_1",
            pixels=1000,
            voltage=12.0,
            watts_per_pixel_full_white=0.3,
            circuit_id="A",
            priority="focal",
        )
        watts = estimate_prop_watts(prop, active_pixel_fraction=0.5, intensity_fraction=0.5)
        self.assertAlmostEqual(watts, 75.0, places=6)

    def test_under_limit_sequence_remains_safe(self) -> None:
        props = [
            PropPowerMeta("prop_1", 300, 12.0, 0.3, "A", "background"),
        ]
        circuits = [
            CircuitMeta("A", breaker_limit_amps=15.0, safe_utilization=0.8, voltage=120.0),
        ]
        frames = [
            FrameInput(timestamp_ms=0, props=[FramePropState("prop_1", 0.2, 0.3)]),
        ]
        logs, report = analyze_power(frames=frames, props=props, circuits=circuits)
        self.assertEqual(len(logs), 1)
        self.assertTrue(report.safe_after_processing)
        self.assertEqual(report.frames_adjusted, 0)
        self.assertEqual(report.corrections_applied, [])
        self.assertAlmostEqual(float(logs[0]["intensity_by_prop"]["prop_1"]), 0.3, places=6)

    def test_over_limit_sequence_is_reduced_and_reported(self) -> None:
        props = [
            PropPowerMeta("prop_1", 2000, 12.0, 0.8, "A", "background"),
        ]
        circuits = [
            CircuitMeta("A", breaker_limit_amps=5.0, safe_utilization=0.8, voltage=120.0),
        ]
        frames = [
            FrameInput(timestamp_ms=100, props=[FramePropState("prop_1", 1.0, 1.0)]),
        ]
        logs, report = analyze_power(frames=frames, props=props, circuits=circuits)
        self.assertGreater(len(report.overload_events), 0)
        self.assertGreater(float(report.overload_events[0]["overload_amps"]), 0.0)
        self.assertGreater(len(report.corrections_applied), 0)
        self.assertTrue(report.safe_after_processing)
        self.assertLessEqual(float(logs[0]["amps_by_circuit"]["A"]), 4.0 + 1e-6)

    def test_focal_preserved_before_background(self) -> None:
        props = [
            PropPowerMeta("focal", 1000, 12.0, 0.3, "A", "focal"),
            PropPowerMeta("bg", 1000, 12.0, 0.3, "A", "background"),
        ]
        circuits = [
            CircuitMeta("A", breaker_limit_amps=4.0, safe_utilization=1.0, voltage=120.0),
        ]
        frames = [
            FrameInput(
                timestamp_ms=0,
                props=[
                    FramePropState("focal", 1.0, 1.0, is_accent=False, effect_family="accent"),
                    FramePropState("bg", 1.0, 1.0, is_accent=False, effect_family="wash"),
                ],
            ),
        ]
        logs, report = analyze_power(frames=frames, props=props, circuits=circuits)
        self.assertTrue(report.safe_after_processing)
        focal_watts = float(logs[0]["watts_by_prop"]["focal"])
        bg_watts = float(logs[0]["watts_by_prop"]["bg"])
        self.assertAlmostEqual(focal_watts, 300.0, places=4)
        self.assertLess(bg_watts, 300.0)
        self.assertLessEqual(float(logs[0]["amps_by_circuit"]["A"]), 4.0 + 1e-6)

    def test_report_schema_is_stable(self) -> None:
        props = []
        circuits = [CircuitMeta("A", breaker_limit_amps=15.0, safe_utilization=0.8, voltage=120.0)]
        frames = [FrameInput(timestamp_ms=0, props=[])]
        _, report = analyze_power(frames=frames, props=props, circuits=circuits)
        payload = report.to_dict()
        self.assertIn("max_amps_by_circuit", payload)
        self.assertIn("overload_events", payload)
        self.assertIn("corrections_applied", payload)
        self.assertIn("frames_adjusted", payload)
        self.assertIn("safe_after_processing", payload)
        self.assertIn("near_limit_events", payload)
        self.assertIn("residual_overload_events", payload)
        self.assertIn("unknown_circuit_events", payload)

    def test_missing_circuit_metadata_marks_report_unsafe(self) -> None:
        props = [
            PropPowerMeta("orphan_prop", 100, 12.0, 0.3, "MISSING", "background"),
        ]
        circuits = [
            CircuitMeta("A", breaker_limit_amps=15.0, safe_utilization=0.8, voltage=120.0),
        ]
        frames = [
            FrameInput(timestamp_ms=0, props=[FramePropState("orphan_prop", 1.0, 1.0)]),
        ]
        logs, report = analyze_power(frames=frames, props=props, circuits=circuits)
        self.assertFalse(report.safe_after_processing)
        self.assertEqual(len(report.unknown_circuit_events), 1)
        self.assertEqual(report.unknown_circuit_events[0]["circuit_id"], "MISSING")
        self.assertEqual(logs[0]["unknown_circuit_events"][0]["prop_id"], "orphan_prop")

    def test_peak_smoothing_reduces_spike_without_erasing_event(self) -> None:
        props = [
            PropPowerMeta("bg", 200, 12.0, 0.2, "A", "background"),
        ]
        circuits = [
            CircuitMeta("A", breaker_limit_amps=20.0, safe_utilization=1.0, voltage=120.0),
        ]
        frames = [
            FrameInput(timestamp_ms=0, props=[FramePropState("bg", 1.0, 0.4)]),
            FrameInput(timestamp_ms=100, props=[FramePropState("bg", 1.0, 1.0)]),
            FrameInput(timestamp_ms=200, props=[FramePropState("bg", 1.0, 0.4)]),
        ]
        logs, report = analyze_power(
            frames=frames,
            props=props,
            circuits=circuits,
            apply_corrections=False,
            enable_peak_smoothing=True,
            smoothing_window_ms=120,
            spike_ratio=1.35,
        )
        mid_intensity = float(logs[1]["intensity_by_prop"]["bg"])
        self.assertLess(mid_intensity, 1.0)
        self.assertGreater(mid_intensity, 0.4)
        smoothing_actions = [event for event in report.corrections_applied if event.get("action") == "peak_smoothing"]
        self.assertGreater(len(smoothing_actions), 0)


if __name__ == "__main__":
    unittest.main()

