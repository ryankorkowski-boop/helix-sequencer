from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools.build_helpers.helixia_xlights import build_helixia_xlights_layout


ROOT = Path(__file__).resolve().parents[2]

HOUSE_STYLE_PRESETS: list[dict[str, Any]] = [
    {
        "style_id": "classic_traditional",
        "display_name": "Classic Traditional",
        "cost_tier": "high",
        "aesthetic": "warm layered nostalgia",
        "preferences": ["wreath symmetry", "roofline rhythm", "cane pathways"],
    },
    {
        "style_id": "modern_minimalist",
        "display_name": "Modern Minimalist",
        "cost_tier": "medium",
        "aesthetic": "clean linear geometry",
        "preferences": ["cold whites", "edge outlines", "negative space"],
    },
    {
        "style_id": "retro_nostalgic",
        "display_name": "Retro & Nostalgic",
        "cost_tier": "medium",
        "aesthetic": "vintage bulbs and signage",
        "preferences": ["script signs", "warm tone strings", "animated window frames"],
    },
    {
        "style_id": "whimsical_cartoon",
        "display_name": "Whimsical Cartoon",
        "cost_tier": "medium",
        "aesthetic": "playful character focus",
        "preferences": ["character props", "rainbow accents", "bounce chases"],
    },
    {
        "style_id": "winter_wonderland",
        "display_name": "Winter Wonderland",
        "cost_tier": "medium",
        "aesthetic": "frosted monochrome glow",
        "preferences": ["snowflakes", "cool white wash", "sparkle shimmer"],
    },
    {
        "style_id": "tune_to_music",
        "display_name": "Tune To The Music",
        "cost_tier": "high",
        "aesthetic": "audio-reactive rhythmic architecture",
        "preferences": ["bar graphs", "beat chases", "timing overlays"],
    },
    {
        "style_id": "spooky_fun",
        "display_name": "Spooky Fun",
        "cost_tier": "low",
        "aesthetic": "high contrast neon mood",
        "preferences": ["purple/green palette", "flicker moments", "silhouette reveals"],
    },
    {
        "style_id": "international",
        "display_name": "International",
        "cost_tier": "high",
        "aesthetic": "multi-cultural motif collage",
        "preferences": ["regional color stories", "flag-inspired symmetry", "global icons"],
    },
    {
        "style_id": "patriotic_pride",
        "display_name": "Patriotic Pride",
        "cost_tier": "medium",
        "aesthetic": "bold red white blue hero moments",
        "preferences": ["star fields", "fan bursts", "stripe chases"],
    },
    {
        "style_id": "all_white_elegance",
        "display_name": "All White Elegance",
        "cost_tier": "high",
        "aesthetic": "single-hue luxury contrast",
        "preferences": ["dimmer curves", "architectural outlines", "sparkle layers"],
    },
    {
        "style_id": "fibonacci_sequence",
        "display_name": "Fibonacci Sequence",
        "cost_tier": "high",
        "aesthetic": "spiral growth geometry",
        "preferences": ["golden-angle spacing", "size progression", "radial gradients"],
    },
]

NATIVE_XLIGHTS_MODEL_TYPES: list[str] = [
    "arch",
    "tree",
    "matrix",
    "line",
    "candy_cane",
    "circle",
    "sphere",
    "star",
    "spinner",
    "icicles",
    "window_frame",
    "dmx",
    "custom",
]

MEGATREE_CONFIGS: list[str] = [
    "mega_360",
    "mega_180",
    "mega_90",
    "mega_pixel_strip",
    "mega_dense_matrix",
    "mega_sparse_outline",
]

ROLE_BY_MODEL_TYPE: dict[str, str] = {
    "arch": "travel",
    "tree": "hero",
    "matrix": "detail_surface",
    "line": "structure",
    "candy_cane": "rhythm",
    "circle": "accent",
    "sphere": "mood",
    "star": "accent",
    "spinner": "motion",
    "icicles": "texture",
    "window_frame": "structure",
    "dmx": "legacy_control",
    "custom": "performer_or_special",
}

FAMILY_BY_MODEL_TYPE: dict[str, str] = {
    "arch": "travel_props",
    "tree": "trees",
    "matrix": "matrices",
    "line": "lines",
    "candy_cane": "canes",
    "circle": "circles",
    "sphere": "spheres",
    "star": "stars",
    "spinner": "spinners",
    "icicles": "icicles",
    "window_frame": "windows",
    "dmx": "legacy_control",
    "custom": "custom_props",
}


@dataclass(frozen=True)
class HouseLot:
    lot_id: str
    style_id: str
    style_name: str
    grid_row: int
    grid_col: int
    world_x_ft: float
    world_y_ft: float
    world_z_ft: float
    cost_tier: str
    aesthetics: str
    preferences: list[str]
    model_types: list[str]


