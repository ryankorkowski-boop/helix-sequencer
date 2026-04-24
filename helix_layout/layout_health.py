from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from core import model_parser as xmp
from core import spatial_scene
from helix_layout.anchor_points import detect_anchor_points
from helix_layout.submodel_recommender import recommend_submodels


@dataclass
class LayoutHealthReport:
    missing_coordinates: list[str] = field(default_factory=list)
    missing_groups: list[str] = field(default_factory=list)
    bad_group_order: list[str] = field(default_factory=list)
    orphan_models: list[str] = field(default_factory=list)
    empty_groups: list[str] = field(default_factory=list)
    duplicate_names: list[str] = field(default_factory=list)
    confusing_names: list[str] = field(default_factory=list)
    no_center_anchor: bool = False
    AC_props_in_pixel_groups: list[str] = field(default_factory=list)
    matrix_in_whole_house_group_warning: list[str] = field(default_factory=list)
    no_singing_face_mapping: list[str] = field(default_factory=list)
    no_submodels_for_complex_props: list[str] = field(default_factory=list)
    low_density_props_targeted_by_high_detail_effects: list[str] = field(default_factory=list)
    symmetry_errors: list[str] = field(default_factory=list)
    render_cost_risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    severity_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_layout_health_report(layout_path: Path) -> LayoutHealthReport:
    parsed = xmp.parse_layout(layout_path)
    scene = spatial_scene.build_scene(parsed)
    report = LayoutHealthReport()
    names = list(parsed.models)
    if len(names) != len(set(name.lower() for name in names)):
        report.duplicate_names = sorted(names)
    report.orphan_models = [name for name in parsed.root_models() if not any(name in group.models for group in parsed.groups.values())][:32]
    report.empty_groups = [name for name, group in parsed.groups.items() if not group.models][:32]
    report.missing_coordinates = [name for name, model in parsed.models.items() if not model.geometry_points and not model.coordinates][:32]
    report.confusing_names = [name for name in names if len(name.strip()) < 3 or "model" == name.strip().lower()][:32]
    report.no_singing_face_mapping = [name for name in names if "face" in name.lower() and not parsed.models[name].submodels][:16]
    report.no_submodels_for_complex_props = [
        name for name, model in parsed.models.items()
        if model.total_pixels >= 100 and not model.submodels and len(recommend_submodels(model)) >= 4
    ][:32]
    report.no_center_anchor = "center" not in detect_anchor_points(scene)
    report.render_cost_risks = [name for name, model in parsed.models.items() if model.total_pixels >= 1500][:24]
    report.recommendations = [
        "Add center-aware groups or anchors for layout-wide motion.",
        "Add submodels for complex props so vocal, rhythm, and hero intents stay readable.",
    ]
    issue_count = sum(
        len(value) if isinstance(value, list) else int(bool(value))
        for key, value in report.to_dict().items()
        if key != "recommendations" and key != "severity_score"
    )
    report.severity_score = round(min(1.0, issue_count / 12.0), 4)
    return report
