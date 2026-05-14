from __future__ import annotations

import argparse
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_helpers.helixville4_full_band import FULL_BAND_SPECS, PerformerSpec, _custom_model, _runs
from tools.build_helpers.helixville4_visible_band import (
    VISIBLE_BAND_MODELS,
    VisibleBandModel,
    custom_model_for_visible_band,
)
from tools.write_helixville4_band_assets import write_band_assets


DEFAULT_OUTPUT_DIR = ROOT / "test_runs" / "helixia_layout_smoke_lightsouttheme" / "helixville4_band_model_exports"
SOURCE_VERSION = "2025.13"


def model_node_count(spec: PerformerSpec) -> int:
    return sum(part.count for part in spec.parts)


def build_xmodel_element(spec: PerformerSpec) -> ET.Element:
    node_count = model_node_count(spec)
    model = ET.Element(
        "custommodel",
        {
            "name": spec.model_name,
            "parm1": str(spec.width),
            "parm2": str(spec.height),
            "Depth": "1",
            "StringType": "RGB Nodes",
            "Transparency": "0",
            "PixelSize": "2",
            "ModelBrightness": "0",
            "Antialias": "1",
            "StartSide": "B",
            "Dir": "L",
            "StrandNames": "",
            "NodeNames": "",
            "LayoutGroup": "HX_SNOWMAN_BAND",
            "CustomModel": _custom_model(spec),
            "CustomModelCompressed": "",
            "SourceVersion": SOURCE_VERSION,
            "HelixVisualTarget": spec.visual_target,
            "HelixImplementationState": spec.state,
            "HelixAnimationStates": ",".join(spec.animation_states),
            "HelixNodeCount": str(node_count),
        },
    )
    ET.SubElement(
        model,
        "subModel",
        {
            "name": "DefaultRenderBuffer",
            "layout": "horizontal",
            "type": "ranges",
            "line0": f"1-{node_count}",
        },
    )
    for name, start, end in _runs(spec.parts, spec.model_name):
        ET.SubElement(
            model,
            "subModel",
            {
                "name": name,
                "layout": "horizontal",
                "type": "ranges",
                "line0": f"{start}-{end}",
                "HelixPixelCount": str(end - start + 1),
            },
        )
    return model


def write_xmodel(spec: PerformerSpec, output_dir: Path) -> Path:
    path = output_dir / f"{spec.model_name}.xmodel"
    tree = ET.ElementTree(build_xmodel_element(spec))
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path


def _visible_node_count(spec: VisibleBandModel) -> int:
    return sum(count for _, count in spec.submodels)


def build_visible_xmodel_element(spec: VisibleBandModel) -> ET.Element:
    node_count = _visible_node_count(spec)
    model = ET.Element(
        "custommodel",
        {
            "name": spec.name,
            "parm1": str(spec.width),
            "parm2": str(spec.height),
            "Depth": "1",
            "StringType": "RGB Nodes",
            "Transparency": "0",
            "PixelSize": "3",
            "ModelBrightness": "0",
            "Antialias": "1",
            "StartSide": "B",
            "Dir": "L",
            "StrandNames": "",
            "NodeNames": "",
            "LayoutGroup": "HX_SNOWMAN_BAND_SEQUENCE_TARGETS",
            "CustomModel": custom_model_for_visible_band(spec),
            "CustomModelCompressed": "",
            "SourceVersion": SOURCE_VERSION,
            "HelixImplementationState": "split_sequence_target_visible_v1",
            "HelixNodeCount": str(node_count),
            "HelixImportNote": "Exact Helixville4 sequence target model name; use this over the legacy combined performer export.",
        },
    )
    ET.SubElement(
        model,
        "subModel",
        {
            "name": "DefaultRenderBuffer",
            "layout": "horizontal",
            "type": "ranges",
            "line0": f"1-{node_count}",
        },
    )
    cursor = 1
    for name, count in spec.submodels:
        ET.SubElement(
            model,
            "subModel",
            {
                "name": name,
                "layout": "horizontal",
                "type": "ranges",
                "line0": f"{cursor}-{cursor + count - 1}",
                "HelixPixelCount": str(count),
            },
        )
        cursor += count
    return model


