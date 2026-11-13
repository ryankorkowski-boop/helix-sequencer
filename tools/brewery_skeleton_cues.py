"""Exclusive four-skeleton pose lanes from the authentic Helix source plan.

No synthetic instrument detections, inferred vocals or continuous beat wash.
Native On effects illuminate one pose silhouette at a time; the body and
instrument remain visible at a restrained fixed intensity.
"""
from __future__ import annotations

from models.brewery_skeleton_band import POSE_STATES


def _source_role(role):
    return "guitarist" if role == "frontman" else role


def _relevant(role, cue):
    if cue.get("kind") == "chord_change":
        return False
    if role == "drummer":
        return cue.get("kind") in ("kick", "snare", "hihat", "cymbal", "tom", "ride", "crash")
    return cue.get("end_ms", 0) > cue.get("start_ms", 0)


def pose_timeline(role, plan, duration_ms, *, frame_ms=50):
    """Return coalesced, nonoverlapping (start, end, pose) windows.

    At every frame, only cues retained by Helix's actual source-role analysis
    can trigger an attack. The frontman follows guitar phrasing rather than
    manufacturing a lead vocal from instrumental audio.
    """
    cues = sorted((c for c in plan.get("cues", {}).get(_source_role(role), ())
                   if _relevant(role, c)),
                  key=lambda c: (int(c["start_ms"]), int(c["end_ms"])))
    duration_ms = int(duration_ms)
    if duration_ms <= 0:
        raise ValueError("Duration must be positive")
    n = (duration_ms + frame_ms - 1) // frame_ms
    states = ["POSE_IDLE"] * n
    # Onsets and rests are source-timed. Distinct accent and recovery windows
    # are bounded and may not extend into the next source attack.
    for cue in cues:
        a, b = int(cue["start_ms"]), int(cue["end_ms"])
        if b <= a or a >= duration_ms:
            continue
        first = max(0, a // frame_ms)
        last = min(n, (b + frame_ms - 1) // frame_ms)
        if first >= last:
            continue
        vel = float(cue.get("velocity", cue.get("expression", {}).get("brightness", .5)))
        if role == "drummer":
            accent = cue.get("kind") in ("crash", "cymbal", "snare", "tom")
        else:
            accent = vel >= .78
        for k in range(first, last):
            # Never animate outside the original cue window.
            frame_start = k * frame_ms
            if frame_start < a or frame_start >= b:
                continue
            elapsed = frame_start - a
            if elapsed < 100:
                pose = "POSE_ACCENT" if accent else "POSE_ATTACK"
            elif elapsed < 240:
                pose = "POSE_RECOVERY"
            else:
                pose = "POSE_IDLE"
            # A concurrent event may upgrade the state but never create a
            # second simultaneously illuminated pose.
            rank = {"POSE_IDLE": 0, "POSE_RECOVERY": 1,
                    "POSE_ATTACK": 2, "POSE_ACCENT": 3}
            if rank[pose] > rank[states[k]]:
                states[k] = pose
    result = []
    start = 0
    for k in range(1, n + 1):
        if k == n or states[k] != states[start]:
            a, b = start * frame_ms, min(k * frame_ms, duration_ms)
            if b > a:
                result.append((a, b, states[start]))
            start = k
    return result


def export_skeleton(sequence, model, plan, duration_ms):
    role = model.details["skeleton_performer_role"]
    windows = pose_timeline(role, plan, duration_ms)
    for part in ("SKULL", "STATIC_BONES", "RIB_CAGE", "LEGS", "INSTRUMENT"):
        if part in model.submodels:
            sequence.effect(model, part, 0, duration_ms, "#C5E8FA", 32)
    for a, b, pose in windows:
        sequence.effect(model, pose, a, b, "#FFE6B0", 75 if pose == "POSE_IDLE" else 100,
                        provenance={"sourceRole": _source_role(role),
                                    "sourceMethod": "helix_source_cue_exclusive_pose",
                                    "sourceStartMs": str(a),
                                    "sourceEndMs": str(b),
                                    "pose": pose})
    return {"model": model.name, "role": role,
            "pose_windows": len(windows),
            "attack_windows": sum(p in ("POSE_ATTACK", "POSE_ACCENT") for _, _, p in windows),
            "exclusive_pose": True, "native_effects": "On",
            "mechanical_actuation": False}
