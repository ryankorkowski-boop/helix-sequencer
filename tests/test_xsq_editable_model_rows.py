from types import SimpleNamespace
import xml.etree.ElementTree as ET

from xlights.layout_sync import sync_xsq_to_layout, validate_xsq_layout_rows


def _layout(path):
    path.write_text("""<xrgb>
      <modelGroups><modelGroup name="Yard Group"/></modelGroups>
      <models>
        <model name="Mega Tree"><subModel name="Left Half"/><subModel name="Right Half"/></model>
        <model name="Arch 1"/>
      </models>
    </xrgb>""", encoding="utf-8")
    return path


def _xsq():
    root = ET.fromstring("""<xsequence>
      <DisplayElements/>
      <ElementEffects>
        <Element type="model" name="Mega Tree"><EffectLayer name="AUTO"><Effect name="On" startTime="0" endTime="500"/></EffectLayer></Element>
        <Element type="model" name="Old Prop"><EffectLayer/></Element>
      </ElementEffects>
    </xsequence>""")
    return SimpleNamespace(root=root, elements={})


def test_sync_creates_editable_rows_for_every_model_and_submodel(tmp_path):
    layout = _layout(tmp_path / "xlights_rgbeffects.xml")
    xsq = _xsq()
    report = sync_xsq_to_layout(xsq, layout)
    validation = validate_xsq_layout_rows(xsq, layout)
    assert validation["passed"] is True
    assert validation["expected_rows"] == 5
    names = {el.attrib.get("name") for el in xsq.root.find("ElementEffects")}
    assert {"Yard Group", "Mega Tree", "Mega Tree/Left Half", "Mega Tree/Right Half", "Arch 1"} <= names
    assert "Old Prop" not in names
    assert report["stale_removed"] >= 1


def test_validator_detects_missing_editable_row(tmp_path):
    layout = _layout(tmp_path / "xlights_rgbeffects.xml")
    xsq = _xsq()
    validation = validate_xsq_layout_rows(xsq, layout)
    assert validation["passed"] is False
    assert "Mega Tree/Left Half" in validation["missing_rows"]


def test_sync_preserves_existing_model_effects(tmp_path):
    layout = _layout(tmp_path / "xlights_rgbeffects.xml")
    xsq = _xsq()
    sync_xsq_to_layout(xsq, layout)
    tree = next(el for el in xsq.root.find("ElementEffects") if el.attrib.get("name") == "Mega Tree")
    effects = tree.findall("./EffectLayer/Effect")
    assert len(effects) == 1
    assert effects[0].attrib["name"] == "On"
