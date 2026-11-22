"""Run with HELIX_XLIGHTS pointing to xLights and an available display."""
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import pytest

from xlights.xml_io import materialize_native_effect_tables
from xlights.xsq_writer import EffectTemplate
from xlights.xml_io import add_effect
from tools.read_recovery_fseq import read_fseq

ROOT = Path(__file__).resolve().parents[1]
RGB_MODELS = (
    "HV3_IMPORT_Arches_2", "HV3_IMPORT_Tree", "HV3_IMPORT_Matrix",
    "NBH_RIGHT_SINGING_FACE_01_PANEL",
)
AC_MODEL = "Roof Lower white"


@pytest.mark.parametrize("configuration", ["rgb", "mixed", "original256"])
def test_native_channel_values(tmp_path, configuration):
    binary = os.environ.get("HELIX_XLIGHTS")
    if not binary:
        pytest.skip("Set HELIX_XLIGHTS to run the native renderer")
    folder = Path(os.environ.get("HELIX_COLOR_EVIDENCE", tmp_path)).resolve() / configuration
    folder.mkdir(exist_ok=True, parents=True)
    layout_file = ROOT / "xlights_rgbeffects.xml"
    targets = [AC_MODEL]
    if configuration != "original256":
        layout_file = ROOT / "helixville3/xlights_rgbeffects.xml"
        targets = list(RGB_MODELS)
        if configuration == "mixed":
            targets.append(AC_MODEL)
    layout = ET.parse(layout_file)
    inventory = {m.get("name"): m for m in layout.findall("./models/model")}
    if configuration == "rgb":
        for model in list(inventory.values()):
            if model.get("name") not in targets:
                layout.getroot().find("models").remove(model)
        groups = layout.getroot().find("modelGroups")
        if groups is not None:
            groups.clear()
    layout.write(folder / "xlights_rgbeffects.xml", encoding="utf-8")
    (folder / "xlights_networks.xml").write_text("<Networks/>")
    xsq = ET.parse(ROOT / "template.xsq")
    head = xsq.find("head")
    head.find("sequenceType").text = "Animation"
    head.find("sequenceDuration").text = "1.000"
    head.find("mediaFile").text = ""
    rows = xsq.find("ElementEffects")
    display = xsq.find("DisplayElements")
    rows.clear()
    display.clear()
    for name in targets:
        ET.SubElement(display, "Element", type="model", name=name, visible="1")
        layer = ET.SubElement(ET.SubElement(rows, "Element", type="model", name=name), "EffectLayer")
        for start, end, color in [(0, 400, "#FF0000"), (400, 700, "#0000FF"), (700, 900, "#FFFFFF")]:
            if name == AC_MODEL:
                color = "#FFFFFF"
            settings = "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100"
            add_effect(layer, start, end, "On", EffectTemplate(settings=settings, palette=f"C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1"))
    materialize_native_effect_tables(xsq.getroot())
    path = folder / "palette.xsq"
    xsq.write(path, encoding="utf-8", xml_declaration=True)
    output = path.with_suffix(".fseq")
    output.unlink(missing_ok=True)
    with (folder / "render.log").open("w") as log:
        subprocess.run([binary, "--headless", "-q", "-s", str(folder), "-od", str(folder), str(path)],
                       stdout=log, stderr=subprocess.STDOUT, timeout=180, check=True)
    frames, step = read_fseq(output)
    assert step == 50 and len(frames) == 20
    for name in targets:
        ch = int(inventory[name].get("StartChannel")) - 1
        if name == AC_MODEL:
            assert frames[2, ch] > 230 and frames[19, ch] == 0
        else:
            for frame, expected in [(2,(255,0,0)), (10,(0,0,255)), (16,(255,255,255)), (19,(0,0,0))]:
                assert tuple(frames[frame, ch:ch+3]) == expected, (name, frame)
