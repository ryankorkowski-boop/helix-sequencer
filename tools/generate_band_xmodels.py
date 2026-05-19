from __future__ import annotations

import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from tools.report_band_geometry_status import DEFAULT_MANIFEST


DISCLAIMER = "draft_geometry_asset_not_physical_render_proof"


def _model_xml(model_name: str, submodels: list[str]) -> str:
    root = Element("xmodel")
    root.set("name", model_name)
    root.set("status", DISCLAIMER)

    model = SubElement(root, "model")
    model.set("name", model_name)
    model.set("type", "custom_draft")

    submodel_root = SubElement(root, "submodels")
    for index, submodel_name in enumerate(submodels):
        submodel = SubElement(submodel_root, "submodel")
        submodel.set("index", str(index))
        submodel.set("name", submodel_name)
        submodel.set("draft_pixels", "1")

    return tostring(root, encoding="unicode") + "\n"


def generate_band_xmodels(manifest_path: str | Path = DEFAULT_MANIFEST) -> list[Path]:
    path = Path(manifest_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    written: list[Path] = []

    for model_name, model_info in sorted(manifest["models"].items()):
        asset_path = Path(model_info["asset_path"])
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_text(_model_xml(model_name, model_info["submodels"]), encoding="utf-8")
        written.append(asset_path)

    return written


if __name__ == "__main__":
    for output in generate_band_xmodels():
        print(output)
