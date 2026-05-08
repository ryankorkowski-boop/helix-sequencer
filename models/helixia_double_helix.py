from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any


DOUBLE_HELIX_SCHEMA = "helixia.double_helix.v1"


@dataclass(frozen=True)
class HelixPoint:
    node_id: str
    strand: str
    index: int
    theta: float
    world_x_ft: float
    world_y_ft: float
    world_z_ft: float
    phase: str


@dataclass(frozen=True)
class HelixRung:
    rung_id: str
    index: int
    strand_a_node: str
    strand_b_node: str
    world_x_ft: float
    world_y_ft: float
    world_z_ft: float
    length_ft: float
    phase: str


@dataclass(frozen=True)
class DoubleHelixConfig:
    height_ft: float = 112.0
    radius_ft: float = 24.0
    turns: float = 4.25
    nodes_per_strand: int = 144
    rung_every: int = 4
    base_y_ft: float = -80.0
    center_x_ft: float = 0.0
    center_z_ft: float = 0.0
    top_input_fraction: float = 0.16
    bottom_output_fraction: float = 0.18


def _phase_for_fraction(fraction: float, config: DoubleHelixConfig) -> str:
    if fraction <= config.bottom_output_fraction:
        return "bottom_output_finished_helix"
    if fraction >= 1.0 - config.top_input_fraction:
        return "top_input_untwisted_audio"
    return "twisted_core"


def _helix_point(*, strand: str, index: int, phase_offset: float, config: DoubleHelixConfig) -> HelixPoint:
    denominator = max(1, config.nodes_per_strand - 1)
    fraction = index / denominator
    theta = (fraction * config.turns * math.tau) + phase_offset
    return HelixPoint(
        node_id=f"HELIXIA_DNA_{strand.upper()}_{index:03d}",
        strand=strand,
        index=index,
        theta=round(theta, 6),
        world_x_ft=round(config.center_x_ft + config.radius_ft * math.cos(theta), 3),
        world_y_ft=round(config.base_y_ft + fraction * config.height_ft, 3),
        world_z_ft=round(config.center_z_ft + config.radius_ft * math.sin(theta), 3),
        phase=_phase_for_fraction(fraction, config),
    )


def _build_rung(index: int, a: HelixPoint, b: HelixPoint) -> HelixRung:
    dx = b.world_x_ft - a.world_x_ft
    dy = b.world_y_ft - a.world_y_ft
    dz = b.world_z_ft - a.world_z_ft
    return HelixRung(
        rung_id=f"HELIXIA_DNA_RUNG_{index:03d}",
        index=index,
        strand_a_node=a.node_id,
        strand_b_node=b.node_id,
        world_x_ft=round((a.world_x_ft + b.world_x_ft) / 2.0, 3),
        world_y_ft=round((a.world_y_ft + b.world_y_ft) / 2.0, 3),
        world_z_ft=round((a.world_z_ft + b.world_z_ft) / 2.0, 3),
        length_ft=round(math.sqrt(dx * dx + dy * dy + dz * dz), 3),
        phase=a.phase if a.phase == b.phase else "phase_transition",
    )


def build_giant_double_helix(config: DoubleHelixConfig = DoubleHelixConfig()) -> dict[str, Any]:
    """Build the Helixia centerpiece: a giant twisted lighted DNA helix.

    The geometry intentionally matches the provided visual direction: a concert-
    scale vertical sculpture with two luminous strands, horizontal color rungs,
    an open/audio-input top region, and a finished/lights-output lower region.
    """
    strand_a = [_helix_point(strand="strand_a", index=idx, phase_offset=0.0, config=config) for idx in range(config.nodes_per_strand)]
    strand_b = [_helix_point(strand="strand_b", index=idx, phase_offset=math.pi, config=config) for idx in range(config.nodes_per_strand)]
    rung_indices = list(range(0, config.nodes_per_strand, max(1, config.rung_every)))
    if rung_indices[-1] != config.nodes_per_strand - 1:
        rung_indices.append(config.nodes_per_strand - 1)
    rungs = [_build_rung(rung_idx, strand_a[rung_idx], strand_b[rung_idx]) for rung_idx in rung_indices]
    submodels = {
        "HELIXIA_DNA_STRAND_A": [point.node_id for point in strand_a],
        "HELIXIA_DNA_STRAND_B": [point.node_id for point in strand_b],
        "HELIXIA_DNA_RUNGS": [rung.rung_id for rung in rungs],
        "HELIXIA_DNA_RUNG_ODD": [rung.rung_id for rung in rungs if rung.index % 2 == 1],
        "HELIXIA_DNA_RUNG_EVEN": [rung.rung_id for rung in rungs if rung.index % 2 == 0],
        "HELIXIA_DNA_TOP_INPUT": [point.node_id for point in (*strand_a, *strand_b) if point.phase == "top_input_untwisted_audio"],
        "HELIXIA_DNA_BOTTOM_OUTPUT": [point.node_id for point in (*strand_a, *strand_b) if point.phase == "bottom_output_finished_helix"],
        "HELIXIA_DNA_CORE": [point.node_id for point in (*strand_a, *strand_b) if point.phase == "twisted_core"],
        "HELIXIA_DNA_FULL": [point.node_id for point in (*strand_a, *strand_b)] + [rung.rung_id for rung in rungs],
    }
    bounds = {
        "min_x_ft": round(min(point.world_x_ft for point in (*strand_a, *strand_b)), 3),
        "max_x_ft": round(max(point.world_x_ft for point in (*strand_a, *strand_b)), 3),
        "min_y_ft": round(min(point.world_y_ft for point in (*strand_a, *strand_b)), 3),
        "max_y_ft": round(max(point.world_y_ft for point in (*strand_a, *strand_b)), 3),
        "min_z_ft": round(min(point.world_z_ft for point in (*strand_a, *strand_b)), 3),
        "max_z_ft": round(max(point.world_z_ft for point in (*strand_a, *strand_b)), 3),
    }
    return {
        "schema": DOUBLE_HELIX_SCHEMA,
        "model_id": "HELIXIA_GIANT_DOUBLE_HELIX",
        "display_name": "Helixia Giant Lighted Double Helix",
        "role": "helixia_centerpiece",
        "visual_reference": {
            "concert_scale_neon_sculpture": True,
            "helix_dna_brand_language": True,
            "audio_in_lights_out_metaphor": True,
        },
        "config": asdict(config),
        "strand_a": [asdict(point) for point in strand_a],
        "strand_b": [asdict(point) for point in strand_b],
        "rungs": [asdict(rung) for rung in rungs],
        "submodels": submodels,
        "bounds_ft": bounds,
        "xlights_export_contract": {
            "target_model_type": "custom_model_with_3d_submodels",
            "node_order": "bottom_to_top_per_strand_then_rungs",
            "must_export_submodels": sorted(submodels),
            "first_sequence_smoke_test": "Audio enters HELIXIA_DNA_TOP_INPUT, spirals through strands/rungs, and resolves through HELIXIA_DNA_BOTTOM_OUTPUT.",
        },
        "validation": {
            "has_two_equal_strands": len(strand_a) == len(strand_b) == config.nodes_per_strand,
            "has_rungs": bool(rungs),
            "has_top_input_zone": bool(submodels["HELIXIA_DNA_TOP_INPUT"]),
            "has_bottom_output_zone": bool(submodels["HELIXIA_DNA_BOTTOM_OUTPUT"]),
            "has_core_zone": bool(submodels["HELIXIA_DNA_CORE"]),
            "height_matches_config": round(bounds["max_y_ft"] - bounds["min_y_ft"], 3) == round(config.height_ft, 3),
        },
    }
