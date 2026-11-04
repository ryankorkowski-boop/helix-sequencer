from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from xlights.layout_sync import layout_entries_and_lookup, sync_xsq_to_layout
from xlights.xml_io import load_xsq
from xlights.xsq_writer import XsqIndex


def _layout(path: Path) -> None:
    path.write_text(
        """
        <xrgb>
          <models>
            <model name="Arch" DisplayAs="Single Line">
              <subModel name="Left"/>
              <subModel name="Right"/>
            </model>
            <model name="Tree" DisplayAs="Tree 360"/>
          </models>
          <modelGroups>
            <modelGroup name="Yard" models="Arch,Tree"/>
          </modelGroups>
        </xrgb>
        """,
        encoding="utf-8",
    )


def _xsq() -> XsqIndex:
    root = ET.fromstring(
        """
        <xsequence>
          <DisplayElements>
            <Element type="timing" name="Beats" visible="1" active="1"/>
            <Element type="model" name="Arch/Left" visible="1"/>
            <Element type="model" name="Gone" visible="1"/>
          </DisplayElements>
          <ElementEffects>
            <Element type="timing" name="Beats" active="1">
              <EffectLayer/>
            </Element>
            <Element type="model" name="Arch/Left">
              <EffectLayer>
                <Effect name="On" startTime="0" endTime="100"/>
              </EffectLayer>
            </Element>
            <Element type="model" name="Gone">
              <EffectLayer/>
            </Element>
          </ElementEffects>
        </xsequence>
        """
    )
    return XsqIndex(tree=ET.ElementTree(root), root=root, elements={}, on_tpl=None, ramp_tpl=None)  # type: ignore[arg-type]


def test_submodel_effects_nest_under_the_parent(tmp_path: Path) -> None:
    layout = tmp_path / "xlights_rgbeffects.xml"
    _layout(layout)
    ordered, lookup = layout_entries_and_lookup(layout)
    assert ordered == ["Yard", "Arch", "Tree"]
    assert lookup["arch/left"] == "Arch/Left"
    assert "Arch/Left" not in ordered

    xsq = _xsq()
    report = sync_xsq_to_layout(xsq, layout)
    assert report["stale_removed"] >= 1

    display_names = [
        (element.attrib.get("type"), element.attrib.get("name"))
        for element in xsq.root.find("DisplayElements")  # type: ignore[union-attr]
    ]
    assert ("model", "Arch/Left") not in display_names
    assert ("model", "Yard") in display_names
    assert ("model", "Arch") in display_names
    assert ("model", "Tree") in display_names
    assert all(name is None or "/" not in name for _kind, name in display_names)

    top_level = [
        (element.attrib.get("type"), element.attrib.get("name"))
        for element in xsq.root.find("ElementEffects")  # type: ignore[union-attr]
    ]
    assert ("model", "Arch/Left") not in top_level
    assert ("model", "Yard") in top_level
    assert all("/" not in (name or "") for _kind, name in top_level)

    parent = xsq.elements["Arch"]
    nested = parent.find("SubModelEffectLayer[@name='Left']")
    assert nested is not None
    effect = nested.find("./EffectLayer/Effect")
    assert effect is not None
    assert effect.attrib["name"] == "On"
    assert xsq.elements["Arch/Left"] is nested
    assert xsq.elements["Arch/Right"].tag == "SubModelEffectLayer"
    assert xsq.elements["Arch/Right"].find("EffectLayer") is not None

    saved = tmp_path / "saved.xsq"
    ET.ElementTree(xsq.root).write(saved, encoding="utf-8")
    reloaded = load_xsq(saved)
    assert reloaded.elements["Arch/Left"].tag == "SubModelEffectLayer"
    assert reloaded.elements["Arch/Left"].find("./EffectLayer/Effect").attrib["name"] == "On"  # type: ignore[union-attr]
