"""A reused template must not truncate or extend the newly generated song."""
import xml.etree.ElementTree as ET

import pytest

from xlights.xml_io import set_sequence_duration


@pytest.mark.parametrize("old", ["1", "237.440", None])
def test_generated_header_matches_soundtrack_and_preserves_other_fields(old):
    root = ET.fromstring('<xsequence><head><mediaFile>track.wav</mediaFile></head>'
                         '<ElementEffects><Element name="Keys"/></ElementEffects></xsequence>')
    if old is not None:
        ET.SubElement(root.find("head"), "sequenceDuration").text = old
    set_sequence_duration(root, 38.32)
    assert root.findtext("./head/sequenceDuration") == "38.320"
    assert len(root.findall("./head/sequenceDuration")) == 1
    assert root.findtext("./head/mediaFile") == "track.wav"
    assert root.find("./ElementEffects/Element").get("name") == "Keys"


def test_minimal_template_gets_soundtrack_duration_at_millisecond_precision():
    root = ET.Element("xsequence")
    set_sequence_duration(root, 2.3754)
    assert root.findtext("./head/sequenceDuration") == "2.375"


@pytest.mark.parametrize("invalid", [0, -1, float("nan"), float("inf"), -float("inf")])
def test_invalid_soundtrack_duration_does_not_modify_header(invalid):
    root = ET.fromstring('<xsequence><head><sequenceDuration>3</sequenceDuration></head></xsequence>')
    before = ET.tostring(root)
    with pytest.raises(ValueError, match="finite positive"):
        set_sequence_duration(root, invalid)
    assert ET.tostring(root) == before
