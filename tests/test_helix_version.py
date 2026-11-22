from __future__ import annotations

from core.helix_version import DISPLAY, TITLE, VERSION, VERSION_CODE
from core.sequence_builder import build_parser


def test_beta_1_4_recovery_version_strings():
    assert VERSION == "1.4.0-beta-recovery"
    assert VERSION_CODE == 10
    assert DISPLAY == "Beta 1.4 recovery"
    assert "Beta 1.4 recovery" in TITLE


def test_cli_version_flag_reports_beta_1_4_recovery(capsys):
    parser = build_parser()
    try:
        parser.parse_args(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()
    assert "Beta 1.4 recovery" in captured.out
    assert "1.4.0-beta-recovery" in captured.out
