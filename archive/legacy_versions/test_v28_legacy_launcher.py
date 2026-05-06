from __future__ import annotations

import sequencer_launcher_v28 as launcher_v28


def test_enable_v28_1_registers_variant_and_style() -> None:
    launcher_v28.enable_v28_1()

    assert any(item.version == "v28.1" and item.label == "Style 1" for item in launcher_v28.legacy.VARIANT_OPTIONS)
    assert any(item.version == "v28.1" for item in launcher_v28.legacy.ACTIVE_VARIANT_OPTIONS)
    assert launcher_v28.legacy.SCRIPT_MAP["v28.1"].name == "v28.1.py"

    style = launcher_v28.legacy.STYLE_TYPE_MAP["Style 1"]
    assert style.versions == ("v28.1",)
    assert style.palette_label == "Workspace Match"
