import pytest
from core.community_layout_presets import PRESETS, rank_layouts


def test_starter_inventory_selects_starter():
    inventory = {"house_outline": 1, "mega_tree": 1, "star": 1, "arches": 4}
    assert rank_layouts(inventory)[0]["preset"] == "starter"


def test_ac_layouts_separate_from_rgb():
    assert all(item["preset"].startswith("legacy_ac") for item in rank_layouts({"ac_channel": 16}, kind="ac"))
    assert rank_layouts({"ac_channel": 16}, kind="ac")[0]["preset"] == "legacy_ac16"


def test_all_presets_have_unique_keys():
    assert len({p.key for p in PRESETS}) == len(PRESETS)


def test_rejects_negative_counts():
    with pytest.raises(ValueError):
        rank_layouts({"arch": -1})
