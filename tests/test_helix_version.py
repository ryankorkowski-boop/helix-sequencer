from __future__ import annotations

from core.helix_version import DISPLAY, TITLE, VERSION, VERSION_CODE
from core.sequence_builder import build_parser


def test_beta_1_3_version_strings():
    assert VERSION == "1.3.0-beta"
    assert VERSION_CODE == 9
    assert DISPLAY == "Beta 1.3"
    assert "Beta 1.3" in TITLE


def test_cli_version_flag_reports_beta_1_3(capsys):
    parser = build_parser()
    try:
        parser.parse_args(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()
    assert "Beta 1.3" in captured.out
    assert "1.3.0-beta" in captured.out
