"""Keep repository preview RGB sampling faithful to per-effect palette refs."""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from tools.preview_renderer import (
    ModelGeom, LayoutData, EffectRecord, SequenceData,
    parse_sequence, build_leaf_intensity_matrix, build_leaf_color_matrix,
)


def _layout():
    return LayoutData(
        leaf_models={"Tree": ModelGeom(
            name="Tree", x1=0, y1=0, x2=10, y2=10,
            points=((0, 0), (10, 10)), display_as="Tree", color=(230, 230, 230)
        )},
        groups={}, bounds=(0, 0, 10, 10)
    )


def test_preview_uses_explicit_palette_color():
    sequence = SequenceData(
        duration_ms=1000,
        model_effects={"Tree": [EffectRecord(
            name="On", start_ms=100, end_ms=500, palette="0"
        )]},
        timing_tracks={},
        palettes=[((255, 0, 0),)]
    )
    names, intensity = build_leaf_intensity_matrix(_layout(), sequence, fps=10)
    colors = build_leaf_color_matrix(_layout(), sequence, 10, names, intensity.shape[1])
    assert intensity[0, 2] > 0
    assert tuple(colors[0, 2]) == (255, 0, 0)
    assert tuple(colors[0, 8]) == (0, 0, 0)


def test_xml_palette_slots_are_extracted(tmp_path: Path):
    xsq = tmp_path / "sample.xsq"
    xsq.write_text(
        '<xsequence><head><sequenceDuration>1</sequenceDuration></head>'
        '<ColorPalettes><ColorPalette>'
        'C_BUTTON_Palette1=#FF0000,C_BUTTON_Palette2=#00FF00,'
        'C_CHECKBOX_Palette1=1,C_CHECKBOX_Palette2=0'
        '</ColorPalette></ColorPalettes>'
        '<ElementEffects><Element type="model" name="Tree"><EffectLayer>'
        '<Effect name="On" startTime="100" endTime="500" palette="0" />'
        '</EffectLayer></Element></ElementEffects></xsequence>'
    )
    seq = parse_sequence(xsq)
    assert seq.palettes == [((255, 0, 0),)]
