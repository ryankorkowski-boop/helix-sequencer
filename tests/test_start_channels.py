from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from core.controller_parser import layout_channel_count
from core.model_parser import parse_layout
from core.start_channels import StartChannelError, resolve_model_channels


def _write_layout(path: Path, models: list[str], networks: str | None = None) -> None:
    body = "\n".join(models)
    path.write_text(f"<xrgb><models>{body}</models></xrgb>", encoding="utf-8")
    if networks is not None:
        (path.parent / "xlights_networks.xml").write_text(networks, encoding="utf-8")


def _model(name: str, start: str, *, nodes: int = 10, submodels: str = "") -> str:
    return (
        f'<model name="{name}" DisplayAs="Single Line" StartChannel="{start}" '
        f'StringType="RGB Nodes" parm1="1" parm2="{nodes}">{submodels}</model>'
    )


def _sub(name: str, line: str) -> str:
    return f'<subModel name="{name}" line0="{line}"/>'


NETWORKS = """
<Networks>
  <Controller Name="Show">
    <network NetworkType="E131" ComPort="10.0.0.5" StartUniverse="1" MaxChannels="510" NumUniverses="4"/>
  </Controller>
  <Controller Name="Yard">
    <network NetworkType="E131" ComPort="10.0.0.6" StartUniverse="5" MaxChannels="512" NumUniverses="2"/>
  </Controller>
</Networks>
"""


def test_absolute_start_and_end(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    _write_layout(path, [_model("Arch", "100", nodes=10)])
    model = parse_layout(path).models["Arch"]
    assert model.start_channel == 100
    assert model.end_channel == 129
    assert model.controller_name is None
    assert model.start_channel_error is None


def test_model_reference_formats(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    _write_layout(
        path,
        [
            _model("Arch", "100", nodes=10),
            _model("After", "&gt;Arch:1", nodes=4),
            _model("Same", "@Arch:1", nodes=2),
            _model("Offset", "@Arch:4", nodes=1),
            _model("Gap", "&gt;Arch:3", nodes=1),
        ],
    )
    models = parse_layout(path).models
    assert (models["After"].start_channel, models["After"].end_channel) == (130, 141)
    assert models["Same"].start_channel == 100
    assert models["Offset"].start_channel == 103
    assert models["Gap"].start_channel == 132


def test_chained_references_resolve_in_dependency_order(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    _write_layout(
        path,
        [
            _model("A", "1", nodes=1),
            _model("C", "&gt;B:1", nodes=1),
            _model("B", "&gt;A:1", nodes=1),
        ],
    )
    models = parse_layout(path).models
    assert models["A"].end_channel == 3
    assert models["B"].start_channel == 4
    assert models["C"].start_channel == 7


def test_universe_and_controller_formats(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    _write_layout(
        path,
        [
            _model("U1", "#1:1", nodes=1),
            _model("U2", "#2:1", nodes=1),
            _model("IP", "#10.0.0.5:2:3", nodes=1),
            _model("Show", "!Show:1", nodes=1),
            _model("Yard", "!Yard:10", nodes=1),
            _model("Legacy", "#5:1", nodes=1),
        ],
        NETWORKS,
    )
    models = parse_layout(path).models
    assert (models["U1"].start_channel, models["U1"].controller_name) == (1, "Show")
    assert (models["U2"].start_channel, models["U2"].controller_name) == (511, "Show")
    assert (models["IP"].start_channel, models["IP"].controller_name) == (513, "Show")
    assert (models["Show"].start_channel, models["Show"].controller_name) == (1, "Show")
    assert models["Yard"].start_channel == 2041 + 9
    assert models["Yard"].controller_name == "Yard"
    assert models["Legacy"].start_channel == 2041
    assert models["Legacy"].controller_name == "Yard"
    assert layout_channel_count(path) == models["Yard"].end_channel


def test_legacy_baud_rate_is_the_universe_number(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    _write_layout(
        path,
        [_model("Porch", "#2:4", nodes=1)],
        """
        <Networks>
          <network NetworkType="E131" ComPort="192.168.1.20" BaudRate="1" MaxChannels="510" Description="First"/>
          <network NetworkType="E131" ComPort="192.168.1.20" BaudRate="2" MaxChannels="510" Description="Second"/>
        </Networks>
        """,
    )
    model = parse_layout(path).models["Porch"]
    assert model.start_channel == 510 + 4
    assert model.controller_name == "Second"


def test_submodel_uses_parent_node_numbers(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    _write_layout(
        path,
        [
            _model("Arch", "1", nodes=10, submodels=_sub("Mouth", "2-4")),
            _model("Next", "&gt;Arch:1", nodes=1),
        ],
    )
    models = parse_layout(path).models
    mouth = models["Arch/Mouth"]
    assert mouth.is_submodel
    assert mouth.start_channel == 4
    assert mouth.end_channel == 12
    assert mouth.controller_name is None
    assert models["Next"].start_channel == 31


def test_submodel_of_a_chained_model(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    _write_layout(
        path,
        [
            _model("Arch", "10", nodes=2),
            _model("Tree", "@Arch:1", nodes=4, submodels=_sub("Top", "1-2")),
        ],
    )
    top = parse_layout(path).models["Tree/Top"]
    assert top.start_channel == 10
    assert top.end_channel == 15


def test_circular_and_missing_references_are_errors(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    _write_layout(
        path,
        [
            _model("A", "&gt;B:1", nodes=1),
            _model("B", "@A:1", nodes=1),
            _model("C", "&gt;Missing:1", nodes=1),
            _model("D", "!Nope:1", nodes=1),
            _model("E", "#9:1", nodes=1),
            _model("F", "0", nodes=1),
        ],
    )
    layout = parse_layout(path)
    assert "circular start-channel reference" in (layout.models["A"].start_channel_error or "")
    assert "->" in (layout.models["A"].start_channel_error or "")
    assert "not in the layout" in (layout.models["C"].start_channel_error or "")
    assert "controller" in (layout.models["D"].start_channel_error or "")
    assert "universe 9" in (layout.models["E"].start_channel_error or "")
    assert ">= 1" in (layout.models["F"].start_channel_error or "")
    with pytest.raises(StartChannelError):
        resolve_model_channels(layout.models, strict=True)
    with pytest.raises(StartChannelError):
        layout_channel_count(path)


def test_layout_channel_count_is_the_highest_end_not_the_sum(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    _write_layout(
        path,
        [
            _model("A", "1", nodes=10),
            _model("B", "1", nodes=10),
        ],
    )
    assert layout_channel_count(path) == 30


def test_xml_escapes_round_trip_the_reference_characters(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    root = ET.Element("xrgb")
    models = ET.SubElement(root, "models")
    ET.SubElement(
        models,
        "model",
        {"name": "Arch", "DisplayAs": "Single Line", "StartChannel": "5", "StringType": "RGB Nodes", "parm1": "1", "parm2": "2"},
    )
    ET.SubElement(
        models,
        "model",
        {"name": "Next", "DisplayAs": "Single Line", "StartChannel": ">Arch:1", "StringType": "RGB Nodes", "parm1": "1", "parm2": "1"},
    )
    ET.ElementTree(root).write(path, encoding="utf-8")
    parsed = parse_layout(path)
    assert parsed.models["Next"].start_channel == 11
