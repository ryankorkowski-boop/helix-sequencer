"""Maps StyleDecision into minimal xLights-style effect records.

This is a thin translation layer. It does NOT modify xsq_writer yet.
It creates simple effect dictionaries that can later be consumed by
existing XML writers.
"""

from tools.style_engine import StyleDecision


def map_decision_to_effects(decision: StyleDecision):
    effects = []

    for target in decision.targets:
        effects.append(
            {
                "model": target,
                "start": decision.start,
                "duration": decision.duration,
                "effect": decision.effect,
                "palette": list(decision.palette),
                "intensity": decision.intensity,
                "motion": decision.motion,
                "intent": decision.intent,
            }
        )

    return effects
