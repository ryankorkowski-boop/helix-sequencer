import pytest

from tools.build_helpers.gui_quality_options import (
    GuiQualityOptionsError,
    normalize_gui_quality_options,
)


def test_default_gui_quality_options_are_safe_and_report_only():
    options = normalize_gui_quality_options()

    assert options.quality_preset == "showcase"
    assert options.style_preset == "general"
    assert options.report_only is True
    assert options.enabled_report_modules() == (
        "prop_roles",
        "density_restraint",
        "section_identity",
        "palette_discipline",
        "motif_memory",
        "manual_locks",
    )


def test_cli_args_document_future_mapping():
    options = normalize_gui_quality_options({
        "quality_preset": "vendor",
        "style_preset": "classic_christmas",
        "enable_motif_memory": False,
    })

    args = options.cli_args()

    assert "--quality-gate-preset" in args
    assert "vendor" in args
    assert "--helix-style-preset" in args
    assert "classic_christmas" in args
    assert "motif_memory" not in args
    assert "density_restraint" in args


def test_invalid_quality_preset_raises_error():
    with pytest.raises(GuiQualityOptionsError, match="Unsupported quality preset"):
        normalize_gui_quality_options({"quality_preset": "maximum_chaos"})


def test_invalid_style_preset_raises_error():
    with pytest.raises(GuiQualityOptionsError, match="Unsupported style preset"):
        normalize_gui_quality_options({"style_preset": "unknown_style"})


def test_manual_locks_cannot_leave_report_only_mode_yet():
    with pytest.raises(GuiQualityOptionsError, match="manual locks are report-only"):
        normalize_gui_quality_options({"report_only": False, "enable_manual_locks": True})


def test_non_report_only_allowed_when_manual_locks_disabled():
    options = normalize_gui_quality_options({"report_only": False, "enable_manual_locks": False})

    assert options.report_only is False
    assert "manual_locks" not in options.enabled_report_modules()
