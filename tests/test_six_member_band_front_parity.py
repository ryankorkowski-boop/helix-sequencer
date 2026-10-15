from core.band_2d_3d_front_contract import (
    ALL_BAND_ASSETS, band_member_variant, verify_band_front_parity,
)


def test_six_performers_have_matching_2d_3d_front_geometry():
    parity = verify_band_front_parity()
    assert len(parity) == 6
    assert all(parity.values())
    assert "snowman_mallet_player" in parity
    assert sum("mallet" in asset.member_id for asset in ALL_BAND_ASSETS) == 1
    for member in parity:
        flat = band_member_variant(member, "2d")
        dimensional = band_member_variant(member, "3d")
        assert flat["front_segments"] == dimensional["front_segments"]
        assert flat["submodels"] == dimensional["submodels"]
        assert flat["projection"] == dimensional["projection"]
        assert flat["depth_fraction"] == 0
        assert dimensional["depth_fraction"] > 0


def test_mallet_has_two_independent_hands_and_three_note_zones():
    player = band_member_variant("snowman_mallet_player", "2d")
    names = " ".join(player["submodels"])
    for label in ("LEFT_MALLET", "RIGHT_MALLET", "KEYS_LOW", "KEYS_MID", "KEYS_HIGH"):
        assert label in names
