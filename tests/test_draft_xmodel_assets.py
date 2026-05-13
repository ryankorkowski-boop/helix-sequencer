from __future__ import annotations

from pathlib import Path

from tools.report_band_geometry_status import load_geometry_manifest



def test_manifest_xmodel_asset_paths_exist() -> None:
    manifest = load_geometry_manifest()

    for model in manifest["models"].values():
        assert Path(model["asset_path"]).exists()



def test_draft_xmodel_assets_include_model_names_and_disclaimer() -> None:
    manifest = load_geometry_manifest()

    for model_name, model in manifest["models"].items():
        text = Path(model["asset_path"]).read_text(encoding="utf-8")
        assert model_name in text
        assert "draft_geometry_asset_not_physical_render_proof" in text



def test_draft_xmodel_assets_include_at_least_one_declared_submodel() -> None:
    manifest = load_geometry_manifest()

    for model in manifest["models"].values():
        text = Path(model["asset_path"]).read_text(encoding="utf-8")
        assert any(submodel in text for submodel in model["submodels"])
