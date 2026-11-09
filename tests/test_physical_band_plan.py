from core.physical_band_plan import build_physical_band_plan

def test_seven_performers_have_disjoint_ac_and_pixel_ranges():
    plan = build_physical_band_plan()
    people = plan["performers"]
    assert len(people) == 7
    assert plan["ac"]["total_capacity"] == 112
    assert plan["rgb"]["pixel_count"] == 1100
    assert plan["rgb"]["rgb_channel_values"] == 3300
    assert [(p["ac_start"], p["ac_end"]) for p in people] == [
        (1, 16), (17, 32), (33, 48), (49, 64),
        (65, 80), (81, 96), (97, 112)]
    assert people[0]["pixel_start"] == 1
    assert people[-1]["pixel_end"] == 1100
    for left, right in zip(people, people[1:]):
        assert left["pixel_end"] + 1 == right["pixel_start"]
        assert left["ac_end"] + 1 == right["ac_start"]

def test_keyboard_and_mallet_hardware_not_misrepresented_as_existing_models():
    people = build_physical_band_plan()["performers"]
    assert people[3]["logical_submodels"] is None
    assert people[4]["logical_submodels"] is None
    assert all(p["proposed_pixels"] > 0 for p in people)
