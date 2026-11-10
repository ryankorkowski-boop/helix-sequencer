from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.audio_intelligence import analyze_audio_file
from core.model_parser import parse_layout
from core.plan.sequence_plan import SequencePlanBuilder
from core.style_engine import infer_style


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Emit a renderer-neutral SequencePlan sidecar without changing XSQ generation."
    )
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--layout", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fps", type=int, default=40)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    analysis = analyze_audio_file(
        args.audio,
        layout_path=args.layout,
        enable_lyrics=False,
    )
    parsed_layout = parse_layout(args.layout)

    tempo = 0.0
    if analysis.tempo_map:
        tempo = float(analysis.tempo_map[0].get("bpm", 0.0) or 0.0)

    style_features = dict(analysis.style_features or {})
    style_features["tempo_bpm"] = tempo
    style_decision = infer_style(style_features)

    builder = SequencePlanBuilder(fps=args.fps)
    plan = builder.from_audio_analysis(
        analysis,
        source_audio=args.audio.name,
        style=style_decision.detected_style,
        style_metadata={
            "style_debug": style_decision.debug,
            "source": "core.style_engine",
        },
    )
    builder.add_layout(plan, parsed_layout)
    builder.apply_style_decision(plan, style_decision)
    plan.metadata["shadow_mode"] = True
    plan.metadata["renderer_changed"] = False
    plan.metadata["contract"] = "docs/sequence_plan_contract.md"
    plan.metadata["audio_analysis_confidence"] = dict(analysis.confidence_scores)

    plan.write_json(args.output)

    print(json.dumps({
        "plan": str(args.output),
        "version": plan.version,
        "sections": len(plan.sections),
        "prop_groups": len(plan.prop_groups),
        "cues": len(plan.cues),
        "style": plan.style,
        "renderer_changed": False,
        "validation_errors": plan.validate(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
