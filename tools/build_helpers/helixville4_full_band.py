from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PartSpec:
    name: str
    kind: str
    count: int


@dataclass(frozen=True)
class PerformerSpec:
    model_name: str
    state: str
    width: int
    height: int
    x: float
    y: float
    z: float
    start_channel: int
    visual_target: str
    animation_states: tuple[str, ...]
    parts: tuple[PartSpec, ...]


BASE_SNOWMAN_PARTS: tuple[PartSpec, ...] = (
    PartSpec("HEAD", "ellipse", 40),
    PartSpec("FACE", "ellipse", 20),
    PartSpec("HAT", "rect", 24),
    PartSpec("HAT_BAND", "line", 10),
    PartSpec("SCARF", "line", 18),
    PartSpec("TORSO", "ellipse", 48),
    PartSpec("BUTTONS", "line", 9),
    PartSpec("LEFT_ARM", "line", 20),
    PartSpec("RIGHT_ARM", "line", 20),
    PartSpec("PLATFORM", "line", 28),
)


def _p(prefix: str, suffix: str) -> str:
    return f"{prefix}_{suffix}"


FULL_BAND_SPECS: tuple[PerformerSpec, ...] = (
    PerformerSpec(
        model_name="HX_SNOWMAN_DRUMMER",
        state="approved_design_drummer_v1",
        width=96,
        height=72,
        x=345.0,
        y=-58.0,
        z=12.0,
        start_channel=900000,
        visual_target="docs/HELIXVILLE4_DRUMMER_TARGET.md",
        animation_states=("idle_ready", "kick_hit", "snare_hit", "hi_hat_pulse", "tom_fill", "cymbal_crash", "stick_accent", "both_arms_up", "downbeat_impact"),
        parts=(
            *BASE_SNOWMAN_PARTS,
            PartSpec("HAT_HOLLY", "ellipse", 10),
            PartSpec("LEFT_STICK", "line", 12),
            PartSpec("RIGHT_STICK", "line", 12),
            PartSpec("KICK", "ellipse", 72),
            PartSpec("KICK_RIM", "ellipse", 48),
            PartSpec("SNARE", "ellipse", 28),
            PartSpec("SNARE_RIM", "ellipse", 18),
            PartSpec("TOM_LEFT", "ellipse", 32),
            PartSpec("TOM_RIGHT", "ellipse", 32),
            PartSpec("HI_HAT", "ellipse", 22),
            PartSpec("CYMBAL_LEFT", "ellipse", 28),
            PartSpec("CYMBAL_RIGHT", "ellipse", 28),
            PartSpec("STANDS", "line", 44),
        ),
    ),
    PerformerSpec(
        model_name="HX_SNOWMAN_BASSIST",
        state="approved_design_bassist_reactive_strings_v1",
        width=92,
        height=86,
        x=285.0,
        y=-48.0,
        z=12.0,
        start_channel=902000,
        visual_target="docs/HELIXVILLE4_BASSIST_REACTIVE_STRINGS.md",
        animation_states=("ready_idle", "groove_start", "pluck_groove", "neck_slide_up", "pluck_accent", "body_rock", "groove_continue", "hit_end"),
        parts=(
            *BASE_SNOWMAN_PARTS,
            PartSpec("HAT_HOLLY", "ellipse", 10),
            PartSpec("BASS_BODY", "ellipse", 84),
            PartSpec("BASS_NECK", "line", 42),
            PartSpec("BASS_SCROLL", "ellipse", 16),
            PartSpec("STRING_E", "line", 38),
            PartSpec("STRING_A", "line", 38),
            PartSpec("STRING_D", "line", 38),
            PartSpec("STRING_G", "line", 38),
            PartSpec("FINGERBOARD", "line", 36),
            PartSpec("NECK_LOW", "line", 12),
            PartSpec("NECK_MID", "line", 12),
            PartSpec("NECK_HIGH", "line", 12),
            PartSpec("PLUCK_ZONE", "ellipse", 24),
            PartSpec("BRIDGE", "line", 14),
            PartSpec("BODY_RESONANCE", "ellipse", 30),
        ),
    ),
    PerformerSpec(
        model_name="HX_SNOWMAN_GUITARIST",
        state="approved_design_guitarist_reactive_strings_v1",
        width=88,
        height=78,
        x=315.0,
        y=-50.0,
        z=12.0,
        start_channel=904000,
        visual_target="docs/HELIXVILLE4_GUITARIST_REACTIVE_STRINGS.md",
        animation_states=("ready_idle", "strum_down", "chord_groove", "neck_move_up", "pick_accent", "neck_slide", "chord_groove_return", "hit_end"),
        parts=(
            *BASE_SNOWMAN_PARTS,
            PartSpec("HAT_HOLLY", "ellipse", 10),
            PartSpec("GUITAR_BODY", "ellipse", 58),
            PartSpec("GUITAR_NECK", "line", 36),
            PartSpec("GUITAR_HEAD", "ellipse", 14),
            PartSpec("STRING_LOW_E", "line", 28),
            PartSpec("STRING_A", "line", 28),
            PartSpec("STRING_D", "line", 28),
            PartSpec("STRING_G", "line", 28),
            PartSpec("STRING_B", "line", 28),
            PartSpec("STRING_HIGH_E", "line", 28),
            PartSpec("PICK_ZONE", "ellipse", 20),
            PartSpec("PICKUPS", "line", 14),
            PartSpec("BRIDGE", "line", 12),
            PartSpec("FRETBOARD_LOW", "line", 10),
            PartSpec("FRETBOARD_MID", "line", 10),
            PartSpec("FRETBOARD_HIGH", "line", 10),
            PartSpec("BODY_RESONANCE", "ellipse", 24),
        ),
    ),
    PerformerSpec(
        model_name="HX_SNOWMAN_SINGER",
        state="approved_design_singer_vocal_performance_v1",
        width=76,
        height=84,
        x=315.0,
        y=-30.0,
        z=12.0,
        start_channel=906000,
        visual_target="docs/HELIXVILLE4_SINGER_VOCAL_PERFORMANCE.md",
        animation_states=("ready_idle", "sing_start", "hand_raise", "point_out", "emote_high", "heart_feel", "sway_groove", "hit_hold"),
        parts=(
            *BASE_SNOWMAN_PARTS,
            PartSpec("CARROT_NOSE", "ellipse", 8),
            PartSpec("HAT_HOLLY", "ellipse", 10),
            PartSpec("LEFT_HAND", "ellipse", 12),
            PartSpec("RIGHT_HAND_MIC", "ellipse", 12),
            PartSpec("MICROPHONE", "ellipse", 26),
            PartSpec("MIC_STAND", "line", 28),
            PartSpec("MOUTH", "ellipse", 16),
            PartSpec("EYES", "ellipse", 12),
            PartSpec("EYEBROWS", "line", 8),
            PartSpec("VOCAL_GLOW", "ellipse", 34),
        ),
    ),
    PerformerSpec(
        model_name="HX_SNOWMAN_SINGER_FEMALE",
        state="approved_design_female_singer_vocal_performance_v1",
        width=78,
        height=84,
        x=350.0,
        y=-32.0,
        z=12.0,
        start_channel=908000,
        visual_target="docs/HELIXVILLE4_FEMALE_SINGER_VOCAL_PERFORMANCE.md",
        animation_states=("ready_idle", "sing_start", "hand_raise", "point_out", "emote_close", "heart_feel", "sway_groove", "big_vocal", "both_hands_up", "hit_hold"),
        parts=(
            *BASE_SNOWMAN_PARTS,
            PartSpec("BOW", "ellipse", 24),
            PartSpec("EYES", "ellipse", 12),
            PartSpec("EYELASHES", "line", 8),
            PartSpec("CARROT_NOSE", "ellipse", 8),
            PartSpec("MOUTH", "ellipse", 16),
            PartSpec("SCARF_TAIL_LEFT", "line", 10),
            PartSpec("SCARF_TAIL_RIGHT", "line", 10),
            PartSpec("LEFT_HAND", "ellipse", 12),
            PartSpec("RIGHT_HAND", "ellipse", 12),
            PartSpec("MICROPHONE", "ellipse", 26),
            PartSpec("MIC_STAND", "line", 28),
            PartSpec("TORSO_UPPER", "ellipse", 24),
            PartSpec("TORSO_LOWER", "ellipse", 24),
            PartSpec("VOCAL_GLOW", "ellipse", 34),
            PartSpec("STAGE_GLOW", "ellipse", 24),
        ),
    ),
)


