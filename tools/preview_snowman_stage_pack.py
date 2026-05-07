from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from export.stage_pack_manifest_export import build_demo_stage_pack_export_manifest


DEFAULT_OUTPUT_PATH = Path("outputs/demo_snowman_stage_pack_preview.svg")


STAGE_POSITIONS = {
    "singer": (170, 150),
    "female_singer": (310, 150),
    "guitarist": (90, 270),
    "bassist": (390, 270),
    "drummer": (240, 300),
    "floor_piano": (240, 430),
}


PERFORMER_LABELS = {
    "singer": "Lead Singer",
    "female_singer": "Female Singer",
    "guitarist": "Guitarist",
    "bassist": "Bassist",
    "drummer": "Drummer",
    "floor_piano": "Floor Piano",
}


def _rows_by_performer(manifest: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in list(manifest.get("rows", []) or []):
        performer = str(row.get("performer", "unknown"))
        grouped.setdefault(performer, []).append(row)
    return grouped


def _top_targets(rows: list[Mapping[str, Any]], limit: int = 4) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        target = str(row.get("target_submodel", ""))
        if not target:
            continue
        counts[target] = counts.get(target, 0) + 1
    return [name for name, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _svg_escape(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _performer_card(performer: str, rows: list[Mapping[str, Any]]) -> str:
    x, y = STAGE_POSITIONS.get(performer, (40, 40))
    label = PERFORMER_LABELS.get(performer, performer)
    faces = sum(1 for row in rows if row.get("effect") == "Faces")
    drums = sum(1 for row in rows if row.get("timing_track") == "drums")
    hooks = sum(1 for row in rows if row.get("source") == "player_piano_hook")
    targets = _top_targets(rows)
    target_text = ", ".join(targets) if targets else "no targets"
    accent = "#f7fbff" if performer != "floor_piano" else "#fff8e6"
    border = "#2c3e50" if performer != "floor_piano" else "#8a5a00"
    return f'''
  <g id="card-{_svg_escape(performer)}">
    <rect x="{x - 72}" y="{y - 48}" width="144" height="96" rx="12" fill="{accent}" stroke="{border}" stroke-width="2"/>
    <text x="{x}" y="{y - 26}" text-anchor="middle" font-size="13" font-weight="700">{_svg_escape(label)}</text>
    <text x="{x}" y="{y - 6}" text-anchor="middle" font-size="11">cues: {len(rows)}</text>
    <text x="{x}" y="{y + 10}" text-anchor="middle" font-size="10">Faces: {faces}  Drums: {drums}  Hooks: {hooks}</text>
    <text x="{x}" y="{y + 28}" text-anchor="middle" font-size="8">{_svg_escape(target_text[:42])}</text>
  </g>'''


def build_stage_pack_preview_svg(manifest: Mapping[str, Any]) -> str:
    grouped = _rows_by_performer(manifest)
    cards = "\n".join(_performer_card(name, grouped.get(name, [])) for name in STAGE_POSITIONS)
    row_count = int(manifest.get("row_count", 0) or 0)
    timing_tracks = ", ".join(str(track) for track in manifest.get("timing_tracks", []))
    drummer_to_piano = any(
        row.get("performer") == "floor_piano" and row.get("source") == "player_piano_hook"
        for row in manifest.get("rows", []) or []
    )
    link_label = "drummer → floor piano: ACTIVE" if drummer_to_piano else "drummer → floor piano: missing"
    link_color = "#0a7a2f" if drummer_to_piano else "#a33"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="520" height="560" viewBox="0 0 520 560">
  <rect x="0" y="0" width="520" height="560" fill="#101820"/>
  <rect x="30" y="72" width="460" height="420" rx="24" fill="#172533" stroke="#d8e6f3" stroke-width="2"/>
  <text x="260" y="34" text-anchor="middle" fill="#ffffff" font-size="21" font-weight="700">Helix Snowman Stage Pack Preview</text>
  <text x="260" y="58" text-anchor="middle" fill="#c9d7e3" font-size="12">rows: {row_count} · timing tracks: {_svg_escape(timing_tracks)}</text>

  <line x1="240" y1="348" x2="240" y2="382" stroke="{link_color}" stroke-width="5" marker-end="url(#arrow)"/>
  <text x="260" y="374" fill="{link_color}" font-size="12" font-weight="700">{_svg_escape(link_label)}</text>

  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="{link_color}"/>
    </marker>
  </defs>

{cards}

  <text x="260" y="524" text-anchor="middle" fill="#d8e6f3" font-size="11">Generated from the flattened stage-pack export manifest, not hand-drawn assumptions.</text>
</svg>
'''


def write_demo_stage_pack_preview(path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    manifest = build_demo_stage_pack_export_manifest()
    svg = build_stage_pack_preview_svg(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    return {
        "path": str(path),
        "row_count": manifest["row_count"],
        "drummer_feeds_floor_piano": any(
            row.get("performer") == "floor_piano" and row.get("source") == "player_piano_hook"
            for row in manifest.get("rows", []) or []
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an SVG preview for the demo snowman stage pack manifest.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    print(json.dumps(write_demo_stage_pack_preview(args.output), indent=2))


if __name__ == "__main__":
    main()
