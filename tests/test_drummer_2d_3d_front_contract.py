from core.drummer_2d_3d_front_contract import (
    drummer_build_variant, validate_front_parity,
)


def test_front_parity():
    assert validate_front_parity()
    flat = drummer_build_variant("2d")
    deep = drummer_build_variant("3d")
    assert flat["depth_fraction"] == 0
    assert deep["depth_fraction"] > 0
    assert flat["front_positions"] == deep["front_positions"]
    assert flat["channels"] == deep["channels"]
    assert len(flat["channels"]) == 16


def test_invalid_variant():
    import pytest
    with pytest.raises(ValueError):
        drummer_build_variant("side")
