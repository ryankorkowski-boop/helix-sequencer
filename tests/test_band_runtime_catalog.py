from __future__ import annotations

from models.helixville4_performer_runtime import build_performer_runtime_catalog, validate_performer_runtime_catalog


def test_performer_runtime_catalog_is_valid() -> None:
    validation = validate_performer_runtime_catalog()
    assert validation["valid"] is True
    assert validation["error_count"] == 0


def test_performer_runtime_catalog_contains_all_five_members() -> None:
    catalog = build_performer_runtime_catalog()
    assert catalog["performer_count"] == 5
    assert catalog["model_names"] == [
        "HX_SNOWMAN_DRUMMER",
        "HX_SNOWMAN_GUITARIST",
        "HX_SNOWMAN_BASSIST",
        "HX_SNOWMAN_SINGER",
        "HX_SNOWMAN_SINGER_FEMALE",
    ]
