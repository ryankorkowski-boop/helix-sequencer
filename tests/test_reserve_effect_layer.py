"""Empty sequencer layers are not created until an effect needs one."""
import xml.etree.ElementTree as ET

from xlights.xml_io import ensure_layer, reserve_effect_layer


def test_only_the_used_lane_is_created():
    model = ET.Element("Element", {"name": "Tree", "type": "model"})
    ET.SubElement(model, "EffectLayer")
    layers = {}
    elements = {"Tree": model}
    layer = reserve_effect_layer(layers, elements, "Tree", "accent", "AUTO_accent", ensure_layer)
    assert layer.attrib["name"] == "AUTO_accent"
    assert [child.attrib.get("name") for child in model] == ["AUTO_accent"]
    again = reserve_effect_layer(layers, elements, "Tree", "accent", "AUTO_accent", ensure_layer)
    assert again is layer
    assert len(list(model)) == 1
    assert "base" not in layers["Tree"]
