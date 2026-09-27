from __future__ import annotations

from pathlib import Path

from core import audio_intelligence
from core import model_parser
from core.plan.sequence_plan import SequencePlan, SequencePlanBuilder


def build_sequence_plan(
    *,
    audio_path: Path | None,
    layout_path: Path | None,
    profile_id: str,
    style_version: str,
    style_title: str,
) -> SequencePlan:
    """Build the renderer-neutral Slice 0 plan from existing Helix analyzers.

    This adapter is read-only with respect to the production renderer. It uses
    the existing audio analyzer and layout parser and returns plan data only.
    """

    source_audio = audio_path.name if audio_path is not None else ""
    plan = SequencePlan(
        source_audio=source_audio,
        fps=40,
        duration_seconds=0.0,
        style=style_version,
        metadata={
            "profile_id": profile_id,
            "style_version": style_version,
            "style_title": style_title,
            "planner": "slice0_existing_analysis",
        },
    )

    builder = SequencePlanBuilder(fps=40)
    if audio_path is not None and audio_path.exists():
        analysis = audio_intelligence.analyze_audio_file(
            audio_path,
            layout_path=layout_path,
            enable_lyrics=False,
        )
        plan = builder.from_audio_analysis(
            analysis,
            source_audio=source_audio,
            style=style_version,
            style_metadata={
                "profile_id": profile_id,
                "style_version": style_version,
                "style_title": style_title,
            },
        )

    if layout_path is not None and layout_path.exists():
        parsed_layout = model_parser.parse_layout(layout_path)
        builder.add_layout(plan, parsed_layout)

    return plan
