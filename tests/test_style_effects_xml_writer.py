import xml.etree.ElementTree as ET

from xlights.style_effects_xml_writer import build_style_effects_xml, write_style_effects_xml


def sample_rows():
    return [
        {
            "model": "MegaTree",
            "start": 0.0,
            "duration": 1.0,
            "effect": "beat_pulse",
            "palette": ["red", "green"],
            "intensity": 0.8,
            "motion": "center_out",
            "intent": "pulse",
        }
    ]


def test_build_style_effects_xml_contains_effect_and_palette():
    root = build_style_effects_xml(sample_rows())

    assert root.tag == "HelixStyleEffects"
    effect = root.find("Effect")
    assert effect is not None
    assert effect.attrib["model"] == "MegaTree"
    assert effect.attrib["effect"] == "beat_pulse"

    colors = [color.attrib["name"] for color in effect.findall("Palette/Color")]
    assert colors == ["red", "green"]


def test_write_style_effects_xml_round_trip(tmp_path):
    output_path = tmp_path / "style_effects.xml"

    written = write_style_effects_xml(sample_rows(), output_path)

    assert written == output_path
    parsed = ET.parse(output_path).getroot()
    assert parsed.tag == "HelixStyleEffects"
    assert parsed.find("Effect").attrib["intent"] == "pulse"
