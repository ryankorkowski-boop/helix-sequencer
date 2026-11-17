"""Conservative orchestration-sidecar versus changed-XSQ provenance comparison."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from core.xsq_effect_inventory import inventory_xsq_outputs


def reconcile_orchestration_xsq(
    report: Any,
    changed_xsq_paths: list[Path],
    *,
    promotion_requested: bool,
) -> dict[str, object]:
    """Never infer a renderer export from an orchestrated sidecar alone."""
    sidecar_raw = getattr(report, "orchestrated_xsq_path", None) if report else None
    sidecar = Path(sidecar_raw) if sidecar_raw else None
    sidecar_resolved = sidecar.resolve(strict=False) if sidecar else None
    changed_resolved = {Path(path).resolve(strict=False) for path in changed_xsq_paths}
    sidecar_changed_this_run = bool(sidecar_resolved and sidecar_resolved in changed_resolved)
    sidecar_inventory = (
        inventory_xsq_outputs([sidecar])
        if sidecar_changed_this_run and sidecar and sidecar.is_file()
        else None
    )
    final_candidates = [
        Path(path) for path in changed_xsq_paths
        if Path(path).resolve(strict=False) != sidecar_resolved
    ]
    final_inventory = inventory_xsq_outputs(final_candidates)
    final_outputs = final_inventory["outputs"]
    sidecar_outputs = sidecar_inventory["outputs"] if sidecar_inventory else []
    sidecar_count = (
        sidecar_outputs[0]["orchestrator_tagged_effects"] if sidecar_outputs else None
    )
    final_tagged_count = sum(
        int(row["orchestrator_tagged_effects"])
        for row in final_outputs if row["orchestrator_tagged_effects"] is not None
    )
    parsed_final_count = sum(row["xml_parse_error"] is None for row in final_outputs)
    return {
        "schema": "helix.orchestration_xsq_reconciliation.v1",
        "promotion_requested": promotion_requested,
        "orchestration_sidecar": str(sidecar) if sidecar else None,
        "sidecar_changed_this_run": sidecar_changed_this_run,
        "sidecar_tagged_effects": sidecar_count,
        "final_candidate_paths": [str(p) for p in final_candidates],
        "parsed_final_candidate_count": parsed_final_count,
        "final_candidate_tagged_effects": final_tagged_count if parsed_final_count else None,
        "tagged_provenance_in_final_candidate": bool(final_tagged_count),
        "native_fseq_verified": False,
        "limitations": (
            "Final candidates are changed XSQ paths other than the orchestration sidecar; "
            "they are not independently confirmed as the authoritative final render. "
            "A sidecar not observed as changed in this run is not counted; XML source tags are not native FSEQ or per-engine effect proof."
        ),
    }
