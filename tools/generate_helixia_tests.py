from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools import helixia_smoke_preview


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "helixiatests"
DEFAULT_AUDIO = ROOT / "LightsOutTheme.mp3"
DEFAULT_LAYOUT = ROOT / "helixville4" / "xlights_rgbeffects.xml"
DEFAULT_TEMPLATE = ROOT / "template.xsq"


@dataclass(frozen=True)
class HelixiaTestPlan:
    label: str
    profile: str
    description: str
    args: tuple[str, ...] = ()


BASE_ARGS: tuple[str, ...] = (
    "--layering-mode",
    "smart_layer",
    "--palette-mode",
    "workspace_match",
    "--spatial-awareness",
    "0.86",
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
    "--audio-reactive-profile",
    "showcase",
    "--max-layers-per-prop",
    "8",
    "--flash-guard",
    "0.64",
)


def build_plans() -> list[HelixiaTestPlan]:
    plans: list[HelixiaTestPlan] = [
        HelixiaTestPlan(
            label="active_v27_3_helix_prime",
            profile="v27.3",
            description="Active master Helix Prime baseline on the Helixia layout.",
        )
    ]
    plans.extend(
        [
            HelixiaTestPlan("v28_1_prime_focus", "v28.1", "Helix Prime Focus refinement."),
            HelixiaTestPlan("v28_2_prime_motion", "v28.2", "Helix Prime Motion refinement."),
            HelixiaTestPlan("v28_3_prime_storyboard", "v28.3", "Helix Prime Storyboard refinement."),
            HelixiaTestPlan("v28_4_prime_stemcraft", "v28.4", "Helix Prime Stemcraft refinement."),
            HelixiaTestPlan("v28_5_prime_signature", "v28.5", "Helix Prime Signature refinement."),
            HelixiaTestPlan("v28_6_prime_matrix", "v28.6", "Helix Prime Matrix refinement."),
            HelixiaTestPlan("v28_7_prime_piano", "v28.7", "Helix Prime Piano refinement."),
            HelixiaTestPlan("v28_8_prime_apex", "v28.8", "Helix Prime Apex refinement."),
            HelixiaTestPlan("v28_9_prime_vendor", "v28.9", "Helix Prime Vendor refinement."),
            HelixiaTestPlan("v29_1_legacy_qm_timing", "v29.1", "Reconfigured legacy Queen Mary timing toolset."),
            HelixiaTestPlan("v29_2_legacy_stem_marks", "v29.2", "Reconfigured legacy stem marks toolset."),
            HelixiaTestPlan("v29_3_legacy_multiband", "v29.3", "Reconfigured legacy multiband MIR toolset."),
            HelixiaTestPlan("v29_4_legacy_audio_routes", "v29.4", "Reconfigured legacy audio routes toolset."),
            HelixiaTestPlan("v29_5_legacy_matrix_plan", "v29.5", "Reconfigured legacy matrix planning toolset."),
            HelixiaTestPlan("v29_6_legacy_chronoflow", "v29.6", "Reconfigured legacy Chronoflow toolset."),
            HelixiaTestPlan("v29_7_legacy_snowman_band", "v29.7", "Reconfigured legacy Snowman Band performer toolset."),
            HelixiaTestPlan(
                "v29_8_legacy_hardkor",
                "v29.8",
                "Reconfigured legacy hardKor AC-first toolset.",
                args=("--hardkor-intensity", "1.25"),
            ),
            HelixiaTestPlan(
                "v29_9_legacy_birdsong",
                "v29.9",
                "Reconfigured legacy Birdsong phrase toolset.",
                args=("--birdsong-min-confidence", "0.22", "--birdsong-intensity", "1.9"),
            ),
            HelixiaTestPlan(
                "optimal_band_apex",
                "v28.8",
                "High-score candidate: Apex style with max audio routes, band/drummer priority, and matrix intelligence.",
                args=(
                    "--audio-reactive-profile",
                    "max",
                    "--audio-reactive-intensity",
                    "1.82",
                    "--matrix-intelligence",
                    "--polish",
                    "--spatial-awareness",
                    "0.94",
                    "--chase-style",
                    "group_to_group",
                    "--max-layers-per-prop",
                    "12",
                    "--flash-guard",
                    "0.58",
                    "--vendor-bar",
                ),
            ),
        ]
    )
    return plans


