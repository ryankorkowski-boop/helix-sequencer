from __future__ import annotations

import json
import shutil
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from helix_intent.xlights_contract_validator import validate_xlights_effect_contract_file

AUTO_LAYER_NAME = "AUTO_Helix_Orchestrated"
DEFAULT_PALETTE = ("#FFFFFF", "#00FFFF", "#FF00FF")


@dataclass(frozen=True)
class XsqTemplateWriteReport:
    schema: str = "helix.xsq_template_writer.v1"
    wrote_sequence: bool = False
    template_path: str = ""
    output_xsq: str = ""
    sidecar_json: str = ""
    effect_count: int = 0
    native_effect_count: int = 0
    contract_effect_count: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _placement_palette(placement: Mapping[str, Any]) -> tuple[str, str, str]:
    raw = placement.get("palette")
    if isinstance(raw, Sequence) and not isinstance(raw, str):
        colors = [str(item).strip() for item in raw if str(item).strip()]
        if colors:
            return tuple((colors + list(DEFAULT_PALETTE))[:3])  # type: ignore[return-value]
    return DEFAULT_PALETTE


def _palette_settings(placement: Mapping[str, Any]) -> str:
    color1, color2, color3 = _placement_palette(placement)
    return f"C_BUTTON_Palette1={color1},C_BUTTON_Palette2={color2},C_BUTTON_Palette3={color3}"


def _append_helix_contract_node(root: ET.Element, contract: Mapping[str, Any]) -> int:
    existing = root.find("HelixEffectContract")
    if existing is not None:
        root.remove(existing)
    node = ET.SubElement(root, "HelixEffectContract", {"schema": "helix.xlights_effect_contract.v1"})
    count = 0
    for placement in list(contract.get("effect_placements", []) or []):
        if not isinstance(placement, Mapping):
            continue
        color1, color2, color3 = _placement_palette(placement)
        ET.SubElement(
            node,
            "EffectPlacement",
            {
                "startTime": str(placement.get("start_time", "")),
                "endTime": str(placement.get("end_time", "")),
                "targetModel": str(placement.get("target_model", "")),
                "effectName": str(placement.get("effect_name", "")),
                "renderStyle": str(placement.get("render_style", "")),
                "brightnessCap": str(placement.get("brightness_cap", "")),
                "sourceVisualIntentId": str(placement.get("source_visual_intent_id", "")),
                "sourceEffectFamily": str(placement.get("source_effect_family", "")),
                "colorStrategy": str(placement.get("color_strategy", "")),
                "curveStrategy": str(placement.get("curve_strategy", "")),
                "palette1": color1,
                "palette2": color2,
                "palette3": color3,
            },
        )
        count += 1
    return count


def _find_or_create_element_effects(root: ET.Element) -> ET.Element:
    for child in root.iter():
        if child.tag.endswith("ElementEffects"):
            return child
    return ET.SubElement(root, "ElementEffects")


def _find_or_create_model_element(element_effects: ET.Element, model_name: str) -> ET.Element:
    for element in element_effects.findall("Element"):
        if element.get("name") == model_name or element.get("Name") == model_name:
            return element
    return ET.SubElement(element_effects, "Element", {"type": "model", "name": model_name})


def _find_or_create_layer(model_element: ET.Element) -> ET.Element:
    for layer in model_element.findall("EffectLayer"):
        if layer.get("name") == AUTO_LAYER_NAME or layer.get("Name") == AUTO_LAYER_NAME:
            return layer
    return ET.SubElement(model_element, "EffectLayer", {"name": AUTO_LAYER_NAME, "visible": "1"})


def _clear_auto_layer(layer: ET.Element) -> None:
    for child in list(layer):
        if child.tag.endswith("Effect"):
            layer.remove(child)


def _seconds_to_ms(value: object) -> int:
    try:
        return int(round(float(value) * 1000.0))
    except (TypeError, ValueError):
        return 0


