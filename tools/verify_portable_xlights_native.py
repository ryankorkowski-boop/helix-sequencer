"""Render portable shows with installed xLights and audit native FSEQ values."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import subprocess

import numpy as np

from tools.build_helpers.ultimate_showcase_preview import read_fseq
from tools.showcase_audio_preview import NativeSongView
from models.showcase_flavors import build_flavor


def audit(folder: Path, sequence: dict) -> dict:
    fseq = (folder / sequence["file"]).with_suffix(".fseq")
    frames, step = read_fseq(fseq)
    expected = int(round(sequence["duration_seconds"] * 1000 / step))
    if len(frames) != expected or step != 50:
        raise ValueError(f"Native frame duration differs for {sequence['file']}")
    manifest = json.loads((folder / "showcase_manifest.json").read_text())
    coverage = []
    omitted_controls = []
    for model in manifest["models"]:
        values = frames[:, model["start_channel"] - 1:model["end_channel"]]
        if model["kind"] == "pixel" and values.shape[1] != model["end_channel"] - model["start_channel"] + 1:
            raise ValueError("FSEQ does not include the declared model channels")
        if model["kind"] == "pixel":
            active = int(np.count_nonzero(values.max(axis=1)))
            coverage.append({"model": model["name"], "active_frames": active, "peak": int(values.max())})
        else:
            if values.any():
                raise ValueError(f"Control channels lit: {model['name']}")
            if model["end_channel"] > frames.shape[1]:
                # xLights trims an unsequenced trailing control range from FSEQ.
                # Such omitted channels are implicit zero, never missing RGB proof.
                omitted_controls.append(model["name"])
    if not coverage or any(m["active_frames"] == 0 for m in coverage):
        raise ValueError(f"Unlit RGB models: {[m['model'] for m in coverage if not m['active_frames']]}")
    if not np.any(frames[1:] != frames[:-1]):
        raise ValueError("Native lighting does not animate")
    if folder.name == "Helix_Fire_and_Ice" and sequence["file"].startswith("Wire_Tree__"):
        garden = build_flavor("fire_and_ice")
        view = NativeSongView(garden, "Wire Tree", 1280, 720)
        review = folder / "native_review_frames"
        review.mkdir(exist_ok=True)
        for seconds in (30, 128, 250):
            view.frame(frames[round(seconds * 1000 / step)]).save(review / f"{seconds}s.png")
    result = {"native_render": "success", "native_frames": len(frames), "native_frame_ms": step,
              "rgb_models": len(coverage), "active_rgb_models": len(coverage),
              "all_rgb_models_active": True, "control_channels_dark": True,
              "lighting_animated": True, "fseq": fseq.name,
              "implicit_zero_trailing_controls": omitted_controls,
              "xsq_sha256": hashlib.sha256((folder / sequence["file"]).read_bytes()).hexdigest(),
              "layout_sha256": hashlib.sha256((folder / "xlights_rgbeffects.xml").read_bytes()).hexdigest(),
              "fseq_sha256": hashlib.sha256(fseq.read_bytes()).hexdigest(), "model_coverage": coverage}
    del frames
    return result


def verify_show(root: Path, show: dict, executable: Path, audit_existing: bool = False) -> tuple[str, list[dict]]:
    folder = root / show["folder"]
    results = []
    for sequence in show["sequences"]:
        xsq = folder / sequence["file"]
        log = folder / (xsq.stem + ".native_render.log")
        command = [str(executable), "--headless", "-q", "-s", str(folder), "-m", str(folder),
                   "-od", str(folder), str(xsq)]
        inputs = [xsq, folder / "xlights_rgbeffects.xml"]
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs]
        if audit_existing:
            fseq = xsq.with_suffix(".fseq")
            if not fseq.is_file() or fseq.stat().st_mtime_ns < max(p.stat().st_mtime_ns for p in inputs):
                raise ValueError("Existing native output is missing or older than its inputs; rerender")
        else:
            with log.open("w") as stream:
                subprocess.run(command, cwd=folder, env={**os.environ, "XL_NO_GPU_COMPUTE": "1"},
                               stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=1800)
        if before != [hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs]:
            raise ValueError("Native rendering changed the sequence or layout")
        result = audit(folder, sequence)
        result["file"] = sequence["file"]
        results.append(result)
        (folder / "native_verification_portable.json").write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps({"stage": "native_verified", "show": folder.name, "sequence": xsq.name,
                          "frames": result["native_frames"], "rgb_models": result["rgb_models"]}), flush=True)
    return show["folder"], results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--xlights", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--audit-existing", action="store_true", help="Audit a just-rendered batch without rendering it again")
    args = parser.parse_args()
    root = args.root.resolve()
    report = json.loads((root / "SHOWS.json").read_text())
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context("spawn")) as pool:
        futures = [pool.submit(verify_show, root, show, args.xlights.resolve(), args.audit_existing) for show in report["shows"]]
        failures = []
        for future in as_completed(futures):
            try:
                name, results = future.result()
            except Exception as exc:
                failures.append(str(exc))
                continue
            show = next(s for s in report["shows"] if s["folder"] == name)
            mapping = {r["file"]: r for r in results}
            for sequence in show["sequences"]:
                sequence["native_verification"] = mapping[sequence["file"]]
            (root / "SHOWS.json").write_text(json.dumps(report, indent=2) + "\n")
    if failures:
        raise RuntimeError("Native verification failed: " + "; ".join(failures))
    print("All seven shows and all sequences rendered and audited.", flush=True)


if __name__ == "__main__":
    main()
