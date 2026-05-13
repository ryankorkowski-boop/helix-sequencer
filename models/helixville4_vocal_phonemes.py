from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SINGER_PREFIX = "HX_SNOWMAN_SINGER"
FEMALE_SINGER_PREFIX = "HX_SNOWMAN_SINGER_FEMALE"
PHONEME_NAMES: tuple[str, ...] = ("REST", "AH", "EE", "OH", "MBP", "FV", "L")


def singer_phoneme_submodel(phoneme: str) -> str:
    return f"{SINGER_PREFIX}_MOUTH_{phoneme}"


def female_singer_phoneme_submodel(phoneme: str) -> str:
    return f"{FEMALE_SINGER_PREFIX}_MOUTH_{phoneme}"


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
        singer_submodels=(singer_phoneme_submodel("REST"), SINGER_PREFIX + "_MOUTH"),
        female_singer_submodels=(female_singer_phoneme_submodel("REST"), FEMALE_SINGER_PREFIX + "_MOUTH"),
    ),
    VocalPhonemeSpec(
        phoneme="AH",
        mouth_shape="wide_open",
        description="Open A/R-style vowel shape.",
        singer_submodels=(singer_phoneme_submodel("AH"), SINGER_PREFIX + "_VOCAL_GLOW"),
        female_singer_submodels=(female_singer_phoneme_submodel("AH"), FEMALE_SINGER_PREFIX + "_VOCAL_GLOW"),
    ),
    VocalPhonemeSpec(
        phoneme="EE",
        mouth_shape="smile_wide",
        description="E/I/Y-style bright vowel shape.",
        singer_submodels=(singer_phoneme_submodel("EE"), SINGER_PREFIX + "_EYES"),
        female_singer_submodels=(female_singer_phoneme_submodel("EE"), FEMALE_SINGER_PREFIX + "_EYES"),
    ),
    VocalPhonemeSpec(
        phoneme="OH",
        mouth_shape="round_open",
        description="O/U/W-style rounded vowel shape.",
        singer_submodels=(singer_phoneme_submodel("OH"), SINGER_PREFIX + "_VOCAL_GLOW"),
        female_singer_submodels=(female_singer_phoneme_submodel("OH"), FEMALE_SINGER_PREFIX + "_VOCAL_GLOW"),
    ),
    VocalPhonemeSpec(
        phoneme="MBP",
        mouth_shape="closed_pop",
        description="Closed-lip M/B/P consonant shape.",
        singer_submodels=(singer_phoneme_submodel("MBP"), SINGER_PREFIX + "_MOUTH"),
        female_singer_submodels=(female_singer_phoneme_submodel("MBP"), FEMALE_SINGER_PREFIX + "_MOUTH"),
    ),
    VocalPhonemeSpec(
        phoneme="FV",
        mouth_shape="teeth_lip",
        description="F/V consonant shape.",
        singer_submodels=(singer_phoneme_submodel("FV"), SINGER_PREFIX + "_EYEBROWS"),
        female_singer_submodels=(female_singer_phoneme_submodel("FV"), FEMALE_SINGER_PREFIX + "_EYELASHES"),
    ),
    VocalPhonemeSpec(
        phoneme="L",
        mouth_shape="tongue_lift",
        description="L/tongue-lift consonant shape.",
        singer_submodels=(singer_phoneme_submodel("L"), SINGER_PREFIX + "_MOUTH"),
        female_singer_submodels=(female_singer_phoneme_submodel("L"), FEMALE_SINGER_PREFIX + "_MOUTH"),
    ),
)


PHONEME_BY_NAME: dict[str, VocalPhonemeSpec] = {spec.phoneme: spec for spec in VOCAL_PHONEMES}


def required_singer_phoneme_submodels() -> tuple[str, ...]:
    return tuple(singer_phoneme_submodel(name) for name in PHONEME_NAMES)


def required_female_singer_phoneme_submodels() -> tuple[str, ...]:
    return tuple(female_singer_phoneme_submodel(name) for name in PHONEME_NAMES)


def build_vocal_phoneme_catalog() -> dict[str, Any]:
    return {
        "schema": "helixville4.vocal_phoneme_catalog.v2",
        "phoneme_count": len(VOCAL_PHONEMES),
        "required_singer_phoneme_submodels": list(required_singer_phoneme_submodels()),
        "required_female_singer_phoneme_submodels": list(required_female_singer_phoneme_submodels()),
        "phonemes": [spec.to_dict() for spec in VOCAL_PHONEMES],
    }


def validate_vocal_phoneme_catalog(*, singer_submodels: tuple[str, ...], female_singer_submodels: tuple[str, ...]) -> dict[str, Any]:
    errors: list[str] = []
    singer_known = set(singer_submodels)
    female_known = set(female_singer_submodels)

    for required in required_singer_phoneme_submodels():
        if required not in singer_known:
            errors.append(f"missing required singer phoneme submodel: {required}")
    for required in required_female_singer_phoneme_submodels():
        if required not in female_known:
            errors.append(f"missing required female singer phoneme submodel: {required}")

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
        "schema": "helixville4.vocal_phoneme_validation.v2",
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "phoneme_count": len(VOCAL_PHONEMES),
    }
