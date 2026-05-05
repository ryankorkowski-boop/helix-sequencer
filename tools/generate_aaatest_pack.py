from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tools import youtube_show_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "aaatest"
DEFAULT_AUDIO_FILE = "13.wav"
DEFAULT_TEMPLATE_FILE = "template.xsq"
DEFAULT_LAYOUT_FILE = "xlights_rgbeffects.xml"
DEFAULT_MIN_FINAL_SCORE = 70.0


@dataclass(frozen=True)
class VariantPlan:
    label: str
    profile: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class GradingResult:
    label: str
    xsq_path: Path
    report_path: Path | None
    summary_path: Path | None
    final_score: float | None
    grade: str
    passed: bool
    problems: int | None


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def _latest_xsq(folder: Path) -> Path:
    candidates = sorted(
        (path for path in folder.rglob("*.xsq") if path.is_file()),
        key=lambda path: path.relative_to(folder).as_posix(),
    )
    if not candidates:
        raise RuntimeError(f"No XSQ found in {folder}")
    candidates.sort(key=lambda path: (path.stat().st_mtime, path.stat().st_size, path.name), reverse=True)
    return candidates[0]


def _cleanup_output_folder(folder: Path) -> None:
    for path in sorted(folder.glob("*"), key=lambda item: item.name):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            continue
        if not _is_generated_output(path):
            path.unlink(missing_ok=True)


def _is_generated_output(path: Path) -> bool:
    name = path.name
    return (
        path.suffix.lower() in {".xsq", ".mp4"}
        or name.endswith(".report.json")
        or name.endswith(".youtube_show_summary.json")
        or name in {"aaatest_grading_summary.json", "aaatest_grading_summary.txt"}
    )


def _clear_prior_outputs(output_dir: Path) -> None:
    patterns = (
        "*.xsq",
        "*.mp4",
        "*.report.json",
        "*.youtube_show_summary.json",
        "aaatest_grading_summary.json",
        "aaatest_grading_summary.txt",
    )
    for pattern in patterns:
        for path in sorted(output_dir.glob(pattern), key=lambda item: item.name):
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
    parser.add_argument("--clean-output", action="store_true", help="Clean output folder to generated assets and grading summaries at completion")
    parser.add_argument(
        "--min-final-score",
        type=float,
        default=DEFAULT_MIN_FINAL_SCORE,
        help="Minimum YouTube show final score for AAA grading pass/fail.",
    )
    return parser.parse_args(argv)


def _copy_report(source_xsq: Path, target_xsq: Path) -> Path | None:
    source_report = source_xsq.with_suffix(".report.json")
    if not source_report.exists():
        return None
    target_report = target_xsq.with_suffix(".report.json")
    shutil.copy2(source_report, target_report)
    return target_report


def _grade_output(label: str, xsq_path: Path, report_path: Path | None, min_final_score: float) -> GradingResult:
    if report_path is None or not report_path.exists():
        return GradingResult(
            label=label,
            xsq_path=xsq_path,
            report_path=report_path,
            summary_path=None,
            final_score=None,
            grade="missing_report",
            passed=False,
            problems=None,
        )

    payload = youtube_show_report.load_report(report_path)
    summary = youtube_show_report.build_summary(payload, xsq_path)
    summary_path = xsq_path.with_suffix(".youtube_show_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    grade_payload = summary["youtube_show_grade"]
    final_score = float(grade_payload.get("final_score", 0.0) or 0.0)
    return GradingResult(
        label=label,
        xsq_path=xsq_path,
        report_path=report_path,
        summary_path=summary_path,
        final_score=final_score,
        grade=str(grade_payload.get("grade", "")),
        passed=final_score >= float(min_final_score),
        problems=int(grade_payload.get("problem_count", 0) or 0),
    )


def _write_grading_report(output_dir: Path, results: list[GradingResult], min_final_score: float) -> Path:
    payload = {
        "schema_version": 1,
        "min_final_score": float(min_final_score),
        "passed": all(item.passed for item in results) if results else False,
        "outputs": [
            {
                "label": item.label,
                "xsq": item.xsq_path.name,
                "report": item.report_path.name if item.report_path else None,
                "summary": item.summary_path.name if item.summary_path else None,
                "final_score": item.final_score,
                "grade": item.grade,
                "passed": item.passed,
                "problems": item.problems,
            }
            for item in results
        ],
    }
    report_path = output_dir / "aaatest_grading_summary.json"
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text_path = output_dir / "aaatest_grading_summary.txt"
    lines = [
        f"AAATEST grading pass: {payload['passed']}",
        f"Minimum final score: {float(min_final_score):.1f}",
    ]
    for item in results:
        score = "missing" if item.final_score is None else f"{item.final_score:.1f}"
        lines.append(f"- {item.label}: {score} {item.grade} pass={item.passed}")
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def generate(
    *,
    output_dir: Path,
    layout_file: str,
    audio_file: str,
    template_file: str,
    clean_output: bool,
    min_final_score: float,
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

    _clear_prior_outputs(output_dir)

    results: list[Path] = []
    grading: list[GradingResult] = []
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
        target_report = _copy_report(source_xsq, target_xsq)
        results.append(target_xsq)
        print(f"  XSQ saved: {target_xsq.name}", flush=True)
        if target_report is not None:
            print(f"  Report saved: {target_report.name}", flush=True)

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
        grade = _grade_output(plan.label, target_xsq, target_report, min_final_score)
        grading.append(grade)
        score = "missing" if grade.final_score is None else f"{grade.final_score:.1f}"
        print(f"  Grade: {score} {grade.grade} pass={grade.passed}", flush=True)

    grading_path = _write_grading_report(output_dir, grading, min_final_score)
    print(f"Grading summary: {grading_path}", flush=True)
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
        min_final_score=float(args.min_final_score),
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
