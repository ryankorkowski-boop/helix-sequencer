"""Export audited single-channel Helix On-only xLights XSQ to legacy LOR LMS.

Older Light-O-Rama Sequencer versions use editable LMS XML; modern S5/S6
applications use LOREDIT, which this tool does not produce. All actual unit
and circuit numbers MUST come from a user-completed mapping CSV. No guesses.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
import json
from pathlib import Path
from xml.etree import ElementTree as ET


def _positive_address(raw: str, field: str) -> int:
    token = str(raw or "").strip()
    if not token:
        raise ValueError(f"Missing {field}. Fill in the controller mapping CSV first.")
    try:
        value = int(token, 16) if token.lower().startswith("0x") else int(token, 10)
    except ValueError as exc:
        raise ValueError(f"Invalid {field}: {token!r} (decimal or 0x-prefixed hex)") from exc
    if value < 1 or value > 255:
        raise ValueError(f"{field} must be between 1 and 255: {token!r}")
    return value


def _circuit(raw: str) -> int:
    token = str(raw or "").strip()
    if not token or not token.isdecimal():
        raise ValueError(f"Invalid or missing controller_circuit {token!r}")
    value = int(token)
    if not 1 <= value <= 16:
        raise ValueError(
            f"Controller circuit {value} is outside the conservative 1–16 AC port range. "
            "Verify your hardware; this exporter currently supports 16-port boards only."
        )
    return value


def read_lor_map(path: Path) -> dict[str, dict]:
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("Mapping CSV is empty")
    models = {}
    addresses = {}
    starts = {}
    for row in rows:
        name = str(row.get("model") or "").strip()
        color = str(row.get("color") or "").strip().lower()
        if not name or color not in {"red", "green", "white"}:
            raise ValueError(f"Invalid AC model/color mapping: {row!r}")
        if name in models:
            raise ValueError(f"Duplicate model mapping: {name}")
        unit = _positive_address(row.get("controller_unit", ""), "controller_unit")
        circuit = _circuit(row.get("controller_circuit", ""))
        start_token = str(row.get("xlights_start_channel") or "").strip()
        if not start_token.isdecimal() or int(start_token) < 1:
            raise ValueError(f"Invalid xLights StartChannel for {name!r}: {start_token!r}")
        start = int(start_token)
        if (unit, circuit) in addresses:
            raise ValueError(
                f"Duplicate LOR Unit/Circuit ({unit},{circuit}): "
                f"{addresses[(unit, circuit)]} and {name}"
            )
        if start in starts:
            raise ValueError(f"Duplicate xLights StartChannel {start} in {path}")
        models[name] = {
            "name": name, "color": color, "unit": unit, "circuit": circuit,
            "start_channel": start,
        }
        addresses[(unit, circuit)] = name
        starts[start] = name
    return models


def _exact_settings(text: str, expected: dict[str, str]) -> bool:
    """Accept only the audited flat-On contract, with no hidden modifiers."""
    parsed = {}
    for item in text.split(","):
        key, separator, value = item.strip().partition("=")
        key, value = key.strip(), value.strip()
        if not separator or not key or key in parsed:
            return False
        parsed[key] = value
    return parsed == expected


def _centiseconds(ms: int, *, ceil: bool = False) -> int:
    return (ms + 9) // 10 if ceil else ms // 10


def export_legacy_lms(ac_xsq: Path, mapping_csv: Path, destination: Path) -> dict:
    ac_xsq, destination = Path(ac_xsq), Path(destination)
    if ac_xsq.resolve() == destination.resolve():
        raise ValueError("Output cannot overwrite input")
    if destination.suffix.lower() != ".lms":
        raise ValueError("Legacy Light-O-Rama output must use .lms extension")
    mapped = read_lor_map(mapping_csv)
    src = ET.parse(ac_xsq).getroot()
    duration_ms = int(round(float(src.findtext("./head/sequenceDuration", "0")) * 1000))
    if duration_ms <= 0:
        raise ValueError("Sequence duration must be positive")
    duration_cs = _centiseconds(duration_ms, ceil=True)
    palette = src.findall("./ColorPalettes/ColorPalette")
    if len(palette) != 1 or not _exact_settings(
        (palette[0].text or "").upper(),
        {"C_BUTTON_PALETTE1": "#FFFFFF", "C_CHECKBOX_PALETTE1": "1"},
    ):
        raise ValueError("Refusing LMS export: source is not an AC-only white-intensity XSQ")
    settings = [e.text or "" for e in src.findall("./EffectDB/Effect")]
    if not settings:
        raise ValueError("AC-only XSQ must contain On settings")
    intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for row in src.findall("./ElementEffects/Element"):
        if row.get("type") == "timing":
            continue
        if row.get("type") != "model":
            raise ValueError(f"Unexpected source Element type: {row.get('type')}")
        name = row.get("name", "")
        if name not in mapped:
            raise ValueError(f"Missing approved LOR unit/circuit mapping for {name!r}")
        for e in row.findall("./EffectLayer/Effect"):
            if e.get("name") != "On" or e.get("palette") != "0":
                raise ValueError(f"Only AC On effects allowed, found {e.get('name')!r} on {name}")
            try:
                ref = int(e.get("ref", "-1"))
            except ValueError as exc:
                raise ValueError("Invalid XSQ effect setting reference") from exc
            if ref < 0 or ref >= len(settings):
                raise ValueError("Invalid XSQ On settings index")
            config = settings[ref]
            if not _exact_settings(config, {
                "E_TEXTCTRL_Eff_On_Start": "100",
                "E_TEXTCTRL_Eff_On_End": "100",
            }):
                raise ValueError("Non-constant intensity or fade effect cannot be exported to full-on LMS")
            try:
                start = int(e.attrib["startTime"])
                end = int(e.attrib["endTime"])
            except (KeyError, ValueError) as exc:
                raise ValueError("Missing or invalid XSQ On interval timestamp") from exc
            if not 0 <= start < end <= duration_ms:
                raise ValueError("Invalid or out-of-bounds On interval")
            start_cs = _centiseconds(start)
            end_cs = min(duration_cs, _centiseconds(end, ceil=True))
            if end_cs <= start_cs:
                end_cs = min(duration_cs, start_cs + 1)
            intervals[name].append((start_cs, end_cs))
    if not intervals:
        raise ValueError("There are no AC effects to export")

    root = ET.Element("sequence", {
        "saveFileVersion": "14",
        "author": "Helix Sequencer",
        "videoUsage": "2",
    })
    music = src.findtext("./head/mediaFile") or ""
    if music:
        root.set("musicFilename", Path(music).name)
    name = src.findtext("./head/song") or ""
    if name:
        root.set("musicTitle", name)
    channels = ET.SubElement(root, "channels")
    exported = 0
    for index, name in enumerate(sorted(intervals, key=lambda n:(mapped[n]["unit"], mapped[n]["circuit"]))):
        info = mapped[name]
        display_color = {"red": "255", "green": "65280", "white": "16777215"}[info["color"]]
        channel = ET.SubElement(channels, "channel", {
            "name": name, "color": display_color, "centiseconds": str(duration_cs),
            "deviceType": "LOR", "unit": str(info["unit"]),
            "circuit": str(info["circuit"]), "savedIndex": str(index),
        })
        merged = []
        for start, end in sorted(intervals[name]):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        for start, end in merged:
            ET.SubElement(channel, "effect", {
                "type": "intensity", "startCentisecond": str(start),
                "endCentisecond": str(end), "intensity": "100",
            })
            exported += 1
    grids = ET.SubElement(root, "timingGrids")
    ET.SubElement(grids, "timingGrid", {
        "saveID": "0", "name": "Fixed Grid: 0.01", "type": "fixed", "spacing": "1"
    })
    tracks = ET.SubElement(root, "tracks")
    track = ET.SubElement(tracks, "track", {
        "totalCentiseconds": str(duration_cs), "timingGrid": "0"
    })
    track_channels = ET.SubElement(track, "channels")
    for index in range(len(channels)):
        ET.SubElement(track_channels, "channel", {"savedIndex": str(index)})
    ET.SubElement(track, "loopLevels")
    ET.SubElement(root, "animation", {"rows": "40", "columns": "60", "image": ""})

    # Reparse in memory before writing: never silently export unbound wiring.
    for channel in channels:
        assert channel.get("deviceType") == "LOR"
        assert 1 <= int(channel.get("unit", "0")) <= 255
        assert 1 <= int(channel.get("circuit", "0")) <= 16
        for effect in channel.findall("effect"):
            assert effect.get("intensity") == "100" and effect.get("type") == "intensity"
    destination.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
    report = {
        "output": str(destination), "input_xsq": str(ac_xsq), "mapping_csv": str(mapping_csv),
        "format": "legacy Light-O-Rama LMS XML (NOT S5/S6 LOREDIT)",
        "mapped_channels": len(channels), "on_effects": exported,
        "duration_centiseconds": duration_cs,
        "verified_lor_import": False, "verified_controller_hardware": False,
        "warning": "Inspect LMS in legacy LOR Sequencer and verify all unit/circuit addresses before playback.",
    }
    destination.with_suffix(".lms_validation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("xsq", type=Path, help="On-only AC output XSQ")
    p.add_argument("--channel-map", type=Path, required=True,
                   help="Complete CSV with controller_unit and controller_circuit columns")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(export_legacy_lms(a.xsq, a.channel_map, a.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
