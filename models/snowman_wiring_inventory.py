"""Auditable snowman submodel node and AC circuit inventory.

Counts are generated geometry, not purchased bulb counts or verified wiring.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


def inventory_model(model) -> dict:
    """Summarize the actual exported model's node ownership."""
    mode = "ac16" if model.kind == "ac" else "pixel"
    submodels = []
    all_ids = set()
    for name, raw_ids in sorted(model.submodels.items()):
        ids = sorted(set(int(node) for node in raw_ids))
        if any(node < 1 for node in ids):
            raise ValueError(f"Invalid node index in {model.name}/{name}")
        all_ids.update(ids)
        submodels.append({
            "name": name,
            "node_count": len(ids) if mode == "pixel" else None,
            "circuit_count": len(ids) if mode == "ac16" else None,
            "node_ids": ids,
            "physical_bulbs_per_strand": None,
        })
    if mode == "ac16" and (len(all_ids) > 16 or any(node > 16 for node in all_ids)):
        raise ValueError(f"AC model exceeds 16 circuits: {model.name}")
    geometry_positions = len(model.points)
    return {
        "model": model.name,
        "role": model.details.get("review_role", ""),
        "mode": mode,
        "geometry_positions": geometry_positions,
        "unique_addressable_nodes": len(all_ids) if mode == "pixel" else None,
        "ac_circuits_used": len(all_ids) if mode == "ac16" else None,
        "controller_unit": None,
        "controller_circuit_mapping_verified": False,
        "physical_bulb_counts_verified": False,
        "submodels": submodels,
    }


def write_inventory(models, destination: Path) -> tuple[Path, Path]:
    """Write JSON plus a practical per-submodel wiring planning CSV."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    records = [inventory_model(model) for model in models]
    json_path = destination / "snowman_submodel_inventory.json"
    csv_path = destination / "snowman_submodel_inventory.csv"
    for path in (json_path, csv_path):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite inventory: {path}")
    json_path.write_text(json.dumps({
        "warning": "AC geometry positions are not individual circuits or verified bulb counts. Controller wiring must be assigned and checked by owner.",
        "models": records,
    }, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=[
            "model", "role", "mode", "submodel", "pixel_nodes",
            "ac_circuits", "geometry_positions", "bulbs_per_ac_strand",
            "controller_unit", "controller_circuit", "wiring_verified",
        ])
        writer.writeheader()
        for model in records:
            for part in model["submodels"]:
                writer.writerow({
                    "model": model["model"], "role": model["role"],
                    "mode": model["mode"], "submodel": part["name"],
                    "pixel_nodes": part["node_count"] if part["node_count"] is not None else "",
                    "ac_circuits": part["circuit_count"] if part["circuit_count"] is not None else "",
                    "geometry_positions": model["geometry_positions"],
                    "bulbs_per_ac_strand": "", "controller_unit": "",
                    "controller_circuit": "", "wiring_verified": "NO",
                })
    return json_path, csv_path
