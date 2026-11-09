from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from models.helixville4_performer_runtime import DRUMMER

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER.xmodel"
V3 = ROOT / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"
MANIFEST = ROOT / "fixtures/band_geometry/geometry_manifest.json"
RANGE_RE = re.compile(r"^\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$")


def _submodels(path: Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    return {node.attrib["name"]: node.attrib.get("line0", "") for node in root.findall("./subModels/subModel")}


def _expand(value: str) -> set[int]:
    nodes: set[int] = set()
    for chunk in value.split(","):
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            nodes.update(range(int(a), int(b) + 1))
        else:
            nodes.add(int(chunk))
    return nodes


def _assert_ranges(path: Path) -> None:
    root = ET.parse(path).getroot()
    max_node = int(root.attrib["parm1"]) * int(root.attrib["parm2"])
    submodels = _submodels(path)
    assert submodels
    for name, line0 in submodels.items():
        assert line0 and RANGE_RE.match(line0), f"{name} has invalid ranges: {line0}"
        nodes = _expand(line0)
        assert min(nodes) >= 1 and max(nodes) <= max_node


def test_starter_and_v3_are_well_formed_custom_models() -> None:
    starter = ET.parse(STARTER).getroot()
    v3 = ET.parse(V3).getroot()
    assert starter.tag == v3.tag == "custommodel"
    assert starter.attrib["name"] == "HX_SNOWMAN_DRUMMER"
    assert v3.attrib["name"] == "HX_SNOWMAN_DRUMMER_V3"
    assert (int(starter.attrib["parm1"]), int(starter.attrib["parm2"])) == (90, 72)
    assert (int(v3.attrib["parm1"]), int(v3.attrib["parm2"])) == (96, 72)
    _assert_ranges(STARTER)
    _assert_ranges(V3)


def test_archived_starter_matches_manifest_and_has_real_unions() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    archived = set(manifest["archived_models"]["HX_SNOWMAN_DRUMMER"]["submodels"])
    actual = set(_submodels(STARTER))
    assert archived == actual

    sub = {name: _expand(value) for name, value in _submodels(STARTER).items()}
    expected_head = (
        sub["HX_SNOWMAN_DRUMMER_HAT"]
        | sub["HX_SNOWMAN_DRUMMER_HAT_BAND"]
        | sub["HX_SNOWMAN_DRUMMER_HAT_HOLLY"]
        | sub["HX_SNOWMAN_DRUMMER_FACE"]
    )
    assert sub["HX_SNOWMAN_DRUMMER_HEAD"] == expected_head

    expected_kit = set()
    for name in (
        "KICK","KICK_RIM","SNARE","SNARE_RIM","TOM_LEFT","TOM_RIGHT",
        "HI_HAT","CYMBAL_LEFT","CYMBAL_RIGHT","STANDS",
    ):
        expected_kit |= sub[f"HX_SNOWMAN_DRUMMER_{name}"]
    assert sub["HX_SNOWMAN_DRUMMER_DRUMKIT_ALL"] == expected_kit


def test_active_manifest_resolves_runtime_v3_contract_exactly() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = manifest["models"]["HX_SNOWMAN_DRUMMER_V3"]
    declared = set(entry["submodels"])
    runtime = set(DRUMMER.submodels)
    actual = set(_submodels(V3))
    assert runtime == declared
    assert declared <= actual
    assert all(name.startswith("HX_SNOWMAN_DRUMMER_V3_") for name in declared)
    assert not any("TOM_4" in name for name in actual)