def _house_model_types(index: int) -> list[str]:
    wheel = [
        ["line", "window_frame", "candy_cane"],
        ["line", "matrix", "star"],
        ["line", "circle", "icicles"],
        ["line", "custom", "spinner"],
        ["line", "tree", "star"],
    ]
    return list(wheel[index % len(wheel)])


def _style_cost_usd(cost_tier: str) -> int:
    table = {"low": 1200, "medium": 2800, "high": 5200}
    return int(table.get(cost_tier, 2400))


def _build_house_grid(*, rows: int, cols: int) -> list[HouseLot]:
    houses: list[HouseLot] = []
    style_cycle = list(HOUSE_STYLE_PRESETS)
    spacing_x = 110.0
    spacing_y = 96.0
    origin_x = -((cols - 1) * spacing_x) / 2.0
    origin_y = ((rows - 1) * spacing_y) / 2.0
    style_index = 0

    for row in range(rows):
        for col in range(cols):
            style = style_cycle[style_index % len(style_cycle)]
            houses.append(
                HouseLot(
                    lot_id=f"house_{row + 1}_{col + 1}",
                    style_id=str(style["style_id"]),
                    style_name=str(style["display_name"]),
                    grid_row=row,
                    grid_col=col,
                    world_x_ft=round(origin_x + (col * spacing_x), 3),
                    world_y_ft=round(origin_y - (row * spacing_y), 3),
                    world_z_ft=0.0,
                    cost_tier=str(style["cost_tier"]),
                    aesthetics=str(style["aesthetic"]),
                    preferences=list(style["preferences"]),
                    model_types=_house_model_types(style_index),
                )
            )
            style_index += 1

    return houses


def _fibonacci_spiral_trees() -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = [
        {
            "tree_id": "fib_tree_center",
            "spiral_index": 0,
            "world_x_ft": 0.0,
            "world_y_ft": -290.0,
            "height_ft": 22.0,
            "model_type": "tree",
            "megatree_config": MEGATREE_CONFIGS[0],
        }
    ]

    count = 12
    golden_angle = math.radians(137.507764)
    for idx in range(1, count + 1):
        radius = 16.0 * math.sqrt(idx)
        angle = idx * golden_angle
        points.append(
            {
                "tree_id": f"fib_tree_{idx}",
                "spiral_index": idx,
                "world_x_ft": round(radius * math.cos(angle), 3),
                "world_y_ft": round(-290.0 + (radius * math.sin(angle)), 3),
                "height_ft": round(max(8.0, 21.0 - (idx * 1.0)), 3),
                "model_type": "tree",
                "megatree_config": MEGATREE_CONFIGS[idx % len(MEGATREE_CONFIGS)],
            }
        )

    return points


def _special_lots() -> list[dict[str, Any]]:
    return [
        {
            "lot_id": "ac_all_white",
            "display_name": "All White AC Property",
            "world_x_ft": -360.0,
            "world_y_ft": -210.0,
            "model_types": ["line", "icicles", "window_frame"],
            "ac_palette": "white_only",
        },
        {
            "lot_id": "ac_rwg",
            "display_name": "Red White Green AC Property",
            "world_x_ft": -500.0,
            "world_y_ft": -210.0,
            "model_types": ["line", "tree", "candy_cane"],
            "ac_palette": "red_white_green",
        },
        {
            "lot_id": "arches_lot",
            "display_name": "Arches Lot",
            "world_x_ft": -420.0,
            "world_y_ft": -60.0,
            "model_types": ["arch", "line"],
        },
        {
            "lot_id": "tunnels_lot",
            "display_name": "Tunnels Lot",
            "world_x_ft": -300.0,
            "world_y_ft": -60.0,
            "model_types": ["arch", "matrix", "line"],
        },
        {
            "lot_id": "snowman_band_stage",
            "display_name": "Snowman Band Stage",
            "world_x_ft": 315.0,
            "world_y_ft": -42.0,
            "model_types": ["custom", "matrix", "line", "circle"],
            "contains": ["lead_singer", "guitarist", "bass_player", "drummer"],
        },
        {
            "lot_id": "dj_radio_booth",
            "display_name": "DJ + Radio Booth",
            "world_x_ft": 430.0,
            "world_y_ft": -42.0,
            "model_types": ["custom", "matrix", "line"],
            "contains": ["dj_cactus", "inflatable_tube_man"],
        },
        {
            "lot_id": "coro_boscoyo_props",
            "display_name": "Coro/Boscoyo-Friendly Props Lot",
            "world_x_ft": 520.0,
            "world_y_ft": -130.0,
            "model_types": ["custom", "matrix", "star", "spinner"],
        },
        {
            "lot_id": "radio_tower",
            "display_name": "Radio Tower",
            "world_x_ft": 580.0,
            "world_y_ft": -20.0,
            "model_types": ["line", "dmx", "custom"],
        },
        {
            "lot_id": "wreath_projection",
            "display_name": "20ft Wreath + Projection Canvas",
            "world_x_ft": 260.0,
            "world_y_ft": -230.0,
            "model_types": ["circle", "matrix", "line"],
            "diameter_ft": 20.0,
        },
        {
            "lot_id": "blow_mold_animals",
            "display_name": "Blow Mold Animal Property",
            "world_x_ft": -180.0,
            "world_y_ft": -220.0,
            "model_types": ["custom", "line", "star"],
        },
        {
            "lot_id": "experimental_3d_playground",
            "display_name": "3D Experimental Playground",
            "world_x_ft": 120.0,
            "world_y_ft": -130.0,
            "model_types": ["arch", "sphere", "star", "custom", "spinner", "matrix"],
            "stacking_examples": [
                "nested_arch_waves",
                "sphere_star_interlocks",
                "submodel_character_stop_motion",
            ],
        },
    ]


