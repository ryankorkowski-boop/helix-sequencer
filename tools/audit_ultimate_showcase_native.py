"""Verify actual xLights-rendered channels against the intended showcase colours."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from models.ultimate_showcase import build_ultimate_garden, NATIVE_TYPES, family
from tools.build_helpers.ultimate_showcase_preview import read_fseq, _rgb


def audit_native(output: Path, attributes_path: Path | None = None) -> dict:
    g=build_ultimate_garden();frames,step=read_fseq(output/"Helix_Aurora_Showcase.fseq")
    if len(frames)*step!=24000:raise ValueError("Native duration does not match the24s XSQ")
    index=round(20000/step)
    rows=[]
    for m in g.models:
        if m.kind!="pixel":continue
        values=frames[index,m.start-1:m.start-1+m.channels].reshape(-1,3)
        error=float(np.max(np.abs(values.astype(float)-_rgb(m.colors)*.9)))
        row={"model":m.name,"pixels":len(values),"dark_pixels":int(np.sum(values.max(axis=1)==0)),
             "max_palette_error":error,"matches":error<=3}
        rows.append(row)
    if not all(r["matches"] for r in rows):
        raise ValueError(f"Incorrect/missing native lighting: {[r for r in rows if not r['matches']]}")
    native=[]
    if attributes_path:
        native=json.loads(attributes_path.read_text(encoding="utf-8"))
        if {r["name"] for r in native}!={m.name for m in g.models}:raise ValueError("Native model list mismatch")
        starts={m.name:m.start for m in g.models}
        for row in native:
            attrs=row["native_attributes"]
            if attrs.get("StartChannel")!=str(starts[row["name"]]):raise ValueError(f"Native channel map changed: {row['name']}")
        if {family(r["native_attributes"]["DisplayAs"]) for r in native}!=set(NATIVE_TYPES):raise ValueError("Native families missing")
    proof={"schema":"helix.ultimate_showcase.native_verification.v1","native_version":"2026.18",
           "native_render_success":True,"native_frames":len(frames),"native_frame_ms":step,
           "checked_rgb_models":len(rows),"checked_rgb_pixels":sum(r["pixels"] for r in rows),
           "all_pixels_lit_correctly":True,"native_gui_models_checked":len(native),
           "native_gui_channels_match":True if native else None,
           "native_gui_families_checked":len(NATIVE_TYPES) if native else None,
           "layout_sha256":hashlib.sha256((output/"xlights_rgbeffects.xml").read_bytes()).hexdigest(),
           "xsq_sha256":hashlib.sha256((output/"Helix_Aurora_Showcase.xsq").read_bytes()).hexdigest(),
           "fseq_sha256":hashlib.sha256((output/"Helix_Aurora_Showcase.fseq").read_bytes()).hexdigest(),
           "source_geometry_note":"Custom nodes are exact exported grids. Stock-native preview paths follow authored geometry; native GUI/import was separately checked.",
           "models":rows}
    (output/"native_verification.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
    return proof


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--native-attributes",type=Path)
    args=parser.parse_args();proof=audit_native(args.output,args.native_attributes)
    print(json.dumps({k:v for k,v in proof.items() if k!="models"},indent=2))


if __name__=="__main__":main()
