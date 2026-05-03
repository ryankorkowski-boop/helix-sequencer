from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


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


def build_helixia_layout(
    output_dir: str | Path,
    *,
    village_rows: int = 3,
    village_cols: int = 4,
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
    (out_dir / "helixia_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "HELIXIA_LAYOUT_NOTES.txt").write_text(
        "Helixia layout scaffold generated.\n"
        "This file is a planning manifest for 2D/3D-coherent model placement and lot zoning.\n",
        encoding="utf-8",
    )
    return payload