def _native_model_coverage(
    houses: list[HouseLot],
    special_lots: list[dict[str, Any]],
    fib_trees: list[dict[str, Any]],
) -> dict[str, list[str]]:
    coverage: dict[str, list[str]] = {name: [] for name in NATIVE_XLIGHTS_MODEL_TYPES}

    for house in houses:
        for model_type in house.model_types:
            if model_type in coverage:
                coverage[model_type].append(house.lot_id)

    for lot in special_lots:
        for model_type in list(lot.get("model_types", []) or []):
            if model_type in coverage:
                coverage[model_type].append(str(lot.get("lot_id", "")))

    for tree in fib_trees:
        coverage["tree"].append(str(tree.get("tree_id", "")))

    return coverage


def _role_metadata_for_lot(lot_id: str, model_types: list[str]) -> dict[str, Any]:
    roles = sorted({ROLE_BY_MODEL_TYPE.get(model_type, "support") for model_type in model_types})
    families = sorted({FAMILY_BY_MODEL_TYPE.get(model_type, "unknown") for model_type in model_types})
    is_stage = lot_id in {"snowman_band_stage", "dj_radio_booth"}
    is_ac = lot_id in {"ac_all_white", "ac_rwg"}
    return {
        "lot_id": lot_id,
        "model_types": list(model_types),
        "families": families,
        "roles": roles,
        "stage_zone": bool(is_stage),
        "legacy_control_zone": bool(is_ac),
    }


def _build_layout_intelligence(
    houses: list[HouseLot],
    special_lots: list[dict[str, Any]],
    fib_trees: list[dict[str, Any]],
    coverage: dict[str, list[str]],
) -> dict[str, Any]:
    house_roles = [
        _role_metadata_for_lot(house.lot_id, house.model_types)
        | {
            "style_id": house.style_id,
            "style_name": house.style_name,
            "grid_row": house.grid_row,
            "grid_col": house.grid_col,
            "world_position_ft": [house.world_x_ft, house.world_y_ft, house.world_z_ft],
        }
        for house in houses
    ]
    special_roles = [
        _role_metadata_for_lot(str(lot.get("lot_id", "")), list(lot.get("model_types", []) or []))
        | {
            "display_name": str(lot.get("display_name", "")),
            "world_position_ft": [float(lot.get("world_x_ft", 0.0)), float(lot.get("world_y_ft", 0.0)), 0.0],
            "contains": list(lot.get("contains", []) or []),
        }
        for lot in special_lots
    ]
    performer_models = {
        "snowman_band": [
            "HX_SNOWMAN_BASSIST_BODY",
            "HX_SNOWMAN_BASSIST_INSTRUMENT",
            "HX_SNOWMAN_GUITARIST_BODY",
            "HX_SNOWMAN_GUITARIST_INSTRUMENT",
            "HX_SNOWMAN_DRUMMER_BODY",
            "HX_SNOWMAN_DRUMMER_INSTRUMENT",
            "HX_SNOWMAN_SINGER_BODY",
            "HX_SNOWMAN_SINGER_INSTRUMENT",
            "HX_SNOWMAN_SINGER_FEMALE_BODY",
            "HX_SNOWMAN_SINGER_FEMALE_INSTRUMENT",
        ],
        "helixville4_band_spec_models": [
            "HX_SNOWMAN_SINGER",
            "HX_SNOWMAN_SINGER_FEMALE",
            "HX_SNOWMAN_GUITARIST",
            "HX_SNOWMAN_BASSIST",
            "HX_SNOWMAN_DRUMMER",
        ],
        "cactus_tubeman": [
            "HX_CACTUS_BODY",
            "HX_CACTUS_FACE",
            "HX_TUBEMAN_BODY",
            "HX_TUBEMAN_ARMS",
            "HX_DJ_BOOTH",
        ],
        "floor_piano": ["HX_FLOOR_PIANO_BASE", "HX_FLOOR_PIANO_KEYS"],
        "reindeer_dance": ["HX_REINDEER_DANCE_BODY", "HX_REINDEER_DANCE_LEGS"],
    }
    required_groups = [
        "HELIXIA_ALL",
        "HELIXIA_HOUSES",
        "HELIXIA_STAGE",
        "HELIXIA_SPECIAL_LOTS",
        "HX_FAMILY_MATRIX",
        "HX_FAMILY_CUSTOM",
        "HX_FAMILY_TREE",
        "HX_FAMILY_ARCH",
        "HX_LOT_SNOWMAN_BAND_STAGE",
        "HX_LOT_DJ_RADIO_BOOTH",
    ]
    return {
        "schema": "helixia.layout_intelligence.v1",
        "role_by_model_type": dict(ROLE_BY_MODEL_TYPE),
        "family_by_model_type": dict(FAMILY_BY_MODEL_TYPE),
        "house_lots": house_roles,
        "special_lots": special_roles,
        "fibonacci_tree_lot": {
            "role": "hero_spiral",
            "family": "trees",
            "tree_count": len(fib_trees),
            "center_tree": "HX_FIB_FIB_TREE_CENTER",
        },
        "performer_models": performer_models,
        "required_groups": required_groups,
        "coverage_complete": all(bool(refs) for refs in coverage.values()),
        "two_dimensional_readability": {
            "houses_use_grid": True,
            "performers_use_stage_zone": True,
            "hero_trees_use_separate_lot": True,
        },
    }


