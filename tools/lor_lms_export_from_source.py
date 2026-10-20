"""Translate Helix AC-safe XSQ into legacy Light-O-Rama LMS using SOURCE wiring.

The supplied original LMS is authoritative for actual Unit ID, circuit,
network data, track organization and channel appearance. Never create/guess
controller addresses. S5/S6 .loredit is not generated or modified.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from tools.lor_lms_import import _source_channels


def _settings(root):
    return [e.text or "" for e in root.findall("./EffectDB/Effect")]


def _start_end(settings: str) -> tuple[int, int]:
    def find(key, default):
        for part in settings.split(","):
            if part.startswith(key + "="):
                try:
                    return max(0, min(100, int(round(float(part.split("=", 1)[1])))))
                except ValueError:
                    return default
        return default
    return (
        find("E_TEXTCTRL_Eff_On_Start", 100),
        find("E_TEXTCTRL_Eff_On_End", 100),
    )


def _lms_effect(name: str, start: int, end: int, settings: str):
    kind = {"On": "intensity", "Off": "intensity",
            "Shimmer": "shimmer", "Twinkle": "twinkle"}.get(name)
    if kind is None:
        raise ValueError(f"Unsupported LOR source effect: {name}")
    a, b = _start_end(settings)
    if name == "Off":
        a = b = 0
    attrs = {
        "type": kind,
        "startCentisecond": str(start),
        "endCentisecond": str(end),
    }
    if a == b:
        attrs["intensity"] = str(a)
    else:
        attrs["startIntensity"] = str(a)
        attrs["endIntensity"] = str(b)
    return attrs


def export_lms_from_xsq(
    xsq: Path, source_lms: Path, destination: Path, manifest_path: Path
) -> dict:
    xsq, source_lms, destination, manifest_path = map(
        Path, (xsq, source_lms, destination, manifest_path)
    )
    if destination.resolve() in {xsq.resolve(), source_lms.resolve()}:
        raise ValueError("Cannot overwrite source XSQ or source LMS")
    if destination.suffix.lower() != ".lms":
        raise ValueError("LOR output must be .lms (S5/S6 .loredit unsupported)")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    import hashlib
    if hashlib.sha256(source_lms.read_bytes()).hexdigest() != manifest["source_lms_sha256"]:
        raise ValueError("LMS source has changed since the channel layout was prepared")
    source_root, _channels = _source_channels(source_lms)
    xsq_root = ET.parse(xsq).getroot()
    duration = float(xsq_root.findtext("./head/sequenceDuration") or "0")
    if duration <= 0:
        raise ValueError("Generated sequence has invalid duration")
    duration_cs = max(1, int(round(duration * 100)))
    duration_ms = max(1, round(duration * 1000))
    models = {
        e["model"]: e for e in manifest["channels"]
    }
    # Sequence engine may place group effects. Expand onto actual physical
    # channels before emitting LMS, without fabricating a group controller.
    virtual_layout = Path(manifest["layout"])
    from tools.lor_compatibility import ac_layout_targets, _safe_leaves
    safe, _other, groups = ac_layout_targets(virtual_layout)
    physical = {
        e.get("savedIndex"): e for e in source_root.findall("./channels/channel")
    }
    settings = _settings(xsq_root)
    events = {}
    valid_count = 0
    for row in xsq_root.findall("./ElementEffects/Element"):
        if row.get("type") == "timing":
            continue
        name = row.get("name", "")
        targets = {name} if name in models else _safe_leaves(name, safe, groups)
        if not targets or not targets <= set(models):
            raise ValueError(
                f"Generated output targets {name!r}, not mapped physical LMS channels"
            )
        for effect in row.findall("./EffectLayer/Effect"):
            label = effect.get("name", "")
            if label not in {"On", "Off", "Shimmer", "Twinkle"}:
                raise ValueError(f"Not LOR-safe effect {label!r}")
            t0 = int(float(effect.get("startTime", "0")))
            t1 = int(float(effect.get("endTime", "0")))
            if t0 < 0 or t1 <= t0 or t0 >= duration_ms or t1 > duration_ms:
                raise ValueError(
                    f"XSQ effect interval {t0}..{t1} ms is outside the declared "
                    f"sequence duration {duration_ms} ms; regenerate with the soundtrack duration"
                )
            a = max(0, min(duration_cs - 1, t0 // 10))
            b = min(duration_cs, (t1 + 9) // 10)
            if b <= a:
                continue
            explicit_settings = effect.get("settings")
            if explicit_settings is not None:
                # Helix's XSQ writer stores effect settings directly on
                # individual nodes. Do not accidentally use the fallback
                # EffectDB row, or legitimate dimmer fades would be lost.
                effect_settings = explicit_settings
            else:
                ref = effect.get("ref") or "0"
                if not ref.isdecimal() or int(ref) >= len(settings):
                    raise ValueError("XSQ effect references unknown intensity settings")
                effect_settings = settings[int(ref)]
            for target_name in targets:
                target = models[target_name]["savedIndex"]
                events.setdefault(target, []).append((a, b, label, effect_settings))
                valid_count += 1
    if valid_count == 0:
        raise ValueError("No mapped LOR channel effects generated")

    for channel in source_root.findall("./channels/channel"):
        if channel.get("deviceType", "").upper() != "LOR":
            # Do not rewrite unsupported controller technologies.
            if channel.findall("effect"):
                raise ValueError("Source contains non-LOR channel effects; refusing mixed output")
            continue
        index = channel.get("savedIndex")
        channel.set("centiseconds", str(duration_cs))
        for child in list(channel):
            if child.tag == "effect":
                channel.remove(child)
        records = events.get(index, [])
        # Resolve overlapping XSQ layers into nonoverlapping single-circuit
        # intervals at centisecond boundaries; later starts take precedence.
        boundaries = sorted({0, duration_cs} | {
            t for lo, hi, _name, _cfg in records for t in (lo, hi)
        })
        intervals = []
        for lo, hi in zip(boundaries, boundaries[1:]):
            active = [
                entry for entry in records if entry[0] <= lo and entry[1] >= hi
            ]
            if not active:
                continue
            # Later-starting effect wins; stable deterministic tie breaking.
            chosen = max(active, key=lambda row: (row[0], row[1], row[2]))
            _st, _en, label, cfg = chosen
            a, b = _start_end(cfg)
            if label == "Off":
                a = b = 0
            if a != b:
                # Derive fade endpoint intensity within original interval.
                fraction0 = (lo - _st) / max(1, _en - _st)
                fraction1 = (hi - _st) / max(1, _en - _st)
                ia = round(a + (b - a) * fraction0)
                ib = round(a + (b - a) * fraction1)
                fade_cfg = (
                    f"E_TEXTCTRL_Eff_On_Start={ia},"
                    f"E_TEXTCTRL_Eff_On_End={ib}"
                )
            else:
                fade_cfg = cfg
            attrs = _lms_effect(label, lo, hi, fade_cfg)
            if intervals and intervals[-1][1] == lo and intervals[-1][2] == attrs:
                # Adjacent equal effects may merge (but offsets differ).
                pass
            intervals.append((lo, hi, attrs))
        for _start, _end, attrs in intervals:
            ET.SubElement(channel, "effect", attrs)
    # Existing beat grids describe the OLD song, so replace them with a
    # regular 50 ms grid while preserving actual LOR channel rows/tracks.
    timing_grids = source_root.find("timingGrids")
    if timing_grids is None:
        timing_grids = ET.SubElement(source_root, "timingGrids")
    timing_grids.clear()
    ET.SubElement(timing_grids, "timingGrid", {
        "saveID": "0", "name": "Helix 50 ms", "type": "fixed", "spacing": "5"
    })
    for track in source_root.findall("./tracks/track"):
        track.set("totalCentiseconds", str(duration_cs))
        track.set("timingGrid", "0")
    source_root.set("musicFilename", Path(xsq_root.findtext("./head/mediaFile") or "").name)
    source_root.set("musicTitle", xsq_root.findtext("./head/song") or destination.stem)
    destination.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(source_root).write(destination, encoding="utf-8", xml_declaration=True)
    output_events = sum(
        len(c.findall("effect")) for c in source_root.findall("./channels/channel")
    )
    report = {
        "schema": "helix.lor_lms_export.v1",
        "output": str(destination),
        "format": "legacy .lms (NOT proprietary .loredit)",
        "source_lms": source_lms.name,
        "source_channel_count": len(models),
        "mapped_input_effects": valid_count,
        "output_effects": output_events,
        "time_rounding": "10 ms centisecond",
        "overlap_policy": "later-starting effect wins",
        "verified_lor_import": False,
        "native_loredit_supported": False,
        "physical_controller_verified": False,
    }
    destination.with_suffix(".lms_validation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report
