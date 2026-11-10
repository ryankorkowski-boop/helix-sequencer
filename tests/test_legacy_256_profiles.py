from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from tools.legacy_256_profiles import legacy_256_profile, list_legacy_256_profiles
from tools.run_legacy_256_profile import build_legacy_256_command, build_parser, main


class Legacy256ProfileTests(unittest.TestCase):
    def test_profiles_are_discoverable(self) -> None:
        names = {item["name"] for item in list_legacy_256_profiles()}

        self.assertEqual(names, {"legacy_256_clean", "legacy_256_showcase", "legacy_256_pro"})

    def test_showcase_profile_uses_showcase_gate_and_constrained_flags(self) -> None:
        profile = legacy_256_profile("legacy_256_showcase")

        self.assertEqual(profile.base_profile, "v9.2")
        self.assertEqual(profile.quality_gate_preset, "showcase")
        self.assertEqual(profile.variants, 3)
        self.assertIn("--no-matrix-intelligence", profile.engine_flags)
        self.assertIn("--no-auto-timing-tracks", profile.engine_flags)

    def test_unknown_profile_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(KeyError, "Unknown legacy 256 profile"):
            legacy_256_profile("not-real")

    def test_runner_builds_existing_engine_command_for_pro_profile(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["legacy_256_pro", "--dry-run"])

        command = build_legacy_256_command(args)

        self.assertEqual(command[:3], [sys.executable, "-m", "core.sequence_builder"])
        self.assertIn("--profile", command)
        self.assertIn("v9.2", command)
        self.assertIn("--template", command)
        self.assertIn("fixtures/legacy_256/converted/template.xsq", command)
        self.assertIn("--layout-file", command)
        self.assertIn("fixtures/legacy_256/converted/xlights_rgbeffects.xml", command)
        self.assertIn("--variants", command)
        self.assertIn("5", command)
        self.assertIn("--vendor-min-quality-score", command)
        self.assertIn("96.0", command)
        self.assertIn("--vendor-min-audit-score", command)
        self.assertIn("90.0", command)
        self.assertIn("--vendor-max-rejected-effects", command)
        self.assertIn("12000", command)

    def test_runner_allows_variant_override_and_extra_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "legacy_256_showcase",
            "--variants",
            "7",
            "--extra-engine-arg",
            "--no-polish",
        ])

        command = build_legacy_256_command(args)

        self.assertIn("7", command)
        self.assertIn("--no-polish", command)

    def test_dry_run_prints_without_subprocess(self) -> None:
        out = io.StringIO()
        with patch("tools.run_legacy_256_profile.subprocess.run") as mock_run:
            with redirect_stdout(out):
                code = main(["legacy_256_clean", "--dry-run"])

        self.assertEqual(code, 0)
        self.assertIn("core.sequence_builder", out.getvalue())
        mock_run.assert_not_called()

    def test_main_executes_when_not_dry_run(self) -> None:
        completed = Mock(returncode=4)
        with patch("tools.run_legacy_256_profile.subprocess.run", return_value=completed) as mock_run:
            code = main(["legacy_256_clean"])

        self.assertEqual(code, 4)
        mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
