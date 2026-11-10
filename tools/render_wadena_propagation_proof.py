"""Render a deterministic Wadena temporal-propagation proof MP4.

This is intentionally renderer-only: no physical channel numbers are inferred.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation

from core.wadena_spatial_graph import wadena_spatial_graph

LANDMARKS = {
    "LEFT_TREE": (122, 302),
    "BLVD_LEFT": (120, 62),
    "BLVD_CENTER": (644, 11),
    "BLVD_RIGHT": (999, -26),
    "RIGHT_LINDEN": (1290, 391),
    "WREATH": (556, 340),
    "GARAGE_SNOWFLAKE": (666, 342),
    "ROOF_SNOWFLAKE": (855, 469),
    "FRONT_IMPACT": (621, 372),
    "RIGHT_IMPACT": (1279, 239),
}


def env(age: float, attack: float = 0.08, decay: float = 0.8) -> float:
    if age < 0:
        return 0.0
    if age < attack:
        return age / attack
    return math.exp(-(age - attack) / decay)


def render(output: Path, duration: float = 12.0, fps: int = 20) -> Path:
    graph = wadena_spatial_graph()
    route_lr = graph.route("LEFT_TREE", "RIGHT_LINDEN")
    route_rl = graph.route("RIGHT_LINDEN", "LEFT_TREE")
    if not route_lr or not route_rl:
        raise RuntimeError("Wadena topology route unavailable")

    events = [
        (1.0, route_lr, 0.95),
        (4.0, route_rl, 0.90),
        (7.0, ["WREATH", "GARAGE_SNOWFLAKE", "ROOF_SNOWFLAKE"], 1.0),
        (9.5, ["FRONT_IMPACT", "RIGHT_IMPACT"], 1.0),
    ]
    travel = 0.55
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.set_xlim(0, 1380)
    ax.set_ylim(-90, 540)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Helix — Wadena Temporal Spatial Propagation Proof")
    ax.set_xlabel("layout X")
    ax.set_ylabel("layout Y")
    ax.scatter([p[0] for p in LANDMARKS.values()], [p[1] for p in LANDMARKS.values()], s=90)
    for name, (x, y) in LANDMARKS.items():
        ax.text(x + 14, y + 10, name.replace("_", " "), fontsize=8)
    for route in (route_lr, route_rl):
        ax.plot([LANDMARKS[n][0] for n in route], [LANDMARKS[n][1] for n in route], linewidth=1, alpha=0.25)
    active = ax.scatter([], [], s=[])
    status = ax.text(0.01, 0.97, "", transform=ax.transAxes, va="top", fontsize=10)

    def update(frame: int):
        t = frame / fps
        pts, sizes, labels = [], [], []
        for launch, route, strength in events:
            for i, node in enumerate(route):
                w = strength * env(t - (launch + i * travel))
                if w > 0.018:
                    pts.append(LANDMARKS[node])
                    sizes.append(70 + 850 * w)
                    labels.append(f"{node} {w:.2f}")
        active.set_offsets(pts if pts else [])
        active.set_sizes(sizes)
        status.set_text(f"t = {t:05.2f}s    active landmarks = {len(pts)}\n" + (" | ".join(labels[:5]) if labels else "quiet / decay"))
        return active, status

    anim = FuncAnimation(fig, update, frames=int(duration * fps), interval=1000 / fps, blit=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    anim.save(output, writer=FFMpegWriter(fps=fps, bitrate=1800))
    plt.close(fig)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--duration", type=float, default=12.0)
    parser.add_argument("--fps", type=int, default=20)
    args = parser.parse_args()
    render(args.output, args.duration, args.fps)
