from types import SimpleNamespace

import pytest

from models.snowman_wiring_inventory import inventory_model, write_inventory


def fake_model(kind, submodels, points=()):
    return SimpleNamespace(
        name="HX_SNOW_LEAD", kind=kind, submodels=submodels,
        points=points, details={"review_role": "lead"},
        attrs={"CustomModelCompressed": ";".join(f"{i},0,0" for i in range(1, max((max(v, default=0) for v in submodels.values()), default=0) + 1))},
    )


def test_pixel_counts_unique_nodes_per_submodel():
    model = fake_model("pixel", {"BODY": [1, 2, 2], "MOUTH_AI": [3, 4]}, [0] * 4)
    report = inventory_model(model)
    assert report["unique_addressable_nodes"] == 4
    assert report["ac_circuits_used"] is None
    assert report["submodels"][0]["node_count"] == 2
    assert report["physical_bulb_counts_verified"] is False


def test_ac_geometry_is_not_mistaken_for_bulbs():
    model = fake_model("ac", {"BODY": [1], "MOUTH_AI": [2]}, [0] * 100)
    report = inventory_model(model)
    assert report["geometry_positions"] == 100
    assert report["ac_circuits_used"] == 2
    assert report["submodels"][0]["node_count"] is None
    assert report["submodels"][0]["physical_bulbs_per_strand"] is None


def test_ac_circuit_limit_enforced():
    with pytest.raises(ValueError, match="16 circuits"):
        inventory_model(fake_model("ac", {"BAD": [17]}))


def test_write_inventory_refuses_overwrite(tmp_path):
    model = fake_model("pixel", {"BODY": [1]}, [0])
    json_path, csv_path = write_inventory([model], tmp_path)
    assert json_path.is_file() and csv_path.is_file()
    assert "wiring_verified" in csv_path.read_text()
    with pytest.raises(FileExistsError):
        write_inventory([model], tmp_path)


def test_duplicate_model_names_refused_before_writing(tmp_path):
    model = fake_model('pixel', {'BODY': [1]}, [0])
    with pytest.raises(ValueError, match='Duplicate snowman model names'):
        write_inventory([model, model], tmp_path)
    assert not (tmp_path / 'snowman_submodel_inventory.json').exists()


def test_pixel_submodel_referencing_missing_geometry_fails():
    model = fake_model('pixel', {'BODY': [1, 2]}, [0, 0])
    model.attrs['CustomModelCompressed'] = '1,0,0'
    with pytest.raises(ValueError, match='undefined pixel nodes'):
        inventory_model(model)


def test_standalone_generator_rejects_missing_band_roles(monkeypatch, tmp_path):
    import tools.export_snowman_band_inventory as generator
    monkeypatch.setattr(generator, 'add_band', lambda garden: [fake_model('pixel', {'BODY': [1]}, [0])])
    with pytest.raises(ValueError, match='seven distinct snowman roles'):
        generator.export_band_inventories(tmp_path)
    assert not (tmp_path / 'pixel').exists()
