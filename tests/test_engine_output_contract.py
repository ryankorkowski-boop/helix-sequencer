import xml.etree.ElementTree as ET

import pytest

from tools.measure_engine_stages import output_contract


def write_sequence(path, *, start="100", end="200", declared="Arch", target="Arch"):
    root = ET.Element("xsequence")
    ET.SubElement(ET.SubElement(root, "head"), "sequenceDuration").text = "1"
    display = ET.SubElement(root, "DisplayElements")
    ET.SubElement(display, "Element", name=declared)
    models = ET.SubElement(root, "ElementEffects")
    layer = ET.SubElement(ET.SubElement(models, "Element", type="model", name=target), "EffectLayer")
    ET.SubElement(layer, "Effect", startTime=start, endTime=end)
    ET.ElementTree(root).write(path)
    return path


def test_valid_contract(tmp_path):
    assert output_contract(write_sequence(tmp_path / "valid.xsq"))["model_effects"] == 1


@pytest.mark.parametrize("change", [
    {"start": "NaN"}, {"end": "inf"}, {"start": "300", "end": "200"},
    {"end": "1001"}, {"target": "missing model"},
])
def test_invalid_time_or_target_is_rejected(tmp_path, change):
    with pytest.raises(AssertionError):
        output_contract(write_sequence(tmp_path / "invalid.xsq", **change))
