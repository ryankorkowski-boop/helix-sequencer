"""Render the Helix-authored XSQ through native xLights and verify its activity."""

import argparse
import json
from pathlib import Path
import time

import numpy as np

from core.output_provenance import sha256
from tools.layout_bench.xlights_fseq import load_fseq, render_sequence_to_fseq
from tools.layout_bench.run_bench import canonical_xsq


def verify(show: Path, sequences: Path, audio: Path, output: Path):
    output.mkdir(parents=True,exist_ok=True)
    layout=show/"xlights_rgbeffects.xml"
    manifest=json.loads((show/"scene_manifest.json").read_text())
    xsq=canonical_xsq(sequences,audio.stem)
    if xsq is None:
        raise ValueError(f"No master-profile XSQ for {audio.name}")
    portable=output/f"{audio.stem}.xsq"
    portable.write_bytes(xsq.read_bytes())
    fseq=portable.with_suffix(".fseq")
    start=time.perf_counter()
    version=render_sequence_to_fseq(layout_xml=layout,xsq_path=portable,media_path=audio,fseq_path=fseq,show_dir=output/"native")
    elapsed=time.perf_counter()-start
    data=load_fseq(fseq)
    channels=manifest["total_rgb_channels"]
    if data.sparse_start or data.channels<channels:
        raise ValueError(f"Native FSEQ channels {data.channels} from {data.sparse_start} do not cover {channels}")
    ever_lit=np.zeros(channels,dtype=bool)
    changed=np.zeros(channels,dtype=bool)
    previous=None
    for frame in data.rows():
        row=frame[:channels]
        ever_lit |= row>0
        if previous is not None:
            changed |= row!=previous
        previous=row
    counts={name:{"mapped":0,"active":0,"changing":0} for name in manifest["districts"]}
    band={}
    for model in manifest["models"]:
        current=counts[model["district"]]
        indices=slice(model["first_channel"]-1,model["last_channel"])
        lit=bool(ever_lit[indices].any())
        moving=bool(changed[indices].any())
        current["mapped"]+=1
        current["active"]+=lit
        current["changing"]+=moving
        if model["model"].startswith("HX_INFINITY_SNOW_"):
            band[model["family"]]={"lit_channels":int(ever_lit[indices].sum()),"changing_channels":int(changed[indices].sum())}
    receipt={"owner_approved":False,"renderer":version,"audio_sha256":sha256(audio),
             "layout_sha256":sha256(layout),"xsq_sha256":sha256(portable),"fseq_sha256":sha256(fseq),
             "frames":data.frames,"step_ms":data.step_ms,"channels":data.channels,
             "native_render_seconds":round(elapsed,3),"districts":counts,"performers":band}
    (output/"native_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))
    if not all(row["changing"] for row in counts.values()):
        raise ValueError("At least one district has no changing native channels")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ("show","sequences","audio","output"):
        parser.add_argument(arg,type=Path)
    args=parser.parse_args()
    verify(args.show,args.sequences,args.audio,args.output)
