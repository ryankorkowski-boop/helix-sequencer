"""Export classified kit cues using the user's actual single-controller LMS.

Run: python -m tools.export_ctb16pc_sequence cues.json --source-lms show.lms
     --unit-id 01 --output new-folder
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from core.ctb16pc_drummer_chorus import ctb16pc_drummer_chorus_patch
from core.ctb16pc_sequence import compile_ctb16pc_sequence
from core.drummer_2d_3d_front_contract import drummer_build_variant
from tools.lor_lms_export_from_source import export_lms_from_xsq
from tools.lor_lms_import import _source_channels, prepare_lms_workspace


def export_ctb16pc_sequence(cues, source_lms, output, *, unit_id):
    patch = ctb16pc_drummer_chorus_patch(unit_id)
    unit = int(unit_id, 16)
    source_lms, output = Path(source_lms), Path(output)
    _root, channels = _source_channels(source_lms)
    if {(c["unit"], c["circuit"]) for c in channels} != {(unit, i) for i in range(1, 17)}:
        raise ValueError("Source LMS must contain exactly the selected unit's sixteen circuits")
    levels = compile_ctb16pc_sequence(cues.get("hits", ()), duration=float(cues["duration"]),
                                    vocals=cues.get("vocals", ()))
    # A fresh directory prevents accidental replacement of any previous show.
    output.mkdir(parents=True, exist_ok=False)
    workspace = prepare_lms_workspace(source_lms, output)
    root = ET.parse(workspace["template"]).getroot()
    duration = len(levels) / 100
    root.find("head/sequenceDuration").text = f"{duration:.2f}"
    root.find("head/sequenceTiming").text = "10 ms"
    root.find("head/mediaFile").text = Path(cues.get("audio_filename", "")).name
    palette = ET.SubElement(root.find("ColorPalettes"), "ColorPalette")
    palette.text = "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
    by_model = {c["model"]: c for c in workspace["channels"]}
    settings_refs = {}
    identifier = 1
    for row in root.findall("ElementEffects/Element"):
        circuit = by_model[row.get("name")]["circuit"]
        values = levels[:, circuit - 1]
        boundaries = np.r_[0, np.flatnonzero(values[1:] != values[:-1]) + 1, len(values)]
        for start, end in zip(boundaries[:-1], boundaries[1:]):
            intensity = int(values[start])
            if not intensity:
                continue
            settings = f"E_TEXTCTRL_Eff_On_Start={intensity},E_TEXTCTRL_Eff_On_End={intensity}"
            if settings not in settings_refs:
                settings_refs[settings] = str(len(root.find("EffectDB")))
                ET.SubElement(root.find("EffectDB"), "Effect").text = settings
            ET.SubElement(row.find("EffectLayer"), "Effect", name="On", ref=settings_refs[settings], palette="0",
                          id=str(identifier), startTime=str(int(start) * 10),
                          endTime=str(int(end) * 10), settings=settings)
            identifier += 1
    root.find("nextid").text = str(identifier)
    xsq = output / "CTB16PC_Drummer_Chorus.xsq"
    ET.ElementTree(root).write(xsq, encoding="utf-8", xml_declaration=True)
    report = export_lms_from_xsq(xsq, source_lms, output / "CTB16PC_Drummer_Chorus.lms",
                                  Path(workspace["manifest"]))
    with (output / "CTB16PC_Wiring.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(patch[0]))
        writer.writeheader()
        writer.writerows(patch)
    variants = {kind: drummer_build_variant(kind) for kind in ("2d", "3d")}
    for variant in variants.values():
        variant.update(unit_id=unit_id.upper(), channels=patch)
    (output / "front_projection_contract.json").write_text(json.dumps(variants, indent=2) + "\n")
    report.update(unit_id=unit_id.upper(), source_lms_sha256=hashlib.sha256(source_lms.read_bytes()).hexdigest(),
                  cue_sha256=hashlib.sha256(json.dumps(cues, sort_keys=True).encode()).hexdigest(),
                  timing_ms=10, physical_controller_verified=False,
                  audio_bundled=False, geometry="synthetic channel grid; front projection is a construction contract")
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cues", type=Path)
    parser.add_argument("--source-lms", type=Path, required=True)
    parser.add_argument("--unit-id", required=True, help="Actual two-digit hexadecimal controller Unit ID")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_ctb16pc_sequence(json.loads(args.cues.read_text()), args.source_lms,
                                             args.output, unit_id=args.unit_id), indent=2))


if __name__ == "__main__":
    main()
