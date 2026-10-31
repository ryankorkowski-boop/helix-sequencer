"""Music-section color stories and strict non-fake showcase reporting."""
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from tools.xsq_palette_repair import _scene, repair_xsq
from tools.showcase_quality_audit import write_showcase_audit


class Event:
    def __init__(self, start, end):
        self.start_ms = start
        self.end_ms = end


def test_color_arc_is_coherent_within_musical_phrase():
    sections = [
        (0, 20000, "VERSE"), (20000, 40000, "CHORUS"),
        (40000, 76000, "BRIDGE"),
    ]
    assert _scene("Rooftop", Event(1000, 1100), sections) == _scene(
        "Random star", Event(1800, 1950), sections
    )
    assert _scene("Rooftop", Event(21000, 21100), sections) == _scene(
        "Tree", Event(21010, 21110), sections
    )
    assert _scene("Rooftop", Event(41000, 41100), sections) != _scene(
        "Rooftop", Event(57000, 57100), sections
    )


def test_neon_quality_rejects_white_only_but_does_not_modify_xsq(tmp_path: Path):
    xsq = tmp_path / "original.xsq"
    xsq.write_text(
        '<xsequence><head><sequenceDuration>5</sequenceDuration></head>'
        '<ColorPalettes><ColorPalette>C_BUTTON_Palette1=#FFFFFF,'
        'C_CHECKBOX_Palette1=1</ColorPalette></ColorPalettes>'
        '<ElementEffects><Element type="model" name="Tree">'
        '<EffectLayer>' +
        ''.join(
            f'<Effect name="On" palette="0" startTime="{i*100}" endTime="{i*100+70}"/>'
            for i in range(25)
        ) +
        '</EffectLayer></Element></ElementEffects></xsequence>'
    )
    before = xsq.read_bytes()
    report = write_showcase_audit(xsq, neon_expected=True)
    assert report["effects"] == 25
    assert not report["quality_gate_pass"]
    assert xsq.read_bytes() == before
    with pytest.raises(ValueError, match="Showcase quality gate failed"):
        write_showcase_audit(xsq, neon_expected=True, strict=True)


def test_neon_palettes_keep_source_effect_timing_and_model_targets(tmp_path: Path):
    src, dest = tmp_path / "raw.xsq", tmp_path / "color.xsq"
    src.write_text(
        '<xsequence><head><sequenceDuration>30</sequenceDuration></head>'
        '<nextid>5</nextid>'
        '<ColorPalettes><ColorPalette>C_BUTTON_Palette1=#FFFFFF,'
        'C_CHECKBOX_Palette1=1</ColorPalette></ColorPalettes>'
        '<EffectDB><Effect /></EffectDB>'
        '<ElementEffects><Element type="model" name="Tree"><EffectLayer>'
        '<Effect name="Wave" startTime="1000" endTime="1300"/>'
        '<Effect name="Bars" startTime="22000" endTime="23100"/>'
        '</EffectLayer></Element>'
        '<Element type="timing" name="AUTO Parts"><EffectLayer>'
        '<Effect label="VERSE" startTime="0" endTime="15000"/>'
        '<Effect label="CHORUS" startTime="15000" endTime="30000"/>'
        '</EffectLayer></Element></ElementEffects></xsequence>'
    )
    before = [(e.get("name"), e.get("startTime"), e.get("endTime"))
              for e in ET.parse(src).getroot().findall("./ElementEffects/Element[@type='model']/EffectLayer/Effect")]
    result = repair_xsq(src, dest)
    after = [(e.get("name"), e.get("startTime"), e.get("endTime"))
             for e in ET.parse(dest).getroot().findall("./ElementEffects/Element[@type='model']/EffectLayer/Effect")]
    assert before == after
    assert result["changes"]["palettes_assigned"] == 2
