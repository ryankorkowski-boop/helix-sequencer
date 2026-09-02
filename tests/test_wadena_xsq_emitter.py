import xml.etree.ElementTree as ET

import pytest

from core.wadena_temporal_renderer import ACSafeLandmarkEvent
from core.wadena_xsq_emitter import emit_wadena_xsq_sequence
from tools.validate_xsq_structure import validate_xsq


def test_emits_validator_compatible_explicit_ac_xsq(tmp_path):
    sequence = emit_wadena_xsq_sequence(
        events=(
            ACSafeLandmarkEvent("LEFT_TREE", 0.013, 0.141, 0.73, "Ramp", 0),
            ACSafeLandmarkEvent("BLVD_LEFT", 0.161, 0.291, 0.51, "Level", 1),
        ),
        landmark_channels={"LEFT_TREE": "CH_001", "BLVD_LEFT": "CH_002"},
    )
    path = tmp_path / "wadena.xsq"
    path.write_text(sequence.xml_text, encoding="utf-8")
    validate_xsq(path)

    root = ET.fromstring(sequence.xml_text)
    elements = root.find("ElementEffects").findall("Element")
    assert [e.attrib["name"] for e in elements] == ["CH_001", "CH_002"]
    assert [e.attrib["start"] for e in elements] == ["0.000000", "0.150000"]
    assert all("rgb" not in key.lower() for e in elements for key in e.attrib)


def test_unknown_landmark_is_not_guessed():
    sequence = emit_wadena_xsq_sequence(
        events=(ACSafeLandmarkEvent("NOT_IN_MAP", 0, 0.2, 1.0, "On", 0),),
        landmark_channels={},
    )
    root = ET.fromstring(sequence.xml_text)
    assert root.find("ElementEffects").findall("Element") == []


def test_invalid_grid_is_rejected():
    with pytest.raises(ValueError):
        emit_wadena_xsq_sequence(events=(), landmark_channels={}, grid_ms=0)
