from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "aaatest"
DEFAULT_AUDIO_FILE = "13.wav"
DEFAULT_TEMPLATE_FILE = "template.xsq"
DEFAULT_LAYOUT_FILE = "xlights_rgbeffects.xml"


@dataclass(frozen=True)
class VariantPlan:
    label: str
    profile: str
    args: tuple[str, ...]


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def _latest_xsq(folder: Path) -> Path:
    candidates = [path for path in folder.rglob("*.xsq") if path.is_file()]
    if not candidates:
        raise RuntimeError(f"No XSQ found in {folder}")
    candidates.sort(key=lambda path: (path.stat().st_mtime, path.stat().st_size), reverse=True)
    return candidates[0]


def _cleanup_output_folder(folder: Path) -> None:
    for path in folder.glob("*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            continue
        if path.suffix.lower() not in {".xsq", ".mp4"}:
            path.unlink(missing_ok=True)


def _build_plans() -> list[VariantPlan]:
    return [
        VariantPlan(
            label="legacy_classic",
            profile="v2.3",
            args=(
                "--ac-lights-only",
                "--no-pixel-reactive",
                "--no-polish",
                "--no-auto-timing-tracks",
                "--flash-guard",
                "0.70",
                "--palette-mode",
                "christmas",
                "--max-layers-per-prop",
                "6",
            ),
        ),
        VariantPlan(
            label="chrono_roles",
            profile="v24.3",
            args=(
                "--spatial-awareness",
                "0.75",
                "--chase-style",
                "group_to_group",
                "--layering-mode",
                "smart_layer",
                "--palette-mode",
                "workspace_match",
            ),
        ),
        VariantPlan(
            label="birdsong_wild",
            profile="v27.3",
            args=(
                "--birdsong",
                "--birdsong-profile",
                "wild",
                "--birdsong-intensity",
                "2.05",
                "--birdsong-min-confidence",
                "0.22",
                "--spatial-awareness",
                "0.72",
                "--chase-style",
                "random_walk",
                "--sync-lyrics-heads",
                "--layering-mode",
                "smart_layer",
                "--flash-guard",
                "0.62",
                "--max-layers-per-prop",
                "10",
                "--palette-mode",
                "christmas",
            ),
        ),
        VariantPlan(
            label="hardkor_ac256",
            profile="v27.3",
            args=(
                "--hardkor",
                "--hardkor-profile",
                "ac256",
                "--hardkor-intensity",
                "1.35",
                "--max-layers-per-prop",
                "64",
                "--ac-lights-only",
                "--base-effect",
                "On",
                "--motion-effect",
                "Ramp",
                "--accent-effect",
                "On",
                "--layering-mode",
                "additive",
                "--palette-mode",
                "christmas",
                "--no-pixel-reactive",
                "--no-birdsong",
                "--no-birdsong-auto",
            ),
        ),
        VariantPlan(
            label="spotify_logic",
            profile="v21.6",
            args=(
                "--spatial-awareness",
                "0.93",
                "--chase-style",
                "wave",
                "--layer-priority-vocals",
                "6",
                "--layer-priority-drums",
                "5",
                "--layer-priority-bass",
                "4",
                "--layer-priority-other",
                "3",
                "--sync-lyrics-heads",
                "--flash-guard",
                "0.58",
                "--layering-mode",
                "smart_layer",
                "--max-layers-per-prop",
                "12",
                "--palette-mode",
                "workspace_match",
            ),
        ),
        VariantPlan(
            label="visualizer_fusion",
            profile="v10.1",
            args=(
                "--spatial-awareness",
                "0.90",
                "--chase-style",
                "wave",
                "--layering-mode",
                "overlay_blend",
                "--matrix-intelligence",
                "--palette-mode",
                "cool",
            ),
        ),
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate AAATEST multi-variant XSQ/MP4 packs.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output folder for final xsq/mp4 files")
    parser.add_argument("--layout-file", default=DEFAULT_LAYOUT_FILE, help="Layout XML/XBKP for engine routing and previews")
    parser.add_argument("--audio-file", default=DEFAULT_AUDIO_FILE, help="Audio file to sequence")
    parser.add_argument("--template-file", default=DEFAULT_TEMPLATE_FILE, help="Template XSQ file")
    parser.add_argument("--clean-output", action="store_true", help="Clean output folder to only xsq/mp4 at completion")
    return parser.parse_args(argv)


def generate(
    *,
    output_dir: Path,
    layout_file: str,
    audio_file: str,
    template_file: str,
    clean_output: bool,
) -> list[Path]:
    work_dir = output_dir / "_work"

    if not (ROOT / audio_file).exists():
        raise RuntimeError(f"Missing audio file: {audio_file}")
    if not (ROOT / template_file).exists():
        raise RuntimeError(f"Missing template file: {template_file}")
    if not (ROOT / layout_file).exists():
        raise RuntimeError(f"Missing layout file: {layout_file}")

    output_dir.mkdir(parents=True, exist_ok=True)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    for path in output_dir.glob("*.xsq"):
        path.unlink(missing_ok=True)
    for path in output_dir.glob("*.mp4"):
        path.unlink(missing_ok=True)

    results: list[Path] = []
    plans = _build_plans()

    for idx, plan in enumerate(plans, start=1):
        variant_dir = work_dir / plan.label
        variant_dir.mkdir(parents=True, exist_ok=True)
        run_cmd = [
            sys.executable,
            "main.py",
            "--profile",
            plan.profile,
            "--",
            "--template",
            template_file,
            "--audio",
            audio_file,
            "--layout-file",
            layout_file,
            "--single",
            "--output-dir",
            str(variant_dir),
            "--variants",
            "1",
            "--no-prompt",
            "--no-save-settings",
            "--no-workspace-history",
            *plan.args,
        ]
        print(f"[{idx}/{len(plans)}] Running {plan.label} ({plan.profile}) ...", flush=True)
        _run(run_cmd)
        source_xsq = _latest_xsq(variant_dir)
        target_xsq = output_dir / f"{idx:02d}_{plan.label}.xsq"
        shutil.copy2(source_xsq, target_xsq)
        results.append(target_xsq)
        print(f"  XSQ saved: {target_xsq.name}", flush=True)

        preview_cmd = [
            sys.executable,
            "-m",
            "tools.preview_renderer",
            str(target_xsq),
            "--layout",
            layout_file,
            "--audio",
            audio_file,
            "--fps",
            "15",
            "--width",
            "1280",
            "--height",
            "720",
        ]
        print(f"  Rendering MP4 preview for {target_xsq.name} ...", flush=True)
        _run(preview_cmd)

    if clean_output:
        _cleanup_output_folder(output_dir)
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
    return results


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    outputs = generate(
        output_dir=Path(args.output_dir).resolve(),
        layout_file=str(args.layout_file),
        audio_file=str(args.audio_file),
        template_file=str(args.template_file),
        clean_output=bool(args.clean_output),
    )
    print("", flush=True)
    print("AAATEST generation complete:", flush=True)
    for output in outputs:
        print(f"- {output}", flush=True)
        mp4 = output.with_suffix(".mp4")
        if mp4.exists():
            print(f"  preview: {mp4}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
