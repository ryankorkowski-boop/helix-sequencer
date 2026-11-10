from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from models.helixville4_performer_runtime import FEMALE_SINGER, SINGER
from models.helixville4_vocal_phonemes import PHONEME_BY_NAME


@dataclass(frozen=True)
class VocalPhonemeTiming:
    performer: str
    phoneme: str
    start: float
    duration: float
    intensity: float = 1.0

    @property
    def end(self) -> float:
        return round(self.start + self.duration, 6)


@dataclass(frozen=True)
class XLightsVocalFaceEffect:
    performer: str
    model_name: str
    phoneme: str
    mouth_shape: str
    submodels: tuple[str, ...]
    effect_type: str
    face_definition: str
    timing_track: str
    start: float
    end: float
    intensity: float

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["submodels"] = list(self.submodels)
        return payload


class BandVocalFaceExportCompiler:
    """Translate approved Helixville4 vocal phonemes into xLights Faces instructions.

    This emits deterministic intermediate export instructions only; it does not
    mutate XSQ/XML files directly.
    """

    PERFORMER_MODELS = {
        "singer": SINGER.model_name,
        "female_singer": FEMALE_SINGER.model_name,
    }
    FACE_DEFINITIONS = {
        "singer": "helixville4_lead_singer_full",
        "female_singer": "helixville4_harmony_singer_full",
    }

    def compile_timing(self, timing: VocalPhonemeTiming) -> XLightsVocalFaceEffect:
        performer = timing.performer
        if performer not in self.PERFORMER_MODELS:
            raise ValueError(f"Unsupported vocal performer: {performer}")

        phoneme = timing.phoneme.upper()
        if phoneme not in PHONEME_BY_NAME:
            raise ValueError(f"Unsupported vocal phoneme: {timing.phoneme}")

        spec = PHONEME_BY_NAME[phoneme]
        submodels = spec.singer_submodels if performer == "singer" else spec.female_singer_submodels

        return XLightsVocalFaceEffect(
            performer=performer,
            model_name=self.PERFORMER_MODELS[performer],
            phoneme=spec.phoneme,
            mouth_shape=spec.mouth_shape,
            submodels=submodels,
            effect_type=spec.xlights_face_effect,
            face_definition=self.FACE_DEFINITIONS[performer],
            timing_track="helixville4_vocal_phonemes",
            start=timing.start,
            end=timing.end,
            intensity=round(max(0.0, min(1.0, timing.intensity)), 4),
        )

    def compile_many(self, timings: Iterable[VocalPhonemeTiming]) -> tuple[XLightsVocalFaceEffect, ...]:
        effects = [self.compile_timing(timing) for timing in timings]
        return tuple(sorted(effects, key=lambda item: (item.start, item.performer, item.phoneme)))

    def build_manifest(self, timings: Iterable[VocalPhonemeTiming]) -> dict[str, Any]:
        effects = self.compile_many(timings)
        return {
            "schema": "helixville4.band_vocal_face_export.v1",
            "effect_count": len(effects),
            "models": sorted({effect.model_name for effect in effects}),
            "performers": sorted({effect.performer for effect in effects}),
            "phonemes": sorted({effect.phoneme for effect in effects}),
            "effects": [effect.to_dict() for effect in effects],
        }


def build_demo_vocal_face_timings() -> tuple[VocalPhonemeTiming, ...]:
    return (
        VocalPhonemeTiming("singer", "AH", 4.0, 0.28, 0.95),
        VocalPhonemeTiming("singer", "EE", 4.3, 0.22, 0.85),
        VocalPhonemeTiming("singer", "MBP", 4.55, 0.18, 0.75),
        VocalPhonemeTiming("female_singer", "OH", 4.85, 0.30, 0.9),
        VocalPhonemeTiming("female_singer", "FV", 5.2, 0.20, 0.7),
        VocalPhonemeTiming("female_singer", "L", 5.45, 0.22, 0.72),
        VocalPhonemeTiming("singer", "REST", 5.75, 0.18, 0.3),
    )
