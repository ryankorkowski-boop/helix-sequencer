"""Validate real native Snowman Band geometry and export auditable positions.

No physical dimensions, mounting hole sizes, or controller addresses are inferred.
Usage: python -m tools.audit_native_snowman_geometry --output-dir build/native_snowman_audit
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from models.native_review_band import add_band, ac_variant, VISEMES
from models.ultimate_showcase import Garden
from core.physical_band_circuits import DRUMMER

ROLES = ("drummer", "bass", "guitar", "piano", "xylophone", "lead", "harmony")


def audit(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    garden = Garden(title="Native snowman geometry audit", slug="Native_Snowman_Audit")
    pixels = add_band(garden)
    if tuple(m.details["review_role"] for m in pixels) != ROLES:
        raise ValueError("Native band does not contain seven expected performers")
    acs = [ac_variant(m) for m in pixels]
    expected_drum = tuple(c.name for c in DRUMMER)
    result = {"schema": "helix.native_snowman_geometry_audit.v1",
              "physical_dimensions_verified": False,
              "controller_mapping_verified": False,
              "models": []}
    for mode, models in (("pixel", pixels), ("ac16", acs)):
        for model in models:
            role = model.details["review_role"]
            names = tuple(model.submodels)
            if role == "drummer" and set(names) != set(expected_drum):
                raise ValueError(f"{model.name}: drummer contract mismatch: {names}")
            if role in ("lead", "harmony"):
                missing = [f"MOUTH_{v}" for v in VISEMES if f"MOUTH_{v}" not in names]
                if missing:
                    raise ValueError(f"{model.name}: missing mouth poses: {missing}")
                if mode == "ac16":
                    circuits = model.details["ac_circuits"]
                    if len([n for n in circuits if n.startswith("MOUTH_")]) != 10:
                        raise ValueError(f"{model.name}: expected 10 independent AC mouth circuits")
                    if len({model.submodels[f"MOUTH_{v}"][0] for v in VISEMES}) != 10:
                        raise ValueError(f"{model.name}: mouth circuits are not independent")
            if mode == "ac16" and len(names) > 16:
                raise ValueError(f"{model.name}: >16 AC circuits")
            entries = model.attrs["CustomModelCompressed"].split(";")
            if len(entries) != len(model.points):
                raise ValueError(f"{model.name}: coordinate serialization length mismatch")
            file = output_dir / f"{model.name}_positions.csv"
            with file.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(("model", "mode", "entry", "node_or_circuit",
                                 "grid_row", "grid_column", "grid_depth",
                                 "design_x", "design_y", "design_z", "submodels"))
                owners = {}
                for name, ids in model.submodels.items():
                    for node in ids:
                        owners.setdefault(node, []).append(name)
                for i, (raw, xyz) in enumerate(zip(entries, model.points)):
                    node, row, col, depth = (int(x) for x in raw.split(","))
                    writer.writerow((model.name, mode, i + 1, node, row, col, depth,
                                     *[float(v) for v in xyz], "|".join(owners.get(node, []))))
            result["models"].append({
                "name": model.name, "role": role, "mode": mode,
                "geometry_positions": len(model.points),
                "submodels": {name: list(map(int, ids)) for name, ids in model.submodels.items()},
                "coordinate_csv": file.name,
                "grid_spacing_design_feet": model.details.get("grid_spacing_ft"),
                "physical_inches_per_design_foot": None,
                "physical_hole_spacing_verified": False,
            })
    (output_dir / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.output_dir)
    print(f"Audited {len(report['models'])} native pixel/AC models; no physical scale inferred.")


if __name__ == "__main__":
    main()