def _run(command: list[str], *, cwd: Path, dry_run: bool) -> None:
    print(" ".join(command), flush=True)
    if not dry_run:
        env = dict(os.environ)
        env.setdefault("HELIX_SKIP_LEGACY_PITCH", "1")
        subprocess.run(command, cwd=cwd, check=True, env=env)


def _sequence_command(plan: HelixiaTestPlan, output_dir: Path, args: argparse.Namespace) -> list[str]:
    engine_args = [
        "--template",
        str(args.template),
        "--audio",
        str(args.audio),
        "--layout-file",
        str(args.layout),
        "--single",
        "--output-dir",
        str(output_dir),
        "--variants",
        "1",
        "--no-prompt",
        "--no-save-settings",
        "--no-workspace-history",
        "--no-learning-memory",
    ]
    engine_args.extend(BASE_ARGS)
    engine_args.extend(plan.args)
    return [sys.executable, "-m", "core.sequence_builder", "--profile", plan.profile, "--", *engine_args]


def _render_command(xsq_path: Path, args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        "-m",
        "tools.preview_renderer",
        str(xsq_path),
        "--layout",
        str(args.layout),
        "--audio",
        str(args.audio),
        "--fps",
        str(args.fps),
        "--width",
        str(args.width),
        "--height",
        str(args.height),
        "--max-seconds",
        str(args.preview_seconds),
    ]


def _artifact_paths(plan: HelixiaTestPlan, output_dir: Path, audio: Path) -> dict[str, Path]:
    xsq = output_dir / f"{audio.stem},{plan.profile}.xsq"
    return {
        "xsq": xsq,
        "mp4": xsq.with_suffix(".mp4"),
        "report": xsq.with_suffix(".report.json"),
        "notes": xsq.with_name(f"{xsq.stem}.sequence_notes.txt"),
    }


def _read_summary(paths: dict[str, Path]) -> dict[str, Any]:
    summary = helixia_smoke_preview.load_report_summary(paths["report"])
    if paths["report"].exists():
        payload = json.loads(paths["report"].read_text(encoding="utf-8"))
        summary["audio_reactive"] = payload.get("audio_reactive", {})
        summary["birdsong"] = payload.get("birdsong", {})
        summary["hardkor"] = payload.get("hardkor", {})
        summary["snowman_band"] = {
            "cue_count": len(((payload.get("snowman_band") or {}).get("timing_track") or [])),
            "debug": (payload.get("snowman_band") or {}).get("debug", {}),
        }
        summary["runtime"] = payload.get("runtime", {})
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Helixia XSQ/MP4 test variants.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--preview-seconds", type=float, default=90.0)
    parser.add_argument("--only", action="append", help="Run only labels containing this text.")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.output_dir = args.output_dir.resolve()
    args.audio = args.audio.resolve()
    args.layout = args.layout.resolve()
    args.template = args.template.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    filters = tuple((item or "").lower() for item in (args.only or ()))
    plans = [
        plan
        for plan in build_plans()
        if not filters or any(item in plan.label.lower() or item in plan.profile.lower() for item in filters)
    ]
    results: list[dict[str, Any]] = []

    for index, plan in enumerate(plans, 1):
        plan_dir = args.output_dir / plan.label
        plan_dir.mkdir(parents=True, exist_ok=True)
        paths = _artifact_paths(plan, plan_dir, args.audio)
        print(f"[{index}/{len(plans)}] {plan.label} ({plan.profile})", flush=True)
        if not (args.skip_existing and paths["xsq"].exists()):
            _run(_sequence_command(plan, plan_dir, args), cwd=ROOT, dry_run=args.dry_run)
        if not args.skip_render and not (args.skip_existing and paths["mp4"].exists()):
            _run(_render_command(paths["xsq"], args), cwd=ROOT, dry_run=args.dry_run)

        summary = {} if args.dry_run else _read_summary(paths)
        results.append(
            {
                "plan": asdict(plan),
                "artifacts": {name: str(path.relative_to(args.output_dir)) for name, path in paths.items()},
                "summary": summary,
            }
        )

    if not args.dry_run:
        summary_path = args.output_dir / "helixia_test_summary.json"
        summary_path.write_text(json.dumps({"plans": results}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Summary: {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
