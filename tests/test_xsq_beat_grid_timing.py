import xml.etree.ElementTree as ET

from core.beat_grid import BeatGrid
from xlights.beat_grid_timing import snap_timing_tracks_in_root


def _sample_xsq_root():
    root = ET.Element("xsequence")
    display = ET.SubElement(root, "DisplayElements")
    ET.SubElement(display, "Element", {"type": "timing", "name": "Auto Beats vtest"})
    ET.SubElement(display, "Element", {"type": "timing", "name": "HX_INTERNAL"})
    element_effects = ET.SubElement(root, "ElementEffects")
    auto = ET.SubElement(element_effects, "Element", {"type": "timing", "name": "Auto Beats vtest"})
    auto_layer = ET.SubElement(auto, "EffectLayer")
    ET.SubElement(auto_layer, "Effect", {"label": "beat", "startTime": "126", "endTime": "200"})
    ET.SubElement(auto_layer, "Effect", {"label": "beat", "startTime": "255", "endTime": "330"})
    hx = ET.SubElement(element_effects, "Element", {"type": "timing", "name": "HX_INTERNAL"})
    hx_layer = ET.SubElement(hx, "EffectLayer")
    ET.SubElement(hx_layer, "Effect", {"label": "internal", "startTime": "126", "endTime": "200"})
    return root


def test_snap_timing_tracks_in_root_snaps_auto_tracks_and_preserves_raw():
    root = _sample_xsq_root()
    grid = BeatGrid(bpm=120, subdivision=16, max_shift_ms=40)

    report = snap_timing_tracks_in_root(root, grid)

    assert report["tracks_touched"] == 1
    assert report["events_touched"] == 2
    assert report["events_changed"] == 2
    auto_events = root.find("ElementEffects").find("Element").find("EffectLayer").findall("Effect")
    assert auto_events[0].attrib["rawStartTime"] == "126"
    assert auto_events[0].attrib["snappedStartTime"] == "125"
    assert auto_events[0].attrib["startTime"] == "125"
    assert auto_events[1].attrib["snappedStartTime"] == "250"


def test_snap_timing_tracks_in_root_skips_hx_internal_tracks_by_default():
    root = _sample_xsq_root()
    grid = BeatGrid(bpm=120, subdivision=16, max_shift_ms=40)

    snap_timing_tracks_in_root(root, grid)

    hx_event = root.find("ElementEffects").findall("Element")[1].find("EffectLayer").find("Effect")
    assert hx_event.attrib["startTime"] == "126"
    assert "snappedStartTime" not in hx_event.attrib


def test_snap_timing_tracks_in_root_can_include_explicit_prefix():
    root = _sample_xsq_root()
    grid = BeatGrid(bpm=120, subdivision=16, max_shift_ms=40)

    report = snap_timing_tracks_in_root(root, grid, include_prefixes=("HX",), exclude_prefixes=())

    assert report["tracks_touched"] == 1
    hx_event = root.find("ElementEffects").findall("Element")[1].find("EffectLayer").find("Effect")
    assert hx_event.attrib["snappedStartTime"] == "125"
