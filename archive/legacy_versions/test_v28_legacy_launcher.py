from __future__ import annotations

import sequencer_launcher_v28 as launcher_v28


def test_enable_v28_styles_registers_each_variant_and_style() -> None:
    launcher_v28.enable_v28_styles()

    expected_versions = {lane.version for lane in launcher_v28.V28_LANES}
    expected_labels = {lane.label for lane in launcher_v28.V28_LANES}

    registered_versions = {item.version for item in launcher_v28.legacy.VARIANT_OPTIONS}
    active_versions = {item.version for item in launcher_v28.legacy.ACTIVE_VARIANT_OPTIONS}
    style_labels = set(launcher_v28.legacy.STYLE_TYPE_MAP)

    assert expected_versions <= registered_versions
    assert expected_versions <= active_versions
    assert expected_labels <= style_labels

    for lane in launcher_v28.V28_LANES:
        assert launcher_v28.legacy.SCRIPT_MAP[lane.version].name == f"{lane.version}.py"
        style = launcher_v28.legacy.STYLE_TYPE_MAP[lane.label]
        assert style.versions == (lane.version,)
        assert style.palette_label == lane.palette_label
        assert style.ac_only == lane.ac_only


def test_enable_v28_1_backcompat_alias_registers_all_styles() -> None:
    launcher_v28.enable_v28_1()
    assert "Style 1" in launcher_v28.legacy.STYLE_TYPE_MAP
    assert "Style 9" in launcher_v28.legacy.STYLE_TYPE_MAP
