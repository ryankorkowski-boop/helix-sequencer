"""Fail-closed trace from source-timed Helix events into native XSQ lanes.

This verifies the *input* to xLights; it does not claim rendered FSEQ pixels
match the input. A native render and FSEQ activity check are still required.
"""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def verify(folder: Path) -> dict:
    folder = Path(folder)
    manifest = json.loads((folder / "run_manifest.json").read_text())
    xsq = folder / manifest["xsq"]
    root = ET.parse(xsq).getroot()
    effect_rows = [(element.get("name", ""), effect)
                   for element in root.findall(".//ElementEffects/Element")
                   for layer in element if layer.tag in {"EffectLayer", "SubModelEffectLayer"}
                   for effect in layer.findall("Effect")]
    effects = [effect for _, effect in effect_rows]
    if not effects:
        raise ValueError("No effects reach the authoritative native XSQ")
    source_effects = [effect for effect in effects if effect.get("sourceMethod", "").startswith("retained_production_")]
    # Validate source event clocks, not merely effect counts. Instrument
    # gesture effects may be shorter than sustained source notes by design.
    duration_ms = round(float(root.findtext("head/sequenceDuration", "0")) * 1000)
    timing_checked = 0
    for name, effect in effect_rows:
        if effect.get("sourceMethod") not in (
            "retained_production_band_plan", "retained_production_drum_plan"
        ):
            continue
        start = effect.get("sourceStartMs")
        if start is None:
            raise ValueError(f"Source effect {name} lacks its original onset clock")
        onset = int(start)
        if onset < 0 or (duration_ms > 0 and onset >= duration_ms):
            raise ValueError(f"Source effect {name} has out-of-range onset {onset}")
        rendered_onset = int(effect.get("startTime", "-1"))
        if rendered_onset != onset:
            raise ValueError(
                f"Native effect {name} starts at {rendered_onset}ms, "
                f"but source event starts at {start}ms"
            )
        end = effect.get("sourceEndMs")
        if end is not None and (int(end) <= onset or (duration_ms > 0 and int(end) > duration_ms)):
            raise ValueError(f"Source effect {name} has invalid source offset {end}")
        timing_checked += 1
    band = (folder / "Band_Instrument_Provenance.json")
    result = {
        "schema": "helix.render_logic_provenance.v1",
        "source_audio_sha256": manifest["source_audio_sha256"],
        "source_analysis_sha256": manifest["source_analysis_sha256"],
        "xsq": manifest["xsq"],
        "xsq_effects": len(effects),
        "source_tagged_effects": len(source_effects),
        "source_timing_checked_effects": timing_checked,
        "native_fseq_verified": False,
        "status": "xsq_source_trace_verified",
    }
    if band.is_file():
        report = json.loads(band.read_text())
        models = report.get("models", {})
        mapped = sum(int(m.get("mapped_events", 0)) for m in models.values())
        result["instrument_mapped_events"] = mapped
        coverage = {}
        for model_name, counts in models.items():
            expected = int(counts.get("mapped_events", 0))
            actual = sum(name.startswith(model_name + "/")
                         and effect.get("sourceMethod") == "retained_production_band_plan"
                         for name, effect in effect_rows)
            coverage[model_name] = {"mapped_events": expected, "source_effects": actual}
            if actual < expected:
                raise ValueError(f"Musician {model_name}: {expected} mapped cues but only {actual} source effects in native XSQ")
        result["instrument_coverage"] = coverage
    drummer = folder / "Canonical_Drummer.json"
    if drummer.is_file():
        report = json.loads(drummer.read_text())
        counts = report.get("event_mapping", {}).get("component_events", {})
        result["drum_component_events"] = counts
        coverage = {}
        for component, count in counts.items():
            expected = int(count)
            suffix = component + "_SURFACE"
            actual = sum(name.endswith(suffix)
                         and effect.get("sourceMethod") == "retained_production_drum_plan"
                         and effect.get("sourceComponent", "").endswith(suffix)
                         for name, effect in effect_rows)
            coverage[component] = {"detected_events": expected, "source_effects": actual}
            if actual < expected:
                raise ValueError(f"Drum {component}: {expected} detected strikes but only {actual} source effects in native XSQ")
        result["drum_coverage"] = coverage
    if band.is_file() and not source_effects and result.get("instrument_mapped_events", 0):
        raise ValueError("Band effects have no source provenance")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.folder)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
