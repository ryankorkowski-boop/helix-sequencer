"""Check that source-tagged musical cues cannot silently disappear before native render."""
import json
import xml.etree.ElementTree as ET

import pytest

from tools.verify_render_logic_provenance import verify


def _fixture(tmp_path, *, source=True, mapped=1, drums=0):
    (tmp_path / "run_manifest.json").write_text(json.dumps({
        "xsq": "Performance.xsq", "source_audio_sha256": "a" * 64,
        "source_analysis_sha256": "b" * 64,
    }))
    root = ET.Element("xsequence")
    elements = ET.SubElement(root, "ElementEffects")
    lane = ET.SubElement(ET.SubElement(elements, "Element", name="GUITAR/STRING_0"), "EffectLayer")
    effect = ET.SubElement(lane, "Effect", startTime="100", endTime="200")
    if source:
        effect.set("sourceMethod", "retained_production_band_plan")
        effect.set("sourceStartMs", "100")
        effect.set("sourceEndMs", "200")
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
    assert report["instrument_mapped_events"] == 1
    assert report["native_fseq_verified"] is False


def test_missing_source_tag_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="mapped cues"):
        verify(_fixture(tmp_path, source=False))


def test_missing_drum_source_tag_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="detected strikes"):
        verify(_fixture(tmp_path, drums=3))


def test_all_panel_counts_use_shared_builder_and_gate():
    """Nine/twelve/sixteen are views of one production pipeline, not engines."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    shared = (root / "tools/build_current_comparison.py").read_text()
    sixteen = (root / "tools/render_full_song_comparison.py").read_text()
    assert "verify_logic(folder)" in shared
    assert "build_layouts(production, vocals, layouts" in sixteen
    assert "layout_builder=build_layout" in sixteen

def test_partial_instrument_coverage_fails(tmp_path):
    with pytest.raises(ValueError, match="2 mapped cues but only 1"):
        verify(_fixture(tmp_path, mapped=2))

def test_out_of_range_source_onset_fails(tmp_path):
    folder = _fixture(tmp_path)
    import xml.etree.ElementTree as ET
    xsq = folder / "Performance.xsq"
    tree = ET.parse(xsq)
    tree.find(".//Effect").set("sourceStartMs", "-1")
    tree.write(xsq)
    with pytest.raises(ValueError, match="out-of-range onset"):
        verify(folder)

def test_native_effect_onset_mismatch_fails(tmp_path):
    folder = _fixture(tmp_path)
    tree = ET.parse(folder / "Performance.xsq")
    tree.find(".//Effect").set("startTime", "120")
    tree.write(folder / "Performance.xsq")
    with pytest.raises(ValueError, match="but source event starts at"):
        verify(folder)
