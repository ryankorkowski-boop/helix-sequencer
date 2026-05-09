#!/usr/bin/env python3
"""
Dream Sequence Weaver Engine — v8.1 (Overwrite + Timing-Track Snap + Drama)

REQUIRES IN SAME FOLDER:
- template .xsq (any existing sequence is OK, even "finished")
- one or more audio files (.wav/.mp3/.flac/.ogg/.m4a)

INSTALL:
  pip install librosa numpy soundfile

RUN:
  python v1.py
  python v1.py --no-prompt
"""

from __future__ import annotations

import argparse, copy, json, sys, time, shutil, re, random, os
from dataclasses import dataclass, field
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import librosa
try:
    import aubio  # type: ignore
except Exception:
    aubio = None

# =============================================================================
#                               v1 CONTROLS
# =============================================================================

VERSION = "v1"

# --- Batch ---
BATCH_MODE = True

# --- Output naming ---
OUTPUT_SUFFIX = ",v1"
SETTINGS_FILENAME = "v1.settings.json"

# --- Overwrite behavior ---
# "layer" = clear only AUTO layer (recommended)
# "all"   = clear ALL effects from targeted elements (aggressive)
CLEAR_MODE = "layer"
AUTO_LAYER_NAME = "AUTO_DreamSequenceWeaver_v1"

# If True, we also try to delete that common "startup blip" (0-400ms) from any layer.
REMOVE_STARTUP_BLIP = True
STARTUP_BLIP_WINDOW_MS = 450

# --- Global feel ---
RANDOMNESS = 0.18
DENSITY = 1.10
SPEED = 1.05
SEED = 1337
VERBOSE = True

# --- Preferred exact names (used only as hints) ---
HOUSE = "18_WHOLE_HOUSE"
GARAGE_ALL = "15_GT_ALL"
ALL_WHITE = "04_ALL_WHITE"
ALL_RED = "05_ALL_RED"
ALL_GREEN = "03_ALL_GREEN"

BLVD_GROUPS = ["BLVD_RIGHT", "BLVD_CENTER", "BLVD_LEFT"]
PERIMETER_OPTIONAL = ["RIGHT_LINDEN", "LEFT_TREE"]

SNOWFLAKE_KEYS = ("snowflake", "sf")
STAR_KEYS = ("star", "stars", "shooting")

ARCH_RE = re.compile(r"arch\s*(\d+)\s*sec\s*(\d+)", re.IGNORECASE)

MEGA_TREE_PREFIX = "Mega Tree"
MEGA_COUNT = 8

ENABLE_CANE_PIANO = True
NORTH_CANE_PREFIX = "North Candy Cane"
SOUTH_CANE_PREFIX = "South Candy Cane"
CANE_COUNT = 16
CANE_GROUP_NORTH = "08_NORTH_CANES"
CANE_GROUP_SOUTH = "09_NOTNORTH_CANES"
NOTES_MAIN = "10_NOTES_MAIN"
NOTES_MIRROR = "11_NOTES_MIRROR"

# --- Timing track names in your template (from your screenshot) ---
TT_BEATS = "Beats"
TT_BARS = "Bars"
TT_ONSETS = "Onsets"
TT_NOTE_ONSETS = "Note Onsets"
TT_PITCH = "Audio Pitch Detector"

# --- Drama / darkness ---
ENABLE_BLACKOUTS = True
BLACKOUT_EVERY_BARS = 4           # blackout at bar boundaries every N bars
BLACKOUT_MS = (160, 320)          # blackout length
PRE_DROP_SPARKLE_MS = 480         # sparkle window before drop-like events
DROP_THRESHOLD = 0.80             # if bass01 near this, treat as drop

# --- Prevent "stuck on" ---
COOLDOWN_RED_MS = 220
COOLDOWN_HOUSE_MS = 140
COOLDOWN_WHITE_MS = 120

# --- Snowflakes: less busy chase ---
SNOW_STEP_MS = 260
SNOW_GATE = 0.12
SNOW_MIN_ON_MS = 35
SNOW_MAX_ON_MS = 160
SNOW_CHASE_COUNT = 1              # 1–2 recommended
SNOW_CHASE_SPREAD = 1
SNOW_CHASE_PROB = 0.75

# --- Stars: more active sparkle ---
STARS_EXTRA_DENSITY = 1.60
STARS_HIT_MS = (55, 130)

# --- Arches ---
BAR_BEATS = 4
FLIP_EVERY_BARS = 2
ARCH_HIT_MS = 130
ARCH_THICKNESS = 5

# --- Ramps / buildups ---
# Requires at least one Ramp effect somewhere in template (otherwise it falls back to On)
BUILDUP_MIN_S = 2.0
BUILDUP_MAX_S = 8.0
BUILDUP_GATE = 0.62              # vocal band average rising above this triggers ramps more often

# --- Mega precision ---
MEGA_ALLOW_TWO_STRINGS = True
MEGA_TWO_STRING_CHANCE = 0.18
MEGA_RED_HIT_MS = (120, 240)
MEGA_GREEN_HIT_MS = (90, 180)
MEGA_WHITE_HIT_MS = (70, 140)

# --- Pitch proxy (fast) ---
HOP_MS = 512
USE_FAST_PITCH = os.environ.get("HELIX_SKIP_LEGACY_PITCH", "").strip().lower() not in {"1", "true", "yes"}

# Safety cap
MAX_EFFECTS_TOTAL = None

# =============================================================================
#                                  UTIL
# =============================================================================

AUDIO_EXTS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
FEEL_PRESETS = {
    "balanced": {"density": 1.00, "speed": 1.00, "randomness": 1.00, "bass": 1.00, "melody": 1.00, "dark": 1.00},
    "aggressive": {"density": 1.22, "speed": 1.12, "randomness": 0.95, "bass": 1.18, "melody": 0.92, "dark": 1.08},
    "airy": {"density": 0.92, "speed": 0.96, "randomness": 1.18, "bass": 0.90, "melody": 1.12, "dark": 0.84},
    "percussive": {"density": 1.12, "speed": 1.05, "randomness": 0.82, "bass": 1.12, "melody": 0.88, "dark": 1.00},
}

@dataclass
class UserProfile:
    feel: str = "balanced"
    density: float = DENSITY
    speed: float = SPEED
    randomness: float = RANDOMNESS
    bass_bias: float = 1.0
    melody_density: float = 1.0
    darkness: float = 1.0
    save_settings: bool = True

@dataclass
class Layout:
    house: str | None
    garage: str | None
    all_white: str | None
    all_red: str | None
    all_green: str | None
    all_notes: str | None
    blvd: list[str]
    blvd_all: str | None
    perim: list[str]
    perim_all: str | None
    snowflakes: list[str]
    stars: list[str]
    arches: dict[int, list[str]]
    mega_group: str | None
    mega_models: list[str]
    line_all: str | None
    line_models: list[str]
    red_models: list[str]
    green_models: list[str]
    white_models: list[str]
    cane_g_n: str | None
    cane_g_s: str | None
    notes_main: str | None
    notes_mirror: str | None
    north_canes: list[str]
    south_canes: list[str]

@dataclass
class TemplateHints:
    guide_models: list[str] = field(default_factory=list)
    green_has_vu: bool = False
    white_has_tendril: bool = False

@dataclass
class PlacementStats:
    counts: dict[str, int] = field(default_factory=dict)

    def bump(self, key: str, amount: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + amount

    def summary(self) -> str:
        if not self.counts:
            return "none"
        return ", ".join(f"{k}={v}" for k, v in sorted(self.counts.items()))

@dataclass
class Section:
    label: str
    start_ms: int
    end_ms: int
    energy: float

def log(msg: str) -> None:
    if not VERBOSE:
        return
    text = f"{msg}\n"
    stream = getattr(sys, "stdout", None)
    if stream is not None:
        try:
            stream.write(text)
            stream.flush()
            return
        except Exception:
            pass

def die(msg: str, code: int = 1) -> None:
    text = f"ERROR: {msg}\n"
    for stream_name in ("stderr", "stdout"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        try:
            stream.write(text)
            stream.flush()
            break
        except Exception:
            continue
    raise SystemExit(code)

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def ms(t_s: float) -> int:
    return int(round(t_s * 1000.0))

def compress_times_ms(times_ms: list[int], min_gap_ms: int) -> list[int]:
    if not times_ms:
        return []
    times_ms = sorted(times_ms)
    out = [times_ms[0]]
    for t in times_ms[1:]:
        if t - out[-1] >= min_gap_ms:
            out.append(t)
    return out

def scaled_gap(base_ms: int) -> int:
    return max(5, int(round(base_ms / max(0.25, DENSITY))))

def scaled_dur(dur_ms: int) -> int:
    return max(15, int(round(dur_ms / max(0.35, SPEED))))

def rng_jitter(rng: random.Random, amount: float, span_ms: int) -> int:
    if amount <= 0:
        return 0
    return int(round(rng.uniform(-span_ms, span_ms) * amount))

def clamp01(v: float) -> float:
    return clamp(v, 0.0, 1.0)

def stable_name_seed(text: str) -> int:
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))

def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()

def prompt_float(label: str, default: float, lo: float, hi: float) -> float:
    try:
        raw = input(f"{label} [{default:.2f}]: ").strip()
    except EOFError:
        return default
    if not raw:
        return default
    try:
        return clamp(float(raw), lo, hi)
    except Exception:
        return default

def prompt_text(label: str, default: str, choices: set[str] | None = None) -> str:
    try:
        raw = input(f"{label} [{default}]: ").strip().lower()
    except EOFError:
        return default
    if not raw:
        return default
    if choices and raw not in choices:
        return default
    return raw

def backup_file(path: Path) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = path.with_suffix(path.suffix + f".bak_{ts}")
    shutil.copy2(path, bak)
    return bak

def find_template_xsq(folder: Path) -> Path:
    xsqs = sorted(folder.glob("*.xsq"))
    if not xsqs:
        die("No .xsq found in folder.")
    scored: list[tuple[int, Path]] = []
    for p in xsqs:
        s = p.name.lower()
        score = 0
        if "template" in s:
            score += 100
        if s.startswith("template"):
            score += 25
        if ",v" in s or ".bak_" in s:
            score -= 80
        if s.startswith("auto_") or s.startswith("test_"):
            score -= 20
        scored.append((score, p))
    scored.sort(key=lambda item: (-item[0], item[1].name.lower()))
    return scored[0][1]

def list_audio_files(folder: Path) -> list[Path]:
    files = []
    for ext in AUDIO_EXTS:
        files += sorted(folder.glob(f"*{ext}"))
    seen = set()
    out = []
    for f in files:
        rp = f.resolve()
        if rp not in seen:
            out.append(f)
            seen.add(rp)
    return out

def output_name(audio_path: Path, folder: Path) -> Path:
    stem = audio_path.stem
    base = folder / f"{stem}{OUTPUT_SUFFIX}.xsq"
    if not base.exists():
        return base
    i = 1
    while True:
        cand = folder / f"{stem}{OUTPUT_SUFFIX} ({i}).xsq"
        if not cand.exists():
            return cand
        i += 1

def load_profile(path: Path) -> UserProfile:
    if not path.exists():
        return UserProfile()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return UserProfile()
    return UserProfile(
        feel=str(data.get("feel", "balanced")).lower(),
        density=float(data.get("density", DENSITY)),
        speed=float(data.get("speed", SPEED)),
        randomness=float(data.get("randomness", RANDOMNESS)),
        bass_bias=float(data.get("bass_bias", 1.0)),
        melody_density=float(data.get("melody_density", 1.0)),
        darkness=float(data.get("darkness", 1.0)),
        save_settings=bool(data.get("save_settings", True)),
    )

