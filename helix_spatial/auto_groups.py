"""Automatic RGB prop detection and spatial grouping from node geometry alone.

Before this, automatic routing only covered AC circuits
(``tools.source_role_routing.configure_source_routes``) and RGB props got a
hand-set LEFT/CENTER/RIGHT ``showcase_group``. Here every pixel model is
classified from its 3D node positions (names and zones are *not* read), then
props of the same class are clustered into physical groups (rows by depth,
runs by X gaps). Each group becomes a route bank: a measured note travels
across the bank in physical order instead of being broadcast to every prop.

The classifier is heuristic geometry, reported with its evidence; it is not a
claim about how a human sequencer would label a custom prop.
"""
from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np

PROP_CLASSES = ("matrix", "mega_tree", "mini_tree", "arch", "ring", "line", "roofline",
                "cane", "helix", "volume", "custom")


def _pca(points):
    centered = points - points.mean(axis=0)
    if len(points) < 3:
        return np.array([1.0, 0.0, 0.0]), np.eye(3)
    cov = np.cov(centered.T)
    values, vectors = np.linalg.eigh(cov)
    order = np.argsort(values)[::-1]
    return np.maximum(values[order], 0), vectors[:, order]


def detect_prop(points) -> tuple[str, dict]:
    p = np.asarray(points, dtype=float).reshape(-1, 3)
    n = len(p)
    span = np.ptp(p, axis=0) if n else np.zeros(3)
    ev, vec = _pca(p)
    total = float(ev.sum()) or 1.0
    linear = float(ev[0] / total)
    planar = float(ev[2] / total)
    evidence = dict(nodes=n, span=[round(float(v), 2) for v in span], linearity=round(linear, 3),
                    planarity_residual=round(planar, 4))
    if n < 4:
        return "custom", evidence
    height = float(span[1])
    horizontal = float(max(span[0], span[2]))
    if linear > 0.97:
        direction = np.abs(vec[:, 0])
        long = float(np.ptp(p @ vec[:, 0])) > 20
        cls = "roofline" if direction[1] < 0.3 and p[:, 1].mean() > 12 and long else "line"
        return cls, evidence
    # Vertical axis radial profile: trees narrow upwards, helices keep radius.
    axis = np.array([p[:, 0].mean(), p[:, 2].mean()])
    radius = np.hypot(p[:, 0] - axis[0], p[:, 2] - axis[1])
    depthy = min(span[0], span[2]) > 0.35 * max(span[0], span[2], 1e-6)
    if depthy and height > 0.8 * horizontal and n >= 40:
        corr = float(np.corrcoef(radius, p[:, 1])[0, 1]) if np.std(radius) > 1e-6 else 0.0
        evidence["radius_height_corr"] = round(corr, 3)
        if corr < -0.55:
            return ("mega_tree" if height >= 30 else "mini_tree"), evidence
        if abs(corr) < 0.3 and height > 2.0 * horizontal:
            return "helix", evidence
    if planar < 0.004:
        # Planar prop: matrix grid, ring, arch or cane.
        normal = np.abs(vec[:, 2])
        u, v = vec[:, 0], vec[:, 1]
        uv = np.c_[(p - p.mean(0)) @ u, (p - p.mean(0)) @ v]
        rows = len(np.unique(np.round(p[:, 1], 1)))
        evidence["distinct_heights"] = rows
        if n >= 200 and rows >= 8 and len(np.unique(np.round(uv[:, 0], 1))) >= 8:
            # A filled lattice has many nodes per row and per column.
            if n / rows >= 8:
                return "matrix", evidence
        centre = uv.mean(axis=0)
        scale = np.maximum(uv.std(axis=0), 1e-6)
        r = np.hypot(*((uv - centre) / scale).T)  # ellipse-normalised radius
        evidence["ring_radius_cv"] = round(float(r.std() / max(r.mean(), 1e-6)), 3)
        if r.mean() > 0 and r.std() / r.mean() < 0.06:
            return "ring", evidence
        if normal[1] < 0.5:  # vertical plane
            low = p[:, 1] - p[:, 1].min()
            xs = (p[:, 0] if span[0] >= span[2] else p[:, 2])
            mid = np.abs(xs - xs.mean()) < 0.15 * max(np.ptp(xs), 1e-6)
            ends = np.abs(xs - xs.mean()) > 0.4 * max(np.ptp(xs), 1e-6)
            if np.ptp(xs) < 0.45 * height and height >= 4:
                return "cane", evidence
            if mid.any() and ends.any() and low[mid].mean() > 0.7 * height and low[ends].mean() < 0.35 * height:
                return "arch", evidence
    if min(span) > 6 and n >= 200:
        return "volume", evidence
    return "custom", evidence


