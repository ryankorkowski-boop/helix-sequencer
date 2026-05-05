from __future__ import annotations

import argparse
from pathlib import Path

from core import audio_intelligence
from core import model_parser as xmp
from core import spatial_scene
from helix_intent.intent_generator import generate_visual_intents
from helix_intent.placement_pipeline import build_and_write_placement_plan, build_placement_plan
from helix_intent.placement_stub_renderer import render_placement_stub_xml
from helix_intent.xlights_effect_contract import write_xlights_effect_contract
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
    stub = sub.add_parser("placement-stub-render")
    stub.add_argument("audio_file")
    stub.add_argument("layout_file")
    stub.add_argument("output_dir")
    stub.add_argument("--minimum-quality-score", type=float, default=0.6)
    contract = sub.add_parser("xlights-effect-contract")
    contract.add_argument("audio_file")
    contract.add_argument("layout_file")
    contract.add_argument("output_json")
    contract.add_argument("--minimum-quality-score", type=float, default=0.6)
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


def _placement_plan_for_inputs(audio_file: Path, layout_file: Path):
    intents = _visual_intents_for_audio(audio_file)
    parsed = xmp.parse_layout(layout_file)
    return build_placement_plan(visual_intents=intents, parsed_layout=parsed)


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
    if args.command == "placement-stub-render":
        placement_report = _placement_plan_for_inputs(Path(args.audio_file), Path(args.layout_file))
        render_report = render_placement_stub_xml(
            placement_report.to_dict(),
            Path(args.output_dir),
            minimum_quality_score=float(args.minimum_quality_score),
        )
        print(render_report.to_dict())
        return 0
    if args.command == "xlights-effect-contract":
        placement_report = _placement_plan_for_inputs(Path(args.audio_file), Path(args.layout_file))
        contract_report = write_xlights_effect_contract(
            placement_report.to_dict(),
            Path(args.output_json),
            minimum_quality_score=float(args.minimum_quality_score),
        )
        print(contract_report.to_dict())
        return 0
    if args.command == "preview":
        intents = _visual_intents_for_audio(Path(args.audio_file))
        _ = spatial_scene.load_scene(Path(args.layout_file))
        parsed = xmp.parse_layout(Path(args.layout_file))
        placement_report = build_placement_plan(visual_intents=intents, parsed_layout=parsed)
        preview_data = generate_preview_data(
            layout_name=Path(args.layout_file).stem,
            intents=[item.to_dict() for item in intents],
            seconds=args.seconds,
            placement_plan=placement_report.to_dict(),
        )
        print(grade_preview(preview_data))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
