from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from models.helixville4_performer_runtime import DRUMMER


ROOT = Path(__file__).resolve().parents[1]
DRUMMER_XMODEL = ROOT / "fixtures" / "band_geometry" / "models" / "HX_SNOWMAN_DRUMMER.xmodel"
MANIFEST = ROOT / "fixtures" / "band_geometry" / "geometry_manifest.json"
RANGE_RE = re.compile(r"^\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$")


def _load_drummer_xmodel() -> ET.Element:
    return ET.parse(DRUMMER_XMODEL).getroot()


def _submodels(root: ET.Element) -> dict[str, str]:
    return {
        node.attrib["name"]: node.attrib.get("line0", "")
        for node in root.findall("./subModels/subModel")
    }


def _expand_ranges(value: str) -> set[int]:
    nodes: set[int] = set()
    for chunk in value.split(","):
        if "-" in chunk:
            start_s, end_s = chunk.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            assert start <= end, f"range starts after it ends: {chunk}"
            nodes.update(range(start, end + 1))
        else:
            nodes.add(int(chunk))
    return nodes


def test_drummer_xmodel_is_well_formed_custom_model() -> None:
    root = _load_drummer_xmodel()

    assert root.tag == "custommodel"
    assert root.attrib["name"] == "HX_SNOWMAN_DRUMMER"
    assert int(root.attrib["parm1"]) == 90
    assert int(root.attrib["parm2"]) == 72
    assert root.attrib["StringType"] == "RGB Nodes"


def test_drummer_xmodel_submodel_ranges_are_numeric_and_in_bounds() -> None:
    root = _load_drummer_xmodel()
    width = int(root.attrib["parm1"])
    height = int(root.attrib["parm2"])
    max_node = width * height
    submodels = _submodels(root)

    assert submodels, "expected checked-in drummer xmodel to contain submodels"
    assert len(submodels) == len(set(submodels)), "duplicate submodel names are not allowed"

    for name, line0 in submodels.items():
        assert line0, f"{name} has no line0 ranges"
        assert RANGE_RE.match(line0), f"{name} has non-numeric node ranges: {line0}"
        nodes = _expand_ranges(line0)
        assert min(nodes) >= 1, f"{name} contains node below 1"
        assert max(nodes) <= max_node, f"{name} contains node above {max_node}"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Current starter asset/manifest/runtime contract is not aligned: "
        "the xmodel omits declared HEAD/DRUMKIT_ALL and runtime arm targets."
    ),
)
def test_drummer_xmodel_matches_manifest_and_runtime_contract() -> None:
    root = _load_drummer_xmodel()
    actual_submodels = set(_submodels(root))

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_submodels = set(manifest["models"]["HX_SNOWMAN_DRUMMER"]["submodels"])
    runtime_submodels = set(DRUMMER.submodels)

    assert actual_submodels == manifest_submodels
    assert runtime_submodels <= actual_submodels
