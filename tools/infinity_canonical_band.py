"""Import the repository's existing six-role canonical band into Infinity XML.

This is a native-format engineering export, not owner-approved visual proof.
"""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


def append_canonical_six_band(path: Path) -> dict:
    # Delay heavyweight optional graphics libraries until the band is requested.
    from models.canonical_native_band import ROLES, add_band
    from models.ultimate_showcase import Garden
    from tools.build_helpers.ultimate_showcase import model_xml

    garden = Garden(title="Helix Infinity Canonical Band", slug="Helix_Infinity_Band")
    performers = add_band(
        garden, prefix="HX_INFINITY_SNOW", position=(0, 0, -14),
        include_xylophonist=False, full_keyboard=True,
        native_extended_mouths=True,
    )
    actual_roles = {m.details.get("final_band_role") for m in performers}
    if len(performers) != 6 or actual_roles != set(ROLES):
        raise ValueError(f"Six-role canonical band requirement failed: {actual_roles}")
    tree = ET.parse(path)
    root = tree.getroot()
    models = root.find("models")
    groups = root.find("modelGroups")
    if models is None or groups is None:
        raise ValueError("Missing xLights root containers")
    next_channel = 150001
    for performer in performers:
        performer.start = next_channel
        next_channel += performer.channels
        if any(m.get("name") == performer.name for m in models.findall("model")):
            raise ValueError(f"Duplicate band model: {performer.name}")
        models.append(model_xml(performer))
    group = ",".join(m.name for m in performers)
    ET.SubElement(groups, "modelGroup", {"name": "HX_SNOWMAN_BAND", "models": group})
    ET.SubElement(groups, "modelGroup", {
        "name": "HX_SNOWMAN_VOCALS",
        "models": ",".join(m.name for m in performers if m.details["final_band_role"] in ("lead", "harmony")),
    })
    ET.SubElement(groups, "modelGroup", {
        "name": "HX_SNOWMAN_INSTRUMENTS",
        "models": ",".join(m.name for m in performers if m.details["final_band_role"] in ("drummer", "bass", "guitar", "piano")),
    })
    source_dir = Path(__file__).resolve().parents[1] / "fixtures/band_geometry/source"
    asset_dir = path.parent / "assets"
    asset_dir.mkdir(exist_ok=True)
    for name in ("drummer_idle.png", "drummerbg.png"):
        source = source_dir / name
        if source.is_file():
            shutil.copyfile(source, asset_dir / name)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return {
        "performer_count": len(performers),
        "roles": sorted(actual_roles),
        "model_names": [m.name for m in performers],
        "first_channel": 150001,
        "last_channel": next_channel - 1,
        "rgb_nodes": sum(m.channels // 3 for m in performers),
        "review_status": "NOT OWNER-APPROVED; real-vocal movement and native xLights geometry unverified",
    }