def _native_settings(placement: Mapping[str, Any]) -> str:
    brightness = placement.get("brightness_cap", 0.62)
    family = placement.get("source_effect_family", "")
    curve = placement.get("curve_strategy", "section_envelope")
    color_strategy = placement.get("color_strategy", "default")
    return (
        f"E_CHECKBOX_OverlayBkg=0,E_SLIDER_Brightness={brightness},"
        f"HELIX_Family={family},HELIX_Curve={curve},HELIX_ColorStrategy={color_strategy}"
    )


def _append_native_effect_rows(root: ET.Element, contract: Mapping[str, Any]) -> int:
    element_effects = _find_or_create_element_effects(root)
    layers_by_model: dict[str, ET.Element] = {}
    count = 0
    for placement in list(contract.get("effect_placements", []) or []):
        if not isinstance(placement, Mapping):
            continue
        model_name = str(placement.get("target_model", "")).strip()
        effect_name = str(placement.get("effect_name", "On")).strip() or "On"
        if not model_name:
            continue
        if model_name not in layers_by_model:
            element = _find_or_create_model_element(element_effects, model_name)
            layer = _find_or_create_layer(element)
            _clear_auto_layer(layer)
            layers_by_model[model_name] = layer
        start_ms = _seconds_to_ms(placement.get("start_time"))
        end_ms = max(start_ms + 50, _seconds_to_ms(placement.get("end_time")))
        ET.SubElement(
            layers_by_model[model_name],
            "Effect",
            {
                "name": effect_name,
                "startTime": str(start_ms),
                "endTime": str(end_ms),
                "settings": _native_settings(placement),
                "palette": _palette_settings(placement),
                "source": "HelixOrchestrator",
                "sourceVisualIntentId": str(placement.get("source_visual_intent_id", "")),
                "sourceEffectFamily": str(placement.get("source_effect_family", "")),
                "sourceColorStrategy": str(placement.get("color_strategy", "default")),
                "sourceCurveStrategy": str(placement.get("curve_strategy", "section_envelope")),
            },
        )
        count += 1
    return count


def write_xsq_from_template(
    *,
    template_path: str | Path,
    effect_contract_json: str | Path,
    output_xsq: str | Path,
    report_path: str | Path | None = None,
) -> XsqTemplateWriteReport:
    template = Path(template_path)
    contract_path = Path(effect_contract_json)
    output = Path(output_xsq)
    sidecar = Path(report_path) if report_path else output.with_suffix(output.suffix + ".helix-render-report.json")

    errors: list[str] = []
    warnings: list[str] = []
    if not template.exists():
        errors.append(f"Missing template XSQ: {template}")
    if not contract_path.exists():
        errors.append(f"Missing xLights effect contract JSON: {contract_path}")
    if errors:
        report = XsqTemplateWriteReport(
            template_path=str(template),
            output_xsq=str(output),
            sidecar_json=str(sidecar),
            warnings=warnings,
            errors=errors,
        )
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    validation = validate_xlights_effect_contract_file(contract_path)
    if not validation.passed:
        errors.extend(validation.errors)
        report = XsqTemplateWriteReport(
            template_path=str(template),
            output_xsq=str(output),
            sidecar_json=str(sidecar),
            warnings=validation.warnings,
            errors=errors,
        )
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    contract_payload = json.loads(contract_path.read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        tree = ET.parse(template)
        root = tree.getroot()
        contract_effect_count = _append_helix_contract_node(root, contract_payload)
        native_effect_count = _append_native_effect_rows(root, contract_payload)
        tree.write(output, encoding="utf-8", xml_declaration=True)
    except ET.ParseError:
        shutil.copyfile(template, output)
        contract_effect_count = len(list(contract_payload.get("effect_placements", []) or []))
        native_effect_count = 0
        warnings.append("Template could not be XML-parsed; copied template unchanged and wrote sidecar report only.")

    report = XsqTemplateWriteReport(
        wrote_sequence=True,
        template_path=str(template),
        output_xsq=str(output),
        sidecar_json=str(sidecar),
        effect_count=native_effect_count or contract_effect_count,
        native_effect_count=native_effect_count,
        contract_effect_count=contract_effect_count,
        warnings=warnings + validation.warnings,
        errors=[],
    )
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
