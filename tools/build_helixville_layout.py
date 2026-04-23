from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLMODELS_LAYOUT = ROOT / "allmodels" / "xlights_rgbeffects.xml"
DEFAULT_ALLMODELS_XBKP = ROOT / "allmodels" / "xlights_rgbeffects.xbkp"
DEFAULT_GPS_LAYOUT = ROOT / "xlights_rgbeffects.xml"
DEFAULT_GPS_XBKP = ROOT / "xlights_rgbeffects.xbkp"


@dataclass(frozen=True)
class DistrictPlan:
    district: str
    target_z: float


def _parse_float(value: str | None, fallback: float = 0.0) -> float:
    try:
        return float(value if value is not None else fallback)
    except Exception:
        return fallback


def _parse_start_channel(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", value)
    if not match:
        return None
    try:
        return int(match.group(0))
    except Exception:
        return None


def _is_ac_reference_model(model: ET.Element) -> bool:
    string_type = str(model.attrib.get("StringType", "")).lower()
    display_as = str(model.attrib.get("DisplayAs", "")).lower()
    if "single color" in string_type:
        return True
    if display_as in {"single line", "custom"} and "single" in string_type:
        return True
    start_channel = _parse_start_channel(model.attrib.get("StartChannel"))
    if start_channel is not None and 1 <= start_channel <= 256:
        return True
    return False


def _classify_model(model: ET.Element, gps_model_names: set[str]) -> DistrictPlan:
    name = str(model.attrib.get("name", "")).lower()
    string_type = str(model.attrib.get("StringType", "")).lower()
    display_as = str(model.attrib.get("DisplayAs", "")).lower()

    if name in gps_model_names:
        if _is_ac_reference_model(model):
            return DistrictPlan("gps_house_ac", 0.0)
        return DistrictPlan("gps_house_core", 0.0)

    if name.startswith("nbh_right") or "right_neighbor" in name:
        return DistrictPlan("neighbor_right", 240.0)
    if name.startswith("nbh_left") or "left_neighbor" in name:
        return DistrictPlan("neighbor_left", -240.0)
    if "single color" in string_type or "dumb" in string_type:
        return DistrictPlan("gps_house_ac", 0.0)
    if any(token in name for token in ("whole_house", "all_red", "all_white", "all_green", "garage", "blvd", "linden")):
        return DistrictPlan("gps_house_core", 0.0)
    if any(token in name for token in ("matrix", "video", "image", "text", "panel")):
        return DistrictPlan("village_matrix", 140.0)
    if any(token in name for token in ("spinner", "pinwheel", "sphere", "spiral", "fan")):
        return DistrictPlan("village_motion", 180.0)
    if any(token in name for token in ("mega", "tree", "arches", "arch", "line")):
        return DistrictPlan("village_structures", 95.0)
    if any(token in name for token in ("cane", "star", "snowflake")):
        return DistrictPlan("village_accents", 70.0)
    if display_as in {"single line", "tree 360", "tree 180"}:
        return DistrictPlan("village_structures", 95.0)
    return DistrictPlan("village_misc", 40.0)


def _discover_source_layout(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    if DEFAULT_ALLMODELS_LAYOUT.exists():
        return DEFAULT_ALLMODELS_LAYOUT
    return DEFAULT_GPS_LAYOUT


def _discover_gps_layout(explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit if explicit.exists() else None
    if DEFAULT_GPS_LAYOUT.exists():
        return DEFAULT_GPS_LAYOUT
    return None


def _discover_source_xbkp(layout_path: Path) -> Path | None:
    if layout_path.name.lower().endswith(".xbkp"):
        return layout_path
    same_folder = layout_path.with_suffix(".xbkp")
    if same_folder.exists():
        return same_folder
    if DEFAULT_ALLMODELS_XBKP.exists():
        return DEFAULT_ALLMODELS_XBKP
    if DEFAULT_GPS_XBKP.exists():
        return DEFAULT_GPS_XBKP
    return None


def _load_gps_reference(gps_layout: Path | None) -> dict[str, tuple[float, float, float]]:
    if gps_layout is None or not gps_layout.exists():
        return {}
    tree = ET.parse(gps_layout)
    root = tree.getroot()
    reference: dict[str, tuple[float, float, float]] = {}
    for model in root.findall(".//model"):
        name = str(model.attrib.get("name", "")).strip().lower()
        if not name:
            continue
        if not _is_ac_reference_model(model):
            continue
        x = _parse_float(model.attrib.get("WorldPosX"), 0.0)
        y = _parse_float(model.attrib.get("WorldPosY"), 0.0)
        z = _parse_float(model.attrib.get("WorldPosZ"), 0.0)
        reference[name] = (x, y, z)
    return reference


def build_helixville_layout(source_layout: Path, output_dir: Path, gps_layout: Path | None = None) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    layout_out = output_dir / "xlights_rgbeffects.xml"
    backup_out = output_dir / "xlights_rgbeffects.source_backup.xml"
    metadata_out = output_dir / "helixville_manifest.json"
    notes_out = output_dir / "HELIXVILLE_LAYOUT_NOTES.txt"

    tree = ET.parse(source_layout)
    root = tree.getroot()

    models = root.findall(".//model")
    district_counts: Counter[str] = Counter()
    updates = 0
    gps_anchors_applied = 0
    z_min = 10**9
    z_max = -(10**9)
    gps_reference = _load_gps_reference(gps_layout)
    gps_model_names = set(gps_reference.keys())

    for model in models:
        model_name = str(model.attrib.get("name", "")).strip().lower()
        district = _classify_model(model, gps_model_names)
        existing_z = _parse_float(model.attrib.get("WorldPosZ"), 0.0)
        if model_name in gps_reference:
            anchor_x, anchor_y, _anchor_z = gps_reference[model_name]
            model.attrib["WorldPosX"] = f"{anchor_x:.4f}"
            model.attrib["WorldPosY"] = f"{anchor_y:.4f}"
            gps_anchors_applied += 1
        if district.district.startswith("gps_house"):
            target_z = district.target_z
        else:
            target_z = district.target_z + (existing_z * 0.20)
        model.attrib["WorldPosZ"] = f"{target_z:.4f}"
        district_counts[district.district] += 1
        updates += 1
        z_min = min(z_min, target_z)
        z_max = max(z_max, target_z)

    tree.write(layout_out, encoding="utf-8", xml_declaration=True)
    shutil.copy2(source_layout, backup_out)

    source_xbkp = _discover_source_xbkp(source_layout)
    xbkp_out = None
    if source_xbkp is not None and source_xbkp.exists():
        xbkp_out = output_dir / "xlights_rgbeffects.xbkp"
        shutil.copy2(source_xbkp, xbkp_out)

    manifest = {
        "layout_name": "helixville",
        "source_layout": str(source_layout),
        "gps_layout": str(gps_layout) if gps_layout is not None else "",
        "output_layout": str(layout_out),
        "output_xbkp": str(xbkp_out) if xbkp_out is not None else "",
        "model_count": len(models),
        "updated_model_count": updates,
        "gps_anchor_model_count": len(gps_reference),
        "gps_anchors_applied": gps_anchors_applied,
        "district_counts": dict(sorted(district_counts.items(), key=lambda item: item[0])),
        "z_range": {"min": round(float(z_min), 4), "max": round(float(z_max), 4)},
        "notes": [
            "Helixville is seeded from GP's House + allmodels neighbors when present.",
            "GP core AC-focused models remain on Z=0 as layout reference anchors.",
            "Neighbor and showcase districts are depth-layered for 3D validation.",
        ],
    }
    metadata_out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    notes = [
        "HELIXVILLE TEST LAYOUT",
        "",
        f"Source layout: {source_layout}",
        f"Output layout: {layout_out}",
        "",
        "Intent:",
        "- Preserve GP's House core reference anchors on baseline depth.",
        "- Keep allmodels coverage and neighbor showcase models.",
        "- Apply deterministic Z-layering so 3D testing and camera passes are meaningful.",
        "",
        "Generated district model counts:",
    ]
    for district, count in sorted(district_counts.items(), key=lambda item: item[0]):
        notes.append(f"- {district}: {count}")
    notes_out.write_text("\n".join(notes) + "\n", encoding="utf-8")

    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Helixville 3D test layout from allmodels / GP sources.")
    parser.add_argument("--source-layout", help="Optional source xlights_rgbeffects.xml path")
    parser.add_argument("--gps-layout", help="Optional GP baseline xlights_rgbeffects.xml path")
    parser.add_argument("--output-dir", default=str(ROOT / "helixville"), help="Helixville show folder output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_layout = _discover_source_layout(Path(args.source_layout).resolve() if args.source_layout else None)
    if not source_layout.exists():
        raise SystemExit(f"Source layout not found: {source_layout}")
    gps_layout = _discover_gps_layout(Path(args.gps_layout).resolve() if args.gps_layout else None)
    output_dir = Path(args.output_dir).resolve()
    manifest = build_helixville_layout(source_layout, output_dir, gps_layout=gps_layout)
    print(f"Helixville layout created: {manifest['output_layout']}")
    print(f"Models updated: {manifest['updated_model_count']}")
    print(f"GP anchors applied: {manifest['gps_anchors_applied']}")
    print(f"Z range: {manifest['z_range']['min']} .. {manifest['z_range']['max']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
