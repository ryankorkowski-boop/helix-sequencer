"""Compatibility bridge for the canonical effects orchestration implementation."""

from core.effects_orchestrator_bridge import (
    EffectsOrchestrationRunReport,
    build_seed_graph,
    effect_contract_path,
    orchestration_report_path,
    placement_report_path,
    run_effects_orchestration,
    visual_intents_from_graph,
    xsq_render_report_path,
    orchestrated_xsq_path,
)

__all__ = [
    "EffectsOrchestrationRunReport",
    "build_seed_graph",
    "effect_contract_path",
    "orchestration_report_path",
    "placement_report_path",
    "run_effects_orchestration",
    "visual_intents_from_graph",
    "xsq_render_report_path",
    "orchestrated_xsq_path",
]
