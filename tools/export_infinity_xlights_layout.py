"""Export the Infinity spatial inventory to xLights layout XML.

Engineering candidate only: native xLights GUI/XSQ/FSEQ acceptance is a separate gate.
This uses the repository's established Poly Line + PointData scheme.
"""
from __future__ import annotations

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from tools.generate_infinity_showcase_geometry import rows
from tools.infinity_canonical_band import append_canonical_six_band

EXPECTED_PIXELS = 38928


def _family(name: str) -> str:
    if name.startswith("DoubleHelix"):
        return "HX_INFINITY_DOUBLE_HELIX"
    if name.startswith("Spiral"):
        return "HX_INFINITY_SPIRALS"
    if name == "PixelVolume":
        return "HX_INFINITY_PIXEL_VOLUME"
    if name.startswith("House"):
        return "HX_INFINITY_RESIDENTIAL"
    if name.startswith("Downtown"):
        return "HX_INFINITY_DOWNTOWN"
    if name.startswith("Megatree"):
        return "HX_INFINITY_MEGATREES"
    if name.startswith("Tunnel"):
        return "HX_INFINITY_TUNNELS"
    return "HX_INFINITY_PATHWAYS"


def _chunk(name: str, pixels: list[tuple]) -> list[tuple[str, list[tuple]]]:
    # A volumetric grid and large facades are segmented into readable
    # physical strings instead of connecting distant pixels into one wire.
    if name == "PixelVolume":
        step = 16
    elif name.startswith("Downtown"):
        step = 40
    elif "WindowMatrix" in name:
        step = 25
    else:
        step = len(pixels)
    return [(name if step == len(pixels) else f"{name}_{i//step+1:03d}", pixels[i:i+step])
            for i in range(0, len(pixels), step)]


