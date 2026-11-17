"""Conservative XML effect inventory for newly written xLights sequence artifacts.

Counts XML effect elements; never attributes them to a particular engine.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


def inventory_xsq_outputs(paths: Iterable[Path]) -> dict[str, object]:
    """Inspect only caller-supplied changed output paths, not source templates."""
    outputs: list[dict[str, object]] = []
    for supplied in paths:
        path = Path(supplied)
        if path.suffix.lower() != ".xsq":
            continue
        count = 0
        error = None
        try:
            for _, element in ET.iterparse(path, events=("end",)):
                if element.tag.rsplit("}", 1)[-1].lower() == "effect":
                    count += 1
                element.clear()
        except (OSError, ET.ParseError, ValueError) as exc:
            error = f"{type(exc).__name__}: {exc}"
        outputs.append({
            "path": str(path),
            "effect_element_count": count if error is None else None,
            "xml_parse_error": error,
        })
    return {
        "schema": "helix.xsq_effect_inventory.v1",
        "outputs": outputs,
        "total_effect_elements": sum(
            int(item["effect_element_count"]) for item in outputs
            if item["effect_element_count"] is not None
        ),
        "all_parsed": all(item["xml_parse_error"] is None for item in outputs),
        "engine_attribution_verified": False,
        "native_fseq_verified": False,
        "limitations": "XML element counts are not proof of native render, model targeting, or engine contribution.",
    }
