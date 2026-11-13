"""Review fixes for showcase lip-sync reservation and AC window channels."""

from pathlib import Path

from core import model_parser as xmp
from core.effect_engine import discover_talking_heads, is_lip_sync_face
from tools.showcase12.xlights_fseq import build_node_drawlist


ROOT = Path(__file__).resolve().parents[1]


def test_numbered_face_discovery_does_not_drop_an_unnumbered_singing_tree():
    names = ["Singing Face 1", "Singing Tree", "Mega Tree", "Singing Face 1/Mouth"]
    discovered = discover_talking_heads(names)
    assert "Singing Face 1" in discovered
    assert "Singing Tree" not in discovered
    reserved = [name for name in names if is_lip_sync_face(name)]
    assert reserved == ["Singing Face 1", "Singing Tree", "Singing Face 1/Mouth"]


def test_ac_window_uses_one_channel():
    layout = ROOT / "fixtures" / "showcase12" / "s01_ac16" / "xlights_rgbeffects.xml"
    parsed = xmp.parse_layout(layout)
    window = parsed.model_for("Window Frame 1")
    nxt = parsed.model_for("Window Frame 2")
    assert window is not None and nxt is not None
    assert window.total_pixels == 1
    assert int(nxt.start_channel) == int(window.start_channel) + 1
    draw = build_node_drawlist(layout, 400, 288)
    window_channels = [
        channel
        for channel, model_name in zip(draw["ch"], draw["model"])
        if model_name == "Window Frame 1"
    ]
    assert window_channels == []
    strand_channels = [item[3] for item in draw["strands"] if item[0] == "Window Frame 1"]
    assert strand_channels == [int(window.start_channel) - 1]
