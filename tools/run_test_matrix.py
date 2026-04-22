from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import birdsong_mode
from tools import build_helixville_layout, preview_renderer


@dataclass
class IterationResult:
    index: int
    score: float
    grade: str
    report_path: Path
    xsq_path: Path
    notes_path: Path | None
    tuning_flags: list[str]


@dataclass
class TaskResult:
    task_name: str
    phase: str
    profile: str
    final_score: float
    final_grade: str
    iterations: list[IterationResult]
    target_xsq: Path
    preview_mp4: Path
    report_path: Path
    readme_path: Path


def _score_to_grade(score: float) -> str:
    if score >= 98.0:
        return "A+"
    if score >= 95.0:
        return "A"
    if score >= 92.0:
        return "A-"
    if score >= 89.0:
        return "B+"
    if score >= 85.0:
        return "B"
    if score >= 80.0:
        return "B-"
    if score >= 75.0:
        return "C+"
    if score >= 70.0:
        return "C"
    return "D"


def _component(quality: dict, key: str, default: float = 0.0) -> float:
    comps = quality.get("component_scores", {})
    value = comps.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _best_report_artifacts(run_dir: Path) -> tuple[Path, Path, Path | None]:
    reports = sorted(run_dir.glob("*.report.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not reports:
        raise RuntimeError(f"No report generated in {run_dir}")
    report = reports[0]
    payload = json.loads(report.read_text(encoding="utf-8"))
    output_name = str(payload.get("output", "")).strip()
    xsq = run_dir / output_name if output_name else None
    if not xsq or not xsq.exists():
        xsqs = sorted(run_dir.glob("*.xsq"), key=lambda item: item.stat().st_mtime, reverse=True)
        if not xsqs:
            raise RuntimeError(f"No XSQ generated in {run_dir}")
        xsq = xsqs[0]
    notes = sorted(run_dir.glob("*.sequence_notes.txt"), key=lambda item: item.stat().st_mtime, reverse=True)
    return report, xsq, (notes[0] if notes else None)


def _read_quality(report_path: Path) -> tuple[float, str, dict]:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    quality = payload.get("quality", {}) if isinstance(payload, dict) else {}
    score = float(quality.get("score", 0.0) or 0.0)
    grade = str(quality.get("grade", "")).strip() or _score_to_grade(score)
    return score, grade, quality


def _improvement_flags(quality: dict, iteration: int) -> list[str]:
    if iteration <= 0:
        return []
    flags: list[str] = []
    density = _component(quality, "density", 100.0)
    audit = _component(quality, "audit", 100.0)
    detail = _component(quality, "detail", 100.0)
    dominance = _component(quality, "dominance", 100.0)
    coverage = _component(quality, "coverage", 100.0)

    if density < 92.0:
        flags += ["--density", "1.10", "--speed", "1.12"]
    if audit < 90.0:
        flags += ["--flash-guard", "0.88", "--layering-mode", "smart_layer", "--randomness", "0.05"]
    if detail < 92.0:
        flags += ["--melody-density", "1.42", "--spatial-awareness", "0.46"]
    if dominance < 96.0:
        flags += ["--palette-mode", "workspace_match", "--chase-style", "group_to_group"]
    if coverage < 97.0:
        flags += ["--pixel-reactive", "--spatial-awareness", "0.52"]
    return flags


def _controllers_summary(networks_xml: Path) -> list[str]:
    root = ET.parse(networks_xml).getroot()
    controllers = root.findall(".//controller")
    lines = [f"Controller count: {len(controllers)}"]
    for ctrl in controllers:
        unit = (ctrl.attrib.get("UnitId") or "?").strip()
        channels = (ctrl.attrib.get("NumChannels") or "?").strip()
        ctype = (ctrl.attrib.get("CntlrType") or "Unknown").strip()
        lines.append(f"- Unit {unit}: {ctype} ({channels} channels)")
    return lines


def _write_run_readme(
    *,
    path: Path,
    preset: birdsong_mode.BirdsongTaskPreset,
    show_folder: Path,
    layout_xml: Path,
    controller_info_path: Path,
    final_score: float,
    final_grade: str,
    iteration_count: int,
) -> None:
    lines = [
        f"Run: {preset.target_xsq_name}",
        "",
        f"Task: {preset.name}",
        f"Description: {preset.description}",
        f"Profile: {preset.profile}",
        f"Final quality score: {final_score:.2f}",
        f"Final grade: {final_grade}",
        f"Iterations used: {iteration_count}",
        "",
        "Show folder to use:",
        str(show_folder),
        "",
        "Layout file to use:",
        str(layout_xml),
        "",
        "Controller information file:",
        str(controller_info_path),
        "",
        "The paired preview MP4 in this run folder was rendered with audio from 2.wav.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _run_one_iteration(
    *,
    preset: birdsong_mode.BirdsongTaskPreset,
    template_path: Path,
    audio_path: Path,
    layout_path: Path,
    out_dir: Path,
    tuning_flags: list[str],
) -> IterationResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    existing_reports = sorted(out_dir.glob("*.report.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if existing_reports:
        report_path, xsq_path, notes_path = _best_report_artifacts(out_dir)
        score, grade, _quality = _read_quality(report_path)
        return IterationResult(
            index=int(out_dir.name.rsplit("_", 1)[-1]),
            score=score,
            grade=grade,
            report_path=report_path,
            xsq_path=xsq_path,
            notes_path=notes_path,
            tuning_flags=list(tuning_flags),
        )

    cmd = [
        sys.executable,
        str(ROOT / "main.py"),
        "--profile",
        preset.profile,
        "--",
        "--template",
        str(template_path),
        "--audio",
        str(audio_path),
        "--layout-file",
        str(layout_path),
        "--output-dir",
        str(out_dir),
        "--single",
        "--no-prompt",
        "--no-save-settings",
        "--quiet",
        *preset.runtime_args,
        *tuning_flags,
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    report_path, xsq_path, notes_path = _best_report_artifacts(out_dir)
    score, grade, _quality = _read_quality(report_path)
    return IterationResult(
        index=int(out_dir.name.rsplit("_", 1)[-1]),
        score=score,
        grade=grade,
        report_path=report_path,
        xsq_path=xsq_path,
        notes_path=notes_path,
        tuning_flags=list(tuning_flags),
    )


def _phase_grade(results: list[TaskResult], phase: str) -> tuple[float, str]:
    scoped = [item.final_score for item in results if item.phase == phase]
    if not scoped:
        return 0.0, "N/A"
    score = sum(scoped) / max(1, len(scoped))
    return score, _score_to_grade(score)


def run_matrix(
    *,
    audio_path: Path,
    template_path: Path,
    allmodels_show_folder: Path,
    output_root: Path,
    max_iterations: int,
    target_score: float,
) -> list[TaskResult]:
    allmodels_layout = allmodels_show_folder / "xlights_rgbeffects.xml"
    allmodels_networks = allmodels_show_folder / "xlights_networks.xml"
    allmodels_keys = allmodels_show_folder / "xlights_keybindings.xml"

    if not allmodels_layout.exists():
        raise FileNotFoundError(f"Allmodels layout not found: {allmodels_layout}")
    if not allmodels_networks.exists():
        raise FileNotFoundError(f"Controller file not found: {allmodels_networks}")

    show_folder_root = output_root / "show_folders"
    helixville_show_folder = show_folder_root / "helixville_3d_start"
    helixville_layout = build_helixville_layout.build_helixville_3d_show_folder(
        source_layout_xml=allmodels_layout,
        source_networks_xml=allmodels_networks,
        source_keybindings_xml=allmodels_keys if allmodels_keys.exists() else None,
        output_show_folder=helixville_show_folder,
    )
    helixville_controllers = helixville_show_folder / "controllers_info.txt"

    allmodels_controller_lines = _controllers_summary(allmodels_networks)
    allmodels_controller_path = show_folder_root / "allmodels_controllers_info.txt"
    allmodels_controller_path.parent.mkdir(parents=True, exist_ok=True)
    allmodels_controller_path.write_text("\n".join(allmodels_controller_lines), encoding="utf-8")

    presets = birdsong_mode.default_task_presets(audio_path)
    results: list[TaskResult] = []
    for preset in presets:
        task_root = output_root / "runs" / preset.name
        task_root.mkdir(parents=True, exist_ok=True)
        iterations: list[IterationResult] = []

        if preset.phase == "helixville_3d":
            layout_path = helixville_layout
            show_folder = helixville_show_folder
            controller_path = helixville_controllers
        else:
            layout_path = allmodels_layout
            show_folder = allmodels_show_folder
            controller_path = allmodels_controller_path

        quality_snapshot: dict = {}
        for iteration in range(1, max_iterations + 1):
            tuning_flags = _improvement_flags(quality_snapshot, iteration - 1)
            iter_dir = task_root / f"iter_{iteration}"
            item = _run_one_iteration(
                preset=preset,
                template_path=template_path,
                audio_path=audio_path,
                layout_path=layout_path,
                out_dir=iter_dir,
                tuning_flags=tuning_flags,
            )
            iterations.append(item)

            score, _grade, quality_snapshot = _read_quality(item.report_path)
            if score >= target_score:
                break

        best = max(iterations, key=lambda row: row.score)
        target_xsq = task_root / preset.target_xsq_name
        shutil.copy2(best.xsq_path, target_xsq)

        report_target = task_root / f"{target_xsq.stem}.report.json"
        shutil.copy2(best.report_path, report_target)
        if best.notes_path and best.notes_path.exists():
            shutil.copy2(best.notes_path, task_root / f"{target_xsq.stem}.sequence_notes.txt")
        shutil.copy2(controller_path, task_root / "controllers_info.txt")

        preview_mp4 = target_xsq.with_suffix(".mp4")
        if not preview_mp4.exists():
            layout_data = preview_renderer.parse_models(layout_path)
            preview_mp4 = preview_renderer.render_sequence_to_mp4(
                sequence_path=target_xsq,
                layout=layout_data,
                audio_path=audio_path,
                fps=18,
                width=1280,
                height=720,
            )

        readme_path = task_root / "README.txt"
        _write_run_readme(
            path=readme_path,
            preset=preset,
            show_folder=show_folder,
            layout_xml=layout_path,
            controller_info_path=task_root / "controllers_info.txt",
            final_score=best.score,
            final_grade=best.grade,
            iteration_count=len(iterations),
        )

        results.append(
            TaskResult(
                task_name=preset.name,
                phase=preset.phase,
                profile=preset.profile,
                final_score=best.score,
                final_grade=best.grade,
                iterations=iterations,
                target_xsq=target_xsq,
                preview_mp4=preview_mp4,
                report_path=report_target,
                readme_path=readme_path,
            )
        )
    return results


def _write_audit(output_root: Path, results: list[TaskResult]) -> Path:
    allmodels_score, allmodels_grade = _phase_grade(results, "allmodels")
    helixville_score, helixville_grade = _phase_grade(results, "helixville_3d")
    overall = sum(item.final_score for item in results) / max(1, len(results))
    lines = [
        "Helixualizer Test Matrix Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Overall score: {overall:.2f}",
        f"Overall grade: {_score_to_grade(overall)}",
        "",
        "Branch grades:",
        f"- allmodels branch: {allmodels_score:.2f} ({allmodels_grade})",
        f"- helixville_3d branch: {helixville_score:.2f} ({helixville_grade})",
        "",
        "Task grades:",
    ]
    for item in results:
        lines.append(f"- {item.task_name}: {item.final_score:.2f} ({item.final_grade}), profile={item.profile}, phase={item.phase}")
        for attempt in item.iterations:
            tuning = " ".join(attempt.tuning_flags) if attempt.tuning_flags else "(base)"
            lines.append(f"  - iter {attempt.index}: {attempt.score:.2f} ({attempt.grade}) tuning={tuning}")

    path = output_root / "AUDIT_SUMMARY.txt"
    path.write_text("\n".join(lines), encoding="utf-8")

    json_payload = {
        "overall_score": overall,
        "overall_grade": _score_to_grade(overall),
        "branch_grades": {
            "allmodels": {"score": allmodels_score, "grade": allmodels_grade},
            "helixville_3d": {"score": helixville_score, "grade": helixville_grade},
        },
        "tasks": [
            {
                "name": item.task_name,
                "phase": item.phase,
                "profile": item.profile,
                "score": item.final_score,
                "grade": item.final_grade,
                "xsq": str(item.target_xsq),
                "preview": str(item.preview_mp4),
                "report": str(item.report_path),
                "iterations": [
                    {
                        "index": it.index,
                        "score": it.score,
                        "grade": it.grade,
                        "tuning_flags": it.tuning_flags,
                        "report_path": str(it.report_path),
                    }
                    for it in item.iterations
                ],
            }
            for item in results
        ],
    }
    (output_root / "AUDIT_SUMMARY.json").write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Helixualizer test matrix XSQ + preview generation with grading.")
    parser.add_argument("--audio", default="2.wav", help="Audio file path")
    parser.add_argument("--template", default="template.xsq", help="Template XSQ file")
    parser.add_argument("--allmodels-show-folder", default=str(Path(r"C:\Users\User\Desktop\cod\allmodels")), help="Show folder containing allmodels layout and controllers")
    parser.add_argument("--output-root", help="Output root folder (default: outputs/test_matrix_<timestamp>)")
    parser.add_argument("--max-iterations", type=int, default=2, help="Maximum reruns per task")
    parser.add_argument("--target-score", type=float, default=97.0, help="Stop reruns once this score is reached")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    audio_path = Path(args.audio)
    if not audio_path.is_absolute():
        audio_path = (ROOT / audio_path).resolve()
    template_path = Path(args.template)
    if not template_path.is_absolute():
        template_path = (ROOT / template_path).resolve()
    allmodels_show_folder = Path(args.allmodels_show_folder).resolve()

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    if args.output_root:
        output_root = Path(args.output_root)
        if not output_root.is_absolute():
            output_root = (ROOT / output_root).resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = ROOT / "outputs" / f"test_matrix_{stamp}"
    output_root.mkdir(parents=True, exist_ok=True)

    results = run_matrix(
        audio_path=audio_path,
        template_path=template_path,
        allmodels_show_folder=allmodels_show_folder,
        output_root=output_root,
        max_iterations=max(1, int(args.max_iterations)),
        target_score=float(args.target_score),
    )
    audit_path = _write_audit(output_root, results)
    print(f"Completed test matrix: {output_root}")
    print(f"Audit summary: {audit_path}")
    for item in results:
        print(f"{item.task_name}: {item.final_score:.2f} ({item.final_grade}) -> {item.target_xsq.name}, {item.preview_mp4.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