def build_helixia_layout(
    output_dir: str | Path,
    *,
    village_rows: int = 3,
    village_cols: int = 4,
    use_helixville4_band_model_specs: bool = False,
) -> dict[str, Any]:
    houses = _build_house_grid(rows=village_rows, cols=village_cols)
    fib_trees = _fibonacci_spiral_trees()
    special_lots = _special_lots()
    coverage = _native_model_coverage(houses, special_lots, fib_trees)
    missing = [model_type for model_type, refs in coverage.items() if not refs]
    if missing:
        raise ValueError(f"Helixia coverage incomplete for native model types: {missing}")

    house_payload: list[dict[str, Any]] = []
    for house in houses:
        item = asdict(house)
        item["estimated_cost_usd"] = _style_cost_usd(house.cost_tier)
        house_payload.append(item)

    payload: dict[str, Any] = {
        "layout_id": "helixia_v1",
        "layout_name": "Helixia (Helixville4)",
        "goal": "3D-forward layout that remains visually coherent in 2D preview",
        "use_helixville4_band_model_specs": bool(use_helixville4_band_model_specs),
        "village_grid": {
            "rows": village_rows,
            "cols": village_cols,
            "houses": house_payload,
        },
        "fibonacci_tree_lot": {
            "description": "Spiral trees with tallest center tree and mixed mega-tree configurations",
            "trees": fib_trees,
            "megatree_configurations": list(MEGATREE_CONFIGS),
        },
        "special_lots": special_lots,
        "native_model_coverage": coverage,
        "layout_intelligence": _build_layout_intelligence(houses, special_lots, fib_trees, coverage),
        "requirements_satisfied": {
            "all_white_ac_property": True,
            "red_white_green_ac_property": True,
            "all_native_model_types_invoked": True,
            "band_stage_with_snowman_band": True,
            "dj_booth_with_cactus_and_tube_man": True,
            "arches_and_tunnels_lots": True,
            "radio_tower_present": True,
            "wreath_projection_property_present": True,
            "blow_mold_property_present": True,
            "experimental_3d_playground_present": True,
        },
        "inspiration_inputs": [
            "helixville4inspirationtemplate.png",
            "snowman band inspiration template.jpeg",
            "drummerinspiration.png",
            "pianoinspiration.jpeg",
        ],
    }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    xlights_payload = build_helixia_xlights_layout(payload, out_dir)
    payload["xlights_layout"] = xlights_payload
    (out_dir / "helixia_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    notes = (
        "Helixia layout scaffold generated.\n"
        "Generated xlights_rgbeffects.xml contains deterministic placeholder models for Helixia v1.\n"
    )
    if use_helixville4_band_model_specs:
        notes += "Helixville4 spec-driven snowman band models are enabled.\n"
    (out_dir / "HELIXIA_LAYOUT_NOTES.txt").write_text(notes, encoding="utf-8")
    return payload
