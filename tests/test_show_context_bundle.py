"""xLights show-directory portability and collision prevention."""
from __future__ import annotations

from pathlib import Path
import json
import xml.etree.ElementTree as ET
import pytest

from tools.show_context_bundle import package_xlights_layout


def make_show(tmp: Path):
    show = tmp / "source-show"
    show.mkdir()
    layout = show / "xlights_rgbeffects.xml"
    layout.write_text('<xrgb><models><model name="Roof" DisplayAs="Single Line"'
                      ' StringType="Single Color Red" StartChannel="1"/></models></xrgb>')
    (show / "xlights_networks.xml").write_text('<Networks/>')
    return layout


def test_bundle_layout_next_to_generated_xsq(tmp_path: Path):
    layout = make_show(tmp_path)
    outputs = tmp_path / "exports"
    outputs.mkdir()
    seq = outputs / "song.xsq"
    seq.write_text("<xsequence/>")
    results = package_xlights_layout([seq], layout)
    assert len(results) == 1
    assert (outputs / "xlights_rgbeffects.xml").read_bytes() == layout.read_bytes()
    assert (outputs / "xlights_networks.xml").exists()
    manifest = json.loads((outputs / "helix_show_context.json").read_text())
    assert manifest["network_config_included"] is True
    assert "song.xsq" in manifest["xsqs"]
    # Idempotence, not silent rewrite
    second = package_xlights_layout([seq], layout)
    assert second[0]["files"]["xlights_rgbeffects.xml"]["status"] == "already_matching"


def test_bundle_refuses_different_existing_layout(tmp_path: Path):
    layout = make_show(tmp_path)
    dest = tmp_path / "out"
    dest.mkdir()
    seq = dest / "song.xsq"
    seq.write_text("<xsequence/>")
    original = dest / "xlights_rgbeffects.xml"
    original.write_text('<xrgb><models><model name="Different"/></models></xrgb>')
    with pytest.raises(ValueError, match="collision"):
        package_xlights_layout([seq], layout)
    assert "Different" in original.read_text()


def test_bundle_rejects_invalid_selected_xml(tmp_path: Path):
    layout = tmp_path / "bad.xml"
    layout.write_text("<not-xlights/>")
    folder = tmp_path / "out"
    folder.mkdir()
    seq = folder / "sample.xsq"
    seq.write_text("<xsequence/>")
    with pytest.raises(ValueError, match="lacks xLights"):
        package_xlights_layout([seq], layout)


def test_bundle_with_multiple_sequences_one_folder(tmp_path: Path):
    layout = make_show(tmp_path)
    folder = tmp_path / "out"
    folder.mkdir()
    a, b = folder / "a.xsq", folder / "b.xsq"
    a.write_text("<xsequence/>")
    b.write_text("<xsequence/>")
    result = package_xlights_layout([a, b], layout)
    assert len(result) == 1
    assert result[0]["xsqs"] == ["a.xsq", "b.xsq"]