def save_profile(path: Path, profile: UserProfile) -> None:
    data = {
        "feel": profile.feel,
        "density": profile.density,
        "speed": profile.speed,
        "randomness": profile.randomness,
        "bass_bias": profile.bass_bias,
        "melody_density": profile.melody_density,
        "darkness": profile.darkness,
        "save_settings": profile.save_settings,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def prompt_for_profile(profile: UserProfile) -> UserProfile:
    if not sys.stdin or not sys.stdin.isatty():
        return profile
    print("\nSequencer controls (press Enter to keep defaults):", flush=True)
    feel = prompt_text("Feel preset: balanced/aggressive/airy/percussive", profile.feel, set(FEEL_PRESETS))
    density = prompt_float("Overall density", profile.density, 0.35, 2.50)
    speed = prompt_float("Effect speed", profile.speed, 0.35, 2.50)
    randomness = prompt_float("Randomness", profile.randomness, 0.00, 1.00)
    bass_bias = prompt_float("Bass focus", profile.bass_bias, 0.50, 2.00)
    melody_density = prompt_float("Melody density", profile.melody_density, 0.50, 2.00)
    darkness = prompt_float("Darkness / drama", profile.darkness, 0.40, 1.80)
    return UserProfile(
        feel=feel,
        density=density,
        speed=speed,
        randomness=randomness,
        bass_bias=bass_bias,
        melody_density=melody_density,
        darkness=darkness,
        save_settings=profile.save_settings,
    )

def apply_profile(profile: UserProfile) -> UserProfile:
    global DENSITY, SPEED, RANDOMNESS
    preset = FEEL_PRESETS.get(profile.feel, FEEL_PRESETS["balanced"])
    applied = UserProfile(
        feel=profile.feel if profile.feel in FEEL_PRESETS else "balanced",
        density=clamp(profile.density * preset["density"], 0.35, 2.50),
        speed=clamp(profile.speed * preset["speed"], 0.35, 2.50),
        randomness=clamp(profile.randomness * preset["randomness"], 0.00, 1.00),
        bass_bias=clamp(profile.bass_bias * preset["bass"], 0.50, 2.20),
        melody_density=clamp(profile.melody_density * preset["melody"], 0.50, 2.20),
        darkness=clamp(profile.darkness * preset["dark"], 0.40, 1.80),
        save_settings=profile.save_settings,
    )
    DENSITY = applied.density
    SPEED = applied.speed
    RANDOMNESS = applied.randomness
    return applied

def choose_exact(names: list[str], preferred: str) -> str | None:
    return preferred if preferred in set(names) else None

def best_name_contains(names: list[str], required: tuple[str, ...], optional: tuple[str, ...] = (),
                       exclude: tuple[str, ...] = ()) -> str | None:
    best = None
    best_score = -1.0
    for name in names:
        norm = normalize_name(name)
        if any(bad in norm for bad in exclude):
            continue
        if any(token not in norm for token in required):
            continue
        score = float(len(required) * 10)
        score += sum(2.0 for token in optional if token in norm)
        score += max(0.0, 4.0 - (len(norm) / 40.0))
        if score > best_score:
            best = name
            best_score = score
    return best

def find_numbered_series(names: list[str], patterns: list[str]) -> list[str]:
    items: list[tuple[int, str]] = []
    for name in names:
        for pattern in patterns:
            m = re.fullmatch(pattern, name.strip(), flags=re.IGNORECASE)
            if m:
                items.append((int(m.group(1)), name))
                break
    items.sort(key=lambda item: item[0])
    return [name for _, name in items]

def find_color_models(names: list[str], color: str, exclude_all: bool = True) -> list[str]:
    out = []
    for name in names:
        norm = normalize_name(name)
        if color not in norm:
            continue
        if exclude_all and " all " in f" {norm} ":
            continue
        out.append(name)
    return sorted(out)

# =============================================================================
#                                  XSQ
# =============================================================================

@dataclass
class EffectTemplate:
    settings: str | None
    palette: str | None

@dataclass
class XsqIndex:
    tree: ET.ElementTree
    root: ET.Element
    elements: dict[str, ET.Element]
    on_tpl: EffectTemplate
    ramp_tpl: EffectTemplate

def _find_any(root: ET.Element, suffix: str) -> list[ET.Element]:
    return [el for el in root.iter() if el.tag.endswith(suffix)]

def _get_attr(el: ET.Element, keys: list[str]) -> str | None:
    for k in keys:
        if k in el.attrib:
            return el.attrib[k]
    return None

def _effect_name(eff: ET.Element) -> str:
    return _get_attr(eff, ["name", "Name", "effectName", "EffectName", "effect", "Effect"]) or ""

def _effect_settings(eff: ET.Element) -> str | None:
    return _get_attr(eff, ["settings", "Settings", "data", "Data"])

def _effect_palette(eff: ET.Element) -> str | None:
    return _get_attr(eff, ["palette", "Palette"])


def effect_name_key(name: str) -> str:
    return (name or "").strip().lower()


def build_effect_template_library(root: ET.Element) -> dict[str, EffectTemplate]:
    """
    Build first-seen template settings/palette per effect name from the source XSQ.
    """
    templates: dict[str, EffectTemplate] = {}
    for eff in _find_any(root, "Effect"):
        name = _effect_name(eff).strip()
        if not name:
            continue
        key = effect_name_key(name)
        if key in templates:
            continue
        templates[key] = EffectTemplate(
            settings=_effect_settings(eff),
            palette=_effect_palette(eff),
        )
    return templates

def load_xsq(path: Path) -> XsqIndex:
    try:
        tree = ET.parse(path)
    except Exception as e:
        die(f"Failed to parse XSQ XML: {path.name}\n{e}")
    root = tree.getroot()

    elements: dict[str, ET.Element] = {}
    for el in _find_any(root, "Element"):
        nm = _get_attr(el, ["name", "Name"])
        if not nm:
            continue
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        if tp == "timing":
            continue
        has_layer = any(c.tag.endswith("EffectLayer") or c.tag.endswith("Layer") for c in list(el))
        has_effect = any(c.tag.endswith("Effect") for c in el.iter())
        if has_layer or has_effect:
            elements[nm.strip()] = el

    # Clone templates for On and Ramp (optional)
    on = EffectTemplate(settings=None, palette=None)
    ramp = EffectTemplate(settings=None, palette=None)

    first_on = None
    first_ramp = None
    for eff in _find_any(root, "Effect"):
        n = _effect_name(eff).strip().lower()
        if first_on is None and n == "on":
            first_on = eff
        if first_ramp is None and n == "ramp":
            first_ramp = eff
        if first_on is not None and first_ramp is not None:
            break

    if first_on is not None:
        on.settings = _effect_settings(first_on)
        on.palette = _effect_palette(first_on)

    if first_ramp is not None:
        ramp.settings = _effect_settings(first_ramp)
        ramp.palette = _effect_palette(first_ramp)

    return XsqIndex(tree=tree, root=root, elements=elements, on_tpl=on, ramp_tpl=ramp)


def _name_lookup_keys(name: str) -> list[str]:
    raw = (name or "").strip()
    if not raw:
        return []
    keys = [raw.lower()]
    norm = normalize_name(raw)
    if norm and norm not in keys:
        keys.append(norm)
    return keys


def _register_lookup_name(lookup: dict[str, str], name: str, *, prefer_exact: bool) -> None:
    for key in _name_lookup_keys(name):
        if prefer_exact:
            lookup[key] = name
        else:
            lookup.setdefault(key, name)


def _layout_entries_and_lookup(layout_path: Path) -> tuple[list[str], dict[str, str]]:
    tree = ET.parse(layout_path)
    root = tree.getroot()

    ordered_names: list[str] = []
    lookup: dict[str, str] = {}

    groups_el = root.find("modelGroups")
    if groups_el is not None:
        for child in list(groups_el):
            name = (child.attrib.get("name") or "").strip()
            if not name:
                continue
            ordered_names.append(name)
            _register_lookup_name(lookup, name, prefer_exact=True)

    models_el = root.find("models")
    if models_el is None:
        return (ordered_names, lookup)
    for child in list(models_el):
        name = (child.attrib.get("name") or "").strip()
        if not name:
            continue
        ordered_names.append(name)
        _register_lookup_name(lookup, name, prefer_exact=True)
        aliases_el = None
        for sub in list(child):
            if sub.tag.endswith("Aliases"):
                aliases_el = sub
                break
        if aliases_el is None:
            aliases = []
        else:
            aliases = list(aliases_el)
        for alias in aliases:
            alias_name = (alias.attrib.get("name") or "").strip()
            if not alias_name:
                continue
            if alias_name.lower().startswith("oldname:"):
                alias_name = alias_name.split(":", 1)[1].strip()
            _register_lookup_name(lookup, alias_name, prefer_exact=False)
        for sub in list(child):
            if not sub.tag.endswith("subModel"):
                continue
            short_name = (sub.attrib.get("name") or "").strip()
            if not short_name:
                continue
            full_name = f"{name}/{short_name}"
            ordered_names.append(full_name)
            _register_lookup_name(lookup, full_name, prefer_exact=True)
            for alias in list(sub.findall("./aliases/alias")):
                alias_name = (alias.attrib.get("name") or "").strip()
                if not alias_name:
                    continue
                if alias_name.lower().startswith("oldname:"):
                    alias_name = alias_name.split(":", 1)[1].strip()
                for candidate in (alias_name, f"{name}/{alias_name}"):
                    _register_lookup_name(lookup, candidate, prefer_exact=False)
    return (ordered_names, lookup)


def _map_layout_name(name: str, lookup: dict[str, str]) -> str | None:
    for key in _name_lookup_keys(name):
        if key in lookup:
            return lookup[key]
    return None


def _new_display_model_entry(name: str) -> ET.Element:
    el = ET.Element("Element")
    el.attrib.update({
        "collapsed": "0",
        "type": "model",
        "name": name,
        "visible": "1",
    })
    return el


def _new_effect_model_entry(name: str) -> ET.Element:
    el = ET.Element("Element")
    el.attrib["type"] = "model"
    el.attrib["name"] = name
    el.append(ET.Element("EffectLayer"))
    return el


def _normalize_view_name(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    out: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        low = item.lower()
        if low in {"0", "default", "master", "master view", "masterview", "master_view"}:
            continue
        if item.isdigit():
            continue
        if low in seen:
            continue
        seen.add(low)
        out.append(item)
    return ",".join(out)


def _ensure_last_view_index(root: ET.Element) -> int:
    last_view = root.find("lastView")
    value = (last_view.text or "").strip() if last_view is not None else ""
    try:
        normalized = max(0, int(value))
    except Exception:
        normalized = 0
    if last_view is None:
        last_view = ET.Element("lastView")
        root.append(last_view)
    last_view.text = str(normalized)
    return normalized


def _is_generated_or_placeholder_timing_track(name: str) -> bool:
    normalized = normalize_name(name)
    if not normalized:
        return False
    if normalized.startswith("auto "):
        return True
    return normalized in {"new timing", "empty", "empty 2"}


def _timing_track_default_visible(track_name: str, active: bool) -> bool:
    if active:
        return True
    return not _is_generated_or_placeholder_timing_track(track_name)


def _merge_effect_model_entry(target: ET.Element, source: ET.Element) -> None:
    existing_names = set()
    unnamed_count = 0
    for layer in list(target):
        if not (layer.tag.endswith("EffectLayer") or layer.tag.endswith("Layer")):
            continue
        lname = (layer.attrib.get("name") or "").strip()
        if lname:
            existing_names.add(lname)
        else:
            unnamed_count += 1
    for layer in list(source):
        if not (layer.tag.endswith("EffectLayer") or layer.tag.endswith("Layer")):
            continue
        lname = (layer.attrib.get("name") or "").strip()
        if lname and lname in existing_names:
            continue
        if not lname and unnamed_count > 0:
            continue
        target.append(copy.deepcopy(layer))
        if lname:
            existing_names.add(lname)
        else:
            unnamed_count += 1


def _collect_effect_elements(root: ET.Element) -> dict[str, ET.Element]:
    elements: dict[str, ET.Element] = {}
    for el in _find_any(root, "Element"):
        nm = _get_attr(el, ["name", "Name"])
        if not nm:
            continue
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        if tp == "timing":
            continue
        has_layer = any(c.tag.endswith("EffectLayer") or c.tag.endswith("Layer") for c in list(el))
        has_effect = any(c.tag.endswith("Effect") for c in el.iter())
        if has_layer or has_effect:
            elements[nm.strip()] = el
    return elements


def sync_xsq_to_layout(xsq: XsqIndex, layout_path: Path | None) -> dict[str, int]:
    if layout_path is None or not layout_path.exists():
        return {"layout_names": 0, "display_updated": 0, "effect_rows_updated": 0, "stale_removed": 0}

    ordered_names, lookup = _layout_entries_and_lookup(layout_path)
    if not ordered_names:
        return {"layout_names": 0, "display_updated": 0, "effect_rows_updated": 0, "stale_removed": 0}

    root = xsq.root
    _ensure_last_view_index(root)
    display = find_root_child(root, "DisplayElements")
    if display is None:
        display = ET.Element("DisplayElements")
        root.append(display)
    element_effects = find_root_child(root, "ElementEffects")
    if element_effects is None:
        element_effects = ET.Element("ElementEffects")
        root.append(element_effects)

    active_timing_display: list[ET.Element] = []
    inactive_timing_display: list[ET.Element] = []
    model_display_by_name: dict[str, ET.Element] = {}
    preserved_order: list[str] = []
    preserved_seen: set[str] = set()
    stale_display = 0
    for el in list(display):
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        if tp == "timing":
            active = (_get_attr(el, ["active", "Active"]) or "").strip()
            el.attrib["views"] = _normalize_view_name(_get_attr(el, ["views", "Views"]))
            bucket = active_timing_display if active == "1" else inactive_timing_display
            bucket.append(copy.deepcopy(el))
            continue
        name = (_get_attr(el, ["name", "Name"]) or "").strip()
        mapped = _map_layout_name(name, lookup)
        if not mapped:
            stale_display += 1
            continue
        clone = copy.deepcopy(el)
        clone.attrib["name"] = mapped
        clone.attrib["type"] = "model"
        if "Views" in clone.attrib:
            del clone.attrib["Views"]
        if "views" in clone.attrib:
            clone.attrib["views"] = _normalize_view_name(clone.attrib.get("views"))
        if mapped not in preserved_seen:
            preserved_seen.add(mapped)
            preserved_order.append(mapped)
        model_display_by_name.setdefault(mapped, clone)

    preferred_names = ordered_names[:]

    for child in list(display):
        display.remove(child)
    for el in active_timing_display:
        display.append(el)
    for name in preferred_names:
        display.append(model_display_by_name.get(name, _new_display_model_entry(name)))
    for el in inactive_timing_display:
        display.append(el)

    active_timing_effects: list[ET.Element] = []
    inactive_timing_effects: list[ET.Element] = []
    model_effects_by_name: dict[str, ET.Element] = {}
    stale_effects = 0
    for el in list(element_effects):
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        if tp == "timing":
            active = (_get_attr(el, ["active", "Active"]) or "").strip()
            bucket = active_timing_effects if active == "1" else inactive_timing_effects
            bucket.append(copy.deepcopy(el))
            continue
        name = (_get_attr(el, ["name", "Name"]) or "").strip()
        mapped = _map_layout_name(name, lookup)
        if not mapped:
            stale_effects += 1
            continue
        clone = copy.deepcopy(el)
        clone.attrib["name"] = mapped
        clone.attrib["type"] = "model"
        existing = model_effects_by_name.get(mapped)
        if existing is None:
            model_effects_by_name[mapped] = clone
        else:
            _merge_effect_model_entry(existing, clone)

    for child in list(element_effects):
        element_effects.remove(child)
    for el in active_timing_effects:
        element_effects.append(el)
    for name in preferred_names:
        element_effects.append(model_effects_by_name.get(name, _new_effect_model_entry(name)))
    for el in inactive_timing_effects:
        element_effects.append(el)

    xsq.elements = _collect_effect_elements(root)
    return {
        "layout_names": len(ordered_names),
        "display_updated": len(model_display_by_name),
        "effect_rows_updated": len(model_effects_by_name),
        "stale_removed": stale_display + stale_effects,
    }

def ensure_layer(el: ET.Element, layer_name: str) -> ET.Element:
    for c in list(el):
        if c.tag.endswith("EffectLayer") or c.tag.endswith("Layer"):
            nm = _get_attr(c, ["name", "Name"])
            if nm and nm.strip() == layer_name:
                return c
    for c in list(el):
        if c.tag.endswith("EffectLayer") or c.tag.endswith("Layer"):
            nm = (_get_attr(c, ["name", "Name"]) or "").strip()
            if not nm:
                c.attrib["name"] = layer_name
                c.attrib.setdefault("visible", "1")
                return c
    layer_tag = None
    for c in list(el):
        if c.tag.endswith("EffectLayer"):
            layer_tag = c.tag
            break
        if c.tag.endswith("Layer"):
            layer_tag = c.tag
            break
    if layer_tag is None:
        layer_tag = "EffectLayer"
    layer = ET.Element(layer_tag)
    layer.attrib["name"] = layer_name
    layer.attrib.setdefault("visible", "1")
    el.append(layer)
    return layer

def _iter_layers(el: ET.Element) -> list[ET.Element]:
    return [c for c in list(el) if c.tag.endswith("EffectLayer") or c.tag.endswith("Layer")]

def clear_effects(el: ET.Element, mode: str, layer_name: str) -> None:
    layers = _iter_layers(el)
    if mode == "all":
        for layer in layers:
            for eff in list(layer):
                if eff.tag.endswith("Effect"):
                    layer.remove(eff)
        return
    # mode == "layer"
    for layer in layers:
        nm = _get_attr(layer, ["name", "Name"]) or ""
        if nm.strip() == layer_name:
            for eff in list(layer):
                if eff.tag.endswith("Effect"):
                    layer.remove(eff)
            return
    # if layer doesn't exist yet, nothing to clear

def remove_startup_blip(el: ET.Element, window_ms: int) -> int:
    removed = 0
    for layer in _iter_layers(el):
        for eff in list(layer):
            if not eff.tag.endswith("Effect"):
                continue
            st = _get_attr(eff, ["startTime", "StartTime"]) or "0"
            en = _get_attr(eff, ["endTime", "EndTime"]) or "0"
            try:
                st_i = int(float(st))
                en_i = int(float(en))
            except Exception:
                continue
            if st_i <= 10 and en_i <= window_ms:
                layer.remove(eff)
                removed += 1
    return removed

def add_effect(layer: ET.Element, start_ms: int, end_ms: int, name: str,
               tpl: EffectTemplate) -> ET.Element:
    eff_tag = None
    for c in list(layer):
        if c.tag.endswith("Effect"):
            eff_tag = c.tag
            break
    if eff_tag is None:
        eff_tag = "Effect"

    start_ms = int(start_ms)
    end_ms = int(max(start_ms + 1, end_ms))

    eff = ET.Element(eff_tag)
    eff.attrib["name"] = name
    eff.attrib["startTime"] = str(start_ms)
    eff.attrib["endTime"] = str(end_ms)

    if tpl.settings is not None:
        eff.attrib["settings"] = tpl.settings
    if tpl.palette is not None:
        eff.attrib["palette"] = tpl.palette

    layer.append(eff)
    return eff

def indent_xml(elem: ET.Element, level: int = 0) -> None:
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent_xml(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# =============================================================================
#                     AUDIO REFERENCE UPDATE (BEST-EFFORT)
# =============================================================================

def replace_audio_references(root: ET.Element, new_audio: Path) -> int:
    new_name = new_audio.name
    changed = 0
    pattern = re.compile(r'[^\\\/"]+\.(wav|mp3|flac|ogg|m4a)', re.IGNORECASE)

    for el in root.iter():
        tag_name = (el.tag.rsplit("}", 1)[-1].lower() if isinstance(el.tag, str) else "")
        handled_text = False

        # Force a portable media reference instead of preserving stale absolute paths.
        if tag_name == "mediafile":
            current = (el.text or "").strip()
            if current != new_name:
                el.text = new_name
                changed += 1
            handled_text = True

        for k in list(el.attrib.keys()):
            v = el.attrib[k]
            if not isinstance(v, str):
                continue
            if pattern.search(v):
                newv, n = pattern.subn(new_name, v)
                if n:
                    el.attrib[k] = newv
                    changed += n
        if not handled_text and el.text and pattern.search(el.text):
            newt, n = pattern.subn(new_name, el.text)
            if n:
                el.text = newt
                changed += n
    return changed

def find_root_child(root: ET.Element, suffix: str) -> ET.Element | None:
    for child in list(root):
        if child.tag.endswith(suffix):
            return child
    return None


def normalize_display_views(root: ET.Element, *, force: bool = True) -> int:
    """
    Keep XSQ view metadata in the simple form xLights expects and hide
    auto-generated timing tracks that would otherwise crowd out model rows.
    """
    display = find_root_child(root, "DisplayElements")
    if display is None:
        return 0
    _ensure_last_view_index(root)
    updated = 0
    for el in list(display):
        tp = (_get_attr(el, ["type", "Type"]) or "").strip().lower()
        if not tp:
            continue
        current = _normalize_view_name(_get_attr(el, ["views", "Views"]))
        if "Views" in el.attrib:
            del el.attrib["Views"]
            updated += 1
        if force or "views" in el.attrib or current:
            if (el.attrib.get("views") or "") != current:
                el.attrib["views"] = current
                updated += 1
        if tp == "timing":
            active = (_get_attr(el, ["active", "Active"]) or "").strip() == "1"
            name = (_get_attr(el, ["name", "Name"]) or "").strip()
            if active or _is_generated_or_placeholder_timing_track(name):
                desired_visible = "1" if _timing_track_default_visible(name, active) else "0"
                if (el.attrib.get("visible") or "") != desired_visible:
                    el.attrib["visible"] = desired_visible
                    updated += 1
            el.attrib.setdefault("collapsed", "0")
            el.attrib.setdefault("active", "1" if active else "0")
            continue
        if "Views" in el.attrib:
            del el.attrib["Views"]
            updated += 1
    return updated


def ensure_master_view_models(root: ET.Element) -> dict[str, int]:
    """
    Ensure DisplayElements + ElementEffects both contain model rows and that
    timing-track visibility does not crowd model rows out of the Sequencer.
    """
    _ensure_last_view_index(root)
    display = find_root_child(root, "DisplayElements")
    if display is None:
        display = ET.Element("DisplayElements")
        root.append(display)
    element_effects = find_root_child(root, "ElementEffects")
    if element_effects is None:
        element_effects = ET.Element("ElementEffects")
        root.append(element_effects)

    updated = 0
    added_display = 0
    added_effects = 0

    display_names: set[str] = set()
    for el in list(display):
        tp = (_get_attr(el, ["type", "Type"]) or "").strip().lower()
        if not tp:
            continue
        if tp == "timing":
            normalized_views = _normalize_view_name(_get_attr(el, ["views", "Views"]))
            if "Views" in el.attrib:
                del el.attrib["Views"]
                updated += 1
            if (el.attrib.get("views") or "") != normalized_views:
                el.attrib["views"] = normalized_views
                updated += 1
            active = (_get_attr(el, ["active", "Active"]) or "").strip() == "1"
            name = (_get_attr(el, ["name", "Name"]) or "").strip()
            if active or _is_generated_or_placeholder_timing_track(name):
                desired_visible = "1" if _timing_track_default_visible(name, active) else "0"
                if (el.attrib.get("visible") or "") != desired_visible:
                    el.attrib["visible"] = desired_visible
                    updated += 1
            el.attrib.setdefault("collapsed", "0")
            el.attrib.setdefault("visible", "1")
            continue
        name = (_get_attr(el, ["name", "Name"]) or "").strip()
        if not name:
            continue
        display_names.add(name)
        normalized_views = _normalize_view_name(_get_attr(el, ["views", "Views"]))
        if "Views" in el.attrib:
            del el.attrib["Views"]
            updated += 1
        if "views" in el.attrib and (el.attrib.get("views") or "") != normalized_views:
            el.attrib["views"] = normalized_views
            updated += 1
        if el.attrib.get("type") != "model":
            el.attrib["type"] = "model"
            updated += 1
        el.attrib.setdefault("collapsed", "0")
        el.attrib.setdefault("visible", "1")

    effect_names: set[str] = set()
    for el in list(element_effects):
        tp = (_get_attr(el, ["type", "Type"]) or "").strip().lower()
        if tp == "timing":
            continue
        name = (_get_attr(el, ["name", "Name"]) or "").strip()
        if not name:
            continue
        effect_names.add(name)
        if el.attrib.get("type") != "model":
            el.attrib["type"] = "model"
            updated += 1
        if not any(c.tag.endswith("EffectLayer") or c.tag.endswith("Layer") for c in list(el)):
            el.append(ET.Element("EffectLayer"))
            updated += 1

    missing_display = sorted(effect_names - display_names)
    for name in missing_display:
        display.append(_new_display_model_entry(name))
        added_display += 1

    missing_effects = sorted(display_names - effect_names)
    if missing_effects:
        insert_at = len(list(element_effects))
        for idx, existing in enumerate(list(element_effects)):
            tp = (_get_attr(existing, ["type", "Type"]) or "").strip().lower()
            if tp != "timing":
                insert_at = idx
                break
        for offset, name in enumerate(missing_effects):
            element_effects.insert(insert_at + offset, _new_effect_model_entry(name))
            added_effects += 1

    return {
        "display_added": added_display,
        "effects_added": added_effects,
        "rows_touched": updated,
    }


def ensure_timing_display_entry(root: ET.Element, track_name: str, active: bool = False) -> ET.Element:
    _ensure_last_view_index(root)
    display = find_root_child(root, "DisplayElements")
    if display is None:
        display = ET.Element("DisplayElements")
        root.append(display)
    desired_visible = "1" if _timing_track_default_visible(track_name, active) else "0"
    for el in list(display):
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        nm = (_get_attr(el, ["name", "Name"]) or "").strip()
        if tp == "timing" and nm == track_name:
            el.attrib["active"] = "1" if active else "0"
            el.attrib.setdefault("collapsed", "0")
            el.attrib["visible"] = desired_visible
            el.attrib["views"] = _normalize_view_name(_get_attr(el, ["views", "Views"]))
            return el
    new_el = ET.Element("Element")
    new_el.attrib.update({
        "collapsed": "0",
        "type": "timing",
        "name": track_name,
        "visible": desired_visible,
        "views": "",
        "active": "1" if active else "0",
    })
    insert_at = len(list(display))
    for idx, existing in enumerate(list(display)):
        tp = (_get_attr(existing, ["type", "Type"]) or "").lower()
        if tp != "timing":
            insert_at = idx
            break
    display.insert(insert_at, new_el)
    return new_el

def ensure_timing_effect_track(root: ET.Element, track_name: str) -> ET.Element:
    element_effects = find_root_child(root, "ElementEffects")
    if element_effects is None:
        element_effects = ET.Element("ElementEffects")
        root.append(element_effects)
    for el in list(element_effects):
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        nm = (_get_attr(el, ["name", "Name"]) or "").strip()
        if tp == "timing" and nm == track_name:
            for child in list(el):
                el.remove(child)
            layer = ET.Element("EffectLayer")
            el.append(layer)
            return layer
    el = ET.Element("Element")
    el.attrib["type"] = "timing"
    el.attrib["name"] = track_name
    layer = ET.Element("EffectLayer")
    el.append(layer)
    insert_at = len(list(element_effects))
    for idx, existing in enumerate(list(element_effects)):
        tp = (_get_attr(existing, ["type", "Type"]) or "").lower()
        if tp != "timing":
            insert_at = idx
            break
    element_effects.insert(insert_at, el)
    return layer

def write_timing_track(root: ET.Element, track_name: str, spans: list[tuple[str, int, int]], active: bool = False) -> None:
    ensure_timing_display_entry(root, track_name, active=active)
    layer = ensure_timing_effect_track(root, track_name)
    for label, st, en in spans:
        eff = ET.Element("Effect")
        eff.attrib["label"] = label
        eff.attrib["startTime"] = str(int(st))
        eff.attrib["endTime"] = str(int(max(st + 1, en)))
        layer.append(eff)


def prune_empty_timing_tracks(root: ET.Element, keep_prefixes: tuple[str, ...] = ()) -> int:
    display = find_root_child(root, "DisplayElements")
    element_effects = find_root_child(root, "ElementEffects")
    if display is None or element_effects is None:
        return 0
    keep_prefixes = tuple(k for k in keep_prefixes if k)
    removed = 0
    keep_names: set[str] = set()
    for el in list(element_effects):
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        if tp != "timing":
            continue
        name = (_get_attr(el, ["name", "Name"]) or "").strip()
        if not name:
            continue
        if keep_prefixes and any(name.startswith(pref) for pref in keep_prefixes):
            keep_names.add(name)
            continue
        has_effect = any(child.tag.endswith("Effect") for child in el.iter())
        if not has_effect:
            element_effects.remove(el)
            removed += 1
        else:
            keep_names.add(name)

    for el in list(display):
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        if tp != "timing":
            continue
        name = (_get_attr(el, ["name", "Name"]) or "").strip()
        if not name:
            continue
        if keep_prefixes and any(name.startswith(pref) for pref in keep_prefixes):
            continue
        if name not in keep_names:
            display.remove(el)
            removed += 1
    return removed


def remove_legacy_timing_tracks(root: ET.Element, *, current_version: str) -> int:
    display = find_root_child(root, "DisplayElements")
    element_effects = find_root_child(root, "ElementEffects")
    if display is None or element_effects is None:
        return 0
    removed = 0
    keep_token = f" {current_version}".lower()
    for el in list(element_effects):
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        if tp != "timing":
            continue
        name = (_get_attr(el, ["name", "Name"]) or "").strip()
        if name.lower().startswith("auto ") and keep_token not in name.lower():
            element_effects.remove(el)
            removed += 1
    for el in list(display):
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        if tp != "timing":
            continue
        name = (_get_attr(el, ["name", "Name"]) or "").strip()
        if name.lower().startswith("auto ") and keep_token not in name.lower():
            display.remove(el)
            removed += 1
    return removed

def report_path_for_output(out_path: Path) -> Path:
    return out_path.with_name(f"{out_path.stem}.report.json")

def write_report_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

# =============================================================================
#                               TIMING TRACKS
# =============================================================================

def read_timing_track_marks_ms(root: ET.Element, track_name: str) -> list[int]:
    """
    Best-effort: find <Element type="timing" name="..."> and extract mark times.
    xLights stores timing marks differently across versions. We try multiple patterns.
    Returns list of mark start times (ms).
    """
    # Find timing element by name
    timing_el = None
    for el in _find_any(root, "Element"):
        tp = (_get_attr(el, ["type", "Type"]) or "").lower()
        nm = (_get_attr(el, ["name", "Name"]) or "").strip()
        if tp == "timing" and nm.lower() == track_name.lower():
            timing_el = el
            break
    if timing_el is None:
        return []

    marks_ms: list[int] = []

    # Pattern A: Timing has child nodes with start/end
    for node in timing_el.iter():
        if node is timing_el:
            continue
        # look for attributes start/end/time
        st = _get_attr(node, ["startTime", "StartTime", "start", "Start", "time", "Time"])
        if st is None:
            continue
        try:
            v = int(round(float(st)))
        except Exception:
            continue
        # sanity: avoid 0-only duplicates
        if v >= 0:
            marks_ms.append(v)

    # De-dup + sort + remove very dense bogus lists if needed
    marks_ms = sorted(set(marks_ms))
    # Often timing elements include both start and end times; we only want starts.
    # If it looks like pairs, we can thin by keeping values that are increasing with reasonable gaps.
    if len(marks_ms) > 20000:
        marks_ms = marks_ms[:20000]
    return marks_ms

# =============================================================================
#                                  AUDIO
# =============================================================================

@dataclass
class Audio:
    sr: int
    y: np.ndarray
    dur_s: float
    onset_ms: list[int]
    beat_ms: list[int]
    times_s: np.ndarray
    centroid: np.ndarray
    rms01: np.ndarray
    bass01: np.ndarray
    vocal01: np.ndarray
    pitch_hz: np.ndarray

def norm01(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    lo = np.nanpercentile(x, 5)
    hi = np.nanpercentile(x, 95)
    if hi <= lo + 1e-9:
        return np.zeros_like(x)
    return np.clip((x - lo) / (hi - lo), 0.0, 1.0)

def analyze(audio_path: Path) -> Audio:
    log(f"Loading audio: {audio_path.name}")
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    dur = float(len(y) / sr)
    log(f"SR={sr} duration={dur:.2f}s")

    hop = HOP_MS
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))**2
    mel = librosa.feature.melspectrogram(S=S, sr=sr, n_mels=128, fmin=20, fmax=11025)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    times_s = librosa.frames_to_time(np.arange(mel.shape[1]), sr=sr, hop_length=hop)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, hop_length=hop,
        backtrack=False, units="frames",
        pre_max=3, post_max=3, pre_avg=3, post_avg=3,
        delta=0.08, wait=0
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop)
    onset_ms = [ms(t) for t in onset_times.tolist()]

    _, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop, units="frames")
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)
    beat_ms = [ms(t) for t in beat_times.tolist()]
    if aubio is not None:
        try:
            beat_ms_aubio = _aubio_beats(y, sr, hop)
            if len(beat_ms_aubio) >= 4:
                beat_ms = beat_ms_aubio
        except Exception:
            pass

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms01 = norm01(rms)

    mel_freqs = librosa.mel_frequencies(n_mels=128, fmin=20, fmax=11025)
    bass_bins = np.where((mel_freqs >= 20) & (mel_freqs <= 180))[0]
    vocal_bins = np.where((mel_freqs >= 300) & (mel_freqs <= 3000))[0]
    bass_db = mel_db[bass_bins, :].mean(axis=0) if len(bass_bins) else mel_db.mean(axis=0)
    vocal_db = mel_db[vocal_bins, :].mean(axis=0) if len(vocal_bins) else mel_db.mean(axis=0)
    bass01 = norm01(bass_db)
    vocal01 = norm01(vocal_db)

    if USE_FAST_PITCH:
        mags = np.sqrt(S)
        pitches, pmags = librosa.piptrack(
            S=mags, sr=sr, hop_length=hop,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7")
        )
        pitch_hz = np.full((pitches.shape[1],), np.nan, dtype=float)
        for t in range(pitches.shape[1]):
            col = pmags[:, t]
            i = int(np.argmax(col))
            p = float(pitches[i, t])
            pitch_hz[t] = p if p > 0 else np.nan
    else:
        pitch_hz = np.full((len(times_s),), np.nan, dtype=float)

    return Audio(sr=sr, y=y, dur_s=dur,
                 onset_ms=onset_ms, beat_ms=beat_ms,
                 times_s=np.asarray(times_s),
                 centroid=np.asarray(centroid),
                 rms01=np.asarray(rms01),
                 bass01=np.asarray(bass01),
                 vocal01=np.asarray(vocal01),
                 pitch_hz=np.asarray(pitch_hz))


