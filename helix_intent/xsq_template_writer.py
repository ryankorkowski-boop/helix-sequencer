from __future__ import annotations

import json
import shutil
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from helix_intent.xlights_contract_validator import validate_xlights_effect_contract_file


@dataclass(frozen=True)
class XsqTemplateWriteReport:
    schema: str = "helix.xsq_template_writer.v1"
    wrote_sequence: bool = False
    template_path: str = ""
    output_xsq: str = ""
    sidecar_json: str = ""
    effect_count: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _append_helix_contract_node(root: ET.Element, contract: Mapping[str, Any]) -> int:
    # Keep this as an explicit Helix extension node. It preserves the original
    # template shape and gives future import/render logic deterministic data.
    existing = root.find("HelixEffectContract")
    if existing is not None:
        root.remove(existing)
    node = ET.SubElement(root, "HelixEffectContract", {"schema": "helix.xlights_effect_contract.v1"})
    count = 0
    for placement in list(contract.get("effect_placements", []) or []):
        if not isinstance(placement, Mapping):
            continue
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
        effect_count = _append_helix_contract_node(root, contract_payload)
        tree.write(output, encoding="utf-8", xml_declaration=True)
    except ET.ParseError:
        # Some legacy/template files may contain xLights XML that ElementTree
        # cannot preserve safely. In that case, copy the template and store the
        # render contract in the sidecar only instead of corrupting the template.
        shutil.copyfile(template, output)
        effect_count = len(list(contract_payload.get("effect_placements", []) or []))
        warnings.append("Template could not be XML-parsed; copied template unchanged and wrote sidecar report only.")

    report = XsqTemplateWriteReport(
        wrote_sequence=True,
        template_path=str(template),
        output_xsq=str(output),
        sidecar_json=str(sidecar),
        effect_count=effect_count,
        warnings=warnings + validation.warnings,
        errors=[],
    )
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
