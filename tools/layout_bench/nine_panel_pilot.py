#!/usr/bin/env python3
"""Nine-panel xLights FSEQ approval pilot; never substitutes synthetic band motion for ground truth."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path
from tools.layout_bench import render_comparisons as bench

# Order is immutable. Existing bench fixtures are explicitly provisional where noted.
PANELS = [
    ("ac16_lor", "16-channel LOR AC", False),
    ("ac64_yard", "256-channel AC + arches + megatree", True),
    ("pixel_classic", "RGB-heavy house", True),
    ("pixel_starter", "Coro singing faces", True),
    ("band_stage", "Canonical six-snowman band", True),
    ("pixel_corner", "Singing trees and matrices", True),
    ("wow_moire", "Birdsong 3D digital matrix", True),
    ("wow_helix", "Piano sequential groupings", True),
    ("wow_showcase", "Ultimate xLights showcase", True),
]

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--audio", type=Path, required=True, help="Real full-mix audio with vocals")
    p.add_argument("--run-root", type=Path, default=bench.ROOT / "test_runs/nine_panel_isolated")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--generate-xsq", action="store_true", help="Generate missing XSQ using isolated single-worker bench")
    p.add_argument("--allow-provisional", action="store_true", help="Allow bench fixture stand-ins for engineering preview only")
    args = p.parse_args()
    if args.output.resolve().is_relative_to((bench.ROOT / "fixtures").resolve()):
        p.error("Output must not overwrite repository fixtures")
    if not args.audio.is_file():
        p.error("Real audio file not found")
    if any(provisional for _, _, provisional in PANELS) and not args.allow_provisional:
        p.error("Eight layouts are provisional bench fixtures, not approved nine-panel layouts. Use --allow-provisional for an explicitly labeled engineering preview.")
    manifest = bench.load_manifest()
    missing = [id for id, _, _ in PANELS if id not in manifest]
    if missing:
        p.error(f"Missing layout fixtures: {missing}")
    if args.generate_xsq:
        missing_xsq = []
        for layout_id, _, _ in PANELS:
            try:
                bench.find_xsq(args.run_root, layout_id, args.audio.stem)
            except FileNotFoundError:
                missing_xsq.append(layout_id)
        if missing_xsq:
            command = [sys.executable, str(bench.ROOT / "tools/layout_bench/run_bench.py"),
                       "--audio-dir", str(args.audio.parent), "--songs", args.audio.name,
                       "--output-dir", str(args.run_root), "--layouts", *missing_xsq, "--workers", "1"]
            subprocess.run(command, check=True, cwd=bench.ROOT)
    paths, reports = [], []
    for idx, (layout_id, title, provisional) in enumerate(PANELS, 1):
        entry = manifest[layout_id]
        layout = bench.ROOT / entry["layout"]
        xsq = bench.find_xsq(args.run_root, layout_id, args.audio.stem)
        bench.ensure_fseq(args.run_root, layout_id, layout, xsq, args.audio)
        panel = {"layout": layout, "fseq": bench._fseq_path(args.run_root, layout_id, args.audio.stem),
                 "channels": entry["channels"], "title": title + (" [PROVISIONAL]" if provisional else "")}
        path = args.run_root / "panels_fseq" / f"nine_{idx:02d}_{args.audio.stem}.mp4"
        result = bench.write_panel_mp4(panel, path)
        paths.append(path)
        reports.append({"position": idx, "fixture": layout_id, "intended": title,
                        "provisional": provisional, "channel_report": result["report"]})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bench.stitch_panels(paths, args.audio, args.output, "HELIX NINE PANEL - ENGINEERING PREVIEW",
                        "Provisional fixtures; canonical band and vocal behavior require owner review")
    # Existing stitcher uses a 480px panel grid; normalize final review encoding to 1080p/30fps.
    normalized = args.output.with_name(args.output.stem + ".1080p.mp4")
    subprocess.run([bench._ffmpeg(), "-y", "-i", str(args.output), "-vf",
                    "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,"
                    "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-c:a", "copy", str(normalized)], check=True)
    normalized.replace(args.output)
    args.output.with_suffix(".manifest.json").write_text(json.dumps({
        "audio": str(args.audio), "video": str(args.output), "target_format": "1920x1080 30fps H.264/AAC", "approval_status": "NOT APPROVED",
        "panels": reports, "known_gaps": ["256-channel target not represented by AC64 fixture",
        "Canonical drummer geometry, three toms, nine cues and alternating sticks unverified",
        "Independent lead/harmony phonemes unverified", "Birdsong and piano mappings unverified",
        "Singing faces/trees and dense 3D layouts require replacement with final layouts",
        "Visual inspection, audio sync, decode and brightness acceptance pending"]
    }, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