def _aubio_beats(y: np.ndarray, sr: int, hop: int) -> list[int]:
    if aubio is None:
        return []
    hop_size = int(hop)
    win_size = max(hop_size * 2, 1024)
    detector = aubio.tempo("default", win_size, hop_size, sr)
    detector.set_silence(-50)
    beats: list[int] = []
    y = np.asarray(y, dtype=np.float32)
    for idx in range(0, len(y), hop_size):
        frame = y[idx: idx + hop_size]
        if len(frame) < hop_size:
            frame = np.pad(frame, (0, hop_size - len(frame)))
        if detector(frame):
            beats.append(int(round(float(detector.get_last_s()) * 1000.0)))
    return compress_times_ms(beats, 30)

def nearest(times: np.ndarray, values: np.ndarray, t: float) -> float:
    if len(times) == 0:
        return float("nan")
    i = int(np.searchsorted(times, t))
    if i <= 0:
        return float(values[0])
    if i >= len(times):
        return float(values[-1])
    return float(values[i] if abs(times[i] - t) < abs(t - times[i - 1]) else values[i - 1])

def peak_times(times_s: np.ndarray, env01: np.ndarray, delta: float, wait_frames: int) -> list[float]:
    if len(env01) < 10:
        return []
    idx = librosa.util.peak_pick(env01, pre_max=3, post_max=3, pre_avg=8, post_avg=8, delta=delta, wait=wait_frames)
    idx = np.asarray(idx, dtype=int)
    idx = idx[(idx >= 0) & (idx < len(times_s))]
    return times_s[idx].tolist()

