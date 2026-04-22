from __future__ import annotations

from dataclasses import dataclass

TASK_CATEGORIES = [
    "layout_setup",
    "model_groups",
    "submodels",
    "timing_marks",
    "beat_sync",
    "lyric_tracks",
    "singing_faces",
    "effects_usage",
    "render_styles",
    "buffer_styles",
    "pixel_mapping",
    "AC_channel_control",
    "WLED",
    "controllers",
    "networking",
    "preview",
    "video_export",
    "sequence_import",
    "sequence_conversion",
    "troubleshooting",
    "performance",
    "best_practices",
]


@dataclass(slots=True)
class TaskClassification:
    task_category: str
    xlights_area: str
    applicable_models: list[str]
    applicable_effects: list[str]
    helix_relevance: str
    needs_human_review: bool


_RULES: list[tuple[list[str], TaskClassification]] = [
    (
        ["model group", "group"],
        TaskClassification(
            task_category="model_groups",
            xlights_area="layout/model groups",
            applicable_models=["model_group"],
            applicable_effects=[],
            helix_relevance="Effect placement engine should support group-level application and model group routing.",
            needs_human_review=False,
        ),
    ),
    (
        ["submodel"],
        TaskClassification(
            task_category="submodels",
            xlights_area="layout/submodels",
            applicable_models=["submodel"],
            applicable_effects=[],
            helix_relevance="Helix should preserve submodel target paths so effects can be scoped to partial props.",
            needs_human_review=False,
        ),
    ),
    (
        ["timing mark", "timing track"],
        TaskClassification(
            task_category="timing_marks",
            xlights_area="timing tracks",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should store timing-track provenance but not assume effects remain linked to timing marks after placement.",
            needs_human_review=False,
        ),
    ),
    (
        ["beat", "latency", "display delay", "lead", "lag"],
        TaskClassification(
            task_category="beat_sync",
            xlights_area="timing sync",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should support beat lead/lag compensation curves.",
            needs_human_review=False,
        ),
    ),
    (
        ["lyric", "phoneme"],
        TaskClassification(
            task_category="lyric_tracks",
            xlights_area="lyrics/timing",
            applicable_models=["matrix", "faces"],
            applicable_effects=["lyric"],
            helix_relevance="Helix should map lyric segments to timing entries and optional face model targets.",
            needs_human_review=False,
        ),
    ),
    (
        ["singing face", "singing", "face"],
        TaskClassification(
            task_category="singing_faces",
            xlights_area="faces",
            applicable_models=["singing_face"],
            applicable_effects=["face"],
            helix_relevance="Helix should expose mouth-shape aware choreography presets and lyric alignment helpers.",
            needs_human_review=False,
        ),
    ),
    (
        ["render style"],
        TaskClassification(
            task_category="render_styles",
            xlights_area="effect rendering",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should preserve render-style intent in effect templates.",
            needs_human_review=False,
        ),
    ),
    (
        ["buffer style"],
        TaskClassification(
            task_category="buffer_styles",
            xlights_area="effect buffering",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should expose buffer-style options as first-class effect parameters.",
            needs_human_review=False,
        ),
    ),
    (
        ["pixel", "mapping"],
        TaskClassification(
            task_category="pixel_mapping",
            xlights_area="pixel mapping",
            applicable_models=["matrix", "props"],
            applicable_effects=[],
            helix_relevance="Helix should support coordinate-aware pixel routing and mapping diagnostics.",
            needs_human_review=False,
        ),
    ),
    (
        ["ac ", "dumb", "relay", "channel"],
        TaskClassification(
            task_category="AC_channel_control",
            xlights_area="ac channels",
            applicable_models=["ac_arch", "ac_channels"],
            applicable_effects=["on", "off", "intensity"],
            helix_relevance="Helix should enforce AC-safe effect families and channel-group controls.",
            needs_human_review=False,
        ),
    ),
    (
        ["wled"],
        TaskClassification(
            task_category="WLED",
            xlights_area="controllers/wled",
            applicable_models=["pixel_props"],
            applicable_effects=[],
            helix_relevance="Helix should include WLED-friendly channel mapping and packet-size heuristics.",
            needs_human_review=False,
        ),
    ),
    (
        ["controller", "e1.31", "ddp", "fpp"],
        TaskClassification(
            task_category="controllers",
            xlights_area="controller setup",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should validate controller protocol assumptions before export.",
            needs_human_review=False,
        ),
    ),
    (
        ["network", "multicast", "universe", "ip"],
        TaskClassification(
            task_category="networking",
            xlights_area="networking",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should include network sanity checks for universe ranges and addressing.",
            needs_human_review=False,
        ),
    ),
    (
        ["preview"],
        TaskClassification(
            task_category="preview",
            xlights_area="preview",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should retain preview-camera and model visibility hints for QA.",
            needs_human_review=False,
        ),
    ),
    (
        ["video export", "export video", "render video"],
        TaskClassification(
            task_category="video_export",
            xlights_area="export",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should preserve export profile presets and target frame-rate consistency.",
            needs_human_review=False,
        ),
    ),
    (
        ["import sequence", "import"],
        TaskClassification(
            task_category="sequence_import",
            xlights_area="sequence import",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should validate imported timing/effect assumptions and emit conversion notes.",
            needs_human_review=False,
        ),
    ),
    (
        ["convert", "conversion"],
        TaskClassification(
            task_category="sequence_conversion",
            xlights_area="sequence conversion",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should emit explicit conversion compatibility reports.",
            needs_human_review=False,
        ),
    ),
    (
        ["troubleshoot", "common mistake", "if this happens", "error", "fix"],
        TaskClassification(
            task_category="troubleshooting",
            xlights_area="troubleshooting",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should surface likely root causes and one-click remediation suggestions.",
            needs_human_review=False,
        ),
    ),
    (
        ["performance", "fps", "lag"],
        TaskClassification(
            task_category="performance",
            xlights_area="performance",
            applicable_models=[],
            applicable_effects=[],
            helix_relevance="Helix should budget effect complexity against render/performance targets.",
            needs_human_review=False,
        ),
    ),
]


