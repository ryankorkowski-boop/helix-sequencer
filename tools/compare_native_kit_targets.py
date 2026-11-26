"""Compare the shipped-layout kit diagnostic with the MASTER_TODO component list."""

import argparse
from collections import Counter
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from core.snowman_band import drummer_placements
from tools.verify_native_xlights_gate import sha256

PREFIX = "HX_SNOWMAN_DRUMMER_"
ORACLE = {"KICK", "SNARE", "HI_HAT", "TOM_1", "TOM_2", "TOM_3", "TOM_4", "CYMBAL_LEFT", "CYMBAL_RIGHT"}
HIT_NAMES = ORACLE | {"TOM", "CYMBALS"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("show", type=Path)
    parser.add_argument("xsq", type=Path)
    parser.add_argument("audio_source", type=Path)
    args = parser.parse_args()
    layout = ET.parse(args.show / "xlights_rgbeffects.xml")
    native = json.loads((args.show / "native-gate.json").read_text())
    if native["xsq_input_sha256"] != sha256(args.xsq):
        raise ValueError("XSQ differs from the native renderer input")
    band = json.loads(args.xsq.with_suffix(".snowman_band.json").read_text())
    rows = ET.parse(args.xsq).findall("./ElementEffects/Element")
    available = {
        model.get("name", "").removeprefix(PREFIX)
        for model in layout.findall("./models/model/subModel")
        if model.get("name", "").startswith(PREFIX)
    } & HIT_NAMES
    generated = {
        (model.get("name", ""), int(effect.get("startTime", "0")))
        for model in rows for layer in model.findall("EffectLayer")
        if layer.get("name", "").startswith("AUTO_DreamSequenceWeaver_")
        for effect in layer.findall("Effect")
    }
    proposed = {(model, start) for model, start, _ in drummer_placements(band, [row.get("name", "") for row in rows])}
    matched = Counter(model.split("/")[-1].removeprefix(PREFIX) for model, _ in proposed & generated)
    report = {
        "scope": "native_render_of_shipped_layout_with_xsq_detector_anchor_comparison",
        "commit": native["commit"],
        "source_sha256": sha256(args.audio_source),
        "excerpt_start_ms": 0,
        "excerpt_duration_ms": 36000,
        "excerpt_sha256": native["audio_input_sha256"],
        "xsq_sha256": native["xsq_input_sha256"],
        "fseq_sha256": native["fseq_sha256"],
        "native_active_frames": native["active_frames"],
        "oracle_commit": "b27e8d77a63027ed32bcf6851dcff3925472c155",
        "oracle_components": sorted(ORACLE),
        "layout_hit_targets": sorted(available),
        "missing_oracle_targets": sorted(ORACLE - available),
        "proposed_distinct_target_onsets": len(proposed),
        "serialized_exact_target_onset_matches": dict(sorted(matched.items())),
        "native_per_component_playback": "unverified",
    }
    (args.show / "kit-comparison.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