# =============================================================================
#                               FINDERS
# =============================================================================

def any_key_match(name: str, keys: tuple[str, ...]) -> bool:
    l = name.lower()
    return any(k in l for k in keys)

def parse_arch(name: str) -> tuple[int, int] | None:
    m = ARCH_RE.search(name)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))

def find_arches_by_archnum(names: list[str]) -> dict[int, list[str]]:
    by_arch: dict[int, list[tuple[int, str]]] = {}
    for n in names:
        if "arch" not in n.lower():
            continue
        p = parse_arch(n)
        if not p:
            continue
        arch_num, sec = p
        by_arch.setdefault(arch_num, []).append((sec, n))
    out: dict[int, list[str]] = {}
    for arch_num, items in by_arch.items():
        items.sort(key=lambda x: x[0])
        out[arch_num] = [nm for _, nm in items]
    return out

def find_canes(names: list[str], prefix: str, count: int) -> list[str]:
    s = set(names)
    out = []
    for i in range(1, count + 1):
        nm = f"{prefix} {i}"
        if nm in s:
            out.append(nm)
    return out

def find_mega_strings(names: list[str]) -> tuple[list[str], list[str], list[str]]:
    s = set(names)
    red, green, white = [], [], []
    for i in range(1, MEGA_COUNT + 1):
        r = f"{MEGA_TREE_PREFIX} {i} Red"
        g = f"{MEGA_TREE_PREFIX} {i} Green"
        w = f"{MEGA_TREE_PREFIX} {i} White"
        if r in s: red.append(r)
        if g in s: green.append(g)
        if w in s: white.append(w)
    return red, green, white

def discover_layout(names: list[str]) -> Layout:
    house = choose_exact(names, HOUSE) or best_name_contains(names, ("whole", "house"))
    garage = choose_exact(names, GARAGE_ALL) or best_name_contains(names, ("gt", "all"), ("garage",))
    all_red = choose_exact(names, ALL_RED) or best_name_contains(names, ("all", "red"))
    all_green = choose_exact(names, ALL_GREEN) or best_name_contains(names, ("all", "green"))
    all_white = choose_exact(names, ALL_WHITE) or best_name_contains(names, ("all", "white"))
    all_notes = best_name_contains(names, ("all", "notes"))

    blvd = [n for n in ["BLVD_RIGHT", "BLVD_CENTER", "BLVD_LEFT"] if n in set(names)]
    if not blvd:
        blvd = [n for n in names if "blvd" in normalize_name(n) and "all" not in normalize_name(n)]
        blvd.sort(key=lambda nm: ("right" not in nm.lower(), "center" not in nm.lower(), "left" not in nm.lower(), nm.lower()))
    blvd_all = best_name_contains(names, ("blvd", "all"))

    perim = [n for n in PERIMETER_OPTIONAL if n in set(names)]
    perim_all = best_name_contains(names, ("perimeter", "all"))

    snowflakes = sorted([n for n in names if any_key_match(n, SNOWFLAKE_KEYS) and "all" not in normalize_name(n)])
    stars = sorted([n for n in names if any_key_match(n, STAR_KEYS) and "all" not in normalize_name(n)])
    arches = find_arches_by_archnum(names)

    mega_group = best_name_contains(names, ("mega",), ("tree", "megatree"))
    mega_models = find_numbered_series(names, [r"mt\s*(\d+)", r"mega tree\s*(\d+)"])
    if not mega_models:
        r, g, w = find_mega_strings(names)
        mega_models = r or g or w

    line_all = best_name_contains(names, ("line", "all"))
    line_models = find_numbered_series(names, [r"line\s*(\d+)"])

    cane_g_n = choose_exact(names, CANE_GROUP_NORTH) or best_name_contains(names, ("north", "canes"))
    cane_g_s = choose_exact(names, CANE_GROUP_SOUTH) or best_name_contains(names, ("notnorth", "canes"), ("south",))
    notes_main = choose_exact(names, NOTES_MAIN) or best_name_contains(names, ("notes", "main"))
    notes_mirror = choose_exact(names, NOTES_MIRROR) or best_name_contains(names, ("notes", "mirror"))

    return Layout(
        house=house,
        garage=garage,
        all_white=all_white,
        all_red=all_red,
        all_green=all_green,
        all_notes=all_notes,
        blvd=blvd,
        blvd_all=blvd_all,
        perim=perim,
        perim_all=perim_all,
        snowflakes=snowflakes,
        stars=stars,
        arches=arches,
        mega_group=mega_group,
        mega_models=mega_models,
        line_all=line_all,
        line_models=line_models,
        red_models=find_color_models(names, "red"),
        green_models=find_color_models(names, "green"),
        white_models=find_color_models(names, "white"),
        cane_g_n=cane_g_n,
        cane_g_s=cane_g_s,
        notes_main=notes_main,
        notes_mirror=notes_mirror,
        north_canes=find_canes(names, NORTH_CANE_PREFIX, CANE_COUNT),
        south_canes=find_canes(names, SOUTH_CANE_PREFIX, CANE_COUNT),
    )

def element_effect_names(el: ET.Element) -> list[str]:
    out = []
    for eff in _find_any(el, "Effect"):
        nm = _effect_name(eff).strip()
        if nm:
            out.append(nm)
    return out

def inspect_template_hints(xsq: XsqIndex, layout: Layout) -> TemplateHints:
    guide_models: list[str] = []
    green_has_vu = False
    white_has_tendril = False
    for nm in [layout.all_red, layout.all_green, layout.all_white]:
        if not nm or nm not in xsq.elements:
            continue
        effects = [name.lower() for name in element_effect_names(xsq.elements[nm])]
        if effects:
            guide_models.append(nm)
        if nm == layout.all_green and any("vu meter" in name for name in effects):
            green_has_vu = True
        if nm == layout.all_white and any("tendril" in name for name in effects):
            white_has_tendril = True
    return TemplateHints(
        guide_models=guide_models,
        green_has_vu=green_has_vu,
        white_has_tendril=white_has_tendril,
    )

def layout_summary(layout: Layout) -> str:
    parts = [
        f"house={layout.house or '-'}",
        f"garage={layout.garage or '-'}",
        f"red={layout.all_red or '-'}",
        f"green={layout.all_green or '-'}",
        f"white={layout.all_white or '-'}",
        f"stars={len(layout.stars)}",
        f"snowflakes={len(layout.snowflakes)}",
        f"arches={len(layout.arches)}",
        f"mega={len(layout.mega_models)}",
        f"lines={len(layout.line_models)}",
        f"north_canes={len(layout.north_canes)}",
        f"south_canes={len(layout.south_canes)}",
    ]
    return ", ".join(parts)

def build_vu_windows(audio: Audio, density: float, darkness: float, max_bars: int) -> list[tuple[int, int, int]]:
    windows: list[tuple[int, int, int]] = []
    if max_bars <= 0:
        return windows
    gate = clamp(0.24 - (density - 1.0) * 0.05, 0.12, 0.38)
    step_s = 0.18
    t = 0.0
    while t < audio.dur_s:
        rms_v = nearest(audio.times_s, audio.rms01, t)
        bass_v = nearest(audio.times_s, audio.bass01, t)
        level = clamp01((0.65 * rms_v) + (0.35 * bass_v))
        if np.isfinite(level) and level >= gate:
            bars = max(1, int(round(level * max_bars)))
            dur = max(70, scaled_dur(int(round(90 + (level * 220 * darkness)))))
            st = ms(t)
            windows.append((st, st + dur, bars))
        t += step_s
    return windows

def detect_sections(audio: Audio) -> list[Section]:
    win_s = 8.0
    step_s = 4.0
    raw: list[Section] = []
    t = 0.0
    while t < audio.dur_s:
        analysis_end = min(audio.dur_s, t + win_s)
        span_end = min(audio.dur_s, t + step_s)
        mask = (audio.times_s >= t) & (audio.times_s < analysis_end)
        if not np.any(mask):
            t += step_s
            continue
        rms_v = float(np.nanmean(audio.rms01[mask]))
        bass_v = float(np.nanmean(audio.bass01[mask]))
        vocal_v = float(np.nanmean(audio.vocal01[mask]))
        energy = (0.45 * rms_v) + (0.35 * bass_v) + (0.20 * vocal_v)
        if energy < 0.22:
            label = "BREAK"
        elif bass_v >= 0.65 and rms_v >= 0.55:
            label = "DROP"
        elif vocal_v >= 0.52 and energy >= 0.40:
            label = "BUILD"
        else:
            label = "GROOVE"
        raw.append(Section(label=label, start_ms=ms(t), end_ms=ms(span_end), energy=energy))
        t += step_s

    if not raw:
        return []

    collapsed: list[Section] = [raw[0]]
    for sec in raw[1:]:
        prev = collapsed[-1]
        if sec.label == prev.label and sec.start_ms <= prev.end_ms + 1:
            prev.end_ms = sec.end_ms
            prev.energy = max(prev.energy, sec.energy)
        else:
            collapsed.append(sec)

    if collapsed and collapsed[0].start_ms == 0 and collapsed[0].energy < 0.45:
        collapsed[0].label = "INTRO"
    if collapsed and (audio.dur_s * 1000.0 - collapsed[-1].start_ms) <= 18000 and collapsed[-1].energy < 0.45:
        collapsed[-1].label = "OUTRO"
    return collapsed

def section_for_time(sections: list[Section], t_ms: int) -> str:
    for sec in sections:
        if sec.start_ms <= t_ms < sec.end_ms:
            return sec.label
    return sections[-1].label if sections else "GROOVE"

def section_weight(label: str) -> float:
    return {
        "INTRO": 0.70,
        "BREAK": 0.72,
        "GROOVE": 1.00,
        "BUILD": 1.10,
        "DROP": 1.22,
        "OUTRO": 0.68,
    }.get(label, 1.0)

# =============================================================================
#                           COOLDOWN TRACKING
# =============================================================================

class Cooldowns:
    def __init__(self):
        self.next_ok: dict[str, int] = {}

    def allow(self, key: str, t_ms: int) -> bool:
        return t_ms >= self.next_ok.get(key, -10**9)

    def block(self, key: str, t_ms: int, cooldown_ms: int) -> None:
        self.next_ok[key] = t_ms + cooldown_ms

# =============================================================================
#                              SEQUENCING
# =============================================================================

