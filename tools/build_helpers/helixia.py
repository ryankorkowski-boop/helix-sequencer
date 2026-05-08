# Helixia Spatial Refactor v2
# 3D Spatial Testing Grounds Upgrade

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools.build_helpers.helixia_xlights import build_helixia_xlights_layout
from tools.write_helixville4_band_assets import write_band_assets

ROOT = Path(__file__).resolve().parents[2]

# --- Spatial Constants ---
FOREGROUND_Y = -320.0
MIDFIELD_OFFSET_Y = 120.0
BACKGROUND_Y = 340.0
HELIX_Y = 400.0

HELIX_SEGMENTS = 16
HELIX_HEIGHT = 26.0
HELIX_RADIUS = 18.0

# Backward compatibility constant expected by older tests
MEGATREE_CONFIGS: list[dict[str, Any]] = []


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


# --- House Grid (Midfield Rhythm Applied) ---

def _build_house_grid(*, rows: int, cols: int) -> list[HouseLot]:
    spacing_x = 110.0
    spacing_y = 96.0
    origin_x = -((cols - 1) * spacing_x) / 2.0
    origin_y = ((rows - 1) * spacing_y) / 2.0

    houses: list[HouseLot] = []
    for row in range(rows):
        for col in range(cols):
            stagger = (-20.0 if row % 2 == 0 else 20.0)
            houses.append(
                HouseLot(
                    lot_id=f"house_{row+1}_{col+1}",
                    style_id="spatial",
                    style_name="Spatial Showcase",
                    grid_row=row,
                    grid_col=col,
                    world_x_ft=round(origin_x + col * spacing_x, 3),
                    world_y_ft=round(origin_y - row * spacing_y + MIDFIELD_OFFSET_Y + stagger, 3),
                    world_z_ft=0.0,
                    cost_tier="medium",
                    aesthetics="3D rhythmic layering",
                    preferences=["symmetry", "travel corridors"],
                    model_types=["line", "matrix", "window_frame"],
                )
            )
    return houses


# --- Fibonacci Trees (True Background) ---

def _fibonacci_spiral_trees() -> list[dict[str, Any]]:
    trees = []
    golden_angle = math.radians(137.507764)
    for i in range(13):
        r = 16.0 * math.sqrt(max(i, 1))
        angle = i * golden_angle
        trees.append(
            {
                "tree_id": f"fib_tree_{i}",
                "world_x_ft": round(r * math.cos(angle), 3),
                "world_y_ft": round(BACKGROUND_Y + r * math.sin(angle), 3),
                "height_ft": 22.0 - i * 0.6,
                "model_type": "tree",
            }
        )
    return trees


# --- Helix Tower (Axial Hero) ---

def _build_helix_tower() -> list[dict[str, Any]]:
    segments = []
    for i in range(HELIX_SEGMENTS):
        angle = (i / HELIX_SEGMENTS) * (2 * math.pi * 2)
        segments.append(
            {
                "segment_id": f"helix_segment_{i}",
                "world_x_ft": round(HELIX_RADIUS * math.cos(angle), 3),
                "world_y_ft": HELIX_Y,
                "world_z_ft": round((HELIX_HEIGHT / HELIX_SEGMENTS) * i, 3),
                "model_type": "line",
            }
        )
    return segments


# --- Special Lots (Foreground + Skyline Placement) ---

def _special_lots() -> list[dict[str, Any]]:
    return [
        {
            "lot_id": "snowman_band_stage",
            "display_name": "Snowman Band Stage",
            "world_x_ft": 0.0,
            "world_y_ft": FOREGROUND_Y,
            "model_types": ["custom", "matrix", "line"],
        },
        {
            "lot_id": "dj_radio_booth",
            "display_name": "DJ Booth",
            "world_x_ft": 120.0,
            "world_y_ft": FOREGROUND_Y + 60.0,
            "model_types": ["custom", "matrix"],
        },
        {
            "lot_id": "radio_tower",
            "display_name": "Radio Tower",
            "world_x_ft": 260.0,
            "world_y_ft": HELIX_Y - 10,
            "model_types": ["line", "dmx"],
        },
    ]


# --- Layout Builder Entry ---

def build_helixia_layout(output_dir: str | Path, *, village_rows: int = 3, village_cols: int = 4, use_helixville4_band_model_specs: bool = False) -> dict[str, Any]:
    houses = _build_house_grid(rows=village_rows, cols=village_cols)
    trees = _fibonacci_spiral_trees()
    helix = _build_helix_tower()
    specials = _special_lots()

    payload = {
        "layout_id": "helixia_v2_spatial",
        "houses": [asdict(h) for h in houses],
        "fibonacci_trees": trees,
        "helix_tower": helix,
        "special_lots": specials,
    }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    xlights_payload = build_helixia_xlights_layout(payload, out_dir)
    payload["xlights_layout"] = xlights_payload

    (out_dir / "helixia_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
