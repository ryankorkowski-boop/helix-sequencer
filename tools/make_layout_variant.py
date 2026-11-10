from __future__ import annotations

import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def transform_pair(x: float, y: float, cx: float, cy: float, sx: float, sy: float, angle: float) -> tuple[float, float]:
    dx, dy = x - cx, y - cy
    ca, sa = math.cos(angle), math.sin(angle)
    return cx + sx * (dx * ca - dy * sa), cy + sy * (dx * sa + dy * ca)


def transform_points(text: str, cx: float, cy: float, sx: float, sy: float, angle: float) -> str:
    if not text:
        return text
    vals = text.split(',')
    if len(vals) % 3:
        return text
    out: list[str] = []
    for i in range(0, len(vals), 3):
        try:
            x, y, z = map(float, vals[i:i+3])
        except ValueError:
            return text
        x, y = transform_pair(x, y, cx, cy, sx, sy, angle)
        out.extend((f"{x:.6f}", f"{y:.6f}", f"{z:.6f}"))
    return ','.join(out)


def make_variant(src: Path, dst: Path) -> None:
    tree = ET.parse(src)
    root = tree.getroot()
    models = root.findall('./models/model')
    positions = []
    for m in models:
        try:
            positions.append((float(m.get('WorldPosX', '0')), float(m.get('WorldPosY', '0'))))
        except ValueError:
            pass
    if not positions:
        raise RuntimeError('No model positions found')

    cx = sum(p[0] for p in positions) / len(positions)
    cy = sum(p[1] for p in positions) / len(positions)

    # Experimental "wide fan" layout: preserve every model/channel assignment,
    # but spread the scene horizontally, compress it vertically, and rotate it
    # slightly so the visual composition is substantially different.
    sx, sy = 1.35, 0.82
    angle = math.radians(7.0)

    for m in models:
        try:
            x = float(m.get('WorldPosX', '0'))
            y = float(m.get('WorldPosY', '0'))
        except ValueError:
            continue
        x, y = transform_pair(x, y, cx, cy, sx, sy, angle)
        m.set('WorldPosX', f'{x:.4f}')
        m.set('WorldPosY', f'{y:.4f}')
        for attr in ('PointData', 'cPointData'):
            if attr in m.attrib:
                m.set(attr, transform_points(m.get(attr, ''), cx, cy, sx, sy, angle))

    dst.parent.mkdir(parents=True, exist_ok=True)
    tree.write(dst, encoding='utf-8', xml_declaration=True)
    print(f'WROTE_VARIANT {dst}')
    print(f'MODELS {len(models)} CENTER {cx:.2f},{cy:.2f} SCALE {sx},{sy} ROTATION_DEG 7')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: make_layout_variant.py INPUT.xml OUTPUT.xml')
    make_variant(Path(sys.argv[1]), Path(sys.argv[2]))