def export_layout(output: Path, *, include_band: bool = True) -> dict:
    if len(rows) != EXPECTED_PIXELS:
        raise AssertionError(f"unexpected pixel inventory: {len(rows)}")
    output.mkdir(parents=True, exist_ok=True)
    root = ET.Element("xrgb")
    models = ET.SubElement(root, "models")
    groups = ET.SubElement(root, "modelGroups")
    families: dict[str, list[str]] = defaultdict(list)
    inventory = defaultdict(int)
    groups_by_name: dict[str, list[tuple]] = defaultdict(list)
    for r in rows:
        groups_by_name[r[0]].append(r)

    seen: set[str] = set()
    spans: list[tuple[int, int, str]] = []
    for source_name, pixels in groups_by_name.items():
        for name, chunk in _chunk(source_name, pixels):
            if name in seen:
                raise AssertionError(f"duplicate model: {name}")
            seen.add(name)
            lo = chunk[0][-1]
            hi = chunk[-1][-1] + 2
            if hi - lo + 1 != 3 * len(chunk):
                raise AssertionError(f"noncontiguous channels: {name}")
            spans.append((lo, hi, name))
            coords = ",".join(f"{p[3]},{p[4]},{p[5]}" for p in chunk)
            ET.SubElement(models, "model", {
                "name": "HX_INFINITY_" + name,
                "DisplayAs": "Poly Line",
                "LayoutGroup": "Default",
                "StringType": "RGB Nodes",
                "StartChannel": str(lo),
                "parm1": "1",
                "parm2": str(len(chunk)),
                "parm3": "1",
                "NumPoints": str(len(chunk)),
                "PointData": coords,
                "cPointData": "",
                "WorldPosX": "0", "WorldPosY": "0", "WorldPosZ": "0",
                "ScaleX": "1", "ScaleY": "1", "ScaleZ": "1",
                "PolyStrings": "1",
                "Antialias": "1", "PixelSize": "2",
            })
            families[_family(source_name)].append("HX_INFINITY_" + name)
            inventory[_family(source_name)] += len(chunk)

    # Native architectural and garden models, preserving the original addresses.
    for m in models.findall("model"):
        name = m.get("name", "")
        pts = [float(v) for v in m.get("PointData", "").split(",")]
        if not pts:
            continue
        if ("_Outline" in name or ("Downtown" in name and "_Facade" in name)
                or "WindowMatrix" in name or "PixelVolume_" in name):
            a, b = pts[:3], pts[-3:]
            m.set("DisplayAs", "Single Line")
            for axis, start, end in zip("XYZ", a, b):
                m.set("WorldPos"+axis, str(start))
                m.set(axis+"2", str(end-start))
        elif "PathArch" in name or "Tunnel" in name:
            a, b = pts[:3], pts[-3:]
            m.set("DisplayAs", "Arches")
            for axis, start, end in zip("XYZ", b, a):
                m.set("WorldPos"+axis, str(start))
                m.set(axis+"2", str(end-start))
            m.set("Height", "0.5")
            m.set("Angle", "0")
            m.set("arc", "180")
    # Explicit groups retain deterministic member ordering and expose roles.
    for prefix in ("House", "Downtown"):
        for i in range(1, 5 if prefix == "House" else 4):
            members = sorted("HX_INFINITY_"+n for n in seen if n.startswith(f"{prefix}{i}_"))
            if members:
                ET.SubElement(groups, "modelGroup", {"name": f"HX_INFINITY_{prefix.upper()}_{i:02d}", "models": ",".join(members)})
    roof = sorted("HX_INFINITY_"+n for n in seen if "_Outline" in n)
    ET.SubElement(groups, "modelGroup", {"name": "HX_INFINITY_ARCHITECTURE_ROOFLINES", "models": ",".join(roof)})
    for role in sorted({r[1] for r in rows}):
        sources = {r[0] for r in rows if r[1] == role}
        members = ["HX_INFINITY_"+n for n in sorted(seen) if n in sources or n.rsplit("_",1)[0] in sources]
        ET.SubElement(groups, "modelGroup", {"name": "HX_INFINITY_MUSIC_"+role.upper(), "models": ",".join(members)})

    # Sort by physical centroids, not lexical model names, for spatial routing.
    import math
    centers = {}
    for m in models.findall("model"):
        p = [float(v) for v in m.get("PointData").split(",")]
        centers[m.get("name")] = tuple(sum(p[i::3])/len(p[i::3]) for i in range(3))
    def route(label, key):
        ordered = sorted(centers, key=lambda n: (key(centers[n]), n))
        ET.SubElement(groups, "modelGroup", {"name": "HX_INFINITY_SPATIAL_"+label, "models": ",".join(ordered)})
    route("WEST_TO_EAST", lambda p: p[0])
    route("GROUND_TO_SKY", lambda p: p[1])
    route("FRONT_TO_BACK", lambda p: p[2])
    route("CENTER_OUT", lambda p: math.hypot(p[0], p[2]-18))
    route("CLOCKWISE_ORBIT", lambda p: -math.atan2(p[2]-18, p[0]))

    spans.sort()
    if spans[0][0] != 1 or spans[-1][1] != EXPECTED_PIXELS * 3:
        raise AssertionError("incorrect first/last address")
    for left, right in zip(spans, spans[1:]):
        if left[1] + 1 != right[0]:
            raise AssertionError(f"channel gap/overlap: {left} -> {right}")
    for group_name, members in families.items():
        ET.SubElement(groups, "modelGroup", {"name": group_name, "models": ",".join(members)})
    ET.SubElement(groups, "modelGroup", {
        "name": "HX_INFINITY_ALL_SPATIAL",
        "models": ",".join("HX_INFINITY_" + name for name in sorted(seen)),
    })
    # Native decorative inventory, using the existing Garden serializer.
    from models.ultimate_showcase import Garden
    from tools.build_helpers.ultimate_showcase import model_xml
    garden = Garden(title="Infinity native ornaments", slug="Infinity_Ornaments")
    for i, x in enumerate((-15, -2, 11, 24), 1):
        garden.star(f"HX_INFINITY_House{i}_Roof_Star", x, 9, 0, 1.5, "RESIDENTIAL")
        garden.circle(f"HX_INFINITY_House{i}_Door_Wreath", x, 2, -.2, 1.2, "RESIDENTIAL", display="Wreath")
        garden.tree(f"HX_INFINITY_House{i}_Garden_MiniTree", x-3, -2, 2.5, .7, 0, 8, 30, "RESIDENTIAL")
    for i, x in enumerate((-20, -10, 10, 20), 1):
        garden.tree(f"HX_INFINITY_Plaza_NativeSpiral_{i}", x, 23, 5, 1.4, 3, 4, 120, "PLAZA")
        garden.star(f"HX_INFINITY_Plaza_SpiralTopper_{i}", x, 5.7, 23, 1.2, "PLAZA")
    next_channel = EXPECTED_PIXELS*3+1
    decorative = []
    for m in garden.models:
        m.start = next_channel
        next_channel += m.channels
        models.append(model_xml(m))
        decorative.append(m.name)
    if next_channel > 150001:
        raise AssertionError("Decorative models overlap reserved band channels")
    ET.SubElement(groups, "modelGroup", {"name": "HX_INFINITY_NATIVE_ORNAMENTS", "models": ",".join(decorative)})
    for i in range(1, 5):
        group = next(g for g in groups if g.get("name") == f"HX_INFINITY_HOUSE_{i:02d}")
        group.set("models", group.get("models")+","+",".join(n for n in decorative if f"House{i}_" in n))
    path = output / "xlights_rgbeffects.xml"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    band_info = None
    if include_band:
        # Reuse original canonical six-role source with a real pianist;
        # visual owner approval is still mandatory.
        band_info = append_canonical_six_band(path)
    parsed = ET.parse(path).getroot()
    full_models = parsed.findall("./models/model")
    names = [m.get("name") for m in full_models]
    if len(set(names)) != len(names):
        raise AssertionError("duplicate XML names")
    note = {
        "schema": "helix.infinity.spatial.v1",
        "source": "tools/generate_infinity_showcase_geometry.py",
        "pixels_spatial": EXPECTED_PIXELS,
        "rgb_channels_spatial": EXPECTED_PIXELS * 3,
        "spatial_model_count": len(seen),
        "total_xml_model_count": len(full_models),
        "native_ornament_count": len(decorative),
        "native_ornament_channels": next_channel-EXPECTED_PIXELS*3-1,
        "family_pixel_counts": dict(inventory),
        "band_import": "models.canonical_native_band" if include_band else "none",
        "band_info": band_info,
        "band_verification": "UNAPPROVED: six canonical roles exported, visual/timing proof still required" if include_band else "band disabled",
        "native_xlights_gui_test": "NOT RUN",
        "native_fseq_test": "NOT RUN",
        "owner_approval": False,
    }
    (output / "infinity_manifest.json").write_text(json.dumps(note, indent=2) + "\n", encoding="utf-8")
    with (output / "infinity_pixel_geometry.csv").open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(["model","role","node","x_m","y_m","z_m","start_channel"])
        writer.writerows(rows)
    return note


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, default=Path("outputs/infinity_showcase"))
    cli.add_argument("--without-band", action="store_true")
    args = cli.parse_args()
    print(json.dumps(export_layout(args.output, include_band=not args.without_band), indent=2))


if __name__ == "__main__":
    main()
