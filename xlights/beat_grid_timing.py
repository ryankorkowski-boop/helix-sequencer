from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Any

from core.beat_grid import BeatGrid, generate_beat_grid, snap_ms_to_grid
from xlights import xml_io
from xlights import xsq_writer as legacy


TIMING_LABEL_ATTRS = ("label", "Label")
TIME_ATTRS = ("startTime", "StartTime", "start", "Start", "time", "Time")
END_ATTRS = ("endTime", "EndTime", "end", "End")


def _get_attr(node: ET.Element, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        if key in node.attrib:
            return node.attrib[key]
    return None


def _set_attr(node: ET.Element, keys: tuple[str, ...], value: int) -> None:
    for key in keys:
        if key in node.attrib:
            node.attrib[key] = str(int(value))
            return
    node.attrib[keys[0]] = str(int(value))


def _duration_ms(root: ET.Element) -> int:
    duration = 1
    for node in root.iter():
        for key in TIME_ATTRS + END_ATTRS:
            if key in node.attrib:
                try:
                    duration = max(duration, int(round(float(node.attrib[key]))))
                except Exception:
                    pass
    return duration + 1000


def _is_timing_element(node: ET.Element) -> bool:
    element_type = (_get_attr(node, ("type", "Type")) or "").lower()
    return element_type == "timing"


def _timing_name(node: ET.Element) -> str:
    return (_get_attr(node, ("name", "Name")) or "").strip()


def _should_snap_track(name: str, include_prefixes: tuple[str, ...], exclude_prefixes: tuple[str, ...]) -> bool:
    if not name:
        return False
    low = name.lower()
    if exclude_prefixes and any(low.startswith(prefix.lower()) for prefix in exclude_prefixes):
        return False
    if include_prefixes:
        return any(low.startswith(prefix.lower()) for prefix in include_prefixes)
    return low.startswith("auto ") or low in {
        "beats",
        "bars",
        "onsets",
        "note onsets",
        "audio pitch detector",
        "phoneme",
        "phonemes",
    }


def snap_timing_tracks_in_root(
    root: ET.Element,
    beat_grid: BeatGrid,
    *,
    include_prefixes: tuple[str, ...] = (),
    exclude_prefixes: tuple[str, ...] = ("hx",),
) -> dict[str, Any]:
    """Snap xLights timing-track effects in an XML root to BeatGrid points.

    This touches only timing elements, not model effect rows. Raw times are
    preserved as rawStartTime/rawEndTime attributes, with snappedStartTime and
    snappedEndTime added for audit/debug visibility inside the XSQ XML.
    """

    duration_ms = _duration_ms(root)
    grid_points = generate_beat_grid(beat_grid, duration_ms)
    tracks = 0
    events = 0
    changed = 0

    for timing_el in legacy._find_any(root, "Element"):
        if not _is_timing_element(timing_el):
            continue
        name = _timing_name(timing_el)
        if not _should_snap_track(name, include_prefixes, exclude_prefixes):
            continue
        track_events = 0
        track_changed = 0
        for node in timing_el.iter():
            if node is timing_el:
                continue
            raw = _get_attr(node, TIME_ATTRS)
            if raw is None:
                continue
            try:
                raw_start = int(round(float(raw)))
            except Exception:
                continue
            raw_end_value = _get_attr(node, END_ATTRS)
            raw_end = raw_start + 1
            if raw_end_value is not None:
                try:
                    raw_end = int(round(float(raw_end_value)))
                except Exception:
                    raw_end = raw_start + 1
            snapped_start = snap_ms_to_grid(raw_start, grid_points, max_shift_ms=beat_grid.max_shift_ms, mode=beat_grid.mode)
            delta = snapped_start - raw_start
            snapped_end = max(snapped_start + 1, raw_end + delta)
            node.attrib.setdefault("rawStartTime", str(raw_start))
            node.attrib.setdefault("rawEndTime", str(raw_end))
            node.attrib["snappedStartTime"] = str(snapped_start)
            node.attrib["snappedEndTime"] = str(snapped_end)
            _set_attr(node, TIME_ATTRS, snapped_start)
            if raw_end_value is not None:
                _set_attr(node, END_ATTRS, snapped_end)
            track_events += 1
            if snapped_start != raw_start or snapped_end != raw_end:
                track_changed += 1
        if track_events:
            tracks += 1
            events += track_events
            changed += track_changed
    return {
        "enabled": True,
        "tracks_touched": tracks,
        "events_touched": events,
        "events_changed": changed,
        "grid_points": len(grid_points),
        "subdivision": beat_grid.subdivision,
        "mode": beat_grid.mode,
    }


def snap_xsq_timing_tracks(path: Path, beat_grid: BeatGrid, *, output_path: Path | None = None) -> dict[str, Any]:
    """Load an XSQ file, snap timing tracks, and write it back or to output_path."""

    tree = ET.parse(path)
    root = tree.getroot()
    report = snap_timing_tracks_in_root(root, beat_grid)
    target = output_path or path
    try:
        legacy.indent_xml(root)
    except Exception:
        pass
    tree.write(target, encoding="utf-8", xml_declaration=True)
    report["path"] = str(target)
    return report
