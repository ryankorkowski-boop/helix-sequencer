"""Run the real master CLI in fresh processes and retain comparable evidence.

Usage: python -m tools.measure_engine_stages --audio SONG --output FRESH_DIR
Set HELIX_AUDIO_CACHE_DIR externally to measure opt-in persistent feature reuse.
No source, threshold, profile default or audio is replaced for this benchmark.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import xml.etree.ElementTree as ET

from tools.profile_real_sequence import musical_signature

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def output_contract(path: Path) -> dict:
    root = ET.parse(path).getroot()
    duration = float(root.findtext("./head/sequenceDuration")) * 1000
    assert math.isfinite(duration) and duration > 0, "Invalid duration"
    declared = {node.get("name") for node in root.findall("./DisplayElements/Element")}
    count = 0
    for model in root.findall("./ElementEffects/Element[@type='model']"):
        assert model.get("name") in declared, f"Undeclared model: {model.get('name')}"
        for layer in model.findall("./EffectLayer"):
            for effect in layer.findall("./Effect"):
                start, end = (float(effect.get(key)) for key in ("startTime", "endTime"))
                assert math.isfinite(start) and math.isfinite(end), "Nonfinite effect time"
                assert 0 <= start <= end <= duration, (model.get("name"), start, end, duration)
                # xLights accepts authoring order in a layer. Preserve existing
                # XML order; chronological interval endpoints are the contract.
                count += 1
    assert count > 0, "No model effects"
    return {"model_effects": count, "duration_seconds": duration / 1000,
            "declared_model_targets": True, "finite_bounded_intervals": True}


def measure(audio: Path, template: Path, layout: Path, output: Path, runs: int = 2) -> dict:
    audio, template, layout, output = (p.resolve() for p in (audio, template, layout, output))
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "helix.master_stage_comparison.v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "inputs": {"audio_sha256": digest(audio), "template_sha256": digest(template),
                   "layout_sha256": digest(layout)},
        "controls": "Fresh processes, identical inputs, two numerical threads, no saved settings/history/learning.",
        "persistent_feature_cache": bool(os.environ.get("HELIX_AUDIO_CACHE_DIR")),
        "limits": ["First run may compile JIT kernels and populate existing stem caches.",
                   "Same-host timings; no Windows or physical-device performance claim.",
                   "Musical/XML contracts do not establish native xLights render acceptance."],
        "runs": [],
    }
    for number in range(1, runs + 1):
        folder = output / f"run-{number}"
        folder.mkdir()
        stages = folder / "stages.json"
        args = [sys.executable, str(ROOT / "main.py"), "--profile", "master", "--",
                "--audio", str(audio), "--template", str(template), "--layout-file", str(layout),
                "--output-dir", str(folder / "sequences"), "--settings", str(folder / "absent-settings.json"),
                "--no-prompt", "--no-save-settings", "--no-workspace-history", "--no-learning-memory"]
        env = dict(os.environ, HELIX_PROFILE_OUTPUT=str(stages), PYTHONHASHSEED="0",
                   OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", NUMBA_NUM_THREADS="2")
        started = perf_counter()
        with (folder / "cli.log").open("w") as stream:
            result = subprocess.run(args, cwd=ROOT, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=1800)
        entry = {"returncode": result.returncode, "cli_wall_seconds": perf_counter() - started,
                 "command": args}
        report["runs"].append(entry)
        if stages.exists():
            entry["metrics"] = json.loads(stages.read_text())
        if result.returncode == 0:
            xsq = folder / "sequences" / f"{audio.stem},v27.3.xsq"
            entry["xsq_sha256"] = digest(xsq)
            entry["musical_signature"], _ = musical_signature(xsq)
            entry["contract"] = output_contract(xsq)
        (output / "measurement.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: v for k, v in entry.items() if k not in ("command", "metrics")}), flush=True)
        if result.returncode:
            raise RuntimeError(f"Master CLI failed; inspect {folder / 'cli.log'}")
    assert digest(audio) == report["inputs"]["audio_sha256"], "Source audio changed"
    assert len({r["musical_signature"] for r in report["runs"]}) == 1, "Musical output drift"
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--template", default=ROOT / "template.xsq", type=Path)
    parser.add_argument("--layout", default=ROOT / "xlights_rgbeffects.xml", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runs", type=int, choices=(1, 2, 3), default=2)
    args = parser.parse_args()
    measure(args.audio, args.template, args.layout, args.output, args.runs)
