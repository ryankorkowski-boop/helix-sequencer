"""Regression smoke for the parade design; no synthetic audio acceptance."""
from models.parade_float import AUDIO, GROUPS, SECTION_MAP, build, inventory


def test_native_float_groups_are_distinct():
    garden, band = build()
    assert band is None
    assert "DRASTIC MEASURES" in garden.title
    assert AUDIO == "Polar Prism Parade.mp3"
    assert all(group.startswith("FLOAT_") for group in GROUPS)
    assert "chorus" in SECTION_MAP
    names = [model.name for model in garden.models]
    assert len(names) == len(set(names))
    assert len(names) >= 100
    assert all(model.start > 0 and model.channels > 0 for model in garden.models)
    assert not any(model.details.get("generic_singer") or model.details.get("review_role")
                   for model in garden.models)
    skeletons = [m for m in garden.models if m.details.get("skeleton_performer_role")]
    assert {m.details["skeleton_performer_role"] for m in skeletons} == {"drummer", "guitarist", "bassist", "frontman"}
    assert all(all("POSE_" + s in m.submodels for s in ("IDLE", "ATTACK", "ACCENT", "RECOVERY")) for m in skeletons)
    assert any(m.details.get("brand_emblem") for m in garden.models)
    assert len([m for m in garden.models if m.details.get("brand_sign")]) == 4
    assert all(model.details.get("musical_role") in
               {"drummer", "guitarist", "bassist", "keyboardist"}
               for model in garden.models)
    assert all(model.details.get("parade_layer") for model in garden.models)


def test_float_spatial_depth_and_groups():
    garden, _ = build()
    inventory_rows = inventory()
    assert inventory_rows["model_count"] == len(garden.models)
    assert set(inventory_rows["zones"]) == {
        zone for members in GROUPS.values() for zone in members
    }
    assert len({round(model.points[:, 2].mean()) for model in garden.models}) > 12
    assert sum(m.zone == "MOIRE_LAYERS" for m in garden.models) >= 12
    assert sum(m.zone == "PERSPECTIVE_VANISHING" for m in garden.models) >= 12
    assert all(model.attrs.get("BlackTransparency") == "100" for model in garden.models)
