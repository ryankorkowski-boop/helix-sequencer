"""Profile the real CLI with reconstructed former and current defaults.

This is a controlled source-bound experiment, not a historical runtime claim.
No audio, DSP function, orchestration function or export is mocked.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import pstats
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def musical_signature(path):
    root = ET.parse(path).getroot()
    facts = {}
    for name in ("ColorPalettes", "EffectDB", "ElementEffects", "DisplayElements"):
        node = root.find(name)
        if node is None:
            raise RuntimeError("Missing sequence component: " + name)
        facts[name] = ET.tostring(node, encoding="unicode")
    effects = root.findall("./ElementEffects/Element[@type='model']/EffectLayer/Effect")
    if not effects:
        raise RuntimeError("CLI produced no editable model effects")
    facts["sequenceDuration"] = root.findtext("./head/sequenceDuration")
    facts["sequenceTiming"] = root.findtext("./head/sequenceTiming")
    return hashlib.sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest(), len(effects)


def profile(audio, expected_sha, output, repeats=2):
    root = Path(__file__).resolve().parent.parent
    audio, output = Path(audio).resolve(), Path(output).resolve()
    if digest(audio) != expected_sha:
        raise ValueError("Original audio SHA256 mismatch")
    if output.exists():
        raise FileExistsError("Use a fresh profiling output directory")
    output.mkdir(parents=True)
    template, layout = root / "template.xsq", root / "xlights_rgbeffects.xml"
    report = {
        "schema": "helix.real_cli_profile.v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "audio_sha256": expected_sha, "template_sha256": digest(template),
        "layout_sha256": digest(layout), "runs": [],
        "comparison": "Current code with reconstructed former defaults versus current defaults; same DSP cache implementation.",
        "controls": "Same runner/input/template/layout; separate processes/output; history and learning disabled; no saved settings.",
        "limits": ["One 36-second real excerpt; not catalog-wide or full-song validation.",
                   "cProfile adds overhead equally; persistent JIT/OS caches may affect order.",
                   "File-level musical parity is not native rendering or musical ground truth.",
                   "Former defaults are reconstructed on current code, not historical executable timings."],
        "native_render_verified": False, "physical_hardware_verified": False,
    }
    # Alternate order to expose first-run/JIT-cache bias.
    order = ["former", "current", "current", "former"] if repeats == 2 else ["former", "current"]
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="2",
               OPENBLAS_NUM_THREADS="2", NUMBA_NUM_THREADS="2")
    for number, mode in enumerate(order, 1):
        run_dir = output / f"{number:02d}-{mode}"
        run_dir.mkdir()
        result_dir = run_dir / "sequences"
        stats_path, rss_path = run_dir / "cli.pstats", run_dir / "resources.txt"
        args = [sys.executable, "-m", "cProfile", "-o", str(stats_path),
                str(root / "main.py"), "--profile", "master", "--",
                "--template", str(template), "--layout-file", str(layout),
                "--audio", str(audio), "--output-dir", str(result_dir),
                "--settings", str(run_dir / "absent-settings.json"),
                "--no-prompt", "--no-save-settings",
                "--no-workspace-history", "--no-learning-memory"]
        if mode == "former":
            args += ["--effects-orchestrator", "--variants", "3"]
        started = time.perf_counter()
        with (run_dir / "cli.log").open("w") as log:
            completed = subprocess.run(
                ["/usr/bin/time", "-f", "%e %M", "-o", str(rss_path), *args],
                cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=1200,
            )
        entry = {"mode": mode, "command": args, "returncode": completed.returncode,
                 "wall_seconds": time.perf_counter() - started}
        if completed.returncode:
            report["runs"].append(entry)
            (output / "real_cli_profile.json").write_text(json.dumps(report, indent=2))
            raise RuntimeError(f"Actual CLI failed: {run_dir / 'cli.log'}")
        measured = rss_path.read_text().split()
        entry["time_wall_seconds"], entry["peak_rss_kib"] = float(measured[0]), int(measured[1])
        xsq = result_dir / (audio.stem + ",v27.3.xsq")
        entry["sequence_sha256"] = digest(xsq)
        entry["musical_signature"], entry["model_effects"] = musical_signature(xsq)
        entry["all_xsq_count"] = len(list(result_dir.rglob("*.xsq")))
        orchestration = list(result_dir.glob("*.effects_orchestration.json"))
        entry["orchestration_reports"] = len(orchestration)
        if mode == "former":
            if len(orchestration) != 1 or not json.loads(orchestration[0].read_text()).get("invoked"):
                raise RuntimeError("Former-default sidecar did not actually execute")
        elif orchestration:
            raise RuntimeError("Current default unexpectedly invoked optional orchestration")
        stats = pstats.Stats(str(stats_path))
        top = sorted(stats.stats.items(), key=lambda item: item[1][3], reverse=True)[:30]
        entry["top_cumulative_functions"] = [
            {"file": key[0], "line": key[1], "function": key[2],
             "primitive_calls": value[0], "calls": value[1],
             "self_seconds": value[2], "cumulative_seconds": value[3]}
            for key, value in top]
        report["runs"].append(entry)
        report["audio_preserved"] = digest(audio) == expected_sha
        (output / "real_cli_profile.json").write_text(json.dumps(report, indent=2))
        print(json.dumps({k: v for k, v in entry.items() if k not in ("command", "top_cumulative_functions")}), flush=True)
    report["musical_parity"] = len({r["musical_signature"] for r in report["runs"]}) == 1
    report["summary"] = {
        mode: {"mean_wall_seconds": sum(r["wall_seconds"] for r in report["runs"] if r["mode"] == mode) / order.count(mode),
               "peak_rss_kib": max(r["peak_rss_kib"] for r in report["runs"] if r["mode"] == mode)}
        for mode in ("former", "current")}
    (output / "real_cli_profile.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"musical_parity": report["musical_parity"], "summary": report["summary"]}), flush=True)
    if not report["musical_parity"] or not report["audio_preserved"]:
        raise RuntimeError("Real-source musical parity/audio preservation failed")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--audio-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    profile(args.audio, args.audio_sha256, args.output, args.repeats)
