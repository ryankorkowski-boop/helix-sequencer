from __future__ import annotations

import argparse
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


def _depth_bias(display_as: str) -> float:
    value = (display_as or "").strip().lower()
    if "matrix" in value:
        return 42.0
    if "tree" in value:
        return 55.0
    if "arch" in value or "cane" in value:
        return 26.0
    if "star" in value or "sphere" in value:
        return 38.0
    if "line" in value:
        return 18.0
    return 30.0


def _stable_name_seed(name: str) -> int:
    return sum(ord(ch) for ch in name) % 17


def _to_float(raw: str | None, default: float = 0.0) -> float:
    try:
        return float(raw or default)
    except (TypeError, ValueError):
        return default


def _fmt(value: float) -> str:
    return f"{value:.4f}"


def _controller_lines(networks_xml: Path) -> list[str]:
    try:
        root = ET.parse(networks_xml).getroot()
    except Exception:
        return ["Controller summary unavailable (failed to parse xlights_networks.xml)."]

    controllers = root.findall(".//controller")
    if not controllers:
        return ["No controller records found in xlights_networks.xml."]

    lines = [f"Controllers detected: {len(controllers)}"]
    for controller in controllers:
        unit = (controller.attrib.get("UnitId") or "?").strip()
        channels = (controller.attrib.get("NumChannels") or "?").strip()
        ctype = (controller.attrib.get("CntlrType") or "Unknown").strip()
        lines.append(f"- Unit {unit}: {ctype} ({channels} channels)")
    return lines


def build_helixville_3d_show_folder(
    *,
    source_layout_xml: Path,
    source_networks_xml: Path,
    source_keybindings_xml: Path | None,
    output_show_folder: Path,
) -> Path:
    output_show_folder.mkdir(parents=True, exist_ok=True)
    tree = ET.parse(source_layout_xml)
    root = tree.getroot()

    model_nodes = root.findall(".//models/model")
    for model in model_nodes:
        name = (model.attrib.get("name") or "").strip()
        display_as = model.attrib.get("DisplayAs") or ""
        x = _to_float(model.attrib.get("WorldPosX"))
        y = _to_float(model.attrib.get("WorldPosY"))
        z = _to_float(model.attrib.get("WorldPosZ"))
        seed = _stable_name_seed(name)

        # Introduce deterministic depth layering while preserving XY footprint.
        radial = ((abs(x) + abs(y)) % 240.0) / 240.0
        z_offset = ((seed - 8) * 9.0) + _depth_bias(display_as) * radial
        if "mega" in name.lower() or "matrix" in name.lower():
            z_offset += 28.0
        if "ac_" in name.lower() or "house" in name.lower():
            z_offset -= 16.0
        model.attrib["WorldPosZ"] = _fmt(z + z_offset)

        if "Z2" in model.attrib:
            z2 = _to_float(model.attrib.get("Z2"), z)
            model.attrib["Z2"] = _fmt(z2 + z_offset)

    for width in root.findall(".//previewWidth"):
        width.attrib["value"] = "1920"
    for height in root.findall(".//previewHeight"):
        height.attrib["value"] = "1080"

    out_layout = output_show_folder / "xlights_rgbeffects.xml"
    tree.write(out_layout, encoding="utf-8", xml_declaration=True)
    shutil.copy2(source_networks_xml, output_show_folder / "xlights_networks.xml")
    if source_keybindings_xml and source_keybindings_xml.exists():
        shutil.copy2(source_keybindings_xml, output_show_folder / "xlights_keybindings.xml")

    readme_lines = [
        "Helixville 3D Test Show Folder",
        "",
        "Use this folder as a dedicated show folder for 3D Helixville validation runs.",
        "Files included:",
        "- xlights_rgbeffects.xml (3D depth-adjusted test layout)",
        "- xlights_networks.xml (controller definitions)",
        "- xlights_keybindings.xml (copied when available)",
        "",
        "Controller summary:",
        *_controller_lines(output_show_folder / "xlights_networks.xml"),
        "",
        "This folder is generated for test sequencing and preview validation.",
    ]
    (output_show_folder / "START_HERE.txt").write_text("\n".join(readme_lines), encoding="utf-8")
    (output_show_folder / "controllers_info.txt").write_text(
        "\n".join(_controller_lines(output_show_folder / "xlights_networks.xml")),
        encoding="utf-8",
    )
    return out_layout


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Helixville 3D xLights test show folder.")
    parser.add_argument("--source-layout", required=True, help="Source xlights_rgbeffects.xml")
    parser.add_argument("--source-networks", required=True, help="Source xlights_networks.xml")
    parser.add_argument("--source-keybindings", help="Optional source xlights_keybindings.xml")
    parser.add_argument("--output-show-folder", required=True, help="Target show folder path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_layout = build_helixville_3d_show_folder(
        source_layout_xml=Path(args.source_layout),
        source_networks_xml=Path(args.source_networks),
        source_keybindings_xml=Path(args.source_keybindings) if args.source_keybindings else None,
        output_show_folder=Path(args.output_show_folder),
    )
    print(f"Created 3D Helixville layout: {out_layout}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
