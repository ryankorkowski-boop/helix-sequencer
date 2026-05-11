from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from core.band_performance_timeline import BandPerformanceEvent


@dataclass(frozen=True)
class XLightsSubmodelEffect:
    model_name: str
    submodel: str
    effect_type: str
    palette: str
    start: float
    end: float
    intensity: float
    performer: str
    performer_state: str
    emphasis: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BandXLightsExportCompiler:
    """Deterministic translation layer from runtime performer events
    into xLights-oriented submodel effect instructions.

    This intentionally emits abstract export instructions rather than
    mutating XSQ/XML directly.
    """

    EMPHASIS_TO_EFFECT = {
        "percussion_hit_focus": "On",
        "rhythmic_foundation": "Bars",
        "riff_motion_focus": "Pinwheel",
        "harmonic_drive": "Morph",
        "low_end_support": "VU Meter",
        "lead_vocal_focus": "Shockwave",
        "front_stage_presence": "Pulse",
        "harmony_vocal_accent": "Ripple",
        "harmony_call_response": "Marquee",
        "ensemble_support": "Color Wash",
    }

    EMPHASIS_TO_PALETTE = {
        "percussion_hit_focus": "Warm Fire",
        "rhythmic_foundation": "Ice Blue",
        "riff_motion_focus": "Party Neon",
        "harmonic_drive": "Electric Winter",
        "low_end_support": "Deep Blue Bass",
        "lead_vocal_focus": "Spotlight White",
        "front_stage_presence": "Frost Glow",
        "harmony_vocal_accent": "Aurora Pink",
        "harmony_call_response": "Candy Cane",
        "ensemble_support": "Classic Christmas",
    }

    def compile_event(self, event: BandPerformanceEvent) -> tuple[XLightsSubmodelEffect, ...]:
        effect = self.EMPHASIS_TO_EFFECT.get(event.instrument_emphasis, "Color Wash")
        palette = self.EMPHASIS_TO_PALETTE.get(event.instrument_emphasis, "Classic Christmas")

        instructions: list[XLightsSubmodelEffect] = []

        for submodel in event.submodels:
            instructions.append(
                XLightsSubmodelEffect(
                    model_name=event.model_name,
                    submodel=submodel,
                    effect_type=effect,
                    palette=palette,
                    start=event.start,
                    end=event.end,
                    intensity=event.intensity,
                    performer=event.performer,
                    performer_state=event.state,
                    emphasis=event.instrument_emphasis,
                )
            )

        return tuple(instructions)

    def compile_many(self, events: Iterable[BandPerformanceEvent]) -> tuple[XLightsSubmodelEffect, ...]:
        compiled: list[XLightsSubmodelEffect] = []

        for event in events:
            compiled.extend(self.compile_event(event))

        return tuple(
            sorted(
                compiled,
                key=lambda item: (
                    item.start,
                    item.performer,
                    item.submodel,
                ),
            )
        )

    def build_manifest(self, events: Iterable[BandPerformanceEvent]) -> dict[str, Any]:
        compiled = self.compile_many(events)

        return {
            "schema": "helixville4.band_xlights_export.v1",
            "effect_count": len(compiled),
            "models": sorted({effect.model_name for effect in compiled}),
            "performers": sorted({effect.performer for effect in compiled}),
            "effects": [effect.to_dict() for effect in compiled],
        }
