from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from core import youtube_show_scorer


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parts_from_payload(payload: dict[str, Any]) -> list[Any]:
    parts = []
    for item in payload.get("parts") or []:
        if not isinstance(item, dict):
            continue
        parts.append(
            SimpleNamespace(
                label=str(item.get("label", "")),
                start_ms=int(item.get("start_ms", 0) or 0),
                end_ms=int(item.get("end_ms", 0) or 0),
            )
        )
    return parts


def build_summary_from_xsq(payload: dict[str, Any], xsq_path: Path) -> dict[str, Any]:
    from tools import preview_renderer

    sequence = preview_renderer.parse_sequence(xsq_path)
    timelines: dict[str, Any] = {}
    for model_name, effects in sorted(sequence.model_effects.items(), key=lambda item: item[0]):
        entries = [
            SimpleNamespace(
                start=effect.start_ms,
                end=effect.end_ms,
                effect_name=effect.name,
                palette=effect.palette,
            )
            for effect in sorted(effects, key=lambda item: (item.start_ms, item.end_ms, item.name))
        ]
        if entries:
            timelines[model_name] = SimpleNamespace(layers={"motion": entries})
    parts = _parts_from_payload(payload)
    if not parts:
        parts = [SimpleNamespace(label="FULL_SHOW", start_ms=0, end_ms=sequence.duration_ms)]
    return youtube_show_scorer.build_show_direction_summary(
        timelines=timelines,
        parts=parts,
        quiet_windows=[],
    )


def build_summary(payload: dict[str, Any], xsq_path: Path | None = None) -> dict[str, Any]:
    score_payload = dict(payload)
    if not score_payload.get("youtube_show_summary") and xsq_path is not None:
        score_payload["youtube_show_summary"] = build_summary_from_xsq(score_payload, xsq_path)
    grade = youtube_show_scorer.score_youtube_show(score_payload)
    section_source = (score_payload.get("youtube_show_summary") or {}) or {}
    return {
        "youtube_show_grade": grade,
        "quality_score": ((score_payload.get("quality") or {}) or {}).get("score"),
        "top_show_score": (((score_payload.get("quality") or {}) or {}).get("top_show_benchmark") or {}).get("score"),
        "effects_total": score_payload.get("effects_total"),
        "duration_seconds": score_payload.get("duration_seconds"),
        "section_count": len(section_source.get("sections") or score_payload.get("sections") or []),
        "section_summary_source": section_source.get("source", "") if section_source else "",
    }


def format_summary(path: Path, summary: dict[str, Any]) -> str:
    grade = summary["youtube_show_grade"]
    lines = [
        f"YouTube show report: {path}",
        f"Final score: {grade.get('final_score')} ({grade.get('grade')})",
        f"Problems: {grade.get('problem_count', 0)}",
        f"Recommendations: {grade.get('recommendation_count', 0)}",
    ]
    if summary.get("quality_score") is not None:
        lines.append(f"Quality score: {summary['quality_score']}")
    if summary.get("top_show_score") is not None:
        lines.append(f"Top-show benchmark: {summary['top_show_score']}")
    if summary.get("effects_total") is not None:
        lines.append(f"Effects total: {summary['effects_total']}")
    if summary.get("section_count") is not None:
        lines.append(f"Show-summary sections: {summary['section_count']}")
    if int(summary.get("section_count") or 0) == 0:
        lines.append("Note: no show-direction section summary found; using aggregate report fallback.")

    problems = list(grade.get("direction_problems") or [])
    if problems:
        lines.append("")
        lines.append("Direction problems:")
        for problem in problems[:12]:
            section = f" [{problem.get('section')}]" if problem.get("section") else ""
            metric = f" ({problem.get('metric')})" if problem.get("metric") else ""
            lines.append(f"- {problem.get('code')}{section}{metric}: {problem.get('message')}")

    recommendations = list(grade.get("director_recommendations") or [])
    if recommendations:
        lines.append("")
        lines.append("Director recommendations:")
        for item in recommendations[:12]:
            section = f" [{item.get('section')}]" if item.get("section") else ""
            lines.append(f"- {item.get('action')}{section}: {item.get('guidance')}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print Helix YouTube-grade show direction scoring for a report JSON.")
    parser.add_argument("report", type=Path, help="Path to a Helix *.report.json file.")
    parser.add_argument("--xsq", type=Path, help="Optional XSQ file to derive section-aware scoring for older reports.")
    parser.add_argument("--json", action="store_true", help="Print the computed summary as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    path = args.report.resolve()
    payload = load_report(path)
    xsq_path = args.xsq.resolve() if args.xsq else None
    summary = build_summary(payload, xsq_path)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(format_summary(path, summary), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