def _runs(parts: tuple[PartSpec, ...], prefix: str) -> list[tuple[str, int, int]]:
    out: list[tuple[str, int, int]] = []
    cursor = 1
    for part in parts:
        out.append((_p(prefix, part.name), cursor, cursor + part.count - 1))
        cursor += part.count
    return out


def _custom_model(spec: PerformerSpec) -> str:
    grid = [["." for _ in range(spec.width)] for _ in range(spec.height)]
    cursor = 1

    def put(x: int, y: int) -> None:
        if 0 <= x < spec.width and 0 <= y < spec.height:
            grid[y][x] = str(cursor)

    def ellipse(cx: float, cy: float, rx: float, ry: float, count: int) -> None:
        nonlocal cursor
        for idx in range(count):
            a = math.tau * idx / max(1, count)
            put(int(round(cx + math.cos(a) * rx)), int(round(cy + math.sin(a) * ry)))
            cursor += 1

    def line(x1: float, y1: float, x2: float, y2: float, count: int) -> None:
        nonlocal cursor
        for idx in range(count):
            r = 0 if count <= 1 else idx / (count - 1)
            put(int(round(x1 + (x2 - x1) * r)), int(round(y1 + (y2 - y1) * r)))
            cursor += 1

    def rect(cx: float, cy: float, w: float, h: float, count: int) -> None:
        nonlocal cursor
        for idx in range(count):
            r = idx / max(1, count)
            edge = int(r * 4)
            local = (r * 4) - edge
            if edge == 0:
                x, y = cx - w / 2 + w * local, cy - h / 2
            elif edge == 1:
                x, y = cx + w / 2, cy - h / 2 + h * local
            elif edge == 2:
                x, y = cx + w / 2 - w * local, cy + h / 2
            else:
                x, y = cx - w / 2, cy + h / 2 - h * local
            put(int(round(x)), int(round(y)))
            cursor += 1

    cx = spec.width * 0.48
    for index, part in enumerate(spec.parts):
        n = part.name
        if n == "HEAD":
            ellipse(cx, spec.height * 0.24, spec.width * 0.15, spec.height * 0.10, part.count)
        elif n == "FACE":
            ellipse(cx, spec.height * 0.25, spec.width * 0.07, spec.height * 0.04, part.count)
        elif n == "HAT":
            rect(cx, spec.height * 0.10, spec.width * 0.20, spec.height * 0.08, part.count)
        elif n == "BOW":
            ellipse(cx + 9, spec.height * 0.08, 8, 5, part.count)
        elif n == "HAT_BAND":
            line(cx - 10, spec.height * 0.14, cx + 10, spec.height * 0.14, part.count)
        elif n == "SCARF":
            line(cx - 14, spec.height * 0.34, cx + 14, spec.height * 0.35, part.count)
        elif n == "SCARF_TAIL_LEFT":
            line(cx - 7, spec.height * 0.36, cx - 12, spec.height * 0.50, part.count)
        elif n == "SCARF_TAIL_RIGHT":
            line(cx + 7, spec.height * 0.36, cx + 12, spec.height * 0.50, part.count)
        elif n in {"TORSO", "TORSO_UPPER", "TORSO_LOWER"}:
            y = spec.height * (0.55 if n == "TORSO" else (0.47 if n.endswith("UPPER") else 0.64))
            ellipse(cx, y, spec.width * 0.19, spec.height * 0.18, part.count)
        elif n == "BUTTONS":
            line(cx, spec.height * 0.43, cx, spec.height * 0.70, part.count)
        elif n == "LEFT_ARM":
            line(cx - 12, spec.height * 0.43, cx - 26, spec.height * 0.58, part.count)
        elif n == "RIGHT_ARM":
            line(cx + 12, spec.height * 0.43, cx + 29, spec.height * 0.33, part.count)
        elif "HAND" in n:
            ellipse(cx + (24 if "RIGHT" in n else -24), spec.height * (0.33 if "RIGHT" in n else 0.58), 5, 4, part.count)
        elif n == "PLATFORM":
            line(5, spec.height - 5, spec.width - 5, spec.height - 5, part.count)
        elif "STRING" in n:
            string_index = sum(1 for prior in spec.parts[:index] if "STRING" in prior.name)
            line(cx + 10 + string_index * 2, spec.height * 0.25, cx + 10 + string_index * 2, spec.height * 0.80, part.count)
        elif any(token in n for token in ("BASS_BODY", "GUITAR_BODY", "BODY_RESONANCE", "VOCAL_GLOW", "STAGE_GLOW")):
            ellipse(cx + 16, spec.height * 0.57, spec.width * 0.16, spec.height * 0.16, part.count)
        elif any(token in n for token in ("NECK", "FRETBOARD", "FINGERBOARD")):
            line(cx + 18, spec.height * 0.22, cx + 4, spec.height * 0.74, part.count)
        elif any(token in n for token in ("MIC_STAND", "STANDS")):
            line(cx + 22, spec.height * 0.30, cx + 22, spec.height * 0.82, part.count)
        elif n == "MICROPHONE":
            ellipse(cx + 22, spec.height * 0.29, 6, 8, part.count)
        elif any(token in n for token in ("KICK", "SNARE", "TOM", "CYMBAL", "HI_HAT", "BRIDGE", "PICK", "PICKUPS", "SCROLL", "MOUTH", "EYES", "EYEBROWS", "EYELASHES", "NOSE", "HOLLY")):
            offset = (sum(ord(ch) for ch in n) % 17) - 8
            ellipse(cx + offset, spec.height * (0.50 + ((sum(ord(ch) for ch in n) % 13) / 100)), 6 + (sum(ord(ch) for ch in n) % 7), 4 + (sum(ord(ch) for ch in n) % 5), part.count)
        else:
            ellipse(cx, spec.height * 0.50, 6, 6, part.count)
    return ";".join(",".join(row) for row in grid)