def _legacy_sequence_one_song(template_xsq: Path, audio_path: Path, out_path: Path) -> None:
    rng = random.Random(SEED + (hash(audio_path.name) % 100000))
    xsq = load_xsq(template_xsq)

    # Update audio references
    rep = replace_audio_references(xsq.root, audio_path)
    log(f"Audio ref replacements: {rep}")

    names = sorted(xsq.elements.keys())
    name_set = set(names)

    def exists(nm: str) -> str | None:
        return nm if nm in name_set else None

    house = exists(HOUSE)
    garage = exists(GARAGE_ALL)
    all_white = exists(ALL_WHITE)
    all_red = exists(ALL_RED)
    all_green = exists(ALL_GREEN)

    blvd = [g for g in BLVD_GROUPS if g in name_set]
    perim = [p for p in PERIMETER_OPTIONAL if p in name_set and p not in set(blvd)]

    snowflakes = sorted([n for n in names if any_key_match(n, SNOWFLAKE_KEYS)])
    stars = sorted([n for n in names if any_key_match(n, STAR_KEYS)])

    arches = find_arches_by_archnum(names)
    arch_nums = sorted(arches.keys())

    mega_r, mega_g, mega_w = find_mega_strings(names)

    cane_g_n = exists(CANE_GROUP_NORTH)
    cane_g_s = exists(CANE_GROUP_SOUTH)
    notes_main = exists(NOTES_MAIN)
    notes_mirror = exists(NOTES_MIRROR)

    north_canes = find_canes(names, NORTH_CANE_PREFIX, CANE_COUNT)
    south_canes = find_canes(names, SOUTH_CANE_PREFIX, CANE_COUNT)

    # --- CLEAR / OVERWRITE ---
    removed_blips = 0
    for nm, el in xsq.elements.items():
        # Clear effects
        clear_effects(el, CLEAR_MODE, AUTO_LAYER_NAME)
        if REMOVE_STARTUP_BLIP:
            removed_blips += remove_startup_blip(el, STARTUP_BLIP_WINDOW_MS)

    if REMOVE_STARTUP_BLIP and removed_blips:
        log(f"Removed startup blip effects: {removed_blips}")

    # Ensure our layer exists everywhere we might write
    layers: dict[str, ET.Element] = {nm: ensure_layer(el, AUTO_LAYER_NAME) for nm, el in xsq.elements.items()}

    total = 0
    cooldowns = Cooldowns()

    ramp_ok = (xsq.ramp_tpl.settings is not None or xsq.ramp_tpl.palette is not None)

    def add(nm: str | None, st: int, en: int, eff: str, tpl: EffectTemplate,
            cd_key: str | None = None, cd_ms: int = 0):
        nonlocal total
        if nm is None or nm not in layers:
            return
        if cd_key and not cooldowns.allow(cd_key, st):
            return
        add_effect(layers[nm], st, en, eff, tpl)
        total += 1
        if cd_key and cd_ms > 0:
            cooldowns.block(cd_key, st, cd_ms)

    a = analyze(audio_path)

    # --- Timing tracks from XSQ (snap grid) ---
    beats_tt = read_timing_track_marks_ms(xsq.root, TT_BEATS)
    bars_tt = read_timing_track_marks_ms(xsq.root, TT_BARS)
    onsets_tt = read_timing_track_marks_ms(xsq.root, TT_ONSETS)
    note_onsets_tt = read_timing_track_marks_ms(xsq.root, TT_NOTE_ONSETS)
    pitch_tt = read_timing_track_marks_ms(xsq.root, TT_PITCH)

    # Fallback to librosa if missing
    beat_ms = beats_tt if len(beats_tt) > 4 else compress_times_ms(a.beat_ms, 40)
    bar_ms = bars_tt if len(bars_tt) > 4 else bar_from_beats(beat_ms, BAR_BEATS)

    onset_ms = onsets_tt if len(onsets_tt) > 8 else compress_times_ms(a.onset_ms, scaled_gap(28))

    # note onset timing helps cane density
    note_onset_ms = note_onsets_tt if len(note_onsets_tt) > 8 else onset_ms

    # --- classify onsets by centroid ---
    hat, snare, kick = [], [], []
    for t_ms in onset_ms:
        c = nearest(a.times_s, a.centroid, t_ms / 1000.0)
        if not np.isfinite(c):
            continue
        if c >= 4500:
            hat.append(t_ms)
        elif c >= 2200:
            snare.append(t_ms)
        else:
            kick.append(t_ms)

    hat = compress_times_ms(hat, scaled_gap(22))
    snare = compress_times_ms(snare, scaled_gap(35))
    kick = compress_times_ms(kick, scaled_gap(45))

    # --- peaks ---
    vocal_peaks = compress_times_ms([ms(t) for t in peak_times(a.times_s, a.vocal01, 0.15, 10)], scaled_gap(110))
    bass_peaks = compress_times_ms([ms(t) for t in peak_times(a.times_s, a.bass01, 0.18, 8)], scaled_gap(85))

    # --- drama blackouts on bar boundaries ---
    blackout_windows: list[tuple[int, int]] = []
    if ENABLE_BLACKOUTS and bar_ms:
        for bi, t in enumerate(bar_ms):
            if bi % max(1, BLACKOUT_EVERY_BARS) == 0 and t > 800:
                dur = scaled_dur(rng.randint(*BLACKOUT_MS))
                blackout_windows.append((t, t + dur))

    def in_blackout(t_ms: int) -> bool:
        for a0, a1 in blackout_windows:
            if a0 <= t_ms <= a1:
                return True
        return False

    # --- backbone ramps (buildups) ---
    # Use vocal-band rising: whenever vocal01 is high, add longer ramps on house/garage.
    if house or garage:
        t = 0.0
        step = 0.25
        while t < a.dur_s:
            v = nearest(a.times_s, a.vocal01, t)
            if np.isfinite(v) and v >= BUILDUP_GATE and rng.random() < 0.12:
                dur_s = rng.uniform(BUILDUP_MIN_S, BUILDUP_MAX_S)
                st = ms(t)
                en = st + ms(dur_s)
                if not in_blackout(st):
                    if ramp_ok:
                        add(house, st, en, "Ramp", xsq.ramp_tpl, cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
                        add(garage, st, en, "Ramp", xsq.ramp_tpl, cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)
                    else:
                        add(house, st, en, "On", xsq.on_tpl, cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
                        add(garage, st, en, "On", xsq.on_tpl, cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)
            t += step

    # --- vocal peaks: pulses + whites ---
    for t_ms in vocal_peaks:
        if in_blackout(t_ms):
            continue
        dur = max(80, scaled_dur(rng.randint(320, 780)) + rng_jitter(rng, RANDOMNESS, 60))
        if ramp_ok:
            add(house, t_ms, t_ms + dur, "Ramp", xsq.ramp_tpl, cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
            add(garage, t_ms, t_ms + dur, "Ramp", xsq.ramp_tpl, cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)
        else:
            add(house, t_ms, t_ms + dur, "On", xsq.on_tpl, cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
            add(garage, t_ms, t_ms + dur, "On", xsq.on_tpl, cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)
        add(all_white, t_ms, t_ms + min(220, dur), "On", xsq.on_tpl, cd_key="white", cd_ms=COOLDOWN_WHITE_MS)

    # --- bass peaks: red punches + pre-drop sparkle ---
    for t_ms in bass_peaks:
        if in_blackout(t_ms):
            continue

        bass_val = nearest(a.times_s, a.bass01, t_ms / 1000.0)
        is_drop = (np.isfinite(bass_val) and bass_val >= DROP_THRESHOLD)

        # pre-drop sparkle window
        if is_drop:
            st = max(0, t_ms - PRE_DROP_SPARKLE_MS)
            for tt in hat:
                if st <= tt < t_ms:
                    d = max(35, scaled_dur(rng.randint(*STARS_HIT_MS)))
                    if stars:
                        add(stars[(tt // 37) % len(stars)], tt, tt + d, "On", xsq.on_tpl)
                    if mega_w:
                        add(mega_w[(tt // 41) % len(mega_w)], tt, tt + d, "On", xsq.on_tpl)

        dur = max(60, scaled_dur(rng.randint(160, 340)) + rng_jitter(rng, RANDOMNESS, 50))
        add(all_red, t_ms, t_ms + dur, "On", xsq.on_tpl, cd_key="red", cd_ms=COOLDOWN_RED_MS)
        add(house, t_ms, t_ms + dur, "On", xsq.on_tpl, cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
        add(garage, t_ms, t_ms + dur, "On", xsq.on_tpl, cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)

    # --- snowflakes: slow sequential chase (volume-gated) ---
    if snowflakes:
        sf_idx = 0
        t = 0.0
        step_s = SNOW_STEP_MS / 1000.0
        while t < a.dur_s:
            if in_blackout(ms(t)):
                t += step_s
                continue
            v = nearest(a.times_s, a.rms01, t)
            if np.isfinite(v) and v >= SNOW_GATE and rng.random() < SNOW_CHASE_PROB:
                on_ms = scaled_dur(int(round(SNOW_MIN_ON_MS + (SNOW_MAX_ON_MS - SNOW_MIN_ON_MS) * float(v))))
                st = ms(t)
                en = st + on_ms
                for j in range(max(1, int(SNOW_CHASE_COUNT))):
                    k = (sf_idx + j * (1 + max(0, int(SNOW_CHASE_SPREAD)))) % len(snowflakes)
                    add(snowflakes[k], st, en, "On", xsq.on_tpl)
                sf_idx = (sf_idx + 1) % len(snowflakes)
            t += step_s

    # --- arches: bar-synced thick sweep with flips ---
    if bar_ms and arch_nums:
        thickness = max(1, int(ARCH_THICKNESS))
        half = thickness // 2

        for bi in range(len(bar_ms) - 1):
            bstart = bar_ms[bi]
            bend = bar_ms[bi + 1]
            if bend - bstart < 200:
                continue
            reverse = ((bi // FLIP_EVERY_BARS) % 2 == 1)

            for arch_num in arch_nums:
                secs = arches.get(arch_num, [])
                if not secs:
                    continue
                order = list(reversed(secs)) if reverse else secs
                step = max(18, int((bend - bstart) / max(1, len(order))))
                hit = scaled_dur(ARCH_HIT_MS)

                for si in range(len(order)):
                    st = bstart + si * step
                    if st >= bend or in_blackout(st):
                        continue
                    en = min(st + hit, bend)

                    try:
                        base_idx = secs.index(order[si])
                    except ValueError:
                        base_idx = si
                    for k in range(base_idx - half, base_idx + half + 1):
                        if 0 <= k < len(secs):
                            add(secs[k], st, en, "On", xsq.on_tpl)

    # --- BLVD: use beats for “phrasing”, melody for selection ---
    if blvd and beat_ms:
        bi = 0
        for t_ms in beat_ms:
            if in_blackout(t_ms):
                continue
            # every 4 beats, do a stronger vocal-ish ramp/pulse
            if bi % 4 == 0 and vocal_peaks:
                dur = max(120, scaled_dur(rng.randint(450, 980)))
                nm = blvd[bi % len(blvd)]
                if ramp_ok:
                    add(nm, t_ms, t_ms + dur, "Ramp", xsq.ramp_tpl)
                else:
                    add(nm, t_ms, t_ms + dur, "On", xsq.on_tpl)
            bi += 1

        # melody accents on onsets
        mi = 0
        for t_ms in note_onset_ms:
            if in_blackout(t_ms):
                continue
            hz = nearest(a.times_s, a.pitch_hz, t_ms / 1000.0)
            if not np.isfinite(hz) or hz <= 0:
                continue
            midi = int(round(float(librosa.hz_to_midi(hz))))
            left = blvd[-1] if len(blvd) >= 3 else blvd[0]
            center = blvd[1] if len(blvd) >= 2 else blvd[0]
            right = blvd[0]

            if midi < 60: nm = left
            elif midi < 72: nm = center
            else: nm = right

            dur = max(60, scaled_dur(rng.randint(130, 280)))
            add(nm, t_ms, t_ms + dur, "On", xsq.on_tpl)
            if all_green and mi % 3 == 0:
                add(all_green, t_ms, t_ms + min(140, dur), "On", xsq.on_tpl)
            mi += 1

    # --- perimeter hat chase ---
    if perim:
        idx = 0
        for t_ms in hat:
            if in_blackout(t_ms):
                continue
            dur = max(40, scaled_dur(rng.randint(70, 130)))
            add(perim[idx % len(perim)], t_ms, t_ms + dur, "On", xsq.on_tpl)
            add(all_white, t_ms, t_ms + min(110, dur), "On", xsq.on_tpl, cd_key="white", cd_ms=COOLDOWN_WHITE_MS)
            idx += 1

    # --- stars: active sparkle from hat onsets ---
    if stars:
        star_gap = max(10, int(round(26 / max(0.5, STARS_EXTRA_DENSITY))))
        star_times = compress_times_ms(hat[:], scaled_gap(star_gap))
        si = 0
        for t_ms in star_times:
            if in_blackout(t_ms):
                continue
            dur = max(35, scaled_dur(rng.randint(*STARS_HIT_MS)))
            add(stars[si % len(stars)], t_ms, t_ms + dur, "On", xsq.on_tpl)
            if rng.random() < 0.25 and len(stars) > 1:
                add(stars[(si + 1) % len(stars)], t_ms + 35, t_ms + 35 + dur, "On", xsq.on_tpl)
            si += 1

    # --- snare/kick colors ---
    for t_ms in snare:
        if in_blackout(t_ms):
            continue
        add(all_green, t_ms, t_ms + scaled_dur(160), "On", xsq.on_tpl)

    for t_ms in kick:
        if in_blackout(t_ms):
            continue
        add(all_red, t_ms, t_ms + scaled_dur(140), "On", xsq.on_tpl, cd_key="red", cd_ms=COOLDOWN_RED_MS)

    # --- mega tree: 1–2 strings at a time ---
    def add_mega(bucket: list[str], idx: int, t_ms: int, dur: int) -> int:
        if not bucket:
            return idx
        add(bucket[idx % len(bucket)], t_ms, t_ms + dur, "On", xsq.on_tpl)
        if MEGA_ALLOW_TWO_STRINGS and len(bucket) > 1 and rng.random() < MEGA_TWO_STRING_CHANCE:
            add(bucket[(idx + 1) % len(bucket)], t_ms, t_ms + dur, "On", xsq.on_tpl)
        return idx + 1

    mr = 0
    for t_ms in bass_peaks:
        if in_blackout(t_ms): continue
        mr = add_mega(mega_r, mr, t_ms, max(60, scaled_dur(rng.randint(*MEGA_RED_HIT_MS))))

    mg = 0
    for t_ms in note_onset_ms:
        if in_blackout(t_ms): continue
        mg = add_mega(mega_g, mg, t_ms, max(50, scaled_dur(rng.randint(*MEGA_GREEN_HIT_MS))))

    mw = 0
    for t_ms in hat:
        if in_blackout(t_ms): continue
        if rng.random() > 0.55:
            continue
        mw = add_mega(mega_w, mw, t_ms, max(40, scaled_dur(rng.randint(*MEGA_WHITE_HIT_MS))))

    # --- cane piano (north + mirrored south + mimic groups) ---
    if ENABLE_CANE_PIANO and north_canes and south_canes:
        note_times = compress_times_ms(note_onset_ms[:], scaled_gap(55))
        n = min(len(north_canes), len(south_canes), CANE_COUNT)
        for t_ms in note_times:
            if in_blackout(t_ms):
                continue
            hz = nearest(a.times_s, a.pitch_hz, t_ms / 1000.0)
            if not np.isfinite(hz) or hz <= 0:
                continue
            midi = int(round(float(librosa.hz_to_midi(hz))))
            idx = int(clamp(round(((midi - 60) / 24.0) * (n - 1)), 0, n - 1))
            idx_m = (n - 1) - idx
            dur = max(45, scaled_dur(rng.randint(90, 170)))

            add(north_canes[idx], t_ms, t_ms + dur, "On", xsq.on_tpl)
            add(south_canes[idx_m], t_ms, t_ms + dur, "On", xsq.on_tpl)
            add(cane_g_n, t_ms, t_ms + dur, "On", xsq.on_tpl)
            add(cane_g_s, t_ms, t_ms + dur, "On", xsq.on_tpl)
            add(notes_main, t_ms, t_ms + dur, "On", xsq.on_tpl)
            add(notes_mirror, t_ms, t_ms + dur, "On", xsq.on_tpl)

    try:
        indent_xml(xsq.root)
    except Exception:
        pass

    xsq.tree.write(out_path, encoding="utf-8", xml_declaration=True)
    log(f"Saved: {out_path.name} | effects added: {total}")

def _v8_2_sequence_one_song(template_xsq: Path, audio_path: Path, out_path: Path, profile: UserProfile) -> None:
    rng = random.Random(SEED + stable_name_seed(audio_path.stem.lower()))

    log("[1/6] Loading template and discovering layout")
    xsq = load_xsq(template_xsq)
    rep = replace_audio_references(xsq.root, audio_path)
    log(f"Audio ref replacements: {rep}")

    names = sorted(xsq.elements.keys())
    layout = discover_layout(names)
    hints = inspect_template_hints(xsq, layout)
    log(f"Layout: {layout_summary(layout)}")
    if hints.guide_models:
        log(f"Guide effects detected on: {', '.join(hints.guide_models)}")

    guide_targets = {nm for nm in hints.guide_models if nm}
    removed_blips = 0
    for nm, el in xsq.elements.items():
        clear_effects(el, "all" if nm in guide_targets else CLEAR_MODE, AUTO_LAYER_NAME)
        if REMOVE_STARTUP_BLIP:
            removed_blips += remove_startup_blip(el, STARTUP_BLIP_WINDOW_MS)
    if REMOVE_STARTUP_BLIP and removed_blips:
        log(f"Removed startup blip effects: {removed_blips}")

    layers: dict[str, ET.Element] = {nm: ensure_layer(el, AUTO_LAYER_NAME) for nm, el in xsq.elements.items()}
    total = 0
    stats = PlacementStats()
    cooldowns = Cooldowns()
    ramp_ok = (xsq.ramp_tpl.settings is not None or xsq.ramp_tpl.palette is not None)

    dark_scale = profile.darkness
    bass_bias = profile.bass_bias
    melody_density = profile.melody_density
    drop_threshold = clamp(DROP_THRESHOLD - ((bass_bias - 1.0) * 0.10), 0.55, 0.92)
    buildup_gate = clamp(BUILDUP_GATE - ((dark_scale - 1.0) * 0.05), 0.42, 0.84)
    blackout_every = max(2, int(round(BLACKOUT_EVERY_BARS / max(0.60, dark_scale))))
    blackout_range = (
        max(90, int(round(BLACKOUT_MS[0] * dark_scale))),
        max(150, int(round(BLACKOUT_MS[1] * dark_scale))),
    )

    def add(nm: str | None, st: int, en: int, eff: str, tpl: EffectTemplate, label: str,
            cd_key: str | None = None, cd_ms: int = 0) -> None:
        nonlocal total
        if nm is None or nm not in layers:
            return
        if MAX_EFFECTS_TOTAL is not None and total >= MAX_EFFECTS_TOTAL:
            return
        if cd_key and not cooldowns.allow(cd_key, st):
            return
        add_effect(layers[nm], st, en, eff, tpl)
        total += 1
        stats.bump(label)
        if cd_key and cd_ms > 0:
            cooldowns.block(cd_key, st, cd_ms)

    def add_bucket(bucket: list[str], idx: int, st: int, en: int, label: str,
                   double_hit: bool = False) -> int:
        if not bucket:
            return idx
        nm = bucket[idx % len(bucket)]
        add(nm, st, en, "On", xsq.on_tpl, label)
        if double_hit and len(bucket) > 1 and rng.random() < MEGA_TWO_STRING_CHANCE:
            add(bucket[(idx + 1) % len(bucket)], st, en, "On", xsq.on_tpl, label)
        return idx + 1

    log("[2/6] Analyzing audio")
    a = analyze(audio_path)

    log("[3/6] Reading timing tracks")
    beats_tt = read_timing_track_marks_ms(xsq.root, TT_BEATS)
    bars_tt = read_timing_track_marks_ms(xsq.root, TT_BARS)
    onsets_tt = read_timing_track_marks_ms(xsq.root, TT_ONSETS)
    note_onsets_tt = read_timing_track_marks_ms(xsq.root, TT_NOTE_ONSETS)
    _ = read_timing_track_marks_ms(xsq.root, TT_PITCH)

    beat_ms = beats_tt if len(beats_tt) > 4 else compress_times_ms(a.beat_ms, 40)
    bar_ms = bars_tt if len(bars_tt) > 4 else bar_from_beats(beat_ms, BAR_BEATS)
    onset_ms = onsets_tt if len(onsets_tt) > 8 else compress_times_ms(a.onset_ms, scaled_gap(28))
    note_gap = max(18, int(round(55 / max(0.50, melody_density))))
    note_onset_source = note_onsets_tt if len(note_onsets_tt) > 8 else onset_ms
    note_onset_ms = compress_times_ms(note_onset_source[:], scaled_gap(note_gap))

    hat, snare, kick = [], [], []
    for t_ms in onset_ms:
        c = nearest(a.times_s, a.centroid, t_ms / 1000.0)
        if not np.isfinite(c):
            continue
        if c >= 4500:
            hat.append(t_ms)
        elif c >= 2200:
            snare.append(t_ms)
        else:
            kick.append(t_ms)

    hat = compress_times_ms(hat, scaled_gap(22))
    snare = compress_times_ms(snare, scaled_gap(35))
    kick = compress_times_ms(kick, scaled_gap(max(30, int(round(45 / max(0.65, bass_bias))))))

    vocal_delta = clamp(0.15 - ((profile.density - 1.0) * 0.02), 0.10, 0.18)
    bass_delta = clamp(0.18 - ((bass_bias - 1.0) * 0.03), 0.10, 0.22)
    vocal_peaks = compress_times_ms([ms(t) for t in peak_times(a.times_s, a.vocal01, vocal_delta, 10)], scaled_gap(110))
    bass_peaks = compress_times_ms(
        [ms(t) for t in peak_times(a.times_s, a.bass01, bass_delta, 8)],
        scaled_gap(max(45, int(round(85 / max(0.50, bass_bias))))),
    )

    blackout_windows: list[tuple[int, int]] = []
    if ENABLE_BLACKOUTS and bar_ms:
        for bi, t_ms in enumerate(bar_ms):
            if bi % blackout_every == 0 and t_ms > 800:
                dur = scaled_dur(rng.randint(*blackout_range))
                blackout_windows.append((t_ms, t_ms + dur))

    def in_blackout(t_ms: int) -> bool:
        for a0, a1 in blackout_windows:
            if a0 <= t_ms <= a1:
                return True
        return False

    log("[4/6] Building effect map")

    if layout.house or layout.garage:
        t = 0.0
        step = 0.25
        while t < a.dur_s:
            v = nearest(a.times_s, a.vocal01, t)
            if np.isfinite(v) and v >= buildup_gate and rng.random() < 0.12:
                dur_s = rng.uniform(BUILDUP_MIN_S, BUILDUP_MAX_S)
                st = ms(t)
                en = st + ms(dur_s)
                if not in_blackout(st):
                    effect_name = "Ramp" if ramp_ok else "On"
                    effect_tpl = xsq.ramp_tpl if ramp_ok else xsq.on_tpl
                    add(layout.house, st, en, effect_name, effect_tpl, "buildups", cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
                    add(layout.garage, st, en, effect_name, effect_tpl, "buildups", cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)
            t += step

    for t_ms in vocal_peaks:
        if in_blackout(t_ms):
            continue
        dur = max(80, scaled_dur(rng.randint(320, 780)) + rng_jitter(rng, RANDOMNESS, 60))
        effect_name = "Ramp" if ramp_ok else "On"
        effect_tpl = xsq.ramp_tpl if ramp_ok else xsq.on_tpl
        add(layout.house, t_ms, t_ms + dur, effect_name, effect_tpl, "vocal_pulses", cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
        add(layout.garage, t_ms, t_ms + dur, effect_name, effect_tpl, "vocal_pulses", cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)
        add(layout.all_white, t_ms, t_ms + min(220, dur), "On", xsq.on_tpl, "white_accents", cd_key="white", cd_ms=COOLDOWN_WHITE_MS)
        if layout.white_models:
            add(layout.white_models[(t_ms // 97) % len(layout.white_models)], t_ms, t_ms + min(180, dur), "On", xsq.on_tpl, "white_accents")

    red_idx = 0
    mega_bass_idx = 0
    for t_ms in bass_peaks:
        if in_blackout(t_ms):
            continue
        bass_val = nearest(a.times_s, a.bass01, t_ms / 1000.0)
        is_drop = (np.isfinite(bass_val) and bass_val >= drop_threshold)
        if is_drop:
            st = max(0, t_ms - PRE_DROP_SPARKLE_MS)
            for tt in hat:
                if st <= tt < t_ms:
                    d = max(35, scaled_dur(rng.randint(*STARS_HIT_MS)))
                    if layout.stars:
                        add(layout.stars[(tt // 37) % len(layout.stars)], tt, tt + d, "On", xsq.on_tpl, "pre_drop")
                    mega_bass_idx = add_bucket(layout.mega_models, mega_bass_idx, tt, tt + d, "pre_drop", double_hit=True)

        dur = max(60, scaled_dur(rng.randint(160, 340)) + rng_jitter(rng, RANDOMNESS, 50))
        add(layout.all_red, t_ms, t_ms + dur, "On", xsq.on_tpl, "bass_red", cd_key="red", cd_ms=COOLDOWN_RED_MS)
        add(layout.house, t_ms, t_ms + dur, "On", xsq.on_tpl, "bass_house", cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
        add(layout.garage, t_ms, t_ms + dur, "On", xsq.on_tpl, "bass_house", cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)
        if layout.red_models:
            red_idx = add_bucket(layout.red_models, red_idx, t_ms, t_ms + dur, "bass_red")
        mega_bass_idx = add_bucket(layout.mega_models, mega_bass_idx, t_ms, t_ms + max(70, scaled_dur(160)), "bass_red", double_hit=True)

    if layout.snowflakes:
        sf_idx = 0
        t = 0.0
        step_s = SNOW_STEP_MS / 1000.0
        snow_gate = clamp(SNOW_GATE - ((melody_density - 1.0) * 0.04), 0.06, 0.24)
        snow_prob = clamp(SNOW_CHASE_PROB * (0.85 + (0.25 * melody_density)), 0.30, 0.98)
        while t < a.dur_s:
            st = ms(t)
            if in_blackout(st):
                t += step_s
                continue
            v = nearest(a.times_s, a.rms01, t)
            if np.isfinite(v) and v >= snow_gate and rng.random() < snow_prob:
                on_ms = scaled_dur(int(round(SNOW_MIN_ON_MS + (SNOW_MAX_ON_MS - SNOW_MIN_ON_MS) * float(v))))
                en = st + on_ms
                for j in range(max(1, int(SNOW_CHASE_COUNT))):
                    k = (sf_idx + j * (1 + max(0, int(SNOW_CHASE_SPREAD)))) % len(layout.snowflakes)
                    add(layout.snowflakes[k], st, en, "On", xsq.on_tpl, "snow_chase")
                sf_idx = (sf_idx + 1) % len(layout.snowflakes)
            t += step_s

    arch_nums = sorted(layout.arches.keys())
    if bar_ms and arch_nums:
        thickness = max(1, int(ARCH_THICKNESS))
        half = thickness // 2
        for bi in range(len(bar_ms) - 1):
            bstart = bar_ms[bi]
            bend = bar_ms[bi + 1]
            if bend - bstart < 200:
                continue
            reverse = ((bi // FLIP_EVERY_BARS) % 2 == 1)
            for arch_num in arch_nums:
                secs = layout.arches.get(arch_num, [])
                if not secs:
                    continue
                order = list(reversed(secs)) if reverse else secs
                step = max(18, int((bend - bstart) / max(1, len(order))))
                hit = scaled_dur(ARCH_HIT_MS)
                for si, sec_name in enumerate(order):
                    st = bstart + si * step
                    if st >= bend or in_blackout(st):
                        continue
                    en = min(st + hit, bend)
                    base_idx = secs.index(sec_name) if sec_name in secs else si
                    for k in range(base_idx - half, base_idx + half + 1):
                        if 0 <= k < len(secs):
                            add(secs[k], st, en, "On", xsq.on_tpl, "arch_sweep")

    phrase_targets = layout.blvd if layout.blvd else layout.line_models
    if phrase_targets and beat_ms:
        for bi, t_ms in enumerate(beat_ms):
            if in_blackout(t_ms):
                continue
            if bi % 4 == 0 and vocal_peaks:
                dur = max(120, scaled_dur(rng.randint(450, 980)))
                nm = phrase_targets[bi % len(phrase_targets)]
                effect_name = "Ramp" if ramp_ok else "On"
                effect_tpl = xsq.ramp_tpl if ramp_ok else xsq.on_tpl
                add(nm, t_ms, t_ms + dur, effect_name, effect_tpl, "phrase_blocks")

    melody_targets = layout.blvd if layout.blvd else layout.line_models
    if melody_targets:
        for i, t_ms in enumerate(note_onset_ms):
            if in_blackout(t_ms):
                continue
            hz = nearest(a.times_s, a.pitch_hz, t_ms / 1000.0)
            if not np.isfinite(hz) or hz <= 0:
                continue
            midi = int(round(float(librosa.hz_to_midi(hz))))
            idx = int(clamp(round(((midi - 52) / 32.0) * (len(melody_targets) - 1)), 0, len(melody_targets) - 1))
            dur = max(60, scaled_dur(rng.randint(130, 280)))
            add(melody_targets[idx], t_ms, t_ms + dur, "On", xsq.on_tpl, "melody_keys")
            if layout.all_green and i % 3 == 0:
                add(layout.all_green, t_ms, t_ms + min(140, dur), "On", xsq.on_tpl, "melody_keys")
            if layout.all_notes:
                add(layout.all_notes, t_ms, t_ms + min(120, dur), "On", xsq.on_tpl, "melody_keys")

    if hints.green_has_vu and (layout.all_green or layout.line_models or layout.green_models):
        vu_targets = layout.line_models if layout.line_models else layout.green_models
        vu_windows = build_vu_windows(a, profile.density, dark_scale, max(len(vu_targets), 1))
        for st, en, bars in vu_windows:
            if in_blackout(st):
                continue
            add(layout.all_green, st, en, "On", xsq.on_tpl, "green_vu", cd_key="green_all", cd_ms=70)
            if vu_targets:
                for nm in vu_targets[:bars]:
                    add(nm, st, en, "On", xsq.on_tpl, "green_vu")

    if layout.perim:
        idx = 0
        for t_ms in hat:
            if in_blackout(t_ms):
                continue
            dur = max(40, scaled_dur(rng.randint(70, 130)))
            add(layout.perim[idx % len(layout.perim)], t_ms, t_ms + dur, "On", xsq.on_tpl, "perimeter")
            add(layout.all_white, t_ms, t_ms + min(110, dur), "On", xsq.on_tpl, "white_accents", cd_key="white", cd_ms=COOLDOWN_WHITE_MS)
            idx += 1

    if layout.stars:
        star_gap = max(10, int(round(26 / max(0.5, STARS_EXTRA_DENSITY * max(0.7, profile.density)))))
        star_times = compress_times_ms(hat[:], scaled_gap(star_gap))
        for si, t_ms in enumerate(star_times):
            if in_blackout(t_ms):
                continue
            dur = max(35, scaled_dur(rng.randint(*STARS_HIT_MS)))
            add(layout.stars[si % len(layout.stars)], t_ms, t_ms + dur, "On", xsq.on_tpl, "stars")
            if rng.random() < 0.25 and len(layout.stars) > 1:
                add(layout.stars[(si + 1) % len(layout.stars)], t_ms + 35, t_ms + 35 + dur, "On", xsq.on_tpl, "stars")

    green_idx = 0
    for t_ms in snare:
        if in_blackout(t_ms):
            continue
        en = t_ms + scaled_dur(160)
        add(layout.all_green, t_ms, en, "On", xsq.on_tpl, "green_hits")
        green_idx = add_bucket(layout.green_models, green_idx, t_ms, en, "green_hits")

    kick_red_idx = red_idx
    for t_ms in kick:
        if in_blackout(t_ms):
            continue
        en = t_ms + scaled_dur(140)
        add(layout.all_red, t_ms, en, "On", xsq.on_tpl, "kick_red", cd_key="red", cd_ms=COOLDOWN_RED_MS)
        kick_red_idx = add_bucket(layout.red_models, kick_red_idx, t_ms, en, "kick_red")

    mega_idx = 0
    for t_ms in note_onset_ms:
        if in_blackout(t_ms):
            continue
        mega_idx = add_bucket(layout.mega_models, mega_idx, t_ms, t_ms + max(50, scaled_dur(rng.randint(*MEGA_GREEN_HIT_MS))), "mega_notes", double_hit=True)

    for t_ms in hat:
        if in_blackout(t_ms) or rng.random() > 0.55:
            continue
        mega_idx = add_bucket(layout.mega_models, mega_idx, t_ms, t_ms + max(40, scaled_dur(rng.randint(*MEGA_WHITE_HIT_MS))), "mega_hats")

    if ENABLE_CANE_PIANO and layout.north_canes and layout.south_canes:
        n = min(len(layout.north_canes), len(layout.south_canes), CANE_COUNT)
        for t_ms in note_onset_ms:
            if in_blackout(t_ms):
                continue
            hz = nearest(a.times_s, a.pitch_hz, t_ms / 1000.0)
            if not np.isfinite(hz) or hz <= 0:
                continue
            midi = int(round(float(librosa.hz_to_midi(hz))))
            idx = int(clamp(round(((midi - 60) / 24.0) * (n - 1)), 0, n - 1))
            idx_m = (n - 1) - idx
            dur = max(45, scaled_dur(rng.randint(90, 170)))
            add(layout.north_canes[idx], t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.south_canes[idx_m], t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.cane_g_n, t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.cane_g_s, t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.notes_main, t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.notes_mirror, t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.all_notes, t_ms, t_ms + min(120, dur), "On", xsq.on_tpl, "cane_piano")

    log("[5/6] Writing sequence")
    try:
        indent_xml(xsq.root)
    except Exception:
        pass

    xsq.tree.write(out_path, encoding="utf-8", xml_declaration=True)
    log(f"[6/6] Saved: {out_path.name} | effects added: {total}")
    log(f"Placement report: {stats.summary()}")

def sequence_one_song(template_xsq: Path, audio_path: Path, out_path: Path, profile: UserProfile) -> None:
    rng = random.Random(SEED + stable_name_seed(audio_path.stem.lower()))

    log("[1/7] Loading template and discovering layout")
    xsq = load_xsq(template_xsq)
    rep = replace_audio_references(xsq.root, audio_path)
    log(f"Audio ref replacements: {rep}")

    names = sorted(xsq.elements.keys())
    layout = discover_layout(names)
    hints = inspect_template_hints(xsq, layout)
    log(f"Layout: {layout_summary(layout)}")
    if hints.guide_models:
        log(f"Guide effects detected on: {', '.join(hints.guide_models)}")

    guide_targets = {nm for nm in hints.guide_models if nm}
    removed_blips = 0
    for nm, el in xsq.elements.items():
        clear_effects(el, "all" if nm in guide_targets else CLEAR_MODE, AUTO_LAYER_NAME)
        if REMOVE_STARTUP_BLIP:
            removed_blips += remove_startup_blip(el, STARTUP_BLIP_WINDOW_MS)
    if REMOVE_STARTUP_BLIP and removed_blips:
        log(f"Removed startup blip effects: {removed_blips}")

    layers: dict[str, ET.Element] = {nm: ensure_layer(el, AUTO_LAYER_NAME) for nm, el in xsq.elements.items()}
    total = 0
    stats = PlacementStats()
    cooldowns = Cooldowns()
    ramp_ok = (xsq.ramp_tpl.settings is not None or xsq.ramp_tpl.palette is not None)

    dark_scale = profile.darkness
    bass_bias = profile.bass_bias
    melody_density = profile.melody_density
    drop_threshold = clamp(DROP_THRESHOLD - ((bass_bias - 1.0) * 0.10), 0.55, 0.92)
    buildup_gate = clamp(BUILDUP_GATE - ((dark_scale - 1.0) * 0.05), 0.42, 0.84)
    blackout_every = max(2, int(round(BLACKOUT_EVERY_BARS / max(0.60, dark_scale))))
    blackout_range = (
        max(90, int(round(BLACKOUT_MS[0] * dark_scale))),
        max(150, int(round(BLACKOUT_MS[1] * dark_scale))),
    )

    timing_buildups: list[tuple[str, int, int]] = []
    timing_bass: list[tuple[str, int, int]] = []
    timing_drops: list[tuple[str, int, int]] = []
    timing_melody: list[tuple[str, int, int]] = []
    timing_green_vu: list[tuple[str, int, int]] = []

    def add(nm: str | None, st: int, en: int, eff: str, tpl: EffectTemplate, label: str,
            cd_key: str | None = None, cd_ms: int = 0) -> None:
        nonlocal total
        if nm is None or nm not in layers:
            return
        if MAX_EFFECTS_TOTAL is not None and total >= MAX_EFFECTS_TOTAL:
            return
        if cd_key and not cooldowns.allow(cd_key, st):
            return
        add_effect(layers[nm], st, en, eff, tpl)
        total += 1
        stats.bump(label)
        if cd_key and cd_ms > 0:
            cooldowns.block(cd_key, st, cd_ms)

    def add_bucket(bucket: list[str], idx: int, st: int, en: int, label: str,
                   double_hit: bool = False) -> int:
        if not bucket:
            return idx
        nm = bucket[idx % len(bucket)]
        add(nm, st, en, "On", xsq.on_tpl, label)
        if double_hit and len(bucket) > 1 and rng.random() < MEGA_TWO_STRING_CHANCE:
            add(bucket[(idx + 1) % len(bucket)], st, en, "On", xsq.on_tpl, label)
        return idx + 1

    log("[2/7] Analyzing audio")
    a = analyze(audio_path)
    sections = detect_sections(a)
    if sections:
        section_text = ", ".join(f"{sec.label}:{sec.start_ms/1000:.1f}-{sec.end_ms/1000:.1f}s" for sec in sections)
        log(f"Sections: {section_text}")

    def sec_name(t_ms: int) -> str:
        return section_for_time(sections, t_ms)

    def allow_event(t_ms: int, base: float = 1.0) -> bool:
        chance = clamp(base * section_weight(sec_name(t_ms)), 0.0, 1.0)
        return rng.random() <= chance

    log("[3/7] Reading timing tracks")
    beats_tt = read_timing_track_marks_ms(xsq.root, TT_BEATS)
    bars_tt = read_timing_track_marks_ms(xsq.root, TT_BARS)
    onsets_tt = read_timing_track_marks_ms(xsq.root, TT_ONSETS)
    note_onsets_tt = read_timing_track_marks_ms(xsq.root, TT_NOTE_ONSETS)
    _ = read_timing_track_marks_ms(xsq.root, TT_PITCH)

    beat_ms = beats_tt if len(beats_tt) > 4 else compress_times_ms(a.beat_ms, 40)
    bar_ms = bars_tt if len(bars_tt) > 4 else bar_from_beats(beat_ms, BAR_BEATS)
    onset_ms = onsets_tt if len(onsets_tt) > 8 else compress_times_ms(a.onset_ms, scaled_gap(28))
    note_gap = max(18, int(round(55 / max(0.50, melody_density))))
    note_onset_source = note_onsets_tt if len(note_onsets_tt) > 8 else onset_ms
    note_onset_ms = compress_times_ms(note_onset_source[:], scaled_gap(note_gap))

    hat, snare, kick = [], [], []
    for t_ms in onset_ms:
        c = nearest(a.times_s, a.centroid, t_ms / 1000.0)
        if not np.isfinite(c):
            continue
        if c >= 4500:
            hat.append(t_ms)
        elif c >= 2200:
            snare.append(t_ms)
        else:
            kick.append(t_ms)

    hat = compress_times_ms(hat, scaled_gap(22))
    snare = compress_times_ms(snare, scaled_gap(35))
    kick = compress_times_ms(kick, scaled_gap(max(30, int(round(45 / max(0.65, bass_bias))))))

    vocal_delta = clamp(0.15 - ((profile.density - 1.0) * 0.02), 0.10, 0.18)
    bass_delta = clamp(0.18 - ((bass_bias - 1.0) * 0.03), 0.10, 0.22)
    vocal_peaks = compress_times_ms([ms(t) for t in peak_times(a.times_s, a.vocal01, vocal_delta, 10)], scaled_gap(110))
    bass_peaks = compress_times_ms(
        [ms(t) for t in peak_times(a.times_s, a.bass01, bass_delta, 8)],
        scaled_gap(max(45, int(round(85 / max(0.50, bass_bias))))),
    )

    blackout_windows: list[tuple[int, int]] = []
    if ENABLE_BLACKOUTS and bar_ms:
        for bi, t_ms in enumerate(bar_ms):
            if bi % blackout_every == 0 and t_ms > 800:
                dur = scaled_dur(rng.randint(*blackout_range))
                blackout_windows.append((t_ms, t_ms + dur))

    def in_blackout(t_ms: int) -> bool:
        for a0, a1 in blackout_windows:
            if a0 <= t_ms <= a1:
                return True
        return False

    log("[4/7] Building effect map")

    if layout.house or layout.garage:
        t = 0.0
        step = 0.25
        while t < a.dur_s:
            v = nearest(a.times_s, a.vocal01, t)
            st = ms(t)
            if np.isfinite(v) and v >= buildup_gate and sec_name(st) in {"BUILD", "GROOVE", "DROP"} and rng.random() < 0.12:
                dur_s = rng.uniform(BUILDUP_MIN_S, BUILDUP_MAX_S)
                en = st + ms(dur_s)
                if not in_blackout(st):
                    effect_name = "Ramp" if ramp_ok else "On"
                    effect_tpl = xsq.ramp_tpl if ramp_ok else xsq.on_tpl
                    add(layout.house, st, en, effect_name, effect_tpl, "buildups", cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
                    add(layout.garage, st, en, effect_name, effect_tpl, "buildups", cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)
                    timing_buildups.append(("Build", st, en))
            t += step

    for t_ms in vocal_peaks:
        if in_blackout(t_ms) or not allow_event(t_ms, 0.90):
            continue
        dur = max(80, scaled_dur(rng.randint(320, 780)) + rng_jitter(rng, RANDOMNESS, 60))
        if sec_name(t_ms) == "BUILD":
            dur = int(dur * 1.18)
        effect_name = "Ramp" if ramp_ok else "On"
        effect_tpl = xsq.ramp_tpl if ramp_ok else xsq.on_tpl
        add(layout.house, t_ms, t_ms + dur, effect_name, effect_tpl, "vocal_pulses", cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
        add(layout.garage, t_ms, t_ms + dur, effect_name, effect_tpl, "vocal_pulses", cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)
        add(layout.all_white, t_ms, t_ms + min(220, dur), "On", xsq.on_tpl, "white_accents", cd_key="white", cd_ms=COOLDOWN_WHITE_MS)
        if layout.white_models:
            add(layout.white_models[(t_ms // 97) % len(layout.white_models)], t_ms, t_ms + min(180, dur), "On", xsq.on_tpl, "white_accents")

    red_idx = 0
    mega_bass_idx = 0
    for t_ms in bass_peaks:
        if in_blackout(t_ms) or not allow_event(t_ms, 0.88):
            continue
        section_label = sec_name(t_ms)
        bass_val = nearest(a.times_s, a.bass01, t_ms / 1000.0)
        is_drop = (np.isfinite(bass_val) and bass_val >= drop_threshold) or section_label == "DROP"
        if is_drop:
            st = max(0, t_ms - PRE_DROP_SPARKLE_MS)
            for tt in hat:
                if st <= tt < t_ms:
                    d = max(35, scaled_dur(rng.randint(*STARS_HIT_MS)))
                    if layout.stars and allow_event(tt, 0.82):
                        add(layout.stars[(tt // 37) % len(layout.stars)], tt, tt + d, "On", xsq.on_tpl, "pre_drop")
                    mega_bass_idx = add_bucket(layout.mega_models, mega_bass_idx, tt, tt + d, "pre_drop", double_hit=True)
            timing_drops.append(("Drop", st, t_ms + scaled_dur(220)))

        dur = max(60, scaled_dur(rng.randint(160, 340)) + rng_jitter(rng, RANDOMNESS, 50))
        if section_label == "DROP":
            dur = int(dur * 1.25)
        add(layout.all_red, t_ms, t_ms + dur, "On", xsq.on_tpl, "bass_red", cd_key="red", cd_ms=COOLDOWN_RED_MS)
        add(layout.house, t_ms, t_ms + dur, "On", xsq.on_tpl, "bass_house", cd_key="house", cd_ms=COOLDOWN_HOUSE_MS)
        add(layout.garage, t_ms, t_ms + dur, "On", xsq.on_tpl, "bass_house", cd_key="garage", cd_ms=COOLDOWN_HOUSE_MS)
        if layout.red_models:
            red_idx = add_bucket(layout.red_models, red_idx, t_ms, t_ms + dur, "bass_red")
            if section_label == "DROP":
                red_idx = add_bucket(layout.red_models, red_idx, t_ms + 40, t_ms + dur, "bass_red")
        mega_bass_idx = add_bucket(layout.mega_models, mega_bass_idx, t_ms, t_ms + max(70, scaled_dur(160)), "bass_red", double_hit=True)
        timing_bass.append(("Bass", t_ms, t_ms + dur))

    if layout.snowflakes:
        sf_idx = 0
        t = 0.0
        step_s = SNOW_STEP_MS / 1000.0
        snow_gate = clamp(SNOW_GATE - ((melody_density - 1.0) * 0.04), 0.06, 0.24)
        snow_prob = clamp(SNOW_CHASE_PROB * (0.85 + (0.25 * melody_density)), 0.30, 0.98)
        while t < a.dur_s:
            st = ms(t)
            if in_blackout(st):
                t += step_s
                continue
            v = nearest(a.times_s, a.rms01, t)
            local_prob = snow_prob * (0.75 if sec_name(st) == "DROP" else 1.0)
            if np.isfinite(v) and v >= snow_gate and rng.random() < local_prob:
                on_ms = scaled_dur(int(round(SNOW_MIN_ON_MS + (SNOW_MAX_ON_MS - SNOW_MIN_ON_MS) * float(v))))
                en = st + on_ms
                for j in range(max(1, int(SNOW_CHASE_COUNT))):
                    k = (sf_idx + j * (1 + max(0, int(SNOW_CHASE_SPREAD)))) % len(layout.snowflakes)
                    add(layout.snowflakes[k], st, en, "On", xsq.on_tpl, "snow_chase")
                sf_idx = (sf_idx + 1) % len(layout.snowflakes)
            t += step_s

    arch_nums = sorted(layout.arches.keys())
    if bar_ms and arch_nums:
        thickness = max(1, int(ARCH_THICKNESS))
        half = thickness // 2
        for bi in range(len(bar_ms) - 1):
            bstart = bar_ms[bi]
            bend = bar_ms[bi + 1]
            if bend - bstart < 200:
                continue
            if sec_name(bstart) in {"BREAK", "OUTRO"} and rng.random() > 0.35:
                continue
            reverse = ((bi // FLIP_EVERY_BARS) % 2 == 1)
            for arch_num in arch_nums:
                secs = layout.arches.get(arch_num, [])
                if not secs:
                    continue
                order = list(reversed(secs)) if reverse else secs
                step = max(18, int((bend - bstart) / max(1, len(order))))
                hit = scaled_dur(ARCH_HIT_MS)
                for si, sec_model in enumerate(order):
                    st = bstart + si * step
                    if st >= bend or in_blackout(st):
                        continue
                    en = min(st + hit, bend)
                    base_idx = secs.index(sec_model) if sec_model in secs else si
                    for k in range(base_idx - half, base_idx + half + 1):
                        if 0 <= k < len(secs):
                            add(secs[k], st, en, "On", xsq.on_tpl, "arch_sweep")

    phrase_targets = layout.blvd if layout.blvd else layout.line_models
    if phrase_targets and beat_ms:
        for bi, t_ms in enumerate(beat_ms):
            if in_blackout(t_ms) or not allow_event(t_ms, 0.82):
                continue
            if bi % 4 == 0 and vocal_peaks:
                dur = max(120, scaled_dur(rng.randint(450, 980)))
                nm = phrase_targets[bi % len(phrase_targets)]
                effect_name = "Ramp" if ramp_ok else "On"
                effect_tpl = xsq.ramp_tpl if ramp_ok else xsq.on_tpl
                add(nm, t_ms, t_ms + dur, effect_name, effect_tpl, "phrase_blocks")

    melody_targets = layout.blvd if layout.blvd else layout.line_models
    if melody_targets:
        for i, t_ms in enumerate(note_onset_ms):
            if in_blackout(t_ms) or not allow_event(t_ms, clamp(0.72 + (0.12 * melody_density), 0.40, 1.0)):
                continue
            hz = nearest(a.times_s, a.pitch_hz, t_ms / 1000.0)
            if not np.isfinite(hz) or hz <= 0:
                continue
            midi = int(round(float(librosa.hz_to_midi(hz))))
            idx = int(clamp(round(((midi - 52) / 32.0) * (len(melody_targets) - 1)), 0, len(melody_targets) - 1))
            dur = max(60, scaled_dur(rng.randint(130, 280)))
            add(melody_targets[idx], t_ms, t_ms + dur, "On", xsq.on_tpl, "melody_keys")
            if layout.all_green and i % 3 == 0:
                add(layout.all_green, t_ms, t_ms + min(140, dur), "On", xsq.on_tpl, "melody_keys")
            if layout.all_notes:
                add(layout.all_notes, t_ms, t_ms + min(120, dur), "On", xsq.on_tpl, "melody_keys")
            timing_melody.append(("Note", t_ms, t_ms + dur))

    if hints.green_has_vu and (layout.all_green or layout.line_models or layout.green_models):
        vu_targets = layout.line_models if layout.line_models else layout.green_models
        vu_windows = build_vu_windows(a, profile.density, dark_scale, max(len(vu_targets), 1))
        for st, en, bars in vu_windows:
            if in_blackout(st) or not allow_event(st, 0.84):
                continue
            add(layout.all_green, st, en, "On", xsq.on_tpl, "green_vu", cd_key="green_all", cd_ms=70)
            if vu_targets:
                for nm in vu_targets[:bars]:
                    add(nm, st, en, "On", xsq.on_tpl, "green_vu")
            timing_green_vu.append(("VU", st, en))

    if layout.perim:
        idx = 0
        for t_ms in hat:
            if in_blackout(t_ms) or not allow_event(t_ms, 0.72):
                continue
            dur = max(40, scaled_dur(rng.randint(70, 130)))
            add(layout.perim[idx % len(layout.perim)], t_ms, t_ms + dur, "On", xsq.on_tpl, "perimeter")
            add(layout.all_white, t_ms, t_ms + min(110, dur), "On", xsq.on_tpl, "white_accents", cd_key="white", cd_ms=COOLDOWN_WHITE_MS)
            idx += 1

    if layout.stars:
        star_gap = max(10, int(round(26 / max(0.5, STARS_EXTRA_DENSITY * max(0.7, profile.density)))))
        star_times = compress_times_ms(hat[:], scaled_gap(star_gap))
        for si, t_ms in enumerate(star_times):
            if in_blackout(t_ms) or not allow_event(t_ms, 0.78):
                continue
            dur = max(35, scaled_dur(rng.randint(*STARS_HIT_MS)))
            add(layout.stars[si % len(layout.stars)], t_ms, t_ms + dur, "On", xsq.on_tpl, "stars")
            if rng.random() < 0.25 and len(layout.stars) > 1:
                add(layout.stars[(si + 1) % len(layout.stars)], t_ms + 35, t_ms + 35 + dur, "On", xsq.on_tpl, "stars")

    green_idx = 0
    for t_ms in snare:
        if in_blackout(t_ms):
            continue
        en = t_ms + scaled_dur(160)
        add(layout.all_green, t_ms, en, "On", xsq.on_tpl, "green_hits")
        green_idx = add_bucket(layout.green_models, green_idx, t_ms, en, "green_hits")

    kick_red_idx = red_idx
    for t_ms in kick:
        if in_blackout(t_ms):
            continue
        en = t_ms + scaled_dur(140)
        add(layout.all_red, t_ms, en, "On", xsq.on_tpl, "kick_red", cd_key="red", cd_ms=COOLDOWN_RED_MS)
        kick_red_idx = add_bucket(layout.red_models, kick_red_idx, t_ms, en, "kick_red")

    mega_idx = 0
    for t_ms in note_onset_ms:
        if in_blackout(t_ms) or not allow_event(t_ms, 0.80):
            continue
        mega_idx = add_bucket(layout.mega_models, mega_idx, t_ms, t_ms + max(50, scaled_dur(rng.randint(*MEGA_GREEN_HIT_MS))), "mega_notes", double_hit=True)

    for t_ms in hat:
        if in_blackout(t_ms) or rng.random() > 0.55 or not allow_event(t_ms, 0.74):
            continue
        mega_idx = add_bucket(layout.mega_models, mega_idx, t_ms, t_ms + max(40, scaled_dur(rng.randint(*MEGA_WHITE_HIT_MS))), "mega_hats")

    if ENABLE_CANE_PIANO and layout.north_canes and layout.south_canes:
        n = min(len(layout.north_canes), len(layout.south_canes), CANE_COUNT)
        for t_ms in note_onset_ms:
            if in_blackout(t_ms) or not allow_event(t_ms, 0.86):
                continue
            hz = nearest(a.times_s, a.pitch_hz, t_ms / 1000.0)
            if not np.isfinite(hz) or hz <= 0:
                continue
            midi = int(round(float(librosa.hz_to_midi(hz))))
            idx = int(clamp(round(((midi - 60) / 24.0) * (n - 1)), 0, n - 1))
            idx_m = (n - 1) - idx
            dur = max(45, scaled_dur(rng.randint(90, 170)))
            add(layout.north_canes[idx], t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.south_canes[idx_m], t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.cane_g_n, t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.cane_g_s, t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.notes_main, t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.notes_mirror, t_ms, t_ms + dur, "On", xsq.on_tpl, "cane_piano")
            add(layout.all_notes, t_ms, t_ms + min(120, dur), "On", xsq.on_tpl, "cane_piano")

    log("[5/7] Writing timing tracks and report")
    track_specs = {
        f"AUTO Sections {VERSION}": [(sec.label, sec.start_ms, sec.end_ms) for sec in sections],
        f"AUTO Buildups {VERSION}": timing_buildups,
        f"AUTO Bass Hits {VERSION}": timing_bass,
        f"AUTO Drops {VERSION}": timing_drops,
        f"AUTO Melody {VERSION}": timing_melody,
        f"AUTO Green VU {VERSION}": timing_green_vu,
    }
    for track_name, spans in track_specs.items():
        if spans:
            write_timing_track(xsq.root, track_name, spans, active=False)

    report_payload = {
        "version": VERSION,
        "audio": audio_path.name,
        "template": template_xsq.name,
        "output": out_path.name,
        "profile": {
            "feel": profile.feel,
            "density": profile.density,
            "speed": profile.speed,
            "randomness": profile.randomness,
            "bass_bias": profile.bass_bias,
            "melody_density": profile.melody_density,
            "darkness": profile.darkness,
        },
        "layout": {
            "house": layout.house,
            "garage": layout.garage,
            "all_red": layout.all_red,
            "all_green": layout.all_green,
            "all_white": layout.all_white,
            "blvd": layout.blvd,
            "perimeter": layout.perim,
            "stars": len(layout.stars),
            "snowflakes": len(layout.snowflakes),
            "arches": len(layout.arches),
            "mega_models": len(layout.mega_models),
            "line_models": len(layout.line_models),
            "north_canes": len(layout.north_canes),
            "south_canes": len(layout.south_canes),
        },
        "guide_models": hints.guide_models,
        "sections": [
            {"label": sec.label, "start_ms": sec.start_ms, "end_ms": sec.end_ms, "energy": round(sec.energy, 4)}
            for sec in sections
        ],
        "timing_tracks": {name: len(spans) for name, spans in track_specs.items() if spans},
        "placements": stats.counts,
        "effects_total": total,
    }
    write_report_json(report_path_for_output(out_path), report_payload)

    log("[6/7] Writing sequence")
    try:
        indent_xml(xsq.root)
    except Exception:
        pass

    xsq.tree.write(out_path, encoding="utf-8", xml_declaration=True)
    log(f"[7/7] Saved: {out_path.name} | effects added: {total}")
    log(f"Placement report: {stats.summary()}")
    log(f"Report saved: {report_path_for_output(out_path).name}")

def bar_from_beats(beats: list[int], beats_per_bar: int) -> list[int]:
    if len(beats) < beats_per_bar:
        return []
    out = []
    for i in range(0, len(beats), beats_per_bar):
        out.append(beats[i])
    return out

# =============================================================================
#                                   MAIN
# =============================================================================

def _legacy_main() -> None:
    folder = Path(".").resolve()
    template = find_template_xsq(folder)
    log(f"Template: {template.name}")
    bak = backup_file(template)
    log(f"Backup: {bak.name}")

    audios = list_audio_files(folder)
    if not audios:
        die("No audio files found.")
    if not BATCH_MODE:
        audios = audios[:1]

    log(f"Processing {len(audios)} audio files...")

    for i, a in enumerate(audios, 1):
        out = output_name(a, folder)
        log(f"\n[{i}/{len(audios)}] {a.name} -> {out.name}")
        try:
            _legacy_sequence_one_song(template, a, out)
        except Exception as e:
            log(f"FAILED: {a.name}: {repr(e)}")

    log("\nDone.")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dream Sequence Weaver xLights auto sequencer v1")
    parser.add_argument("--template", help="Path to template .xsq")
    parser.add_argument("--audio", nargs="*", help="Optional audio file(s) to process")
    parser.add_argument("--single", action="store_true", help="Process only the first audio file")
    parser.add_argument("--feel", choices=sorted(FEEL_PRESETS.keys()))
    parser.add_argument("--density", type=float)
    parser.add_argument("--speed", type=float)
    parser.add_argument("--randomness", type=float)
    parser.add_argument("--bass-bias", type=float, dest="bass_bias")
    parser.add_argument("--melody-density", type=float, dest="melody_density")
    parser.add_argument("--darkness", type=float)
    parser.add_argument("--settings", default=SETTINGS_FILENAME, help="Settings JSON path")
    parser.add_argument("--no-prompt", action="store_true", help="Run without interactive prompts")
    parser.add_argument("--no-save-settings", action="store_true", help="Do not save chosen settings")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output")
    return parser.parse_args()

def resolve_path(folder: Path, raw: str | None) -> Path | None:
    if raw is None:
        return None
    p = Path(raw)
    return p if p.is_absolute() else folder / p

def resolve_audio_inputs(folder: Path, raw_files: list[str] | None) -> list[Path]:
    if not raw_files:
        return list_audio_files(folder)
    out: list[Path] = []
    for raw in raw_files:
        p = resolve_path(folder, raw)
        if p is None or not p.exists():
            die(f"Audio file not found: {raw}")
        out.append(p)
    return out

def merge_profile(base: UserProfile, args: argparse.Namespace) -> UserProfile:
    return UserProfile(
        feel=(args.feel or base.feel).lower(),
        density=float(args.density if args.density is not None else base.density),
        speed=float(args.speed if args.speed is not None else base.speed),
        randomness=float(args.randomness if args.randomness is not None else base.randomness),
        bass_bias=float(args.bass_bias if args.bass_bias is not None else base.bass_bias),
        melody_density=float(args.melody_density if args.melody_density is not None else base.melody_density),
        darkness=float(args.darkness if args.darkness is not None else base.darkness),
        save_settings=(False if args.no_save_settings else base.save_settings),
    )

def main() -> None:
    global VERBOSE
    args = parse_args()
    VERBOSE = not args.quiet

    folder = Path(".").resolve()
    settings_path = resolve_path(folder, args.settings) or (folder / SETTINGS_FILENAME)
    profile = merge_profile(load_profile(settings_path), args)
    if not args.no_prompt:
        profile = prompt_for_profile(profile)
    profile.save_settings = (not args.no_save_settings)
    profile = apply_profile(profile)
    if profile.save_settings:
        save_profile(settings_path, profile)
        log(f"Settings saved: {settings_path.name}")

    template = resolve_path(folder, args.template) if args.template else find_template_xsq(folder)
    if template is None or not template.exists():
        die("Template .xsq not found.")
    audios = resolve_audio_inputs(folder, args.audio)
    if not audios:
        die("No audio files found.")
    if args.single or not BATCH_MODE:
        audios = audios[:1]

    log(f"Template: {template.name}")
    log(
        "Profile: "
        f"feel={profile.feel}, density={profile.density:.2f}, speed={profile.speed:.2f}, "
        f"randomness={profile.randomness:.2f}, bass={profile.bass_bias:.2f}, "
        f"melody={profile.melody_density:.2f}, dark={profile.darkness:.2f}"
    )
    log(f"Processing {len(audios)} audio file(s)...")

    for i, audio in enumerate(audios, 1):
        out = output_name(audio, folder)
        log(f"\n[{i}/{len(audios)}] {audio.name} -> {out.name}")
        try:
            sequence_one_song(template, audio, out, profile)
        except Exception as e:
            log(f"FAILED: {audio.name}: {repr(e)}")

    log("\nDone.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        die("Interrupted.", 130)
    except Exception as e:
        die(f"Unhandled exception: {repr(e)}", 2)
