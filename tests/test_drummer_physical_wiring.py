from core.drummer_physical_wiring import build_drummer_wiring_plan

def test_drumming_circuits_unique_and_fit_one_lor_bank():
    plan = build_drummer_wiring_plan()
    channels = [item["channel"] for item in plan["circuits"]]
    assert channels == list(range(1, 13))
    assert plan["spare_channels"] == [13, 14, 15, 16]
    assert plan["controller_capacity"] == 16

def test_idle_poses_are_independent_of_hit_poses():
    plan = build_drummer_wiring_plan()
    by_key = {item["key"]: item for item in plan["circuits"]}
    assert by_key["left_stick_idle"]["channel"] != by_key["left_cymbal_contact"]["channel"]
    assert by_key["right_stick_idle"]["channel"] != by_key["snare_right_contact"]["channel"]
    assert by_key["body_kit_dim"]["behavior"] == "always_dim"

def test_drum_layout_and_contact_strings():
    plan = build_drummer_wiring_plan()
    assert plan["layout_viewer_left_to_right"] == [
        "left_cymbal", "floor_tom", "mid_tom", "kick",
        "snare", "high_tom", "hi_hat", "right_cymbal"]
    assert "right arm/hand/stick" in plan["circuits"][0]["physical_string"]
