"""Compatibility bridge for the effects orchestration module.

The canonical implementation lives in ``core.effects_orchestrator_bridge``.
Keep this compatibility name because existing CLI/bootstrap code imports the
older ``*_orchestration_bridge`` module name.
"""

from core.effects_orchestrator_bridge import *  # noqa: F401,F403
from core.effects_orchestrator_bridge import EffectsOrchestrationRunReport

__all__ = [
    "EffectsOrchestrationRunReport",
    "build_seed_graph",
    "effect_contract_path",
    "orchestration_report_path",
    "orchestrated_xsq_path",
    "placement_report_path",
    "run_effects_orchestration",
    "visual_intents_from_graph",
    "xsq_render_report_path",
]
