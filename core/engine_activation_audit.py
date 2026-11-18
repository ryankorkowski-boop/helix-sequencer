"""Evidence-based engine activation audit for a Helix sequencing run.

Distinguishes invocation, opt-outs, sidecar production, and actual promotion.
Never infers that an effect was exported merely because its planner ran.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


def build_engine_activation_audit(
    args: Sequence[str],
    orchestration: Any = None,
    *,
    completed: bool = False,
    failed: str | None = None,
) -> dict[str, Any]:
    flags = set(args)
    orchestrator_requested = "--no-effects-orchestrator" not in flags
    invoked = bool(getattr(orchestration, "invoked", False))
    sidecar = bool(getattr(orchestration, "xsq_written", False))
    promoted = bool(
        invoked and sidecar and bool(getattr(orchestration, "orchestrated_xsq_path", None))
        and "--promote-orchestrated-template" in flags
        and "--no-orchestrator-template-promotion" not in flags
    )
    source_sections_requested = "--orchestration-sections-json" in flags
    source_sections_validated = bool(invoked and source_sections_requested)
    synthetic_seed_only = bool(invoked and not source_sections_requested)
    synthetic_birdsong_hook_requested = bool(flags.intersection({
        "--enable-birdsong", "--birdsong", "--birdsong-enabled",
    }))
    engines: dict[str, Mapping[str, Any]] = {
        "nine_pass_orchestrator": {
            "requested": orchestrator_requested,
            "invoked": invoked,
            "status": ("disabled" if not orchestrator_requested else
                       "failed_or_unavailable" if orchestration is not None and not invoked else
                       "invoked" if invoked else "not_observed"),
            "sidecar_xsq_written": sidecar,
            "source_sections_requested": source_sections_requested,
            "source_sections_validated": source_sections_validated,
            "synthetic_seed_only": synthetic_seed_only,
            "input_intents": getattr(orchestration, "input_intents", None) if invoked else None,
            "final_intents": getattr(orchestration, "final_intents", None) if invoked else None,
            "placement_candidates": getattr(orchestration, "placement_count", None) if invoked else None,
            "effect_contract_placements": getattr(orchestration, "effect_contract_placement_count", None) if invoked else None,
            "orchestrated_sidecar_effects": getattr(orchestration, "xsq_effect_count", None) if invoked and sidecar else None,
            "placement_source": getattr(orchestration, "placement_source", None) if invoked else None,
            "promoted_to_renderer": promoted,
            "exported_effects_verified": False,
            "error": str(getattr(orchestration, "error", "") or ""),
        },
        "matrix_intelligence": {
            "requested": "--no-matrix-intelligence" not in flags,
            "invoked": None,
            "status": "disabled_by_flag" if "--no-matrix-intelligence" in flags else "unverified_in_engine",
            "exported_effects_verified": False,
        },
        "birdsong": {
            "requested": "--no-birdsong" not in flags,
            "invoked": None,
            "status": "disabled_by_flag" if "--no-birdsong" in flags else "unverified_in_engine",
            "exported_effects_verified": False,
        },
        "birdsong_post_run_hook": {
            "requested": synthetic_birdsong_hook_requested,
            "invoked": None,
            "status": "synthetic_diagnostic_hook_requested" if synthetic_birdsong_hook_requested else "not_requested",
            "real_audio_analysis_verified": False,
            "exported_effects_verified": False,
            "note": "Optional hook uses synthetic feature frames; do not count as song-derived Birdsong output.",
        },
        "spatial_mapping_planner": {
            "requested": None, "invoked": None, "status": "integration_unverified",
            "exported_effects_verified": False,
        },
        "effect_layering_planner": {
            "requested": None, "invoked": None, "status": "integration_unverified",
            "exported_effects_verified": False,
        },
    }
    return {
        "schema": "helix.engine_activation_audit.v1",
        "run_completed": completed,
        "run_error": failed,
        "engines": engines,
        "limitations": [
            "Flags do not prove engine invocation or successful placement.",
            "No effect-count reconciliation with final XSQ/FSEQ is available.",
            "Birdsong and matrix runtime enablement may differ from raw flags.",
            "Without validated --orchestration-sections-json, nine-pass intents use synthetic seed sections.",
            "Orchestration placement counts do not prove final renderer output.",
        ],
    }


def write_engine_activation_audit(path: Path, audit: Mapping[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path
