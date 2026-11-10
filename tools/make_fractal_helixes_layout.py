from __future__ import annotations

import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def transform_points(text: str, ox: float, oy: float, angle: float, scale: float) -> str:
    if not text:
        return text
    vals = text.split(',')
    if len(vals) % 3:
        return text
    ca, sa = math.cos(angle), math.sin(angle)
    out: list[str] = []
    for i in range(0, len(vals), 3):
        try:
            x, y, z = map(float, vals[i:i + 3])
        except ValueError:
            return text
        x *= scale
        y *= scale
        rx = x * ca - y * sa + ox
        ry = x * sa + y * ca + oy
        out.extend((f"{rx:.6f}", f"{ry:.6f}", f"{z:.6f}"))
    return ','.join(out)


def make_fractal(src: Path, dst: Path) -> None:
    tree = ET.parse(src)
    root = tree.getroot()
    models = root.findall('./models/model')
    if not models:
        raise RuntimeError('No models found in layout')

    # Arrange the existing model population along six intertwined logarithmic
    # helix arms. Model identities, channel assignments, and point geometry are
    # retained; only the visual placement is changed for the preview.
    arms = 6
    golden = (1.0 + math.sqrt(5.0)) / 2.0
    center_x, center_y = 0.0, 0.0
    count = len(models)
    radius_max = 900.0
    radius_min = 70.0

    for i, model in enumerate(models):
        arm = i % arms
        turn = i // arms
        u = turn / max(1, math.ceil(count / arms) - 1)
        radius = radius_min + (radius_max - radius_min) * (u ** 0.82)
        theta = (2.0 * math.pi * arm / arms) + (turn * math.pi / 5.0)
        # Add a secondary Fibonacci-scale modulation so the arms do not read
        # as six simple spokes.
        theta += 0.34 * math.sin(turn * golden)
        x = center_x + radius * math.cos(theta)
        y = center_y + radius * math.sin(theta) * 0.72

        try:
            old_x = float(model.get('WorldPosX', '0'))
            old_y = float(model.get('WorldPosY', '0'))
        except ValueError:
            old_x = old_y = 0.0

        # Keep each model's local shape recognizable while fitting it into the
        # fractal composition. Rotate the existing point cloud with its arm.
        local_angle = theta - math.atan2(old_y, old_x) if (old_x or old_y) else theta
        model.set('WorldPosX', f'{x:.4f}')
        model.set('WorldPosY', f'{y:.4f}')
        for attr in ('PointData', 'cPointData'):
            if attr in model.attrib:
                model.set(attr, transform_points(model.get(attr, ''), x, y, local_angle, 0.72))

    dst.parent.mkdir(parents=True, exist_ok=True)
    tree.write(dst, encoding='utf-8', xml_declaration=True)
    print(f'WROTE_FRACTAL_HELIXES {dst}')
    print(f'MODELS {count} ARMS {arms} RADIUS {radius_min}-{radius_max}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: make_fractal_helixes_layout.py INPUT.xml OUTPUT.xml')
    make_fractal(Path(sys.argv[1]), Path(sys.argv[2]))
