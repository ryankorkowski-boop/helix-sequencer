"""Check that source-tagged musical cues cannot silently disappear before native render."""
import json
import xml.etree.ElementTree as ET

import pytest

from tools.verify_render_logic_provenance import verify


def _fixture(tmp_path, *, source=True, mapped=2, drums=0):
    (tmp_path / "run_manifest.json").write_text(json.dumps({
        "xsq": "Performance.xsq", "source_audio_sha256": "a" * 64,
        "source_analysis_sha256": "b" * 64,
    }))
    root = ET.Element("xsequence")
    elements = ET.SubElement(root, "ElementEffects")
    lane = ET.SubElement(ET.SubElement(elements, "Element", name="GUITAR"), "EffectLayer")
    effect = ET.SubElement(lane, "Effect")
    if source:
        effect.set("sourceMethod", "retained_production_band_plan")
    ET.ElementTree(root).write(tmp_path / "Performance.xsq")
    (tmp_path / "Band_Instrument_Provenance.json").write_text(json.dumps({
        "models": {"GUITAR": {"mapped_events": mapped}}
    }))
    if drums:
        (tmp_path / "Canonical_Drummer.json").write_text(json.dumps({
            "event_mapping": {"component_events": {"KICK": drums}}
        }))
    return tmp_path


def test_source_cues_reach_xsq(tmp_path):
    report = verify(_fixture(tmp_path))
    assert report["source_tagged_effects"] == 1
    assert report["instrument_mapped_events"] == 2
    assert report["native_fseq_verified"] is False


def test_missing_source_tag_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="never reached"):
        verify(_fixture(tmp_path, source=False))


def test_missing_drum_source_tag_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="Detected drum cues"):
        verify(_fixture(tmp_path, drums=3))
