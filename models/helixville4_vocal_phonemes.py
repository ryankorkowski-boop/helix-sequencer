from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class VocalPhonemeSpec:
    phoneme: str
    mouth_shape: str
    description: str
    singer_submodels: tuple[str, ...]
    female_singer_submodels: tuple[str, ...]
    xlights_face_effect: str = "Faces"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


VOCAL_PHONEMES: tuple[VocalPhonemeSpec, ...] = (
    VocalPhonemeSpec(
        phoneme="REST",
        mouth_shape="closed",
        description="Closed or resting mouth between syllables.",
        singer_submodels=("HX_SNOWMAN_SINGER_MOUTH",),
        female_singer_submodels=("HX_SNOWMAN_SINGER_FEMALE_MOUTH",),
    ),
    VocalPhonemeSpec(
        phoneme="AH",
        mouth_shape="wide_open",
        description="Open A/R-style vowel shape.",
        singer_submodels=("HX_SNOWMAN_SINGER_MOUTH", "HX_SNOWMAN_SINGER_VOCAL_GLOW"),
        female_singer_submodels=("HX_SNOWMAN_SINGER_FEMALE_MOUTH", "HX_SNOWMAN_SINGER_FEMALE_VOCAL_GLOW"),
    ),
    VocalPhonemeSpec(
        phoneme="EE",
        mouth_shape="smile_wide",
        description="E/I/Y-style bright vowel shape.",
        singer_submodels=("HX_SNOWMAN_SINGER_MOUTH", "HX_SNOWMAN_SINGER_EYES"),
        female_singer_submodels=("HX_SNOWMAN_SINGER_FEMALE_MOUTH", "HX_SNOWMAN_SINGER_FEMALE_EYES"),
    ),
    VocalPhonemeSpec(
        phoneme="OH",
        mouth_shape="round_open",
        description="O/U/W-style rounded vowel shape.",
        singer_submodels=("HX_SNOWMAN_SINGER_MOUTH", "HX_SNOWMAN_SINGER_VOCAL_GLOW"),
        female_singer_submodels=("HX_SNOWMAN_SINGER_FEMALE_MOUTH", "HX_SNOWMAN_SINGER_FEMALE_VOCAL_GLOW"),
    ),
    VocalPhonemeSpec(
        phoneme="MBP",
        mouth_shape="closed_pop",
        description="Closed-lip M/B/P consonant shape.",
        singer_submodels=("HX_SNOWMAN_SINGER_MOUTH",),
        female_singer_submodels=("HX_SNOWMAN_SINGER_FEMALE_MOUTH",),
    ),
    VocalPhonemeSpec(
        phoneme="FV",
        mouth_shape="teeth_lip",
        description="F/V consonant shape.",
        singer_submodels=("HX_SNOWMAN_SINGER_MOUTH", "HX_SNOWMAN_SINGER_EYEBROWS"),
        female_singer_submodels=("HX_SNOWMAN_SINGER_FEMALE_MOUTH", "HX_SNOWMAN_SINGER_FEMALE_EYELASHES"),
    ),
    VocalPhonemeSpec(
        phoneme="L",
        mouth_shape="tongue_lift",
        description="L/tongue-lift consonant shape.",
        singer_submodels=("HX_SNOWMAN_SINGER_MOUTH",),
        female_singer_submodels=("HX_SNOWMAN_SINGER_FEMALE_MOUTH",),
    ),
)


PHONEME_BY_NAME: dict[str, VocalPhonemeSpec] = {spec.phoneme: spec for spec in VOCAL_PHONEMES}


def build_vocal_phoneme_catalog() -> dict[str, Any]:
    return {
        "schema": "helixville4.vocal_phoneme_catalog.v1",
        "phoneme_count": len(VOCAL_PHONEMES),
        "phonemes": [spec.to_dict() for spec in VOCAL_PHONEMES],
    }


def validate_vocal_phoneme_catalog(*, singer_submodels: tuple[str, ...], female_singer_submodels: tuple[str, ...]) -> dict[str, Any]:
    errors: list[str] = []
    singer_known = set(singer_submodels)
    female_known = set(female_singer_submodels)

    for spec in VOCAL_PHONEMES:
        if not spec.phoneme:
            errors.append("phoneme name is required")
        if not spec.singer_submodels:
            errors.append(f"{spec.phoneme} has no singer submodels")
        if not spec.female_singer_submodels:
            errors.append(f"{spec.phoneme} has no female singer submodels")
        missing_singer = sorted(set(spec.singer_submodels) - singer_known)
        missing_female = sorted(set(spec.female_singer_submodels) - female_known)
        if missing_singer:
            errors.append(f"{spec.phoneme} references missing singer submodels: {missing_singer}")
        if missing_female:
            errors.append(f"{spec.phoneme} references missing female singer submodels: {missing_female}")

    return {
        "schema": "helixville4.vocal_phoneme_validation.v1",
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "phoneme_count": len(VOCAL_PHONEMES),
    }
