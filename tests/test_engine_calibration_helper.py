from __future__ import annotations

import unittest

from tools.build_helpers import (
    EngineQualityGateConfig,
    apply_quality_gate_overrides,
    engine_quality_gate_config,
    engine_threshold_cli_args,
    engine_threshold_kwargs,
)


class EngineCalibrationHelperTests(unittest.TestCase):
    def test_engine_quality_gate_config_resolves_showcase(self) -> None:
        config = engine_quality_gate_config("showcase")

        self.assertIsInstance(config, EngineQualityGateConfig)
        self.assertEqual(config.preset, "showcase")
        self.assertEqual(config.min_quality_score, 93.0)
        self.assertEqual(config.min_audit_score, 86.0)
        self.assertEqual(config.max_rejected_effects, 18000)

    def test_engine_quality_gate_config_falls_back_to_general(self) -> None:
        config = engine_quality_gate_config("not-a-real-preset")

        self.assertEqual(config.preset, "general")
        self.assertEqual(config.min_quality_score, 90.0)

    def test_apply_quality_gate_overrides_keeps_unspecified_values(self) -> None:
        base = engine_quality_gate_config("showcase")
        config = apply_quality_gate_overrides(base, min_quality_score=95.0)

        self.assertEqual(config.preset, "showcase")
        self.assertEqual(config.min_quality_score, 95.0)
        self.assertEqual(config.min_audit_score, 86.0)
        self.assertEqual(config.max_rejected_effects, 18000)

    def test_engine_threshold_kwargs_match_existing_helper_names(self) -> None:
        config = engine_quality_gate_config("vendor")
        kwargs = engine_threshold_kwargs(config)

        self.assertEqual(
            kwargs,
            {
                "min_quality_score": 96.0,
                "min_audit_score": 90.0,
                "max_rejected_effects": 12000,
            },
        )

    def test_engine_threshold_cli_args_match_existing_vendor_flags(self) -> None:
        config = engine_quality_gate_config("showcase")
        args = engine_threshold_cli_args(config)

        self.assertEqual(
            args,
            [
                "--vendor-min-quality-score",
                "93.0",
                "--vendor-min-audit-score",
                "86.0",
                "--vendor-max-rejected-effects",
                "18000",
            ],
        )


if __name__ == "__main__":
    unittest.main()
