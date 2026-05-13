from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from models.helixville4_vocal_phonemes import PHONEME_NAMES


@dataclass(frozen=True)
class StemTarget:
    stem: str
    timing_lanes: tuple[str, ...]
    model: str
    submodels: tuple[str, ...]
    purpose: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timing_lanes"] = list(self.timing_lanes)
        payload["submodels"] = list(self.submodels)
        return payload


def _phoneme_targets(prefix: str) -> tuple[str, ...]:
    return tuple(f"{prefix}_MOUTH_{phoneme}" for phoneme in PHONEME_NAMES)


HELIXVILLE4_BAND_STEM_TARGETS: tuple[StemTarget, ...] = (
    StemTarget(
        stem="vocals",
        timing_lanes=("lyrics", "phonemes", "vocal_phrases", "chorus_hooks"),
        model="HX_SNOWMAN_SINGER",
        submodels=(
            *_phoneme_targets("HX_SNOWMAN_SINGER"),
            "HX_SNOWMAN_SINGER_MOUTH",
            "HX_SNOWMAN_SINGER_EYES",
            "HX_SNOWMAN_SINGER_EYEBROWS",
            "HX_SNOWMAN_SINGER_VOCAL_GLOW",
            "HX_SNOWMAN_SINGER_MICROPHONE",
        ),
        purpose="Lead-vocal mouth shapes, face expression, and microphone glow.",
    ),
    StemTarget(
        stem="harmony",
        timing_lanes=("lyrics", "phonemes", "harmony_phrases", "call_response"),
        model="HX_SNOWMAN_SINGER_FEMALE",
        submodels=(
            *_phoneme_targets("HX_SNOWMAN_SINGER_FEMALE"),
            "HX_SNOWMAN_SINGER_FEMALE_MOUTH",
            "HX_SNOWMAN_SINGER_FEMALE_EYES",
            "HX_SNOWMAN_SINGER_FEMALE_EYELASHES",
            "HX_SNOWMAN_SINGER_FEMALE_VOCAL_GLOW",
            "HX_SNOWMAN_SINGER_FEMALE_MICROPHONE",
            "HX_SNOWMAN_SINGER_FEMALE_STAGE_GLOW",
        ),
        purpose="Harmony-vocal mouth shapes, expression, and stage glow.",
    ),
    StemTarget(
        stem="kick",
        timing_lanes=("kick", "downbeats"),
        model="HX_SNOWMAN_DRUMMER",
        submodels=("HX_SNOWMAN_DRUMMER_KICK", "HX_SNOWMAN_DRUMMER_KICK_RIM", "HX_SNOWMAN_DRUMMER_PLATFORM"),
        purpose="Kick drum impact and stage-floor punch.",
    ),
    StemTarget(
        stem="snare",
        timing_lanes=("snare", "accent_hits"),
        model="HX_SNOWMAN_DRUMMER",
        submodels=("HX_SNOWMAN_DRUMMER_SNARE", "HX_SNOWMAN_DRUMMER_SNARE_RIM", "HX_SNOWMAN_DRUMMER_LEFT_STICK", "HX_SNOWMAN_DRUMMER_RIGHT_STICK"),
        purpose="Snare hits with stick accents.",
    ),
    StemTarget(
        stem="hihat",
        timing_lanes=("hihat", "eighth_notes", "sixteenth_notes"),
        model="HX_SNOWMAN_DRUMMER",
        submodels=("HX_SNOWMAN_DRUMMER_HI_HAT", "HX_SNOWMAN_DRUMMER_LEFT_STICK", "HX_SNOWMAN_DRUMMER_RIGHT_STICK"),
        purpose="High-frequency rhythmic pulse.",
    ),
    StemTarget(
        stem="cymbals",
        timing_lanes=("cymbals", "crashes", "section_peaks"),
        model="HX_SNOWMAN_DRUMMER",
        submodels=("HX_SNOWMAN_DRUMMER_CYMBAL_LEFT", "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT", "HX_SNOWMAN_DRUMMER_STANDS"),
        purpose="Crash/ride accents and big transitions.",
    ),
    StemTarget(
        stem="toms",
        timing_lanes=("fills", "tom_fills"),
        model="HX_SNOWMAN_DRUMMER",
        submodels=("HX_SNOWMAN_DRUMMER_TOM_LEFT", "HX_SNOWMAN_DRUMMER_TOM_RIGHT", "HX_SNOWMAN_DRUMMER_LEFT_STICK", "HX_SNOWMAN_DRUMMER_RIGHT_STICK"),
        purpose="Drum fill sweeps and tom movement.",
    ),
    StemTarget(
        stem="bass",
        timing_lanes=("bass_hits", "bass_groove", "downbeats", "section_pulses"),
        model="HX_SNOWMAN_BASSIST",
        submodels=(
            "HX_SNOWMAN_BASSIST_STRING_E",
            "HX_SNOWMAN_BASSIST_STRING_A",
            "HX_SNOWMAN_BASSIST_STRING_D",
            "HX_SNOWMAN_BASSIST_STRING_G",
            "HX_SNOWMAN_BASSIST_PLUCK_ZONE",
            "HX_SNOWMAN_BASSIST_BODY_RESONANCE",
            "HX_SNOWMAN_BASSIST_FINGERBOARD",
            "HX_SNOWMAN_BASSIST_NECK_LOW",
            "HX_SNOWMAN_BASSIST_NECK_MID",
            "HX_SNOWMAN_BASSIST_NECK_HIGH",
        ),
        purpose="Bass groove, plucks, string chases, and neck movement.",
    ),
    StemTarget(
        stem="guitar",
        timing_lanes=("guitar_strums", "chorus_hooks", "accent_hits"),
        model="HX_SNOWMAN_GUITARIST",
        submodels=(
            "HX_SNOWMAN_GUITARIST_STRING_LOW_E",
            "HX_SNOWMAN_GUITARIST_STRING_A",
            "HX_SNOWMAN_GUITARIST_STRING_D",
            "HX_SNOWMAN_GUITARIST_STRING_G",
            "HX_SNOWMAN_GUITARIST_STRING_B",
            "HX_SNOWMAN_GUITARIST_STRING_HIGH_E",
            "HX_SNOWMAN_GUITARIST_PICK_ZONE",
            "HX_SNOWMAN_GUITARIST_BODY_RESONANCE",
            "HX_SNOWMAN_GUITARIST_FRETBOARD_LOW",
            "HX_SNOWMAN_GUITARIST_FRETBOARD_MID",
            "HX_SNOWMAN_GUITARIST_FRETBOARD_HIGH",
        ),
        purpose="Guitar strums, string activity, fretting, and resonance.",
    ),
)


def build_helixville4_band_stem_map() -> dict[str, Any]:
    return {
        "schema": "helixville4.band_stem_map.v1",
        "stem_count": len(HELIXVILLE4_BAND_STEM_TARGETS),
        "targets": [target.to_dict() for target in HELIXVILLE4_BAND_STEM_TARGETS],
    }


def validate_stem_map_against_submodels(model_submodels: dict[str, set[str]]) -> dict[str, Any]:
    errors: list[str] = []
    for target in HELIXVILLE4_BAND_STEM_TARGETS:
        available = model_submodels.get(target.model)
        if available is None:
            errors.append(f"{target.stem} references missing model: {target.model}")
            continue
        for submodel in target.submodels:
            if submodel not in available:
                errors.append(f"{target.stem} references missing submodel: {target.model}/{submodel}")
    return {
        "schema": "helixville4.band_stem_map_validation.v1",
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
    }
