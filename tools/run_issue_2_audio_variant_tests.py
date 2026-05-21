from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Sequence

from tools.export_helix_flow_review_artifacts import export_review_artifacts


VARIANTS: tuple[dict[str, Any], ...] = (
    {
        "name": "balanced_phrase_flow",
        "description": "Baseline Issue #2 logic: balanced phrase spacing, stable BPM, strongest all-around candidate.",
        "duration_seconds": 20.0,
        "step_seconds": 1.0,
        "bpm": 120.0,
    },
    {
        "name": "dense_onset_cascade",
        "description": "Higher-resolution phrase/onset sampling for denser cascades and more layered visible motion.",
        "duration_seconds": 20.0,
        "step_seconds": 0.5,
        "bpm": 128.0,
    },
    {
        "name": "cinematic_spatial_sweep",
        "description": "Slightly slower phrase cadence for wider spatial sweeps and more emotionally readable motion.",
        "duration_seconds": 20.0,
        "step_seconds": 0.75,
        "bpm": 96.0,
    },
)


GRADE_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (0.97, "A+"),
    (0.93, "A-"),
    (0.90, "B+"),
    (0.85, "B"),
    (0.80, "B-"),
    (0.75, "C+"),
    (0.70, "C"),
)


def grade_for(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "Needs work"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def variant_sort_key(result: dict[str, Any]) -> tuple[float, float, float, float, int]:
    score = float(result["quality"].get("score", 0.0))
    spatial = float(result["quality"].get("spatial_coherence", 0.0))
    layering = float(result["quality"].get("layering", 0.0))
    musicality = float(result["quality"].get("musicality", 0.0))
    intent_count = int(result["quality"].get("intent_count", 0))
    return (score, spatial, layering, musicality, intent_count)


def export_variant(output_root: Path, audio: Path, variant: dict[str, Any]) -> dict[str, Any]:
    variant_dir = output_root / str(variant["name"])
    paths = export_review_artifacts(
        variant_dir,
        duration_seconds=float(variant["duration_seconds"]),
        step_seconds=float(variant["step_seconds"]),
        bpm=float(variant["bpm"]),
        audio=audio,
    )
    quality = read_json(paths["quality"])
    preview = read_json(paths["preview_metadata"])
    result: dict[str, Any] = {
        "name": variant["name"],
        "description": variant["description"],
        "parameters": {
            "duration_seconds": variant["duration_seconds"],
            "step_seconds": variant["step_seconds"],
            "bpm": variant["bpm"],
            "audio": str(audio),
        },
        "grade": grade_for(float(quality.get("score", 0.0))),
        "quality": quality,
        "preview_metadata": preview,
        "artifacts": {key: str(path) for key, path in paths.items()},
    }
    return result


def write_scorecard(output_root: Path, results: list[dict[str, Any]]) -> tuple[Path, Path]:
    ranked = sorted(results, key=variant_sort_key, reverse=True)
    winner = ranked[0]
    scorecard = {
        "issue": 2,
        "logic": "Birdsong Engine / Helix Flow phrase-based sequencing acceptance test",
        "variant_count": len(results),
        "winner": winner["name"],
        "winner_grade": winner["grade"],
        "winner_score": winner["quality"].get("score"),
        "ranking": [result["name"] for result in ranked],
        "results": ranked,
    }
    json_path = output_root / "issue_2_audio_variant_scorecard.json"
    json_path.write_text(json.dumps(scorecard, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Issue #2 Audio Variant Test Scorecard",
        "",
        "Audio source: `Helix Audiolights.mp3`",
        "",
        f"Winner: `{winner['name']}` — **{winner['grade']}** ({winner['quality'].get('score')})",
        "",
        "| Rank | Variant | Grade | Score | Musicality | Spatial | Layering | Novelty | Emotion | XSQ | MP4 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for index, result in enumerate(ranked, start=1):
        quality = result["quality"]
        artifacts = result["artifacts"]
        lines.append(
            "| {rank} | `{name}` | {grade} | {score} | {musicality} | {spatial} | {layering} | {novelty} | {emotion} | `{xsq}` | `{mp4}` |".format(
                rank=index,
                name=result["name"],
                grade=result["grade"],
                score=quality.get("score"),
                musicality=quality.get("musicality"),
                spatial=quality.get("spatial_coherence"),
                layering=quality.get("layering"),
                novelty=quality.get("novelty"),
                emotion=quality.get("emotion"),
                xsq=artifacts.get("xsq"),
                mp4=artifacts.get("mp4"),
            )
        )
    lines.extend(
        [
            "",
            "## Variant intent",
            "",
        ]
    )
    for result in ranked:
        lines.extend(
            [
                f"### {result['name']}",
                result["description"],
                "",
                f"Parameters: BPM `{result['parameters']['bpm']}`, step seconds `{result['parameters']['step_seconds']}`, duration `{result['parameters']['duration_seconds']}`.",
                "",
            ]
        )
    md_path = output_root / "issue_2_audio_variant_scorecard.md"
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return json_path, md_path


def copy_winner(output_root: Path, result: dict[str, Any]) -> None:
    winner_dir = output_root / "winner"
    winner_dir.mkdir(parents=True, exist_ok=True)
    artifacts = result["artifacts"]
    for key in ("xsq", "mp4", "quality", "preview_metadata", "acceptance_summary"):
        source = Path(artifacts[key])
        if source.exists():
            shutil.copy2(source, winner_dir / f"winner_{source.name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run three Issue #2 Helix Flow variants against the uploaded test audio.")
    parser.add_argument("--audio", type=Path, default=Path("Helix Audiolights.mp3"))
    parser.add_argument("--output-dir", type=Path, default=Path("test_runs/issue_2_audio_variants"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.audio.exists():
        raise FileNotFoundError(f"Audio file not found: {args.audio}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    results = [export_variant(args.output_dir, args.audio, variant) for variant in VARIANTS]
    ranked = sorted(results, key=variant_sort_key, reverse=True)
    write_scorecard(args.output_dir, results)
    copy_winner(args.output_dir, ranked[0])

    print(json.dumps({"winner": ranked[0]["name"], "grade": ranked[0]["grade"], "score": ranked[0]["quality"].get("score")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
