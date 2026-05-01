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

    def test_over_limit_sequence_reports_overload(self) -> None:
        props = [
            PropPowerMeta("prop_1", 2000, 12.0, 0.8, "A", "background"),
        ]
        circuits = [
            CircuitMeta("A", breaker_limit_amps=5.0, safe_utilization=0.8, voltage=120.0),
        ]
        frames = [
            FrameInput(timestamp_ms=100, props=[FramePropState("prop_1", 1.0, 1.0)]),
        ]
        _, report = analyze_power(frames=frames, props=props, circuits=circuits)
        self.assertFalse(report.safe_after_processing)
        self.assertGreater(len(report.overload_events), 0)
        self.assertGreater(float(report.overload_events[0]["overload_amps"]), 0.0)

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


if __name__ == "__main__":
    unittest.main()

