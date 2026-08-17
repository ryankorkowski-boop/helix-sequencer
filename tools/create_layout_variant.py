from __future__ import annotations

import argparse
import math
import xml.etree.ElementTree as ET
from pathlib import Path


def f(v: str, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def transform_points(data: str, sx: float, sy: float, angle_deg: float) -> str:
    vals = [x for x in data.split(',') if x != '']
    if len(vals) < 3:
        return data
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for i in range(0, len(vals) - 2, 3):
        x, y, z = map(float, vals[i:i+3])
        x, y = x * sx, y * sy
        out.extend((f'{x * ca - y * sa:.6f}', f'{x * sa + y * ca:.6f}', f'{z:.6f}'))
    return ','.join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('output')
    ap.add_argument('--scale-x', type=float, default=1.35)
    ap.add_argument('--scale-y', type=float, default=0.82)
    ap.add_argument('--rotate-deg', type=float, default=7.0)
    args = ap.parse_args()

    src, dst = Path(args.source), Path(args.output)
    tree = ET.parse(src)
    root = tree.getroot()
    for model in root.iter('model'):
        if 'WorldPosX' in model.attrib and 'WorldPosY' in model.attrib:
            x, y = f(model.get('WorldPosX')), f(model.get('WorldPosY'))
            x, y = x * args.scale_x, y * args.scale_y
            a = math.radians(args.rotate_deg)
            model.set('WorldPosX', f'{x * math.cos(a) - y * math.sin(a):.4f}')
            model.set('WorldPosY', f'{x * math.sin(a) + y * math.cos(a):.4f}')
        if 'PointData' in model.attrib:
            model.set('PointData', transform_points(model.get('PointData', ''), args.scale_x, args.scale_y, args.rotate_deg))
    tree.write(dst, encoding='utf-8', xml_declaration=True)
    print(f'WROTE {dst}')


if __name__ == '__main__':
    main()
