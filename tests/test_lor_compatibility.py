"""LOR Compatible is an xLights effect contract, NOT an LMS converter."""
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from tools.lor_compatibility import (
    AC_EFFECTS, ac_layout_targets, enforce_lor_xsq, inspect_lor_xsq,
)


def _layout(path: Path):
    path.write_text(
        '<xrgb><models>'
        '<model name="R" StringType="Single Color Red" StartChannel="1"/>'
        '<model name="G" StringType="Single Color Green" StartChannel="2"/>'
        '<model name="W" StringType="Single Color White" StartChannel="3"/>'
        '<model name="Traditional AC" StringType="Single Color Intensity" StartChannel="4"/>'
        '<model name="RGB pixels" StringType="RGB Nodes" parm1="1" parm2="20" StartChannel="5"/>'
        '</models><modelGroups>'
        '<modelGroup name="All AC" models="R,G,W,Traditional AC"/>'
        '<modelGroup name="Mixed" models="R,Traditional AC,RGB pixels"/>'
        '</modelGroups></xrgb>',
        encoding="utf-8"
    )


def _xsq(path: Path):
    path.write_text(
        '<xsequence><head><sequenceDuration>5</sequenceDuration></head>'
        '<nextid>10</nextid>'
        '<ColorPalettes><ColorPalette>C_BUTTON_Palette1=#FF00EE,'
        'C_CHECKBOX_Palette1=1</ColorPalette></ColorPalettes>'
        '<EffectDB><Effect>E_TEXTCTRL_Eff_On_Start=100,'
        'E_TEXTCTRL_Eff_On_End=100</Effect></EffectDB>'
        '<DataLayers><DataLayer source="unused_rgb"/></DataLayers>'
        '<DisplayElements>'
        '<Element type="timing" name="Parts"/>'
        '<Element type="model" name="All AC"/>'
        '<Element type="model" name="Mixed"/>'
        '<Element type="model" name="RGB pixels"/>'
        '</DisplayElements>'
        '<ElementEffects>'
        '<Element type="timing" name="Parts"><EffectLayer>'
        '<Effect startTime="0" endTime="3000" label="VERSE" id="1"/>'
        '</EffectLayer></Element>'
        '<Element type="model" name="Traditional AC"><EffectLayer>'
        '<Effect name="Ramp" startTime="100" endTime="700" palette="0" ref="0" id="4"/>'
        '<Effect name="Shimmer" startTime="800" endTime="1200" palette="0" ref="0" id="5"/>'
        '</EffectLayer></Element>'
        '<Element type="model" name="G"><EffectLayer>'
        '<Effect name="Twinkle" startTime="400" endTime="900" palette="0" ref="0" id="6"/>'
        '</EffectLayer></Element>'
        '<Element type="model" name="Mixed"><EffectLayer>'
        '<Effect name="Bars" startTime="1500" endTime="1850" palette="0" ref="0" id="7"/>'
        '</EffectLayer></Element>'
        '<Element type="model" name="RGB pixels"><EffectLayer>'
        '<Effect name="Plasma" startTime="100" endTime="2000" palette="0" ref="0" id="8"/>'
        '</EffectLayer></Element>'
        '</ElementEffects></xsequence>'
    )


def test_lor_keeps_intensity_and_rgw_but_discards_rgb(tmp_path: Path):
    layout, source, output = [tmp_path / s for s in ("layout.xml", "song.xsq", "song.ac.xsq")]
    _layout(layout)
    _xsq(source)
    original = source.read_bytes()
    report = enforce_lor_xsq(source, output, layout)
    assert source.read_bytes() == original
    assert report["layout_single_color_models"] == 4
    assert report["layout_non_ac_models"] == 1
    assert report["used_single_color_models"] == 3  # G, R, Traditional AC
    assert report["counts"]["Ramp_to_On_fade"] == 1
    assert report["counts"]["unsupported_to_On"] == 2  # Bars applied to R and traditional AC
    assert report["counts"]["unmapped_or_rgb_rows_removed"] == 1
    assert inspect_lor_xsq(output, layout)["valid"]
    parsed = ET.parse(output).getroot()
    effects = parsed.findall("./ElementEffects/Element[@type='model']/EffectLayer/Effect")
    assert {e.get("name") for e in effects} <= AC_EFFECTS
    assert {"On", "Shimmer", "Twinkle"} <= {e.get("name") for e in effects}
    assert not parsed.findall("./DataLayers/DataLayer")
    assert {e.get("name") for e in parsed.findall("./ElementEffects/Element[@type='model']")} == {
        "Traditional AC", "G", "R"
    }
    for effect in effects:
        palette_idx = int(effect.get("palette"))
        palette = parsed.findall("./ColorPalettes/ColorPalette")[palette_idx].text
        assert "#FFFFFF" in palette
    assert parsed.find("./ElementEffects/Element[@type='timing']") is not None
    all_ids = [effect.get("id") for effect in parsed.findall("./ElementEffects/Element/EffectLayer/Effect")]
    assert len(all_ids) == len(set(all_ids))
    assert all(int(e.get("endTime")) > int(e.get("startTime")) for e in effects)


def test_lor_rejects_source_overwrite(tmp_path: Path):
    layout, source = [tmp_path / s for s in ("layout.xml", "in.xsq")]
    _layout(layout)
    _xsq(source)
    with pytest.raises(ValueError, match="Cannot overwrite"):
        enforce_lor_xsq(source, source, layout)


def test_lor_rejects_rgb_only_layout(tmp_path: Path):
    layout, source, output = [tmp_path / s for s in ("rgb.xml", "in.xsq", "out.xsq")]
    layout.write_text(
        '<xrgb><models><model name="matrix" StringType="RGB Nodes" StartChannel="1"/></models></xrgb>'
    )
    _xsq(source)
    with pytest.raises(ValueError, match="No xLights Single Color"):
        enforce_lor_xsq(source, output, layout)


def test_lor_rejects_unmapped_only_rows(tmp_path: Path):
    layout, source, output = [tmp_path / s for s in ("layout.xml", "in.xsq", "out.xsq")]
    _layout(layout)
    _xsq(source)
    s = source.read_text()
    s = s.replace('type="model" name="Traditional AC"', 'type="model" name="RGB pixels"')
    s = s.replace('type="model" name="G"', 'type="model" name="RGB pixels"')
    s = s.replace('type="model" name="Mixed"', 'type="model" name="RGB pixels"')
    source.write_text(s)
    with pytest.raises(ValueError, match="No compatible single-color"):
        enforce_lor_xsq(source, output, layout)


def test_original_256_layout_preserves_generic_ac_channels():
    layout = Path(__file__).resolve().parents[1] / "xlights_rgbeffects.xml"
    if not layout.exists():
        pytest.skip("Repo layout unavailable")
    safe, other, _groups = ac_layout_targets(layout)
    assert len(safe) == 255
    assert len(other) == 1


def test_compatibility_has_no_lms_converter_interface():
    import tools.lor_compatibility as lor
    assert not hasattr(lor, "export_lms")
    assert not hasattr(lor, "read_lor_map")


def test_ac_only_does_not_activate_neon_palette_color_repair():
    from core.sequence_builder import _apply_neon_palettes_to_generated_sequences
    # An ordinary AC-only run never triggers an RGB neon palette rewrite.
    # Hook is no-op with no root artifacts or fixture files.
    assert _apply_neon_palettes_to_generated_sequences(["--ac-lights-only"], [], {}, None) is None