def _infer_model_tags(text: str) -> list[str]:
    lowered = text.lower()
    models: list[str] = []
    if "arch" in lowered:
        if "ac" in lowered:
            models.append("ac_arch")
        if "pixel" in lowered:
            models.append("pixel_arch")
        if "reverse" in lowered:
            models.append("reverse_direction_arch")
        if not models:
            models.append("arch")
    if "megatree" in lowered or "mega tree" in lowered:
        models.append("megatree")
    if "matrix" in lowered:
        models.append("matrix")
    if "singing" in lowered and "face" in lowered:
        models.append("singing_face")
    return sorted(set(models))


def _infer_effect_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for token in ("chase", "wave", "morph", "bars", "on", "off"):
        if token in lowered:
            tags.append(token)
    return sorted(set(tags))


def classify_task_text(text: str) -> TaskClassification:
    lowered = (text or "").lower()
    for keys, classification in _RULES:
        if any(key in lowered for key in keys):
            models = sorted(set(classification.applicable_models + _infer_model_tags(lowered)))
            effects = sorted(set(classification.applicable_effects + _infer_effect_tags(lowered)))
            return TaskClassification(
                task_category=classification.task_category,
                xlights_area=classification.xlights_area,
                applicable_models=models,
                applicable_effects=effects,
                helix_relevance=classification.helix_relevance,
                needs_human_review=classification.needs_human_review,
            )

    return TaskClassification(
        task_category="best_practices",
        xlights_area="general",
        applicable_models=_infer_model_tags(lowered),
        applicable_effects=_infer_effect_tags(lowered),
        helix_relevance="Helix should treat this as advisory guidance and require review before automation.",
        needs_human_review=True,
    )
