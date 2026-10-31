"""Verify optional RGB accents use physical layout x-order, not random prop IDs."""
from pathlib import Path
import xml.etree.ElementTree as ET

from tools.spatial_choreography import add_spatial_accents


def _assets(tmp_path, *, rgb=True):
    layout = tmp_path / "xlights_rgbeffects.xml"
    kind = "RGB Nodes" if rgb else "Single Color Red"
    layout.write_text(
        "<xrgb><models>" + "".join(
            f'<model name="m{i}" StringType="{kind}" WorldPosX="{i * 20}" StartChannel="{i * 3 + 1}"/>'
            for i in range(4)
        ) + "</models></xrgb>"
    )
    xsq = tmp_path / "song.xsq"
    xsq.write_text(
        '<xsequence><head><sequenceDuration>4</sequenceDuration></head>'
        '<nextid>2</nextid><ColorPalettes>'
        '<ColorPalette>C_BUTTON_Palette1=#00D9FF,C_CHECKBOX_Palette1=1</ColorPalette>'
        '</ColorPalettes><EffectDB><Effect /></EffectDB>'
        '<DisplayElements />'
        '<ElementEffects><Element type="timing" name="AUTO Parts"><EffectLayer>'
        '<Effect label="CHORUS" startTime="1000" endTime="3500"/>'
        '</EffectLayer></Element></ElementEffects></xsequence>'
    )
    return layout, xsq


def test_rgb_chorus_creates_ordered_nonoverlapping_on_accents(tmp_path):
    layout, xsq = _assets(tmp_path)
    original = xsq.read_bytes()
    out = tmp_path / "spatial.xsq"
    report = add_spatial_accents(xsq, layout, out)
    assert xsq.read_bytes() == original
    assert report["added"] == 4
    root = ET.parse(out).getroot()
    emitted = []
    for row in root.findall("./ElementEffects/Element[@type='model']"):
        for e in row.findall("./EffectLayer/Effect"):
            emitted.append((row.get("name"), int(e.get("startTime")), e.get("name")))
    assert [name for name, _, _ in emitted] == ["m0", "m1", "m2", "m3"]
    assert [t for _, t, _ in emitted] == [1000, 1240, 1480, 1720]
    assert {kind for _, _, kind in emitted} == {"On"}


def test_spatial_never_fabricates_ac_rgb_models(tmp_path):
    layout, xsq = _assets(tmp_path, rgb=False)
    out = tmp_path / "out.xsq"
    result = add_spatial_accents(xsq, layout, out)
    assert result["added"] == 0
    assert not out.exists()
