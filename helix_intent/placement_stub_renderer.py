from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from helix_intent.render_gate import evaluate_render_permission


@dataclass(frozen=True)
class PlacementStubRenderReport:
    schema: str = "helix.placement_stub_render.v1"
    rendered: bool = False
    output_xml: str = ""
    output_report: str = ""
    placement_count: int = 0
    skipped_reason: str = ""
    permission: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe_attr(value: object) -> str:
    return str(value or "")


def render_placement_stub_xml(
    placement_plan: Mapping[str, Any],
    output_dir: str | Path,
    *,
    minimum_quality_score: float = 0.6,
) -> PlacementStubRenderReport:
    """Render a reviewable XML stub for placement plans.

    This is intentionally not the final xLights effect renderer. It writes a
    deterministic XML contract showing what would be placed, after validation and
    quality gates pass. The heavy renderer can later consume the same plan.
    """
    permission = evaluate_render_permission(placement_plan, minimum_quality_score=minimum_quality_score)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_xml = out_dir / "placement_stub.xml"
    output_report = out_dir / "placement_stub_report.json"

    if not permission.allowed:
        report = PlacementStubRenderReport(
            rendered=False,
            output_xml=str(output_xml),
            output_report=str(output_report),
            placement_count=0,
            skipped_reason="render_permission_blocked",
            permission=permission.to_dict(),
        )
        output_report.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    root = ET.Element("helixPlacementStub", {"schema": "helix.placement_stub.v1"})
    placements_el = ET.SubElement(root, "placements")
    placements = list(placement_plan.get("prop_effect_intents", []) or [])
    for index, placement in enumerate(placements, start=1):
        if not isinstance(placement, Mapping):
            continue
        ET.SubElement(
            placements_el,
            "placement",
            {
                "index": str(index),
                "visualIntentId": _safe_attr(placement.get("visual_intent_id")),
                "targetProp": _safe_attr(placement.get("target_prop")),
                "targetRole": _safe_attr(placement.get("target_role")),
                "effectFamily": _safe_attr(placement.get("effect_family")),
                "renderStyle": _safe_attr(placement.get("render_style")),
                "curveType": _safe_attr(placement.get("curve_type")),
                "brightnessCap": _safe_attr(placement.get("brightness_cap")),
                "confidence": _safe_attr(placement.get("confidence")),
            },
        )

    ET.ElementTree(root).write(output_xml, encoding="utf-8", xml_declaration=True)
    report = PlacementStubRenderReport(
        rendered=True,
        output_xml=str(output_xml),
        output_report=str(output_report),
        placement_count=len(placements),
        permission=permission.to_dict(),
    )
    output_report.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