def write_visible_xmodel(spec: VisibleBandModel, output_dir: Path) -> Path:
    path = output_dir / f"{spec.name}.xmodel"
    tree = ET.ElementTree(build_visible_xmodel_element(spec))
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path


def copy_show_support_files(output_dir: Path) -> dict[str, str]:
    copied: dict[str, str] = {}
    sources = {
        "xlights_rgbeffects.xml": ROOT / "helixville4" / "xlights_rgbeffects.xml",
        "xlights_keybindings.xml": ROOT / "helixville4" / "xlights_keybindings.xml",
    }
    for name, source in sources.items():
        if source.exists():
            dest = output_dir / name
            shutil.copy2(source, dest)
            copied[name] = str(dest)
    return copied


def write_readme(output_dir: Path, manifest: dict[str, object]) -> Path:
    path = output_dir / "README_IMPORT_BAND_MODELS.txt"
    model_lines = "\n".join(f"- {model['xmodel']}" for model in manifest["models"])  # type: ignore[index]
    target_lines = "\n".join(f"- {model['xmodel']}" for model in manifest["sequence_target_models"])  # type: ignore[index]
    path.write_text(
        "Helixville4 Snowman Band xLights Model Exports\n"
        "================================================\n\n"
        "For the existing Helixville4 sequences, import the sequence_target_xmodels first.\n"
        "Those names match the active sequence rows: *_BODY and *_INSTRUMENT.\n\n"
        "Sequence target models:\n"
        f"{target_lines}\n\n"
        "The legacy combined performer models are included only as reference/full-performer exports.\n"
        "They will not replace the active split rows in the current sequences unless the sequences\n"
        "are retargeted.\n\n"
        "Use the Helixville4 show folder/layout, not the allmodels layout, or existing\n"
        "Helixville4 sequences will play audio with no visible model matches.\n\n"
        "Legacy combined models:\n"
        f"{model_lines}\n\n"
        "If xLights already has a placeholder with the same name, remove/replace that placeholder\n"
        "or use the patched xlights_rgbeffects.xml in the Helixville4 show folder.\n",
        encoding="utf-8",
    )
    return path


def export_band_xmodels(output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> dict[str, object]:
    out_dir = Path(output_dir)
    xmodel_dir = out_dir / "xmodels"
    sequence_target_dir = out_dir / "sequence_target_xmodels"
    xmodel_dir.mkdir(parents=True, exist_ok=True)
    sequence_target_dir.mkdir(parents=True, exist_ok=True)

    models: list[dict[str, object]] = []
    for spec in FULL_BAND_SPECS:
        path = write_xmodel(spec, xmodel_dir)
        models.append(
            {
                "model_name": spec.model_name,
                "xmodel": str(path),
                "node_count": model_node_count(spec),
                "submodel_count": len(spec.parts) + 1,
                "animation_states": list(spec.animation_states),
            }
        )
    sequence_target_models: list[dict[str, object]] = []
    for spec in VISIBLE_BAND_MODELS:
        path = write_visible_xmodel(spec, sequence_target_dir)
        sequence_target_models.append(
            {
                "model_name": spec.name,
                "xmodel": str(path),
                "node_count": _visible_node_count(spec),
                "submodel_count": len(spec.submodels) + 1,
                "role": spec.role,
                "sequence_target": True,
            }
        )

    assets = write_band_assets(out_dir / "svg_reference_assets")
    support_files = copy_show_support_files(out_dir)
    manifest: dict[str, object] = {
        "schema": "helixville4.band_xmodel_exports.v1",
        "output_dir": str(out_dir),
        "model_count": len(models),
        "models": models,
        "sequence_target_model_count": len(sequence_target_models),
        "sequence_target_models": sequence_target_models,
        "svg_reference_assets": assets,
        "show_support_files": support_files,
        "import_note": "Use sequence_target_xmodels for current Helixville4 sequences; allmodels and legacy combined exports will not bind split sequence rows.",
    }
    manifest_path = out_dir / "helixville4_band_xmodel_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme_path = write_readme(out_dir, manifest)
    manifest["manifest"] = str(manifest_path)
    manifest["readme"] = str(readme_path)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export Helixville4 snowman band members as importable xLights .xmodel files.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = export_band_xmodels(args.output_dir)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
