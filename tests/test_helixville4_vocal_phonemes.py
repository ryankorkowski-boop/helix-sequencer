from __future__ import annotations

from models.helixville4_performer_runtime import FEMALE_SINGER, SINGER, build_performer_runtime_catalog, validate_performer_runtime_catalog
from models.helixville4_vocal_phonemes import (
    PHONEME_BY_NAME,
    VOCAL_PHONEMES,
    build_vocal_phoneme_catalog,
    required_female_singer_phoneme_submodels,
    required_singer_phoneme_submodels,
    validate_vocal_phoneme_catalog,
)


REQUIRED_PHONEMES = {"REST", "AH", "EE", "OH", "MBP", "FV", "L"}


def test_vocal_phoneme_catalog_contains_required_shapes() -> None:
    catalog = build_vocal_phoneme_catalog()
    assert catalog["schema"] == "helixville4.vocal_phoneme_catalog.v2"
    assert {spec.phoneme for spec in VOCAL_PHONEMES} == REQUIRED_PHONEMES
    assert set(PHONEME_BY_NAME) == REQUIRED_PHONEMES


def test_vocal_phonemes_have_explicit_mouth_shape_targets() -> None:
    singer_required = set(required_singer_phoneme_submodels())
    female_required = set(required_female_singer_phoneme_submodels())
    assert singer_required <= set(SINGER.submodels)
    assert female_required <= set(FEMALE_SINGER.submodels)
    for spec in VOCAL_PHONEMES:
        assert f"HX_SNOWMAN_SINGER_MOUTH_{spec.phoneme}" in spec.singer_submodels
        assert f"HX_SNOWMAN_SINGER_FEMALE_MOUTH_{spec.phoneme}" in spec.female_singer_submodels


def test_vocal_phonemes_reference_real_singer_submodels() -> None:
    validation = validate_vocal_phoneme_catalog(
        singer_submodels=SINGER.submodels,
        female_singer_submodels=FEMALE_SINGER.submodels,
    )
    assert validation["valid"] is True
    assert validation["error_count"] == 0


def test_performer_runtime_manifest_includes_valid_vocal_phonemes() -> None:
    validation = validate_performer_runtime_catalog()
    catalog = build_performer_runtime_catalog()
    assert validation["valid"] is True
    assert validation["phoneme_count"] == len(REQUIRED_PHONEMES)
    assert catalog["vocal_phonemes"]["phoneme_count"] == len(REQUIRED_PHONEMES)