def add_performer_model(models_el: ET.Element, spec: PerformerSpec) -> ET.Element:
    model = ET.SubElement(models_el, "model", {
        "name": spec.model_name,
        "DisplayAs": "Custom",
        "WorldPosX": f"{spec.x:.3f}",
        "WorldPosY": f"{spec.y:.3f}",
        "WorldPosZ": f"{spec.z:.3f}",
        "StartChannel": str(spec.start_channel),
        "StringType": "RGB Nodes",
        "parm1": str(spec.width),
        "parm2": str(spec.height),
        "CustomWidth": str(spec.width),
        "CustomHeight": str(spec.height),
        "CustomModel": _custom_model(spec),
        "HelixVisualTarget": spec.visual_target,
        "HelixImplementationState": spec.state,
        "HelixAnimationStates": ",".join(spec.animation_states),
        "HelixNodeCount": str(sum(part.count for part in spec.parts)),
    })
    for name, start, end in _runs(spec.parts, spec.model_name):
        ET.SubElement(model, "subModel", {"name": name, "line0": f"{start}-{end}", "HelixPixelCount": str(end - start + 1)})
    return model


def add_full_helixville4_band_models(layout_path: Path) -> None:
    tree = ET.parse(layout_path)
    root = tree.getroot()
    models_el = root.find("models")
    if models_el is None:
        models_el = ET.SubElement(root, "models")
    groups_el = root.find("modelGroups")
    if groups_el is None:
        groups_el = ET.SubElement(root, "modelGroups")
    for spec in FULL_BAND_SPECS:
        add_performer_model(models_el, spec)
    members = ",".join(spec.model_name for spec in FULL_BAND_SPECS)
    ET.SubElement(groups_el, "modelGroup", {"name": "HX_SNOWMAN_BAND", "models": members})
    ET.SubElement(groups_el, "modelGroup", {"name": "HX_SNOWMAN_VOCALS", "models": "HX_SNOWMAN_SINGER,HX_SNOWMAN_SINGER_FEMALE"})
    ET.SubElement(groups_el, "modelGroup", {"name": "HX_SNOWMAN_INSTRUMENTS", "models": "HX_SNOWMAN_GUITARIST,HX_SNOWMAN_BASSIST,HX_SNOWMAN_DRUMMER"})
    ET.SubElement(groups_el, "modelGroup", {"name": "HX_SNOWMAN_DRUMS", "models": "HX_SNOWMAN_DRUMMER"})
    ET.SubElement(groups_el, "modelGroup", {"name": "HX_SNOWMAN_STRINGS", "models": "HX_SNOWMAN_GUITARIST,HX_SNOWMAN_BASSIST"})
    tree.write(layout_path, encoding="utf-8", xml_declaration=True)
