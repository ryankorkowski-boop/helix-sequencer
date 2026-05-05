from __future__ import annotations

import argparse
from pathlib import Path

from core import audio_intelligence
from core import model_parser as xmp
from core import spatial_scene
from helix_intent.intent_generator import generate_visual_intents
from helix_intent.placement_pipeline import build_and_write_placement_plan, build_placement_plan
from helix_knowledge.cli import main as knowledge_cli_main
from helix_layout.layout_health import build_layout_health_report
from helix_music.section_planner import plan_song_sections
from helix_preview.preview_generator import generate_preview_data
from helix_preview.preview_grader import grade_preview


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Helix professional sequencing helper.")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("knowledge")
    health = sub.add_parser("layout-health")
    health.add_argument("layout_file")
    analyze = sub.add_parser("analyze-audio")
    analyze.add_argument("audio_file")
    plan = sub.add_parser("plan-song")
    plan.add_argument("audio_file")
    placement = sub.add_parser("placement-plan")
    placement.add_argument("audio_file")
    placement.add_argument("layout_file")
    placement.add_argument("--output", help="Optional JSON output path for the placement plan")
    preview = sub.add_parser("preview")
    preview.add_argument("audio_file")
    preview.add_argument("layout_file")
    preview.add_argument("--seconds", type=int, default=30)
    return parser


def _visual_intents_for_audio(audio_file: Path):
    analysis = audio_intelligence.analyze_audio_file(audio_file, enable_lyrics=False)
    sections = plan_song_sections(
        float(analysis.metadata.get("duration_ms", 0)) / 1000.0,
        analysis.style_features.get("tempo_class", "medium"),
    )
    return generate_visual_intents([section.to_dict() for section in sections])


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    if args.command == "knowledge":
        return knowledge_cli_main(unknown)
    if args.command == "layout-health":
        report = build_layout_health_report(Path(args.layout_file))
        print(report.to_dict())
        return 0
    if args.command == "analyze-audio":
        result = audio_intelligence.analyze_audio_file(Path(args.audio_file), enable_lyrics=False)
        print(result.to_dict()["metadata"])
        return 0
    if args.command == "plan-song":
        analysis = audio_intelligence.analyze_audio_file(Path(args.audio_file), enable_lyrics=False)
        sections = plan_song_sections(float(analysis.metadata.get("duration_ms", 0)) / 1000.0, analysis.style_features.get("tempo_class", "medium"))
        print([section.to_dict() for section in sections])
        return 0
    if args.command == "placement-plan":
        intents = _visual_intents_for_audio(Path(args.audio_file))
        parsed = xmp.parse_layout(Path(args.layout_file))
        if args.output:
            path = build_and_write_placement_plan(
                visual_intents=intents,
                parsed_layout=parsed,
                output_path=Path(args.output),
            )
            print({"output": str(path)})
        else:
            report = build_placement_plan(visual_intents=intents, parsed_layout=parsed)
            print(report.to_dict())
        return 0
    if args.command == "preview":
        analysis = audio_intelligence.analyze_audio_file(Path(args.audio_file), enable_lyrics=False)
        _ = spatial_scene.load_scene(Path(args.layout_file))
        sections = plan_song_sections(float(analysis.metadata.get("duration_ms", 0)) / 1000.0, analysis.style_features.get("tempo_class", "medium"))
        intents = [item.to_dict() for item in generate_visual_intents([section.to_dict() for section in sections])]
        preview_data = generate_preview_data(layout_name=Path(args.layout_file).stem, intents=intents, seconds=args.seconds)
        print(grade_preview(preview_data))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
