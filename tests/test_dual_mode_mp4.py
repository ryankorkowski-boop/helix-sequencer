"""Both sequencer modes can emit a short honest simulation MP4."""
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from tools.lor_lms_import import prepare_lms_workspace
from tools.preview_renderer import parse_models, render_sequence_to_mp4


def test_lor_source_colors_create_preview_swatches(tmp_path: Path):
    source = tmp_path / "source.lms"
    source.write_text(
        '<sequence><channels>'
        '<channel name="red" deviceType="LOR" unit="1" circuit="1" color="255" savedIndex="0"/>'
        '<channel name="green" deviceType="LOR" unit="1" circuit="2" color="65280" savedIndex="1"/>'
        '<channel name="white" deviceType="LOR" unit="1" circuit="3" color="16777215" savedIndex="2"/>'
        '</channels></sequence>'
    )
    imported = prepare_lms_workspace(source, tmp_path / "workspace")
    layout = parse_models(Path(imported["layout"]))
    colors = {name: geom.color for name, geom in layout.leaf_models.items()}
    assert any(c[0] > c[1] and c[0] > c[2] for c in colors.values())
    assert any(c[1] > c[0] and c[1] > c[2] for c in colors.values())
    assert any(max(c) == min(c) for c in colors.values())


def test_sample_mp4_preserves_editable_xsq_and_truncates_preview(tmp_path: Path):
    pytest.importorskip("imageio")
    pytest.importorskip("PIL")
    pytest.importorskip("imageio_ffmpeg")
    source = tmp_path / "source.lms"
    source.write_text(
        '<sequence><channels>'
        '<channel name="red" deviceType="LOR" unit="1" circuit="1" color="255" savedIndex="0"/>'
        '</channels></sequence>'
    )
    imported = prepare_lms_workspace(source, tmp_path / "workspace")
    xsq = tmp_path / "song.xsq"
    tree = ET.parse(imported["template"])
    root = tree.getroot()
    root.find("./head/sequenceDuration").text = "10"
    palette_root = root.find("ColorPalettes")
    ET.SubElement(palette_root, "ColorPalette").text = (
        "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
    )
    row = root.find("./ElementEffects/Element[@type='model']")
    ET.SubElement(row.find("EffectLayer"), "Effect", {
        "name": "On", "startTime": "0", "endTime": "9000",
        "palette": "0", "ref": "0"
    })
    tree.write(xsq, encoding="utf-8")
    original = xsq.read_bytes()
    output = render_sequence_to_mp4(
        sequence_path=xsq,
        layout=parse_models(Path(imported["layout"])),
        audio_path=None, fps=10, width=320, height=240,
        max_seconds=0.3, use_palette_colors=False
    )
    assert output.exists() and output.stat().st_size > 100
    assert xsq.read_bytes() == original



def test_lor_preview_simulates_fades_shimmer_and_independent_twinkle():
    import numpy as np
    from tools.preview_renderer import EffectRecord, _ac_pulse_curve

    times = np.arange(0, 1000, 50, dtype=np.float32)
    fade = EffectRecord(
        name="On", start_ms=0, end_ms=1000,
        settings="E_TEXTCTRL_Eff_On_Start=0,E_TEXTCTRL_Eff_On_End=100"
    )
    brightness = _ac_pulse_curve(fade, times, "Roof red")
    assert brightness[0] == 0
    assert 0.4 < brightness[10] < 0.6
    assert brightness[-1] > 0.90

    shimmer = EffectRecord(name="Shimmer", start_ms=0, end_ms=1000)
    pulses = _ac_pulse_curve(shimmer, times, "Roof green")
    assert np.any(pulses == 0) and np.any(pulses > 0)

    twinkle = EffectRecord(name="Twinkle", start_ms=0, end_ms=1000)
    a = _ac_pulse_curve(twinkle, times, "Roof red")
    b = _ac_pulse_curve(twinkle, times, "Roof green")
    assert not np.array_equal(a, b)
    assert np.array_equal(a, _ac_pulse_curve(twinkle, times, "Roof red"))
