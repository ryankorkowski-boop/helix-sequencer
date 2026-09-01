"""Render an existing XSQ through the Wadena physical-geometry overlay.

This is intentionally a wrapper around the stable preview renderer: electrical
truth and sequence parsing remain unchanged while selected physical props are
reprojected into their observed Wadena-style geometry.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from core.wadena_preview_mapper import map_model_path
from tools import preview_renderer


def apply_wadena_geometry(layout: preview_renderer.LayoutData) -> int:
    changed = 0
    for name, geom in layout.leaf_models.items():
        mapped = map_model_path(name, geom.points)
        if mapped is None:
            continue
        geom.points = mapped.points
        geom.x1, geom.y1 = mapped.points[0]
        geom.x2, geom.y2 = mapped.points[-1]
        changed += 1
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an XSQ using Wadena physical preview geometry.")
    parser.add_argument("xsq")
    parser.add_argument("--layout", default=preview_renderer.DEFAULT_LAYOUT)
    parser.add_argument("--audio", default=None)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    args = parser.parse_args()

    root = preview_renderer.ROOT
    xsq = (root / args.xsq).resolve() if not Path(args.xsq).is_absolute() else Path(args.xsq)
    layout_path = (root / args.layout).resolve() if not Path(args.layout).is_absolute() else Path(args.layout)
    audio = None
    if args.audio:
        audio = (root / args.audio).resolve() if not Path(args.audio).is_absolute() else Path(args.audio)

    layout = preview_renderer.parse_models(layout_path)
    changed = apply_wadena_geometry(layout)
    print(f"Wadena physical geometry mapped {changed} models from {layout_path.name}", flush=True)

    out = preview_renderer.render_sequence_to_mp4(
        sequence_path=xsq,
        layout=layout,
        audio_path=audio,
        fps=args.fps,
        width=args.width,
        height=args.height,
    )
    print(f"Created Wadena preview: {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
