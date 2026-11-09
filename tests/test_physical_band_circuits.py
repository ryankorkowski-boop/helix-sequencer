from core.physical_band_circuits import (
    DRUMMER, VOCAL_STATES, physical_drummer_plan, singer_pose_plan, validate_drummer_plan,
)


def test_drummer_pose_contract():
    validate_drummer_plan()
    plan = physical_drummer_plan(101)
    assert [p["channel"] for p in plan] == list(range(101, 111))
    assert plan[0]["dim_base"]
    assert all(not p["dim_base"] for p in plan[1:])
    assert len(DRUMMER) == 10


def test_separate_snare_contact_and_shared_surface():
    left, right = DRUMMER[4:6]
    assert left.name != right.name
    assert "snare_surface" in left.elements and "snare_surface" in right.elements
    assert "left_arm_snare_contact" in left.elements
    assert "right_arm_snare_contact" in right.elements


def test_singer_seven_phonemes():
    assert VOCAL_STATES == ("REST", "AH", "EE", "OH", "MBP", "FV", "L")
    for member in ("snowman_singer", "snowman_singer_female"):
        plan = singer_pose_plan(member, 21)
        assert len(plan) == 7
        assert plan[-1]["channel"] == 27
