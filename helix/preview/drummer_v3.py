"""Asset-first preview support for the authored Drummer V3 artwork.

The production drummer remains xLights/xmodel driven. This adapter makes the
preview renderer use the same authored background and the same named physical
submodel targets used by the V3 contract. Hit events are rendered as additive
illumination over the authored base rather than as whole-frame pose swaps.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_V3_BACKDROP = "fixtures/band_geometry/source/drummerbg_preview_backdrop.png"
DRUMMER_V3_SOURCE = "fixtures/band_geometry/source/drummerbg.png"
DRUMMER_V3_LAYER_MANIFEST = "fixtures/band_geometry/drummer_v3_png_layer_manifest.json"

POSE_TO_LAYER: Mapping[str, str] = {
    "idle_ready": "drummer_idle_ready.png",
    "kick_hit": "drummer_hit_kick.png",
    "snare_hit": "drummer_hit_snare.png",
    "hi_hat_pulse": "drummer_hit_hi_hat.png",
    "left_tom_hit": "drummer_hit_left_tom.png",
    "right_tom_hit": "drummer_hit_right_tom.png",
    "left_crash": "drummer_hit_left_crash.png",
    "right_crash": "drummer_hit_right_crash.png",
    "both_crash": "drummer_hit_both_crash.png",
}

POSE_TO_SUBMODELS: Mapping[str, tuple[str, ...]] = {
    "idle_ready": (),
    "kick_hit": ("HX_SNOWMAN_DRUMMER_V3_KICK",),
    "snare_hit": ("HX_SNOWMAN_DRUMMER_V3_SNARE",),
    "hi_hat_pulse": ("HX_SNOWMAN_DRUMMER_V3_HI_HAT",),
    "left_tom_hit": ("HX_SNOWMAN_DRUMMER_V3_TOM_LEFT",),
    "right_tom_hit": ("HX_SNOWMAN_DRUMMER_V3_TOM_RIGHT",),
    "left_crash": ("HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",),
    "right_crash": ("HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",),
    "both_crash": (
        "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT",
        "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT",
    ),
}

DRUM_TYPE_TO_POSE: Mapping[str, str] = {
    "kick": "kick_hit",
    "snare": "snare_hit",
    "hihat": "hi_hat_pulse",
    "tom": "left_tom_hit",
    "cymbal": "right_crash",
    "drum_bus": "idle_ready",
}


@dataclass(frozen=True)
class DrummerV3RenderEvent:
    timestamp_ms: int
    end_ms: int
    pose: str
    intensity: float
    submodels: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp_ms": self.timestamp_ms,
            "end_ms": self.end_ms,
            "pose": self.pose,
            "intensity": self.intensity,
            "submodels": list(self.submodels),
        }


def pose_for_drum_type(drum_type: str, *, index: int = 0) -> str:
    """Resolve a detector type into the authored V3 pose/submodel target."""
    normalized = str(drum_type or "").strip().lower()
    if normalized == "tom":
        return "right_tom_hit" if index % 2 else "left_tom_hit"
    if normalized == "cymbal":
        return ("left_crash", "right_crash", "both_crash")[index % 3]
    return DRUM_TYPE_TO_POSE.get(normalized, "idle_ready")


def layer_path(asset_root: str | Path, pose: str) -> Path:
    root = Path(asset_root)
    filename = POSE_TO_LAYER.get(str(pose), POSE_TO_LAYER["idle_ready"])
    return root / "fixtures/band_geometry/layers" / filename


def submodels_for_pose(pose: str) -> tuple[str, ...]:
    return tuple(POSE_TO_SUBMODELS.get(str(pose), ()))


def _manifest_path(asset_root: str | Path) -> Path:
    return Path(asset_root) / DRUMMER_V3_LAYER_MANIFEST


def illumination_specs_for_pose(asset_root: str | Path, pose: str) -> list[dict[str, Any]]:
    """Return additive illumination commands for a V3 submodel target.

    The PNG pose files remain an asset-contract resource, but they are no longer
    the canonical hit renderer. The layer manifest's target components and
    normalized commands are the preview illumination contract.
    """
    path = _manifest_path(asset_root)
    if not path.is_file() or pose == "idle_ready":
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data.get("layers", []):
        if item.get("id") == pose:
            return list(item.get("commands", []))
    return []


def illumination_targets_for_pose(asset_root: str | Path, pose: str) -> tuple[str, ...]:
    """Return the named physical V3 submodels targeted by a pose."""
    _ = asset_root
    return submodels_for_pose(pose)


def build_render_event(
    *,
    timestamp_ms: int,
    drum_type: str,
    velocity: float,
    index: int = 0,
    duration_ms: int = 150,
) -> DrummerV3RenderEvent:
    pose = pose_for_drum_type(drum_type, index=index)
    return DrummerV3RenderEvent(
        timestamp_ms=int(timestamp_ms),
        end_ms=int(timestamp_ms) + max(1, int(duration_ms)),
        pose=pose,
        intensity=max(0.0, min(1.0, float(velocity))),
        submodels=submodels_for_pose(pose),
    )


def render_events_from_reactive_cues(cues: list[Mapping[str, Any]]) -> list[DrummerV3RenderEvent]:
    """Bridge reactive drummer cues into V3 submodel-targeted events."""
    events: list[DrummerV3RenderEvent] = []
    for cue in cues:
        pose = str(cue.get("pose", cue.get("v3_pose", "idle_ready")) or "idle_ready")
        if pose == "downbeat_impact":
            pose = "idle_ready"
        start_ms = int(cue.get("pose_start_ms", cue.get("start_ms", 0)) or 0)
        end_ms = int(cue.get("pose_end_ms", cue.get("end_ms", start_ms + 150)) or (start_ms + 150))
        intensity = float(cue.get("v3_intensity", cue.get("velocity", 0.0)) or 0.0)
        events.append(
            DrummerV3RenderEvent(
                timestamp_ms=start_ms,
                end_ms=max(start_ms + 1, end_ms),
                pose=pose if pose in POSE_TO_LAYER else "idle_ready",
                intensity=max(0.0, min(1.0, intensity)),
                submodels=tuple(cue.get("v3_submodels", ())) or submodels_for_pose(pose),
            )
        )
    return events


def validate_asset_contract(asset_root: str | Path) -> list[str]:
    """Return missing authored assets; an empty list means the contract is intact."""
    root = Path(asset_root)
    required = [
        root / DRUMMER_V3_BACKDROP,
        root / DRUMMER_V3_SOURCE,
        root / DRUMMER_V3_LAYER_MANIFEST,
    ]
    required.extend(layer_path(root, pose) for pose in POSE_TO_LAYER)
    return [str(path) for path in required if not path.is_file()]


def active_events(events: list[DrummerV3RenderEvent], timestamp_ms: int) -> list[DrummerV3RenderEvent]:
    """Return V3 events active at a preview timestamp."""
    return [event for event in events if event.timestamp_ms <= timestamp_ms < event.end_ms]
