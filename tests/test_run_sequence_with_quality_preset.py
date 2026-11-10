from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from tools import run_sequence_with_quality_preset as runner


class RunSequenceWithQualityPresetTests(unittest.TestCase):
    def test_build_command_appends_showcase_thresholds(self) -> None:
        parser = runner.build_parser()
        args = parser.parse_args([
            "--quality-gate-preset",
            "showcase",
            "--dry-run",
            "--",
            "--profile",
            "v27.3",
            "--",
            "--template",
            "template.xsq",
        ])

        command = runner.build_command(args)

        self.assertEqual(command[:3], [sys.executable, "-m", "core.sequence_builder"])
        self.assertIn("--profile", command)
        self.assertIn("v27.3", command)
        self.assertIn("--vendor-min-quality-score", command)
        self.assertIn("93.0", command)
        self.assertIn("--vendor-min-audit-score", command)
        self.assertIn("86.0", command)
        self.assertIn("--vendor-max-rejected-effects", command)
        self.assertIn("18000", command)

    def test_build_command_allows_explicit_overrides(self) -> None:
        parser = runner.build_parser()
        args = parser.parse_args([
            "--quality-gate-preset",
            "showcase",
            "--min-quality-score",
            "95",
            "--max-rejected-effects",
            "9000",
            "--",
            "--profile",
            "v27.3",
        ])

        command = runner.build_command(args)

        self.assertIn("95.0", command)
        self.assertIn("9000", command)
        self.assertNotIn("18000", command)

    def test_dry_run_prints_command_without_subprocess(self) -> None:
        out = io.StringIO()
        with patch("tools.run_sequence_with_quality_preset.subprocess.run") as mock_run:
            with redirect_stdout(out):
                code = runner.main(["--quality-gate-preset", "showcase", "--dry-run", "--", "--profile", "v27.3"])

        self.assertEqual(code, 0)
        self.assertIn("core.sequence_builder", out.getvalue())
        mock_run.assert_not_called()

    def test_main_executes_child_command_when_not_dry_run(self) -> None:
        completed = Mock(returncode=7)
        with patch("tools.run_sequence_with_quality_preset.subprocess.run", return_value=completed) as mock_run:
            code = runner.main(["--quality-gate-preset", "general", "--", "--profile", "v27.3"])

        self.assertEqual(code, 7)
        mock_run.assert_called_once()
        command = mock_run.call_args.args[0]
        self.assertIn("core.sequence_builder", command)
        self.assertIn("--vendor-min-quality-score", command)
        self.assertIn("90.0", command)


if __name__ == "__main__":
    unittest.main()
