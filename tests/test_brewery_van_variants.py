"""Native brewery van variant smoke tests; not a substitute for MP4 verification."""
from models.brewery_van_variants import VARIANTS, build, inventory


def test_both_van_variants_have_unique_native_models():
    assert VARIANTS == ("clean_matrix_van", "extreme_skeleton_van")
    for variant in VARIANTS:
        garden, singer = build(variant)
        assert singer is None
        assert len(garden.models) > 10
        names = [m.name for m in garden.models]
        assert len(names) == len(set(names))
        assert all(m.start > 0 and m.channels > 0 for m in garden.models)
        assert any(m.details.get("brand_emblem") for m in garden.models)
        assert inventory(variant)["native_video_verified"] is False


def test_clean_and_extreme_have_distinct_prop_sets():
    clean, _ = build("clean_matrix_van")
    extreme, _ = build("extreme_skeleton_van")
    assert any(m.zone == "BRAND_MATRIX" for m in clean.models)
    assert not any(m.details.get("skeleton_performer_role") for m in clean.models)
    assert {m.details.get("skeleton_performer_role") for m in extreme.models
            if m.details.get("skeleton_performer_role")} == {
                "drummer", "guitarist", "bassist", "frontman"}
    assert len(extreme.models) > len(clean.models)
