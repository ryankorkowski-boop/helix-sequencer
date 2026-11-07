"""Physical 2D/3D band projection regression coverage."""
from core.band_2d_3d_front_contract import band_member_variant, verify_band_front_parity


def test_catalog_front_parity():
    results = verify_band_front_parity()
    assert len(results) >= 5
    assert all(results.values())
    for member in results:
        flat = band_member_variant(member, "2d")
        raised = band_member_variant(member, "3d")
        assert flat["front_segments"] == raised["front_segments"]
        assert flat["submodels"] == raised["submodels"]
        assert flat["depth_fraction"] == 0
        assert raised["depth_fraction"] > 0