def _clusters(values, gap):
    order = np.argsort(values)
    groups, current = [], [order[0]]
    for a, b in zip(order, order[1:]):
        if values[b] - values[a] > gap:
            groups.append(current)
            current = []
        current.append(b)
    groups.append(current)
    return groups


def auto_group(models, *, order_axis: str = "x", direction: int = 1, step_ms: int = 30,
               role_for_prop: dict[str, str] | None = None, drum_cycle=("kick", "snare", "hihat", "cymbal", "tom", "ride"),
               bank_routes: bool = True, overwrite_roles: bool = True):
    """Classify and group pixel props in-place; return an audit report."""
    pixel = [m for m in models if m.kind == "pixel" and not m.details.get("review_role")
             and not m.details.get("generic_singer") and len(m.points) >= 4]
    classes: dict[str, list] = defaultdict(list)
    for model in pixel:
        prop, evidence = detect_prop(model.points)
        model.details["auto_prop"] = prop
        model.details["auto_prop_evidence"] = evidence
        classes[prop].append(model)
    report = dict(method="helix_spatial.auto_groups.v1 (geometry only; names/zones not read)",
                  props=dict(Counter({k: len(v) for k, v in classes.items()})), groups={})
    all_centres = np.array([m.points.mean(axis=0) for m in pixel]) if pixel else np.zeros((1, 3))
    lo, hi = all_centres.min(axis=0), all_centres.max(axis=0)
    axis_index = {"x": 0, "height": 1, "depth": 2}.get(order_axis, 0)
    for prop, members in classes.items():
        centres = np.array([m.points.mean(axis=0) for m in members])
        widths = np.array([max(np.ptp(m.points[:, 0]), 1.0) for m in members])
        depth_rows = _clusters(centres[:, 2], gap=max(6.0, float(np.median(widths)) * 0.8))
        for row_index, row in enumerate(depth_rows):
            runs = _clusters(centres[row, 0], gap=max(10.0, float(np.median(widths[row])) * 2.2))
            for run_index, run in enumerate(runs):
                group = [members[row[i]] for i in run]
                name = f"AUTO_{prop.upper()}_R{row_index + 1}_G{run_index + 1}"
                role = (role_for_prop or {}).get(prop)
                key = lambda m: m.points.mean(axis=0)[axis_index] * direction
                group.sort(key=key)
                for rank, model in enumerate(group):
                    model.details["auto_group"] = name
                    if role and (overwrite_roles or "musical_role" not in model.details):
                        model.details["musical_role"] = role
                        if role == "drummer":
                            model.details["percussion_component"] = drum_cycle[rank % len(drum_cycle)]
                    if bank_routes and len(group) > 1 and model.details.get("musical_role") in ("guitarist", "bassist", "keyboardist"):
                        model.details.update(source_route_bank=f"auto|{name}|{model.details['musical_role']}",
                                             source_route_rank=rank, source_route_count=len(group))
                    c = model.points.mean(axis=0)
                    span = max(hi[axis_index] - lo[axis_index], 1e-6)
                    frac = float((c[axis_index] - lo[axis_index]) / span)
                    if order_axis == "center_out":
                        frac = float(abs(c[0] - (lo[0] + hi[0]) / 2) / max((hi[0] - lo[0]) / 2, 1e-6))
                    if direction < 0:
                        frac = 1 - frac
                    model.details["spatial_phase"] = round(min(max(frac, 0.0), 1.0), 4)
                    model.details["spatial_direction"] = direction
                    # Bounded so short notes keep sounding after the spatial offset (end is clamped to the source offset).
                    model.details["propagation_delay_ms"] = int(round(frac * min(3 * step_ms, 150)))
                report["groups"][name] = [m.name for m in group]
    report["group_count"] = len(report["groups"])
    return report
