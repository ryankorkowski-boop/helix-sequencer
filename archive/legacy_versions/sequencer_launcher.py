from __future__ import annotations

import os
import queue
import json
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

try:
    from PIL import Image, ImageTk  # type: ignore
except Exception:
    Image = None
    ImageTk = None

import xlights_feature_bridge as xfb
import xlights_model_parser as xmp
import v1 as base


APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
WORK_ROOT = Path.cwd().resolve()
ROOT = WORK_ROOT if WORK_ROOT.exists() else APP_ROOT
USER_HOME = Path.home()
AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
CATALOG_PATH = ROOT / xfb.CATALOG_FILENAME
LAYOUT_FALLBACK = ROOT / "xlights_rgbeffects.xml"
if not LAYOUT_FALLBACK.exists() and (ROOT / "xlights_rgbeffects.xbkp").exists():
    LAYOUT_FALLBACK = ROOT / "xlights_rgbeffects.xbkp"
SUPPORT_DONATE_URL = "https://www.paypal.com/donate/?hosted_button_id=BB6366BT755H6"
AUTHOR_SUPPORT_URL = "https://paypal.me/ryankorkowski"
SUPPORT_FACEBOOK_URL = "https://www.facebook.com/groups/628061113896314/"
XLIGHTS_HOME_URL = "https://www.xlights.org/"
XLIGHTS_MANUAL_URL = "https://manual.xlights.org/"
XLIGHTS_REPO_URL = "https://github.com/xLightsSequencer/xLights"
XLIGHTS_LICENSE_URL = "https://github.com/xLightsSequencer/xLights/blob/master/License.txt"
LUA_LICENSE_URL = "https://www.lua.org/license.html"
THIRD_PARTY_LICENSES_FILE = ROOT / "THIRD_PARTY_LICENSES.md"
APP_BRAND = "Helix Sequence Weaver"
BETA_RELEASE_TEXT = "Beta"
BANNER_BG = "#f8f8f8"
BANNER_BORDER = "#d7d7d7"
LAUNCHER_STATE_FILE = ROOT / "launcher_state.json"

XLIGHTS_LICENSE_NOTICE = (
    "xLights License Notice\n"
    "xLights is distributed by the xLights project under the GNU General Public License, Version 3 (GPL-3.0).\n\n"
    "What this means for distributions:\n"
    "- If you distribute xLights itself, or a derivative work based on GPL-licensed xLights code, GPL-3.0 obligations apply.\n"
    "- GPL-3.0 generally requires preserving notices, providing the GPL license text, and making corresponding source available to recipients.\n"
    "- GPL-3.0 also includes a no-warranty disclaimer.\n\n"
    "Project relationship:\n"
    f"- {APP_BRAND} is an independent tool and is not affiliated with, endorsed by, sponsored by, or officially connected to the xLights development team.\n\n"
    "Official sources:\n"
    "- xLights repository: https://github.com/xLightsSequencer/xLights\n"
    "- xLights license file: https://github.com/xLightsSequencer/xLights/blob/master/License.txt\n"
    "- Lua license page (MIT-style): https://www.lua.org/license.html\n\n"
    "Lua scripting note:\n"
    "- xLights supports Lua scripts via its Run Scripts tooling. The Lua language is MIT-licensed; include Lua license notice where applicable.\n"
)

HELIX_COMMERCIAL_NOTICE = (
    "\nHelix Sequence Weaver Publisher Policy (notice only; not legal advice)\n"
    "- This policy applies to Helix Sequence Weaver-authored templates, presets, scripts, and branded assets included with this tool.\n"
    "- This policy does not change rights granted by third-party licenses (including xLights GPL-3.0 and Lua MIT).\n"
    "- Personal/homeowner use is free.\n"
    "- Nonprofit/community use is free when no sequence sales occur.\n"
    "- For commercial sequence sales based on Helix Sequence Weaver-generated starter output, a one-time author support fee is strongly suggested before first sale.\n"
    "- Recommended minimum one-time support fee: $150 USD.\n"
    "- Attribution is required when redistributing Helix Sequence Weaver-authored template material or branded assets in commercial deliverables.\n"
    "- Recommended attribution text: 'Base sequence generated with Helix Sequence Weaver.'\n"
    "- Vendors are encouraged to donate directly to the xLights project.\n"
    "- Only process songs/sequences you are licensed to use.\n"
    f"- {APP_BRAND} and its publisher are not responsible for user misuse of licensed third-party content.\n"
)

PYTHON_PATH = next(
    (
        path
        for path in (
            Path(r"C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"),
            APP_ROOT / "python312.cmd",
            Path(sys.executable),
        )
        if path.exists()
    ),
    Path(sys.executable),
)


@dataclass(frozen=True)
class VariantOption:
    version: str
    label: str
    note: str
    group: str


@dataclass(frozen=True)
class StyleTypePreset:
    label: str
    note: str
    versions: tuple[str, ...]
    density: float
    speed: float
    randomness: float
    energy: float
    palette_label: str = "Workspace Match"
    ac_only: bool = False


VARIANT_OPTIONS: list[VariantOption] = [
    VariantOption("v10.1", "Matrix Narrative", "Scene-morph storytelling for matrix-style movement.", "Proven Picks"),
    VariantOption("v10.2", "Kinetic Relay", "Percussion relay handoffs with tight motion pacing.", "Proven Picks"),
    VariantOption("v10.3", "Choir Focus", "Vocal-forward choreography with support accents.", "Proven Picks"),
    VariantOption("v11.1", "Spatial Conductor", "High-control spatial routing with strict layering.", "Proven Picks"),
    VariantOption("v11.2", "Orbital Anthem", "Big orbital sweeps and dramatic section builds.", "Proven Picks"),
    VariantOption("v11.3", "Universal Showcase", "Wide model integration across the full layout.", "Proven Picks"),
    VariantOption("v12.1", "Build Pulse", "Intensity build ramps and drop-focused timing.", "New Explorers"),
    VariantOption("v12.2", "Drop Sculpt", "Bass-drop sculpting with rhythmic matrix accents.", "New Explorers"),
    VariantOption("v12.3", "Sequential Drift", "Sequential relay motion tuned to timing tracks.", "New Explorers"),
    VariantOption("v13.1", "Spatial Story", "Section storytelling with layout-aware travel.", "New Explorers"),
    VariantOption("v13.2", "Bassline Flow", "Low-end led movement with structured sweeps.", "New Explorers"),
    VariantOption("v13.3", "Luma Finale", "Layered cinematic finale with rich palette shifts.", "New Explorers"),
    VariantOption("v14.1", "Phrase Architect", "Section-first choreography with restrained, deliberate prop roles.", "Focused Intent"),
    VariantOption("v14.2", "Stem Command", "Bass, drums, and vocal roles separated into intentional lanes.", "Focused Intent"),
    VariantOption("v14.3", "Contour Waves", "Beat and note contour bursts that reverse with musical motion.", "Focused Intent"),
    VariantOption("v15.1", "Cinematic Arc", "Phrase architecture expanded with premium timing accents.", "Prime Time"),
    VariantOption("v15.2", "Orchestra Drive", "Instrument-led sequencing with richer premium support layers.", "Prime Time"),
    VariantOption("v15.3", "PrimeTime Finale", "Big-show sequencing that combines scene control and impact moments.", "Prime Time"),
    VariantOption("v16.1", "Show Arc", "Structured section arcs with disciplined scene intent.", "Advanced Lab"),
    VariantOption("v16.2", "Stagecraft Stems", "Bass, drums, and melody staged like a hand-tuned show sequence.", "Advanced Lab"),
    VariantOption("v16.3", "Choreo Waves", "Arches and sequential props wave on beats and note contour with reversals.", "Advanced Lab"),
    VariantOption("v17.1", "Signature Show", "Polished showcase pass that blends scenes, vocals, and motion with restraint.", "Spotlight"),
    VariantOption("v17.2", "Choir Cinema", "Vocal-led showcase choreography with harmony support and lyric-friendly pacing.", "Spotlight"),
    VariantOption("v17.3", "Showstopper Cut", "Big finale treatment aimed at showcase-scale energy.", "Spotlight"),
    VariantOption("v19.1", "Piano Spine", "Player-piano-first choreography routed through cane and white-spine lanes.", "Keyboard Lab"),
    VariantOption("v19.2", "Keyed Stems", "Stem-separated sequencing that keeps the keyboard lanes front and center.", "Keyboard Lab"),
    VariantOption("v19.3", "Grand Keys", "Showcase phrasing with more premium piano-lane movement.", "Keyboard Lab"),
    VariantOption("v20.1", "Studio Recall", "Local-history guided scene arcs with disciplined placement logic.", "Private Studio"),
    VariantOption("v20.2", "Stem Recall", "Your own workspace tendencies routed into cleaner stem roles.", "Private Studio"),
    VariantOption("v20.3", "Signature Recall", "Showcase polish that leans on local palette and effect habits.", "Private Studio"),
    VariantOption("v21.1", "Scene Logic", "Transparent scene-building based on open xLights-style heuristics.", "Director Drafts"),
    VariantOption("v21.2", "Lane Logic", "Open, role-separated routing for bass, drums, vocals, and support.", "Director Drafts"),
    VariantOption("v21.3", "Finale Logic", "Premium finale shaping with bold transitions and restrained flash.", "Director Drafts"),
    VariantOption("v22.1", "Premium Storyboard", "Cleaner scene-first premium pass with keyboard lanes kept supportive.", "Premium Refined"),
    VariantOption("v22.2", "Submodel Maestro", "Submodel-led premium pass with tighter restraint and stronger stem discipline.", "Premium Refined"),
    VariantOption("v22.3", "Pixel Prestige", "Richer pixel-aware premium showcase with lower keyboard dominance.", "Premium Refined"),
    VariantOption("v23.1", "Scenic Director", "Scene-first choreography with stronger restraint and model-fit effects.", "Premium Apex"),
    VariantOption("v23.2", "Detail Director", "Submodel-aware premium sequencing with cleaner family balance and tighter stems.", "Premium Apex"),
    VariantOption("v23.3", "Headliner Pixel", "Polished pixel showcase with premium family coverage and lower keyboard dominance.", "Premium Apex"),
    VariantOption("v23.4", "Noir Stemcraft", "Darker suspense windows with disciplined stem-lane control and pixel-aware restraint.", "Premium Apex"),
    VariantOption("v23.5", "Suspense Signature", "Showcase signature moments with cinematic darkness and stronger part-to-part contrast.", "Premium Apex"),
    VariantOption("v23.6", "Apex Stem Noir", "Deep suspense windows with disciplined stem routing and premium pixel-family balance.", "Premium Apex"),
    VariantOption("v24.1", "Role Architect", "Foreground/midground/background role orchestration with part-aware dynamics.", "Apex Vanguard"),
    VariantOption("v24.2", "Context Choreo", "Energy-aware effect selection that reshapes model roles across song sections.", "Apex Vanguard"),
    VariantOption("v24.3", "Apex Storyboard", "High-polish hierarchy pass tuned for drops, suspense windows, and directional motion.", "Apex Vanguard"),
    VariantOption("v25.1", "Raw Auto", "Maximum musical reactivity with clean stem lanes and aggressive timing snap.", "Vendor Edition"),
    VariantOption("v25.2", "Pro Vendor", "Vendor-grade polish with section storytelling and premium layer discipline.", "Vendor Edition"),
    VariantOption("v26.1", "Raw Auto", "Next-gen snap timing and stem separation with stronger section contrast.", "Vendor Edition"),
    VariantOption("v26.2", "Pro Vendor", "Highest-polish vendor pass with tighter grid alignment and disciplined layering.", "Vendor Edition"),
    VariantOption("v27.1", "Raw Auto", "Finalized raw pass with vendor-grade pacing and stronger piano timing.", "Vendor Edition"),
    VariantOption("v27.2", "Helix Final", "Bulletproof vendor showpiece with player-piano sequencing on sequential props.", "Vendor Edition"),
    VariantOption("v27.3", "Helix Prime", "Refined Helix pass balancing piano-lane clarity, section contrast, and cleaner drop windows.", "Vendor Edition"),
]

def _major_version(version: str) -> int:
    try:
        token = version.lower().lstrip("v").split(".", 1)[0]
        return int(token)
    except Exception:
        return 0


ACTIVE_VARIANT_OPTIONS: list[VariantOption] = [
    item for item in VARIANT_OPTIONS if _major_version(item.version) >= 20
]

SCRIPT_MAP: dict[str, Path] = {item.version: APP_ROOT / f"{item.version}.py" for item in ACTIVE_VARIANT_OPTIONS}
PALETTE_MODES: list[tuple[str, str]] = [
    ("Template", "template"),
    ("Christmas", "christmas"),
    ("Warm", "warm"),
    ("Cool", "cool"),
    ("Neon", "neon"),
    ("Random", "random"),
    ("Workspace Match", "workspace_match"),
]

INPUT_HELP = {
    "template": "Template XSQ = a working .xsq that already matches your current layout and model names.",
    "audio": "Audio input(s) = choose one or many files. .wav is preferred for best analysis, but .mp3, .flac, .ogg, and .m4a are also accepted.",
    "output": "Output folder = where finished sequences are written. Defaults to your Documents\\DreamSequenceWeaver\\Outputs folder for safer customer use.",
    "layout": "Layout = auto-detects your newest xlights_rgbeffects.xml or .xbkp. Choose your current xLights layout here if needed.",
    "style_folder": "Style XSQ Folder = optional reference folder only. Current builds do not learn from this folder to avoid external sequence contamination.",
    "learn_from_me": "Learn From My XSQs = when enabled, the app scans your own generated and finished XSQ files in the selected output workspace over time to build a local sense of your preferred palettes, effect families, and placement tendencies.",
    "palette": "Color palette chooser = steers how generated palettes are selected while optionally drawing from recent XSQ colors in your workspace.",
    "ac_only": "AC Only = limits the engine to dumb-light-friendly looks like On, fades, pulses, shimmers, twinkles, and strobes.",
    "pixel_reactive": "Pixel Reactive+ = adds family-aware music-driven pixel choreography so matrices, trees, spinners, spheres, arches, lines, and windows get stronger model-fit effects instead of generic placeholders.",
    "style_type": "Style Type = a curated professional sequencing direction. Apply one to auto-pick the most relevant engine versions and recommended slider defaults.",
    "preflight": "Preflight Audit = scans the selected template, layout, audio, and output path for model drift, pixel-model coverage, missing files, and sequencing risks before generation.",
}

STYLE_TYPE_OPTIONS: list[StyleTypePreset] = [
    StyleTypePreset(
        label="Customer Ready",
        note="Apex v24 hierarchy bundle tuned for role-based layering, suspense windows, and stronger pixel-family intent.",
        versions=("v24.1", "v24.2", "v24.3"),
        density=0.98,
        speed=1.04,
        randomness=0.10,
        energy=0.72,
    ),
    StyleTypePreset(
        label="Story Blend",
        note="Balanced, song-first choreography with disciplined whole-house restraint and stronger scene intent.",
        versions=("v17.1", "v21.1", "v22.1", "v23.1"),
        density=0.96,
        speed=1.00,
        randomness=0.16,
        energy=0.62,
    ),
    StyleTypePreset(
        label="Stem Choreo",
        note="Bass, drums, vocals, and support lanes are kept intentionally separated like a hand-built sequence.",
        versions=("v16.2", "v19.2", "v21.2", "v22.2", "v23.2", "v23.4"),
        density=0.96,
        speed=1.02,
        randomness=0.12,
        energy=0.64,
    ),
    StyleTypePreset(
        label="Piano Spatial",
        note="Polyphonic notes and spatial lanes drive candy canes, white spines, and sequential props with clear musical mapping.",
        versions=("v19.1", "v19.3"),
        density=1.04,
        speed=1.02,
        randomness=0.10,
        energy=0.64,
        palette_label="Template",
    ),
    StyleTypePreset(
        label="Cinematic Finale",
        note="Premium showcase energy with cleaner builds, bigger impacts, and stronger closing scenes.",
        versions=("v15.1", "v17.3", "v21.3", "v22.3", "v23.3", "v23.5", "v23.6", "v24.3"),
        density=1.02,
        speed=1.04,
        randomness=0.13,
        energy=0.74,
    ),
    StyleTypePreset(
        label="A+++++ Vendor",
        note="Top-tier role hierarchy choreography for musically reactive, model-fit sequencing on both AC and pixel props.",
        versions=("v23.5", "v23.6", "v24.1", "v24.2", "v24.3"),
        density=1.04,
        speed=1.08,
        randomness=0.11,
        energy=0.76,
    ),
    StyleTypePreset(
        label="AC Heritage",
        note="Safer dumb-light-forward choreography that still follows structure, contrast, and musical phrasing.",
        versions=("v14.1", "v16.1"),
        density=0.88,
        speed=0.94,
        randomness=0.08,
        energy=0.52,
        ac_only=True,
    ),
    StyleTypePreset(
        label="Motion Showcase",
        note="Purposeful wave, chase, and sweep movement for displays that want strong travel and direction changes without pure chaos.",
        versions=("v14.3", "v16.3", "v21.3"),
        density=1.08,
        speed=1.14,
        randomness=0.16,
        energy=0.74,
    ),
]

STYLE_TYPE_MAP = {item.label: item for item in STYLE_TYPE_OPTIONS}


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def default_audio() -> str:
    for path in sorted(ROOT.iterdir()):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTS:
            return str(path)
    return ""


def default_template() -> str:
    return ""


def load_launcher_state() -> dict:
    try:
        if LAUNCHER_STATE_FILE.exists():
            data = json.loads(LAUNCHER_STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def save_launcher_state(payload: dict) -> None:
    try:
        LAUNCHER_STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def default_output_folder() -> Path:
    docs = USER_HOME / "Documents"
    if docs.exists():
        return docs / "DreamSequenceWeaver" / "Outputs"
    return USER_HOME / "DreamSequenceWeaver" / "Outputs"


def latest_layout_path() -> Path | None:
    skip_dirs = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "build",
        "dist",
        "RenderCache",
        ".previewdeps",
        "finalists",
    }
    xml_hits: list[tuple[float, Path]] = []
    xbkp_hits: list[tuple[float, Path]] = []
    for root_dir, dir_names, file_names in os.walk(ROOT):
        dir_names[:] = [name for name in dir_names if name not in skip_dirs]
        for file_name in file_names:
            lower = file_name.lower()
            if "rgbeffects" not in lower:
                continue
            path = Path(root_dir) / file_name
            try:
                stamp = path.stat().st_mtime
            except OSError:
                continue
            if lower.endswith(".xml"):
                xml_hits.append((stamp, path))
            elif lower.endswith(".xbkp"):
                xbkp_hits.append((stamp, path))
    if xml_hits:
        return max(xml_hits, key=lambda item: item[0])[1]
    if xbkp_hits:
        return max(xbkp_hits, key=lambda item: item[0])[1]
    return LAYOUT_FALLBACK if LAYOUT_FALLBACK.exists() else None


def find_ui_image(name_tokens: tuple[str, ...], fallback_paths: tuple[Path, ...]) -> Path | None:
    skip_dirs = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "build",
        "dist",
        "RenderCache",
        ".previewdeps",
        "finalists",
        "outputs",
        "xlights_src",
        "xlights_upstream",
    }
    candidates: list[tuple[int, float, Path]] = []
    tokens = tuple(token.lower() for token in name_tokens if token.strip())
    search_roots: list[Path] = []
    for root in (ROOT, APP_ROOT, USER_HOME / "Downloads", USER_HOME / "Pictures", USER_HOME / "Desktop"):
        if root.exists() and root not in search_roots:
            search_roots.append(root)
    for search_root in search_roots:
        for root_dir, dir_names, file_names in os.walk(search_root):
            dir_names[:] = [name for name in dir_names if name not in skip_dirs]
            for file_name in file_names:
                lower = file_name.lower()
                if Path(file_name).suffix.lower() not in IMAGE_EXTS:
                    continue
                if tokens and not all(token in lower for token in tokens):
                    continue
                path = Path(root_dir) / file_name
                try:
                    stamp = path.stat().st_mtime
                except OSError:
                    stamp = 0.0
                depth_score = 0 if path.parent == ROOT else 1
                candidates.append((depth_score, -stamp, path))
    if candidates:
        candidates.sort(key=lambda item: (item[0], item[1], str(item[2]).lower()))
        return candidates[0][2]
    for fallback in fallback_paths:
        if fallback.exists():
            return fallback
    return None


def find_app_icon() -> Path | None:
    candidates = [
        ROOT / "app_icon.ico",
        APP_ROOT / "app_icon.ico",
        ROOT / "c82.ico",
        APP_ROOT / "c82.ico",
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def open_path(path: Path) -> None:
    if hasattr(os, "startfile"):
        os.startfile(str(path))
    else:
        subprocess.Popen(["xdg-open", str(path)])


def build_python_cmd(script_path: Path, args: list[str], python_path: Path) -> list[str]:
    if getattr(sys, "frozen", False):
        exe = str(Path(sys.executable))
        stem = script_path.stem.lower()
        if stem in SCRIPT_MAP:
            return [exe, "--run-variant", stem, *args]
        return [exe, *args]
    if python_path.suffix.lower() in {".cmd", ".bat"}:
        return ["cmd.exe", "/c", str(python_path), str(script_path), *args]
    return [str(python_path), str(script_path), *args]


def energy_profile(energy: float) -> dict[str, float | str]:
    e = clamp(energy, 0.0, 1.0)
    if e < 0.34:
        feel = "airy"
    elif e < 0.68:
        feel = "balanced"
    else:
        feel = "aggressive"
    return {
        "feel": feel,
        "bass_bias": clamp(0.72 + 1.35 * e, 0.55, 2.30),
        "melody_density": clamp(1.20 - 0.35 * e, 0.55, 2.20),
        "darkness": clamp(1.22 - 0.60 * e, 0.55, 1.55),
        "spatial": clamp(0.30 + 0.60 * e, 0.15, 0.95),
        "keyboard_mix": clamp(0.85 + 0.45 * e, 0.40, 1.80),
        "cane_focus": clamp(1.02 + 0.52 * e, 0.70, 2.20),
        "flash_guard": clamp(0.93 - 0.44 * e, 0.40, 0.96),
    }


def chase_style_for_energy(energy: float) -> str:
    if energy >= 0.84:
        return "wave"
    if energy >= 0.66:
        return "group_to_group"
    if energy >= 0.48:
        return "left_to_right"
    return "radial_out"


def layering_for_energy(energy: float) -> str:
    if energy >= 0.75:
        return "overlay_blend"
    if energy >= 0.45:
        return "smart_layer"
    return "replace"


class HoverTip:
    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 350) -> None:
        self.widget = widget
        self.text = text.strip()
        self.delay_ms = delay_ms
        self.tip_window: tk.Toplevel | None = None
        self.after_id: str | None = None
        if not self.text:
            return
        self.widget.bind("<Enter>", self._enter, add="+")
        self.widget.bind("<Leave>", self._leave, add="+")
        self.widget.bind("<ButtonPress>", self._leave, add="+")

    def _enter(self, _event: tk.Event) -> None:
        self._cancel()
        self.after_id = self.widget.after(self.delay_ms, self._show)

    def _leave(self, _event: tk.Event) -> None:
        self._cancel()
        self._hide()

    def _cancel(self) -> None:
        if self.after_id is not None:
            try:
                self.widget.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def _show(self) -> None:
        if self.tip_window is not None or not self.text:
            return
        x = self.widget.winfo_rootx() + 14
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tip,
            text=self.text,
            justify="left",
            bg="#0f2030",
            fg="#edf7ff",
            relief="solid",
            borderwidth=1,
            padx=9,
            pady=7,
            wraplength=420,
        )
        label.pack()
        self.tip_window = tip

    def _hide(self) -> None:
        if self.tip_window is not None:
            self.tip_window.destroy()
            self.tip_window = None


class Launcher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_BRAND)
        self.minsize(1080, 640)
        self.configure(bg="#0d1820")
        self._icon_photo = None

        self.log_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.running = False
        self.hero_photo: tk.PhotoImage | None = None
        self.progress_window: tk.Toplevel | None = None
        self.progress_log: ScrolledText | None = None
        self.progress_status_var = tk.StringVar(value="Waiting to start.")
        self.progress_line_var = tk.StringVar(value="No active run.")
        self.progress_bar: ttk.Progressbar | None = None
        self.instructions_window: tk.Toplevel | None = None
        self.license_window: tk.Toplevel | None = None
        self.third_party_window: tk.Toplevel | None = None
        self.last_output_dir: Path | None = None

        layout_guess = latest_layout_path()
        state = load_launcher_state()
        saved_template = str(state.get("last_template", "")).strip()
        if saved_template and not Path(saved_template).exists():
            saved_template = ""
        initial_audio = default_audio()
        self.audio_files: list[str] = [initial_audio] if initial_audio else []

        self.template_var = tk.StringVar(value=saved_template or default_template())
        self.audio_var = tk.StringVar(value="; ".join(self.audio_files))
        self.layout_var = tk.StringVar(value=str(layout_guess) if layout_guess else "")
        self.output_folder_var = tk.StringVar(value=str(default_output_folder()))
        self.style_folder_var = tk.StringVar(value="")

        self.density_var = tk.DoubleVar(value=1.08)
        self.speed_var = tk.DoubleVar(value=1.05)
        self.randomness_var = tk.DoubleVar(value=0.28)
        self.energy_var = tk.DoubleVar(value=0.68)
        self.style_type_var = tk.StringVar(value=STYLE_TYPE_OPTIONS[0].label)

        self.ac_only_var = tk.BooleanVar(value=False)
        self.pixel_reactive_var = tk.BooleanVar(value=True)
        self.learn_from_me_var = tk.BooleanVar(value=True)
        self.palette_label_var = tk.StringVar(value="Workspace Match")
        self.status_var = tk.StringVar(value="Ready.")
        self.catalog_var = tk.StringVar(value="Checking xLights feature catalog...")
        self.auto_summary_var = tk.StringVar(
            value="Auto helpers on: Queen Mary timing tracks, lyric sync, template analysis, reactive pixel choreography, optional style-folder guidance, optional Learn From My XSQs memory, and strict xLights effect validation."
        )
        self.advanced_versions_visible = False
        self.advanced_versions_frame: ttk.Frame | None = None
        self.advanced_versions_actions: ttk.Frame | None = None
        self.advanced_versions_button: ttk.Button | None = None
        self.shell_canvas: tk.Canvas | None = None

        self.variant_vars: dict[str, tk.BooleanVar] = {}
        self.variant_rows: dict[str, dict[str, tk.Widget]] = {}
        for item in ACTIVE_VARIANT_OPTIONS:
            selected = item.version.startswith("v17.")
            if item.group == "Legacy Compatible":
                selected = False
            self.variant_vars[item.version] = tk.BooleanVar(value=selected)

        self._build_ui()
        self._apply_style_type()
        self._apply_window_icon()
        self._fit_to_screen()
        self.after(120, self._poll_queue)
        self.after(250, self._refresh_catalog_async)

    def _save_template_state(self, template_path: str) -> None:
        clean = template_path.strip()
        if not clean:
            return
        state = load_launcher_state()
        state["last_template"] = clean
        save_launcher_state(state)

    def _normalize_audio_files(self, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in values:
            item = str(raw).strip().strip('"').strip("'")
            if not item:
                continue
            path_text = str(Path(item).expanduser())
            key = path_text.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(path_text)
        return cleaned

    def _set_audio_files(self, values: list[str]) -> None:
        self.audio_files = self._normalize_audio_files(values)
        self.audio_var.set("; ".join(self.audio_files))

    def _parse_audio_var(self) -> list[str]:
        raw = self.audio_var.get().strip()
        if not raw:
            return self._normalize_audio_files(self.audio_files)
        merged = raw.replace("\r", "\n").replace("\n", ";")
        parts = [part.strip() for part in merged.split(";")]
        parsed = self._normalize_audio_files(parts)
        if parsed:
            return parsed
        return self._normalize_audio_files(self.audio_files)

    def _resolved_audio_paths(self) -> list[Path]:
        parsed = self._parse_audio_var()
        self._set_audio_files(parsed)
        return [Path(item) for item in self.audio_files]

    def _apply_window_icon(self) -> None:
        icon_path = find_app_icon()
        if icon_path is not None:
            try:
                self.iconbitmap(str(icon_path))
                return
            except Exception:
                pass
        if Image is not None and ImageTk is not None:
            png_fallback = find_ui_image(("c82",), (ROOT / "c82.png", APP_ROOT / "c82.png"))
            if png_fallback is not None and png_fallback.exists():
                try:
                    image = Image.open(png_fallback)
                    self._icon_photo = ImageTk.PhotoImage(image)
                    self.iconphoto(True, self._icon_photo)
                except Exception:
                    pass

    def _fit_to_screen(self) -> None:
        screen_w = max(1200, self.winfo_screenwidth())
        screen_h = max(700, self.winfo_screenheight())
        width = min(1320, screen_w - 40)
        height = min(820, screen_h - 70)
        x = max(10, (screen_w - width) // 2)
        y = max(10, (screen_h - height) // 2 - 10)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _fit_child_window(self, win: tk.Toplevel, desired_w: int, desired_h: int) -> None:
        screen_w = max(1000, self.winfo_screenwidth())
        screen_h = max(650, self.winfo_screenheight())
        width = min(desired_w, screen_w - 50)
        height = min(desired_h, screen_h - 80)
        x = max(10, (screen_w - width) // 2)
        y = max(10, (screen_h - height) // 2 - 10)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def _bind_vertical_scroll(self, canvas: tk.Canvas) -> None:
        def _on_mousewheel(event: tk.Event) -> None:
            delta = getattr(event, "delta", 0)
            if delta:
                canvas.yview_scroll(int(-delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _pick_font(self, families: tuple[str, ...], size: int, *styles: str) -> tuple[str, int, *tuple[str, ...]]:
        available = {family.lower(): family for family in tkfont.families()}
        for family in families:
            match = available.get(family.lower())
            if match:
                return (match, size, *styles)
        return ("Segoe UI", size, *styles)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background="#0d1820", foreground="#ebf6ff")
        style.configure("TLabel", background="#0d1820", foreground="#ebf6ff")
        style.configure("TLabelframe", background="#0d1820", foreground="#9fe0ff")
        style.configure("TLabelframe.Label", background="#0d1820", foreground="#9fe0ff")
        style.configure("TFrame", background="#0d1820")
        style.configure("TEntry", fieldbackground="#132634", foreground="#ebf6ff")
        style.configure("TCheckbutton", background="#0d1820", foreground="#ebf6ff")
        style.configure("TButton", padding=(8, 5))
        style.configure(
            "Dark.TCombobox",
            fieldbackground="#132634",
            background="#132634",
            foreground="#ebf6ff",
            arrowcolor="#8fd5ff",
        )
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", "#132634"), ("!disabled", "#132634")],
            foreground=[("readonly", "#ebf6ff"), ("!disabled", "#ebf6ff")],
            selectforeground=[("readonly", "#ebf6ff")],
            selectbackground=[("readonly", "#132634")],
        )
        style.configure("Header.TLabel", font=("Segoe UI", 17, "bold"), foreground="#b7e5ff")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10), foreground="#8eb5d8")

        shell_host = ttk.Frame(self)
        shell_host.pack(fill="both", expand=True)
        shell_host.columnconfigure(0, weight=1)
        shell_host.rowconfigure(0, weight=1)

        shell_canvas = tk.Canvas(shell_host, bg="#0d1820", highlightthickness=0, bd=0)
        shell_canvas.grid(row=0, column=0, sticky="nsew")
        shell_scroll = ttk.Scrollbar(shell_host, orient="vertical", command=shell_canvas.yview)
        shell_scroll.grid(row=0, column=1, sticky="ns")
        shell_canvas.configure(yscrollcommand=shell_scroll.set)
        self.shell_canvas = shell_canvas
        self._bind_vertical_scroll(shell_canvas)

        shell = ttk.Frame(shell_canvas, padding=10)
        shell_window = shell_canvas.create_window((0, 0), window=shell, anchor="nw")

        def _sync_shell_body(_event=None) -> None:
            shell_canvas.configure(scrollregion=shell_canvas.bbox("all"))

        def _sync_shell_width(event: tk.Event) -> None:
            shell_canvas.itemconfigure(shell_window, width=event.width)

        shell.bind("<Configure>", _sync_shell_body)
        shell_canvas.bind("<Configure>", _sync_shell_width)
        shell.columnconfigure(0, weight=3)
        shell.columnconfigure(1, weight=2)
        shell.rowconfigure(2, weight=2)
        shell.rowconfigure(4, weight=1)

        self._build_banner(shell)

        io_card = ttk.LabelFrame(shell, text="Inputs")
        io_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(12, 10))
        io_card.columnconfigure(1, weight=1)
        self._entry_row(io_card, 0, "Template XSQ", self.template_var, browse_fn=self._pick_template, tooltip=INPUT_HELP["template"])
        self._entry_row(io_card, 1, "Audio Input(s)", self.audio_var, browse_fn=self._pick_audio, tooltip=INPUT_HELP["audio"])
        self._entry_row(io_card, 2, "Layout (Auto Detect)", self.layout_var, browse_fn=self._pick_layout, auto_fn=self._refresh_layout, tooltip=INPUT_HELP["layout"])
        self._entry_row(io_card, 3, "Output Folder", self.output_folder_var, browse_fn=self._pick_output_folder, open_fn=self._open_output_folder, tooltip=INPUT_HELP["output"])
        self._entry_row(
            io_card,
            4,
            "Style XSQ Folder (Opt-In)",
            self.style_folder_var,
            browse_fn=self._pick_style_folder,
            open_fn=self._open_style_folder,
            tooltip=INPUT_HELP["style_folder"],
        )
        style_notice = ttk.Label(
            io_card,
            text=(
                "Style XSQ Folder is currently reference-only. Learning history is restricted to app-generated output files."
            ),
            wraplength=620,
            justify="left",
            foreground="#8fb6d2",
        )
        style_notice.grid(row=5, column=0, columnspan=4, sticky="w", padx=10, pady=(2, 8))
        self._add_tip(style_notice, INPUT_HELP["style_folder"])

        options_card = ttk.LabelFrame(shell, text="Sequencing Options")
        options_card.grid(row=1, column=1, sticky="nsew", pady=(12, 10))
        options_card.columnconfigure(0, weight=1)
        options_card.columnconfigure(1, weight=1)
        style_frame = ttk.Frame(options_card)
        style_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        style_frame.columnconfigure(1, weight=1)
        style_label = ttk.Label(style_frame, text="Style Type")
        style_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        style_combo = ttk.Combobox(
            style_frame,
            state="readonly",
            values=[item.label for item in STYLE_TYPE_OPTIONS],
            textvariable=self.style_type_var,
            style="Dark.TCombobox",
        )
        style_combo.grid(row=0, column=1, sticky="ew")
        style_combo.current(0)
        apply_style = ttk.Button(style_frame, text="Apply", command=self._apply_style_type)
        apply_style.grid(row=0, column=2, padx=(8, 0))
        style_note = ttk.Label(
            options_card,
            text=STYLE_TYPE_MAP[self.style_type_var.get()].note,
            foreground="#8fb6d2",
            wraplength=380,
            justify="left",
        )
        style_note.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 6))
        self.style_note_label = style_note
        self.style_type_var.trace_add("write", lambda *_args: self._sync_style_type_note())
        self._add_tip(style_label, INPUT_HELP["style_type"])
        self._add_tip(style_combo, INPUT_HELP["style_type"])
        self._add_tip(apply_style, INPUT_HELP["style_type"])
        self._add_tip(style_note, INPUT_HELP["style_type"])
        ac_toggle = tk.Checkbutton(
            options_card,
            text="AC Only",
            variable=self.ac_only_var,
            bg="#0d1820",
            fg="#ebf6ff",
            activebackground="#0d1820",
            activeforeground="#ebf6ff",
            selectcolor="#132634",
            highlightthickness=0,
            anchor="w",
        )
        ac_toggle.grid(row=2, column=0, sticky="w", padx=10, pady=(2, 8))
        self._add_tip(ac_toggle, INPUT_HELP["ac_only"])
        pixel_toggle = tk.Checkbutton(
            options_card,
            text="Pixel Reactive+",
            variable=self.pixel_reactive_var,
            bg="#0d1820",
            fg="#ebf6ff",
            activebackground="#0d1820",
            activeforeground="#ebf6ff",
            selectcolor="#132634",
            highlightthickness=0,
            anchor="w",
        )
        pixel_toggle.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 8))
        self._add_tip(pixel_toggle, INPUT_HELP["pixel_reactive"])

        slider_card = ttk.LabelFrame(shell, text="Feel Controls")
        slider_card.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        slider_card.columnconfigure(0, weight=1)
        self._slider_row(slider_card, 0, "Effects Density", self.density_var, 0.40, 2.40, 0.01, "Overall event density and layering.")
        self._slider_row(slider_card, 1, "Effects Speed", self.speed_var, 0.40, 2.40, 0.01, "How quickly motion changes move across props.")
        self._slider_row(slider_card, 2, "Randomness", self.randomness_var, 0.00, 1.00, 0.01, "How much variation gets introduced across the show.")
        self._slider_row(slider_card, 3, "Energy", self.energy_var, 0.00, 1.00, 0.01, "Auto-shapes buildups, drops, brightness ramps, and spatial intensity.")

        palette_strip = ttk.Frame(slider_card)
        palette_strip.grid(row=4, column=0, sticky="ew", padx=10, pady=(4, 10))
        palette_strip.columnconfigure(1, weight=1)
        palette_label = ttk.Label(palette_strip, text="Color Palette")
        palette_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        palette_combo = ttk.Combobox(
            palette_strip,
            state="readonly",
            values=[label for label, _mode in PALETTE_MODES],
            textvariable=self.palette_label_var,
            style="Dark.TCombobox",
        )
        palette_combo.grid(row=0, column=1, sticky="ew")
        palette_combo.current(6)
        self._add_tip(palette_label, INPUT_HELP["palette"])
        self._add_tip(palette_combo, INPUT_HELP["palette"])

        versions_card = ttk.LabelFrame(shell, text="Advanced Engine Mix")
        versions_card.grid(row=2, column=1, sticky="nsew", pady=(0, 10))
        versions_card.columnconfigure(0, weight=1)
        versions_card.rowconfigure(1, weight=1)

        ttk.Label(
            versions_card,
            text="Style Type is the premium workflow. Use the advanced engine mix only if you want to hand-pick raw variants.",
            foreground="#8fb6d2",
            wraplength=420,
            justify="left",
        ).grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

        toggle_bar = ttk.Frame(versions_card)
        toggle_bar.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
        toggle_bar.columnconfigure(0, weight=1)
        self.advanced_versions_button = ttk.Button(toggle_bar, text="Show Advanced Variants", command=self._toggle_advanced_versions)
        self.advanced_versions_button.grid(row=0, column=0, sticky="w")

        by_group: dict[str, list[VariantOption]] = {}
        for option in ACTIVE_VARIANT_OPTIONS:
            by_group.setdefault(option.group, []).append(option)

        versions_view = ttk.Frame(versions_card)
        versions_view.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 4))
        versions_view.columnconfigure(0, weight=1)
        versions_view.rowconfigure(0, weight=1)
        versions_canvas = tk.Canvas(versions_view, bg="#0d1820", highlightthickness=0, bd=0)
        versions_canvas.grid(row=0, column=0, sticky="nsew")
        versions_scroll = ttk.Scrollbar(versions_view, orient="vertical", command=versions_canvas.yview)
        versions_scroll.grid(row=0, column=1, sticky="ns")
        versions_canvas.configure(yscrollcommand=versions_scroll.set)
        versions_body = ttk.Frame(versions_canvas)
        versions_window = versions_canvas.create_window((0, 0), window=versions_body, anchor="nw")

        def _sync_versions_body(_event=None) -> None:
            versions_canvas.configure(scrollregion=versions_canvas.bbox("all"))

        def _sync_versions_width(event: tk.Event) -> None:
            versions_canvas.itemconfigure(versions_window, width=event.width)

        versions_body.bind("<Configure>", _sync_versions_body)
        versions_canvas.bind("<Configure>", _sync_versions_width)

        preferred_group_order = (
            "Proven Picks",
            "New Explorers",
            "Focused Intent",
            "Prime Time",
            "Advanced Lab",
            "Spotlight",
            "Keyboard Lab",
            "Private Studio",
            "Director Drafts",
            "Premium Refined",
            "Premium Apex",
        )
        ordered_groups = [group_name for group_name in preferred_group_order if by_group.get(group_name)]
        ordered_groups.extend(sorted(group_name for group_name in by_group if group_name not in preferred_group_order))

        row = 0
        for group_name in ordered_groups:
            items = by_group.get(group_name, [])
            if not items:
                continue
            ttk.Label(versions_body, text=group_name, foreground="#7cc8ff").grid(row=row, column=0, sticky="w", padx=8, pady=(8 if row == 0 else 6, 2))
            row += 1
            for item in items:
                line = tk.Frame(versions_body, bg="#12202b", highlightbackground="#294456", highlightthickness=1, padx=8, pady=4, cursor="hand2")
                line.grid(row=row, column=0, sticky="ew", padx=8, pady=1)
                line.columnconfigure(1, weight=1)
                check = tk.Checkbutton(
                    line,
                    text=f"{item.label}  [{item.version}]",
                    variable=self.variant_vars[item.version],
                    bg="#12202b",
                    fg="#f2fbff",
                    activebackground="#12202b",
                    activeforeground="#f2fbff",
                    selectcolor="#12202b",
                    indicatoron=False,
                    borderwidth=0,
                    highlightthickness=0,
                    anchor="w",
                    cursor="hand2",
                    padx=6,
                    pady=4,
                )
                check.grid(row=0, column=0, sticky="w")
                note = tk.Label(line, text=item.note, fg="#8fb6d2", bg="#12202b", anchor="w", justify="left")
                note.grid(row=0, column=1, sticky="w", padx=(8, 0))
                badge = tk.Label(
                    line,
                    text="Selected",
                    fg="#08151b",
                    bg="#7ce0c2",
                    anchor="center",
                    padx=8,
                    pady=2,
                    font=("Segoe UI", 9, "bold"),
                    cursor="hand2",
                )
                badge.grid(row=0, column=2, sticky="e", padx=(8, 0))
                tip = f"{item.label} ({item.version})\n{item.note}"
                self._add_tip(check, tip)
                self._add_tip(note, tip)
                self._add_tip(badge, tip)
                self._add_tip(line, tip)
                self.variant_rows[item.version] = {
                    "frame": line,
                    "check": check,
                    "note": note,
                    "badge": badge,
                }
                self.variant_vars[item.version].trace_add("write", lambda *_args, version=item.version: self._apply_variant_row_style(version))
                line.bind("<Button-1>", lambda _event, version=item.version: self._toggle_variant(version))
                note.bind("<Button-1>", lambda _event, version=item.version: self._toggle_variant(version))
                badge.bind("<Button-1>", lambda _event, version=item.version: self._toggle_variant(version))
                row += 1

        for item in ACTIVE_VARIANT_OPTIONS:
            self._apply_variant_row_style(item.version)

        actions = ttk.Frame(versions_card)
        actions.grid(row=3, column=0, sticky="ew", padx=8, pady=(4, 8))
        for idx in range(6):
            actions.columnconfigure(idx, weight=1)
        ttk.Button(actions, text="Select v20", command=self._select_v20).grid(row=0, column=0, sticky="ew", padx=2)
        ttk.Button(actions, text="Select v21", command=self._select_v21).grid(row=0, column=1, sticky="ew", padx=2)
        ttk.Button(actions, text="Select v22", command=self._select_v22).grid(row=0, column=2, sticky="ew", padx=2)
        ttk.Button(actions, text="Select v23", command=self._select_v23).grid(row=0, column=3, sticky="ew", padx=2)
        ttk.Button(actions, text="Select v24+v25", command=self._select_latest).grid(row=0, column=4, sticky="ew", padx=2)
        ttk.Button(actions, text="Clear", command=self._select_none).grid(row=0, column=5, sticky="ew", padx=2)
        self.advanced_versions_frame = versions_view
        self.advanced_versions_actions = actions
        versions_view.grid_remove()
        actions.grid_remove()

        run_bar = ttk.Frame(shell)
        run_bar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        run_bar.columnconfigure(0, weight=1)
        ttk.Label(run_bar, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Button(run_bar, text="Instructions", command=self._open_instructions).grid(row=0, column=1, padx=4)
        self.run_button = ttk.Button(run_bar, text="Generate Sequence Set", command=self._start_generation)
        self.run_button.grid(row=0, column=2, padx=(8, 0))

        log_card = ttk.LabelFrame(shell, text="Run Log")
        log_card.grid(row=4, column=0, columnspan=2, sticky="nsew")
        self.log_box = ScrolledText(
            log_card,
            height=8,
            bg="#0c141b",
            fg="#daf2ff",
            insertbackground="#daf2ff",
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=8,
        )
        self.log_box.pack(fill="both", expand=True)
        self.log_box.configure(state="disabled")

    def _build_banner(self, parent: ttk.Frame) -> None:
        banner = tk.Frame(parent, bg=BANNER_BG, highlightbackground=BANNER_BORDER, highlightthickness=1, padx=14, pady=10)
        banner.grid(row=0, column=0, columnspan=2, sticky="ew")
        banner.grid_columnconfigure(1, weight=1)
        banner.grid_columnconfigure(2, weight=0)

        hero_path = find_ui_image(
            ("helixmascot",),
            (
                ROOT / "helixmascot.jpg",
                APP_ROOT / "helixmascot.jpg",
                ROOT / "helixmascot.jpeg",
                APP_ROOT / "helixmascot.jpeg",
                ROOT / "helixmascot.png",
                APP_ROOT / "helixmascot.png",
                ROOT / "c82.png",
                ROOT / "13v1_frame0.png",
            ),
        )
        self.hero_photo = self._load_photo(hero_path, 152, 152)

        if self.hero_photo is not None:
            tk.Label(banner, image=self.hero_photo, bg=BANNER_BG).grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 14))

        title_font = self._pick_font(("Segoe Script", "Lucida Handwriting", "Brush Script MT", "Gabriola"), 26, "bold")
        beta_font = self._pick_font(("Segoe UI",), 11)
        subtitle_font = self._pick_font(("Segoe UI",), 10)

        title_row = tk.Frame(banner, bg=BANNER_BG)
        title_row.grid(row=0, column=1, sticky="w")
        tk.Label(
            title_row,
            text=APP_BRAND,
            font=title_font,
            bg=BANNER_BG,
            fg="#1f6f66",
            anchor="w",
        ).pack(side="left")
        tk.Label(
            title_row,
            text="beta",
            font=beta_font,
            bg=BANNER_BG,
            fg="#2a8a76",
            anchor="sw",
            padx=8,
        ).pack(side="left", pady=(10, 0))

        tk.Label(
            banner,
            text="Sequencing, Simplified.\n            Helix and Relax.",
            font=subtitle_font,
            bg=BANNER_BG,
            fg="#4f6670",
            anchor="w",
            justify="left",
        ).grid(row=1, column=1, sticky="w", pady=(1, 6))

        side = tk.Frame(banner, bg=BANNER_BG)
        side.grid(row=0, column=2, rowspan=2, sticky="ne")
        tk.Label(side, textvariable=self.catalog_var, bg=BANNER_BG, fg="#6f8893", justify="right").pack(anchor="e", pady=(6, 4))
        buttons = tk.Frame(side, bg=BANNER_BG)
        buttons.pack(anchor="e")
        ttk.Button(buttons, text="Instructions", command=self._open_instructions).grid(row=0, column=0, padx=3)
        ttk.Button(buttons, text="License", command=self._open_license_window).grid(row=0, column=1, padx=3)
        ttk.Button(buttons, text="Support Author", command=lambda: webbrowser.open(AUTHOR_SUPPORT_URL)).grid(row=0, column=2, padx=3)
        ttk.Button(buttons, text="Support xLights", command=lambda: webbrowser.open(SUPPORT_DONATE_URL)).grid(row=0, column=3, padx=3)

    def _entry_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        browse_fn=None,
        auto_fn=None,
        open_fn=None,
        tooltip: str = "",
    ) -> None:
        label_widget = ttk.Label(parent, text=label)
        label_widget.grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", padx=6, pady=4)
        col = 2
        if browse_fn is not None:
            browse_btn = ttk.Button(parent, text="Browse", command=browse_fn)
            browse_btn.grid(row=row, column=col, padx=2, pady=4)
            self._add_tip(browse_btn, tooltip)
            col += 1
        if auto_fn is not None:
            auto_btn = ttk.Button(parent, text="Auto", command=auto_fn)
            auto_btn.grid(row=row, column=col, padx=2, pady=4)
            self._add_tip(auto_btn, tooltip)
            col += 1
        if open_fn is not None:
            open_btn = ttk.Button(parent, text="Open", command=open_fn)
            open_btn.grid(row=row, column=col, padx=2, pady=4)
            self._add_tip(open_btn, tooltip)
        self._add_tip(label_widget, tooltip)
        self._add_tip(entry, tooltip)

    def _slider_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.DoubleVar,
        lo: float,
        hi: float,
        step: float,
        note: str,
    ) -> None:
        line = ttk.Frame(parent)
        line.grid(row=row, column=0, sticky="ew", padx=8, pady=4)
        line.columnconfigure(1, weight=1)
        label_widget = ttk.Label(line, text=label, width=18)
        label_widget.grid(row=0, column=0, sticky="w")
        value_label = ttk.Label(line, text=f"{variable.get():.2f}", width=6, foreground="#8dc8f4")
        value_label.grid(row=0, column=2, sticky="e", padx=(8, 0))
        scale = tk.Scale(
            line,
            orient="horizontal",
            from_=lo,
            to=hi,
            resolution=step,
            variable=variable,
            showvalue=False,
            length=460,
            bg="#0d1820",
            fg="#b5dcff",
            activebackground="#6bbfff",
            troughcolor="#243748",
            highlightthickness=0,
            command=lambda _value: value_label.configure(text=f"{variable.get():.2f}"),
        )
        scale.grid(row=0, column=1, sticky="ew")
        note_label = ttk.Label(line, text=note, foreground="#8fb6d2")
        note_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 0))
        self._add_tip(label_widget, note)
        self._add_tip(scale, note)
        self._add_tip(note_label, note)

    def _load_photo(self, path: Path | None, max_width: int, max_height: int) -> tk.PhotoImage | None:
        if path is None or not path.exists():
            return None
        try:
            if Image is not None and ImageTk is not None:
                image = Image.open(path)
                image.thumbnail((max_width, max_height))
                return ImageTk.PhotoImage(image)
            photo = tk.PhotoImage(file=str(path))
            scale_x = max(1, int((photo.width() + max_width - 1) / max_width))
            scale_y = max(1, int((photo.height() + max_height - 1) / max_height))
            scale = max(scale_x, scale_y)
            return photo.subsample(scale, scale) if scale > 1 else photo
        except Exception:
            return None

    def _add_tip(self, widget: tk.Widget, text: str) -> None:
        HoverTip(widget, text)

    def _open_license_window(self) -> None:
        if self.license_window is not None and self.license_window.winfo_exists():
            self.license_window.deiconify()
            self.license_window.lift()
            return

        win = tk.Toplevel(self)
        win.title("License")
        self._fit_child_window(win, 760, 620)
        win.configure(bg="#0f1820")
        self.license_window = win

        header = tk.Frame(win, bg="#173042", padx=14, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="License Information", font=("Segoe UI Semibold", 18), bg="#173042", fg="#edf9ff").pack(anchor="w")
        tk.Label(header, text="xLights GPL-3.0, Lua MIT, and Helix Sequence Weaver policy notices", bg="#173042", fg="#9ed7f0").pack(anchor="w")

        body = ScrolledText(
            win,
            bg="#0c141b",
            fg="#dcefff",
            insertbackground="#dcefff",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=10,
            wrap="word",
        )
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.insert("1.0", XLIGHTS_LICENSE_NOTICE + HELIX_COMMERCIAL_NOTICE)
        body.configure(state="disabled")

        links = ttk.Frame(win)
        links.pack(fill="x", padx=12, pady=(0, 12))
        for col in range(6):
            links.columnconfigure(col, weight=1)
        ttk.Button(links, text="xLights Repo", command=lambda: webbrowser.open(XLIGHTS_REPO_URL)).grid(row=0, column=0, sticky="ew", padx=3)
        ttk.Button(links, text="xLights License", command=lambda: webbrowser.open(XLIGHTS_LICENSE_URL)).grid(row=0, column=1, sticky="ew", padx=3)
        ttk.Button(links, text="Lua MIT License", command=lambda: webbrowser.open(LUA_LICENSE_URL)).grid(row=0, column=2, sticky="ew", padx=3)
        ttk.Button(links, text="GPL-3.0 Text", command=lambda: webbrowser.open("https://www.gnu.org/licenses/gpl-3.0.txt")).grid(row=0, column=3, sticky="ew", padx=3)
        ttk.Button(links, text="Third-Party List", command=self._open_third_party_licenses).grid(row=0, column=4, sticky="ew", padx=3)
        ttk.Button(links, text="Close", command=win.destroy).grid(row=0, column=5, sticky="ew", padx=3)

    def _open_third_party_licenses(self) -> None:
        if self.third_party_window is not None and self.third_party_window.winfo_exists():
            self.third_party_window.deiconify()
            self.third_party_window.lift()
            return
        if not THIRD_PARTY_LICENSES_FILE.exists():
            messagebox.showerror("Third-Party Licenses", f"File not found:\n{THIRD_PARTY_LICENSES_FILE}")
            return

        win = tk.Toplevel(self)
        win.title("Third-Party License List")
        self._fit_child_window(win, 760, 640)
        win.configure(bg="#0f1820")
        self.third_party_window = win

        header = tk.Frame(win, bg="#173042", padx=14, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="Third-Party License Checklist", font=("Segoe UI Semibold", 18), bg="#173042", fg="#edf9ff").pack(anchor="w")
        tk.Label(header, text=str(THIRD_PARTY_LICENSES_FILE.name), bg="#173042", fg="#9ed7f0").pack(anchor="w")

        body = ScrolledText(
            win,
            bg="#0c141b",
            fg="#dcefff",
            insertbackground="#dcefff",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=10,
            wrap="word",
        )
        body.pack(fill="both", expand=True, padx=12, pady=12)
        try:
            text = THIRD_PARTY_LICENSES_FILE.read_text(encoding="utf-8")
        except Exception as exc:
            text = f"Unable to read {THIRD_PARTY_LICENSES_FILE.name}.\n\n{exc!r}"
        body.insert("1.0", text)
        body.configure(state="disabled")

        links = ttk.Frame(win)
        links.pack(fill="x", padx=12, pady=(0, 12))
        for col in range(4):
            links.columnconfigure(col, weight=1)
        ttk.Button(links, text="Open In Notepad", command=lambda: self._open_text_in_notepad(THIRD_PARTY_LICENSES_FILE)).grid(row=0, column=0, sticky="ew", padx=3)
        ttk.Button(links, text="Open Folder", command=lambda: open_path(THIRD_PARTY_LICENSES_FILE.parent)).grid(row=0, column=1, sticky="ew", padx=3)
        ttk.Button(links, text="Reload", command=lambda: (win.destroy(), self._open_third_party_licenses())).grid(row=0, column=2, sticky="ew", padx=3)
        ttk.Button(links, text="Close", command=win.destroy).grid(row=0, column=3, sticky="ew", padx=3)

    def _open_text_in_notepad(self, path: Path) -> None:
        try:
            subprocess.Popen(["notepad.exe", str(path)])
        except Exception:
            open_path(path)

    def _open_instructions(self) -> None:
        if self.instructions_window is not None and self.instructions_window.winfo_exists():
            self.instructions_window.deiconify()
            self.instructions_window.lift()
            return

        win = tk.Toplevel(self)
        win.title("Instructions and Troubleshooting")
        self._fit_child_window(win, 760, 700)
        win.configure(bg="#0f1820")
        self.instructions_window = win

        header = tk.Frame(win, bg="#173042", padx=14, pady=12)
        header.pack(fill="x")
        tk.Label(header, text=f"{APP_BRAND} beta", font=("Segoe UI Semibold", 18), bg="#173042", fg="#edf9ff").pack(anchor="w")

        body = ScrolledText(
            win,
            bg="#0c141b",
            fg="#dcefff",
            insertbackground="#dcefff",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=10,
            wrap="word",
        )
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.insert(
            "1.0",
            "Quick steps\n"
            "1. Pick a template XSQ that already matches your current layout.\n"
            "2. Pick your song audio. WAV is best, but MP3, FLAC, OGG, and M4A also work.\n"
            "3. Confirm the auto-detected layout file is your current xlights_rgbeffects.xml or .xbkp.\n"
            "4. Choose the output folder where finished sequences should land.\n"
            "5. Optional: choose a Style XSQ Folder for reference only.\n"
            "6. Optional: apply a Style Type preset to auto-select a more focused, professional sequencing direction.\n"
            "7. Set the feel sliders for density, speed, randomness, and energy.\n"
            "8. Turn on AC Only only if you want dumb-light-safe effects only.\n"
            "9. Run Preflight Audit if you want a quick sanity check before generation.\n"
            "10. Pick the version styles you want to generate, then click Generate Sequence Set.\n\n"
            "Troubleshooting\n"
            "- If models are missing in xLights, your template XSQ and layout file probably do not match.\n"
            "- If the sequence feels too busy, lower Density, Randomness, or Energy.\n"
            "- If the sequence feels too empty, raise Density and Energy first.\n"
            "- Lyrics/transcription relies on local analysis unless you explicitly wire cloud services.\n"
            "- If AC Only is enabled, pixel-only effects are intentionally filtered out.\n"
            "- If xLights warns about model mismatches, re-check the selected template and layout before generating again.\n"
            "- Use Preflight Audit to catch template/layout drift, missing files, and skipped model families before a long run.\n\n"
            "Disclaimers\n"
            "- This is a beta helper.\n"
            "- Review legal and licensing requirements before any commercial distribution.\n"
            "- Style XSQ Folder is reference-only in current builds.\n"
            "- Local learning uses only your own workspace/output XSQ files over time.\n"
            "- External sequence files are not used for learning history.\n"
            "- Review generated sequences inside xLights before using them in a live show.\n"
            "- Keep backups of your layout, media, and template work.\n"
            f"- {APP_BRAND} and its creator are not affiliated with, endorsed by, sponsored by, or officially connected to the xLights development team or project.\n"
            "- xLights remains its own separate project. Please support the official xLights community through its official channels if this tool helps your show.\n"
            "- You are responsible for song licensing, public performance rights, and verifying that generated sequences are safe and appropriate for your setup.\n"
            "- Generated output should always be reviewed, rendered, and sanity-checked before a live event.\n"
            "- This helper is provided as-is, without guarantees that every layout, controller setup, or third-party dependency will behave perfectly.\n\n"
            "Absurd but important fine print\n"
            f"- {APP_BRAND} is not responsible for pregnancies resulting from your newly acquired badassery.\n"
            f"- {APP_BRAND} is not responsible for quantum-entanglement-related incidents across dimensional layers or spacetime variants.\n"
            f"- {APP_BRAND} is not responsible for aiding and abetting squirrel seizures.\n"
            f"- {APP_BRAND} is not responsible for accidental losses involving hypnotized microbiology.\n"
        )
        body.configure(state="disabled")

        links = ttk.Frame(win)
        links.pack(fill="x", padx=12, pady=(0, 12))
        for col in range(5):
            links.columnconfigure(col, weight=1)
        ttk.Button(links, text="xLights Home", command=lambda: webbrowser.open(XLIGHTS_HOME_URL)).grid(row=0, column=0, sticky="ew", padx=3)
        ttk.Button(links, text="xLights Manual", command=lambda: webbrowser.open(XLIGHTS_MANUAL_URL)).grid(row=0, column=1, sticky="ew", padx=3)
        ttk.Button(links, text="Support Author", command=lambda: webbrowser.open(AUTHOR_SUPPORT_URL)).grid(row=0, column=2, sticky="ew", padx=3)
        ttk.Button(links, text="Support xLights", command=lambda: webbrowser.open(SUPPORT_DONATE_URL)).grid(row=0, column=3, sticky="ew", padx=3)
        ttk.Button(links, text="Official Facebook", command=lambda: webbrowser.open(SUPPORT_FACEBOOK_URL)).grid(row=0, column=4, sticky="ew", padx=3)

    def _show_progress_window(self, reset: bool) -> None:
        if self.progress_window is None or not self.progress_window.winfo_exists():
            win = tk.Toplevel(self)
            win.title("Progress Report")
            self._fit_child_window(win, 880, 520)
            win.configure(bg="#0f1820")
            self.progress_window = win

            head = tk.Frame(win, bg="#173042", padx=12, pady=10)
            head.pack(fill="x")
            tk.Label(head, text="Generation Progress Report", font=("Segoe UI Semibold", 16), bg="#173042", fg="#eefaff").pack(anchor="w")
            tk.Label(head, textvariable=self.progress_status_var, bg="#173042", fg="#9ed8ef").pack(anchor="w", pady=(2, 0))
            tk.Label(head, textvariable=self.progress_line_var, bg="#173042", fg="#d5edf8", wraplength=820, justify="left").pack(anchor="w", pady=(6, 0))

            self.progress_bar = ttk.Progressbar(win, mode="indeterminate")
            self.progress_bar.pack(fill="x", padx=12, pady=(10, 6))

            self.progress_log = ScrolledText(
                win,
                bg="#0c141b",
                fg="#dcefff",
                insertbackground="#dcefff",
                relief="flat",
                borderwidth=0,
                padx=8,
                pady=8,
            )
            self.progress_log.pack(fill="both", expand=True, padx=12, pady=(0, 12))
            self.progress_log.configure(state="disabled")

        if reset:
            self.progress_status_var.set("Preparing run...")
            self.progress_line_var.set("Waiting for worker output.")
            if self.progress_log is not None:
                self.progress_log.configure(state="normal")
                self.progress_log.delete("1.0", "end")
                self.progress_log.configure(state="disabled")
            if self.progress_bar is not None:
                self.progress_bar.start(10)
        self.progress_window.deiconify()
        self.progress_window.lift()

    def _append_progress(self, text: str) -> None:
        if self.progress_log is None:
            return
        self.progress_log.configure(state="normal")
        self.progress_log.insert("end", text + "\n")
        self.progress_log.see("end")
        self.progress_log.configure(state="disabled")

    def _pick_template(self) -> None:
        path = filedialog.askopenfilename(initialdir=str(ROOT), filetypes=[("xLights Sequence", "*.xsq"), ("All files", "*.*")])
        if path:
            self.template_var.set(path)
            self._save_template_state(path)

    def _pick_audio(self) -> None:
        paths = filedialog.askopenfilenames(
            initialdir=str(ROOT),
            filetypes=[("Audio", "*.wav *.mp3 *.flac *.ogg *.m4a"), ("All files", "*.*")],
        )
        if paths:
            self._set_audio_files(list(paths))

    def _pick_layout(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(ROOT),
            filetypes=[("xLights Layout", "*.xml *.xbkp"), ("All files", "*.*")],
        )
        if path:
            self.layout_var.set(path)

    def _pick_output_folder(self) -> None:
        path = filedialog.askdirectory(initialdir=str(ROOT))
        if path:
            self.output_folder_var.set(path)

    def _pick_style_folder(self) -> None:
        path = filedialog.askdirectory(initialdir=str(ROOT))
        if path:
            self.style_folder_var.set(path)

    def _refresh_layout(self) -> None:
        path = latest_layout_path()
        if path:
            self.layout_var.set(str(path))
            self._push_log(f"Layout auto-selected: {path}")
        else:
            self._push_log("Layout auto-detect could not find a current rgbeffects layout file.")

    def _palette_mode(self) -> str:
        for label, mode in PALETTE_MODES:
            if label == self.palette_label_var.get():
                return mode
        return "template"

    def _selected_versions(self) -> list[str]:
        selected = [version for version, var in self.variant_vars.items() if bool(var.get())]
        selected.sort(key=lambda version: [item.version for item in ACTIVE_VARIANT_OPTIONS].index(version))
        return selected

    def _apply_style_type(self) -> None:
        preset = STYLE_TYPE_MAP.get(self.style_type_var.get())
        if preset is None:
            return
        self.density_var.set(preset.density)
        self.speed_var.set(preset.speed)
        self.randomness_var.set(preset.randomness)
        self.energy_var.set(preset.energy)
        self.palette_label_var.set(preset.palette_label)
        self.ac_only_var.set(bool(preset.ac_only))
        selected_versions = set(preset.versions)
        for version, var in self.variant_vars.items():
            var.set(version in selected_versions)
        self.style_note_label.configure(text=preset.note)
        self.status_var.set(f"Applied style type: {preset.label}")

    def _sync_style_type_note(self) -> None:
        preset = STYLE_TYPE_MAP.get(self.style_type_var.get())
        if preset is None:
            return
        self.style_note_label.configure(text=preset.note)

    def _apply_best_seller_preset(self) -> None:
        best_label = "Customer Ready"
        if best_label in STYLE_TYPE_MAP:
            self.style_type_var.set(best_label)
            self._apply_style_type()
        else:
            selected_versions = {"v24.1", "v24.2", "v24.3"}
            for version, var in self.variant_vars.items():
                var.set(version in selected_versions)
        preferred_output = default_output_folder()
        current_output = self.output_folder_var.get().strip()
        old_default = str(ROOT / "outputs")
        if not current_output or current_output == old_default:
            self.output_folder_var.set(str(preferred_output))
        self.status_var.set("Applied customer preset: v24.1 + v24.2 + v24.3")

    def _build_preflight_report(self) -> tuple[list[str], list[str], str]:
        info: list[str] = []
        warnings: list[str] = []

        template = Path(self.template_var.get().strip()) if self.template_var.get().strip() else None
        audio_files = [Path(item) for item in self._parse_audio_var()]
        layout = Path(self.layout_var.get().strip()) if self.layout_var.get().strip() else None
        output_root = Path(self.output_folder_var.get().strip() or str(default_output_folder()))

        if template is None or not template.exists():
            warnings.append("Template XSQ is missing or invalid.")
        else:
            info.append(f"Template XSQ: {template}")
        if not audio_files:
            warnings.append("Audio file is missing or invalid.")
        else:
            missing_audio = [path for path in audio_files if not path.exists()]
            valid_audio = [path for path in audio_files if path.exists()]
            if valid_audio:
                preview = ", ".join(path.name for path in valid_audio[:4])
                suffix = "" if len(valid_audio) <= 4 else f", +{len(valid_audio) - 4} more"
                info.append(f"Audio files: {len(valid_audio)} ({preview}{suffix})")
            if missing_audio:
                warnings.append(
                    f"Audio files missing: {len(missing_audio)}. Example: {[str(path) for path in missing_audio[:3]]}"
                )
            non_wav = [path.name for path in valid_audio if path.suffix.lower() != ".wav"]
            if non_wav:
                warnings.append(
                    f"Non-WAV audio detected: {len(non_wav)} file(s). Supported, but WAV usually gives cleaner analysis."
                )
        if layout is None or not layout.exists():
            warnings.append("Layout file is missing or invalid.")
        else:
            info.append(f"Layout file: {layout.name}")
        try:
            output_root.mkdir(parents=True, exist_ok=True)
            info.append(f"Output folder: {output_root}")
        except Exception as exc:
            warnings.append(f"Output folder is not writable: {exc}")

        if template is not None and template.exists() and layout is not None and layout.exists():
            try:
                xsq = base.load_xsq(template)
                ordered_layout, lookup = base._layout_entries_and_lookup(layout)
                seq_names = sorted(xsq.elements.keys())
                mapped = [base._map_layout_name(name, lookup) for name in seq_names]
                missing = [name for name, actual in zip(seq_names, mapped) if not actual]
                mapped_names = {name for name in mapped if name}
                unused = [name for name in ordered_layout if name not in mapped_names]
                info.append(f"Template element rows: {len(seq_names)}")
                info.append(f"Layout models/groups: {len(ordered_layout)}")
                if missing:
                    warnings.append(f"Template rows not found in current layout: {len(missing)}. Example: {missing[:6]}")
                else:
                    info.append("Template and layout names line up cleanly.")
                if unused:
                    warnings.append(f"Current layout rows not represented in template: {len(unused)}. Example: {unused[:6]}")
            except Exception as exc:
                warnings.append(f"Template/layout audit failed: {exc}")

        if layout is not None and layout.exists():
            try:
                parsed = xmp.parse_layout(layout)
                type_counts = Counter(model.type for model in parsed.models.values())
                multi_node_models = sum(1 for model in parsed.models.values() if model.is_pixel_model())
                rgb_models = sum(1 for model in parsed.models.values() if model.is_rgb_capable())
                info.append(f"Parsed layout models: {len(parsed.models)}")
                info.append(f"Parsed layout groups: {len(parsed.groups)}")
                info.append(f"Multi-node models: {multi_node_models}")
                info.append(f"RGB-capable models: {rgb_models}")
                info.append("Model types: " + ", ".join(f"{kind}:{count}" for kind, count in sorted(type_counts.items())))
                if multi_node_models == 0:
                    warnings.append("No multi-node models detected, so spatial and pixel-region logic will stay limited.")
                if rgb_models == 0:
                    warnings.append("No RGB-capable models detected, so full color-morph and RGB-specific effects will stay limited.")
                if type_counts.get("matrix", 0) == 0:
                    warnings.append("No matrix models detected. Matrix-specific effects will be skipped.")
                if type_counts.get("spinner", 0) == 0:
                    warnings.append("No spinner models detected. Spinner-specific effects will be skipped.")
                if type_counts.get("arch", 0) == 0:
                    warnings.append("No arch-style polyline models detected. Arch wave choreography will be reduced.")
            except Exception as exc:
                warnings.append(f"Layout parser audit failed: {exc}")

        selected = self._selected_versions()
        if not selected:
            warnings.append("No versions are currently selected.")
        else:
            info.append(f"Selected versions: {', '.join(selected)}")
        preset = STYLE_TYPE_MAP.get(self.style_type_var.get())
        if preset is not None:
            info.append(f"Style type: {preset.label}")
            info.append(f"Style note: {preset.note}")

        report_lines = [f"{APP_BRAND} Preflight Audit", "=" * 40, ""]
        report_lines.append("Info")
        for line in info:
            report_lines.append(f"- {line}")
        report_lines.append("")
        report_lines.append("Warnings")
        if warnings:
            for line in warnings:
                report_lines.append(f"- {line}")
        else:
            report_lines.append("- No blocking issues detected.")
        return info, warnings, "\n".join(report_lines)

    def _show_preflight_audit(self) -> None:
        _info, warnings, text = self._build_preflight_report()
        self._show_progress_window(reset=False)
        self._push_log("")
        self._push_log("[PREFLIGHT]")
        for line in text.splitlines():
            self._push_log(line)
        self.status_var.set("Preflight audit complete.")
        title = "Preflight Audit"
        if warnings:
            messagebox.showwarning(title, text)
        else:
            messagebox.showinfo(title, text)

    def _toggle_variant(self, version: str) -> None:
        var = self.variant_vars.get(version)
        if var is None:
            return
        var.set(not bool(var.get()))

    def _toggle_advanced_versions(self) -> None:
        self.advanced_versions_visible = not self.advanced_versions_visible
        if self.advanced_versions_frame is not None:
            if self.advanced_versions_visible:
                self.advanced_versions_frame.grid()
            else:
                self.advanced_versions_frame.grid_remove()
        if self.advanced_versions_actions is not None:
            if self.advanced_versions_visible:
                self.advanced_versions_actions.grid()
            else:
                self.advanced_versions_actions.grid_remove()
        if self.advanced_versions_button is not None:
            self.advanced_versions_button.configure(
                text="Hide Advanced Variants" if self.advanced_versions_visible else "Show Advanced Variants"
            )
        self.status_var.set(
            "Advanced variants visible." if self.advanced_versions_visible else "Premium style mode active."
        )

    def _apply_variant_row_style(self, version: str) -> None:
        widgets = self.variant_rows.get(version)
        var = self.variant_vars.get(version)
        if not widgets or var is None:
            return
        selected = bool(var.get())
        frame = widgets["frame"]
        check = widgets["check"]
        note = widgets["note"]
        badge = widgets["badge"]
        bg = "#1e4f63" if selected else "#12202b"
        border = "#8ce8ff" if selected else "#294456"
        fg = "#ffffff" if selected else "#f2fbff"
        note_fg = "#dff7ff" if selected else "#8fb6d2"
        badge_bg = "#7ce0c2" if selected else "#314652"
        badge_fg = "#08151b" if selected else "#b8d3e0"
        frame.configure(bg=bg, highlightbackground=border, highlightthickness=(2 if selected else 1))
        check.configure(
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            selectcolor=bg,
            relief=("sunken" if selected else "flat"),
        )
        note.configure(bg=bg, fg=note_fg)
        badge.configure(
            bg=badge_bg,
            fg=badge_fg,
            text=("Selected" if selected else "Click To Use"),
        )

    def _style_folder_path(self) -> Path | None:
        raw = self.style_folder_var.get().strip()
        if not raw:
            return None
        return Path(raw)

    def _history_enabled(self) -> bool:
        style_folder = self._style_folder_path()
        if style_folder is not None and style_folder.exists():
            return True
        return bool(self.learn_from_me_var.get())

    def _select_v20(self) -> None:
        for item in ACTIVE_VARIANT_OPTIONS:
            self.variant_vars[item.version].set(item.group == "Private Studio")

    def _select_v21(self) -> None:
        for item in ACTIVE_VARIANT_OPTIONS:
            self.variant_vars[item.version].set(item.group == "Director Drafts")

    def _select_v22(self) -> None:
        for item in ACTIVE_VARIANT_OPTIONS:
            self.variant_vars[item.version].set(item.group == "Premium Refined")

    def _select_v23(self) -> None:
        for item in ACTIVE_VARIANT_OPTIONS:
            self.variant_vars[item.version].set(item.group == "Premium Apex")

    def _select_latest(self) -> None:
        for item in ACTIVE_VARIANT_OPTIONS:
            self.variant_vars[item.version].set(item.group in {"Apex Vanguard", "Vendor Edition"})

    def _select_all(self) -> None:
        for var in self.variant_vars.values():
            var.set(True)

    def _select_none(self) -> None:
        for var in self.variant_vars.values():
            var.set(False)

    def _set_running(self, running: bool) -> None:
        self.running = running
        self.run_button.configure(state=("disabled" if running else "normal"))
        if not running and self.progress_bar is not None:
            self.progress_bar.stop()

    def _start_generation(self) -> None:
        if self.running:
            return
        template = Path(self.template_var.get().strip())
        audio_files = self._resolved_audio_paths()
        if not template.exists():
            messagebox.showerror("Missing Template", "Select a valid template XSQ first.")
            return
        if not audio_files:
            messagebox.showerror("Missing Audio", "Select one or more valid audio files first.")
            return
        missing_audio = [path for path in audio_files if not path.exists()]
        if missing_audio:
            sample = "\n".join(str(path) for path in missing_audio[:4])
            messagebox.showerror(
                "Missing Audio",
                "One or more selected audio files are missing:\n\n" + sample,
            )
            return
        style_folder = self._style_folder_path()
        if style_folder is not None and not style_folder.exists():
            messagebox.showerror("Missing Style Folder", "Select a valid Style XSQ Folder or leave it blank.")
            return
        self._save_template_state(str(template))
        if not self.layout_var.get().strip():
            self._refresh_layout()
        _preflight_info, preflight_warnings, preflight_text = self._build_preflight_report()
        selected = self._selected_versions()
        if not selected:
            messagebox.showerror("No Versions Selected", "Select at least one descriptor.")
            return
        total_jobs = len(selected) * len(audio_files)
        self._set_running(True)
        self._show_progress_window(reset=True)
        self.status_var.set(f"Running {len(selected)} version(s) across {len(audio_files)} audio file(s)...")
        self._push_log("=" * 72)
        self._push_log(f"Run started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        self._push_log(f"Template: {template}")
        self._push_log(f"Audio files ({len(audio_files)}):")
        for path in audio_files:
            self._push_log(f"  - {path}")
        self._push_log(f"Layout: {self.layout_var.get().strip()}")
        self._push_log(f"Style Type: {self.style_type_var.get()}")
        if style_folder is not None:
            self._push_log(f"Style XSQ Folder: {style_folder}")
            self._push_log("Style XSQ Folder is reference-only in this build. Learning uses app-generated outputs only.")
        else:
            self._push_log("Style XSQ Folder: none selected")
        if self.learn_from_me_var.get():
            self._push_log("Learn From My XSQs: enabled (the app will scan your local output workspace over time)")
        else:
            self._push_log("Learn From My XSQs: disabled")
        self._push_log("[PREFLIGHT]")
        for line in preflight_text.splitlines():
            self._push_log(line)
        if preflight_warnings:
            self._push_log(f"Preflight warnings: {len(preflight_warnings)}")
        else:
            self._push_log("Preflight warnings: none")
        self._push_log(f"Versions: {', '.join(selected)}")
        self._push_log(f"Total jobs: {total_jobs}")
        self.worker = threading.Thread(target=self._run_worker, args=(selected, audio_files), daemon=True)
        self.worker.start()

    def _run_worker(self, selected: list[str], audio_files: list[Path]) -> None:
        try:
            total_jobs = len(selected) * len(audio_files)
            job_index = 0
            for audio in audio_files:
                for version in selected:
                    job_index += 1
                    self._push_status(f"Running {version} on {audio.name} ({job_index}/{total_jobs})...")
                    self._run_single_variant(version, job_index, total_jobs, audio)
            self._push_status(
                "Generation complete. Final XSQ files are ready."
            )
            if self.last_output_dir is not None and self.last_output_dir.exists():
                try:
                    open_path(self.last_output_dir)
                except Exception as exc:
                    self._push_log(f"[WARN] Output folder open skipped: {exc}")
        except Exception as exc:
            self._push_status(f"Run failed: {exc!r}")
            self._push_log(f"[ERROR] {exc!r}")
        finally:
            self.log_queue.put(("done", ""))

    def _run_single_variant(self, version: str, index: int, total: int, audio: Path) -> None:
        script = SCRIPT_MAP.get(version)
        if script is None:
            raise RuntimeError(f"Unknown version: {version}")
        if not getattr(sys, "frozen", False) and not script.exists():
            raise RuntimeError(f"Script not found for {version}: {script}")

        template = Path(self.template_var.get().strip())
        layout = Path(self.layout_var.get().strip()) if self.layout_var.get().strip() else None
        output_root = Path(self.output_folder_var.get().strip() or str(default_output_folder()))
        style_folder = self._style_folder_path()
        output_dir = output_root / version
        output_dir.mkdir(parents=True, exist_ok=True)
        self.last_output_dir = output_dir
        python_path = PYTHON_PATH if PYTHON_PATH.exists() else Path(sys.executable)

        profile = energy_profile(float(self.energy_var.get()))
        feel = str(profile["feel"])
        bass_bias = float(profile["bass_bias"])
        melody_density = float(profile["melody_density"])
        darkness = float(profile["darkness"])
        spatial = float(profile["spatial"])
        keyboard_mix = float(profile["keyboard_mix"])
        cane_focus = float(profile["cane_focus"])
        flash_guard = float(profile["flash_guard"])
        chase = chase_style_for_energy(float(self.energy_var.get()))
        layering = layering_for_energy(float(self.energy_var.get()))
        polyphony = 3 if self.energy_var.get() < 0.38 else 4 if self.energy_var.get() < 0.76 else 5

        args: list[str] = [
            "--template",
            str(template),
            "--audio",
            str(audio),
            "--output-dir",
            str(output_dir),
            "--no-prompt",
            "--feel",
            feel,
            "--density",
            f"{float(self.density_var.get()):.3f}",
            "--speed",
            f"{float(self.speed_var.get()):.3f}",
            "--randomness",
            f"{float(self.randomness_var.get()):.3f}",
            "--bass-bias",
            f"{bass_bias:.3f}",
            "--melody-density",
            f"{melody_density:.3f}",
            "--darkness",
            f"{darkness:.3f}",
            "--polyphony",
            str(polyphony),
            "--cane-focus",
            f"{cane_focus:.3f}",
            "--flash-guard",
            f"{flash_guard:.3f}",
            "--keyboard-mix",
            f"{keyboard_mix:.3f}",
            "--spatial-awareness",
            f"{spatial:.3f}",
            "--chase-style",
            chase,
            "--layering-mode",
            layering,
            "--layer-priority-vocals",
            "4",
            "--layer-priority-drums",
            "3",
            "--layer-priority-bass",
            "2",
            "--layer-priority-other",
            "1",
            "--palette-mode",
            self._palette_mode(),
            "--workspace-history-limit",
            "60",
            "--base-effect",
            "On",
            "--motion-effect",
            "Single Strand",
            "--accent-effect",
            "Shimmer",
            "--max-layers-per-prop",
            "3",
            "--min-effect-ms",
            "60",
            "--sync-lyrics-heads",
            "--template-guidance",
            "--auto-timing-tracks",
            "--strict-xlights-effects",
        ]
        if self.pixel_reactive_var.get():
            args.append("--pixel-reactive")
        else:
            args.append("--no-pixel-reactive")

        if self.ac_only_var.get():
            args.extend(["--ac-lights-only", "--motion-effect", "Shimmer", "--accent-effect", "Twinkle"])
        if layout is not None and layout.exists():
            args.extend(["--layout-file", str(layout)])
        repo = xfb.discover_xlights_repo(ROOT) or xfb.discover_xlights_repo(APP_ROOT)
        if repo is not None and repo.exists():
            args.extend(["--xlights-repo", str(repo)])
        if CATALOG_PATH.exists():
            args.extend(["--xlights-features-json", str(CATALOG_PATH)])
        output_root.mkdir(parents=True, exist_ok=True)
        if self._history_enabled():
            args.extend(["--workspace-history-folder", str(output_root)])
        else:
            args.append("--no-workspace-history")
        moises_key = os.environ.get("MOISES_API_KEY", "").strip()
        if moises_key:
            args.extend(["--use-moises", "--moises-api-key", moises_key])

        cmd = build_python_cmd(script, args, python_path)
        self._push_log("")
        self._push_log(f"[{index}/{total}] {version} | {audio.name} -> {output_dir}")
        self._push_log("CMD: " + " ".join(f'\"{part}\"' if " " in part else part for part in cmd))

        if getattr(sys, "frozen", False):
            self._run_variant_inline(version, args)
            self._log_quality_summary(output_dir, audio.stem, version)
            self._push_log(f"[OK] {version} complete")
            return

        process = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            self._push_log(line.rstrip())
        rc = process.wait()
        if rc != 0:
            raise RuntimeError(f"{version} failed with exit code {rc}")
        self._log_quality_summary(output_dir, audio.stem, version)
        self._push_log(f"[OK] {version} complete")

    def _run_variant_inline(self, version: str, args: list[str]) -> None:
        import variant_engine

        prior_variant_log = getattr(variant_engine, "log", None)
        prior_base_log = variant_engine.base.log
        prior_base_die = variant_engine.base.die
        prior_verbose = variant_engine.base.VERBOSE

        def ui_log(message: str) -> None:
            self._push_log(str(message))

        def ui_die(message: str, code: int = 1) -> None:
            raise RuntimeError(str(message) or f"{version} failed with exit code {code}")

        try:
            variant_engine.base.log = ui_log
            variant_engine.log = ui_log
            variant_engine.base.die = ui_die
            variant_engine.main_for(version, args)
        except SystemExit as exc:
            exit_code = exc.code if isinstance(exc.code, int) else 1
            if exit_code not in (0, None):
                raise RuntimeError(f"{version} exited with code {exit_code}") from exc
        finally:
            variant_engine.base.log = prior_base_log
            if prior_variant_log is not None:
                variant_engine.log = prior_variant_log
            variant_engine.base.die = prior_base_die
            variant_engine.base.VERBOSE = prior_verbose

    def _latest_report_for(self, output_dir: Path, audio_stem: str, version: str) -> Path | None:
        candidates = sorted(
            output_dir.glob(f"{audio_stem},{version}*.report.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return candidates[0] if candidates else None

    def _log_quality_summary(self, output_dir: Path, audio_stem: str, version: str) -> None:
        report = self._latest_report_for(output_dir, audio_stem, version)
        if report is None:
            return
        try:
            payload = json.loads(report.read_text(encoding="utf-8"))
        except Exception as exc:
            self._push_log(f"[QUALITY] Could not read {report.name}: {exc!r}")
            return
        quality = payload.get("quality", {}) or {}
        score = quality.get("score", "")
        grade = quality.get("grade", "")
        strengths = ", ".join((quality.get("strengths", []) or [])[:2])
        cautions = ", ".join((quality.get("cautions", []) or [])[:1])
        summary = f"[QUALITY] {version}: {score} ({grade})"
        if strengths:
            summary += f" | strengths: {strengths}"
        if cautions:
            summary += f" | caution: {cautions}"
        self._push_log(summary)

    def _open_output_folder(self) -> None:
        root_path = Path(self.output_folder_var.get().strip() or str(default_output_folder()))
        root_path.mkdir(parents=True, exist_ok=True)
        open_path(root_path)

    def _open_style_folder(self) -> None:
        style_folder = self._style_folder_path()
        if style_folder is None:
            messagebox.showinfo("Style XSQ Folder", "Choose a Style XSQ Folder first.")
            return
        style_folder.mkdir(parents=True, exist_ok=True)
        open_path(style_folder)

    def _refresh_catalog_async(self) -> None:
        thread = threading.Thread(target=self._refresh_catalog_worker, daemon=True)
        thread.start()

    def _refresh_catalog_worker(self) -> None:
        try:
            repo = xfb.discover_xlights_repo(ROOT) or xfb.discover_xlights_repo(APP_ROOT)
            catalog = xfb.load_or_build_catalog(ROOT, repo_root=repo, cache_path=CATALOG_PATH)
            if catalog:
                count = int(catalog.get("effect_count", 0))
                src = catalog.get("source_repo", "") or (str(repo) if repo else "cached catalog")
                self.log_queue.put(("catalog", f"xLights features detected: {count} effects"))
                self.log_queue.put(("log", f"xLights feature catalog ready: {count} effects ({src})"))
            else:
                self.log_queue.put(("catalog", "xLights feature catalog unavailable"))
                self.log_queue.put(("log", "xLights feature catalog was not available, but generation can still continue."))
        except Exception as exc:
            self.log_queue.put(("catalog", "xLights feature catalog unavailable"))
            self.log_queue.put(("log", f"xLights catalog refresh failed: {exc!r}"))

    def _push_log(self, text: str) -> None:
        self.log_queue.put(("log", text))

    def _push_status(self, text: str) -> None:
        self.log_queue.put(("status", text))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == "log":
                    self.log_box.configure(state="normal")
                    self.log_box.insert("end", payload + "\n")
                    self.log_box.see("end")
                    self.log_box.configure(state="disabled")
                    self._append_progress(payload)
                    if payload.strip():
                        self.progress_line_var.set(payload)
                elif kind == "status":
                    self.status_var.set(payload)
                    self.progress_status_var.set(payload)
                elif kind == "catalog":
                    self.catalog_var.set(payload)
                elif kind == "done":
                    self._set_running(False)
                    if self.progress_bar is not None:
                        self.progress_bar.stop()
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)

def _dispatch_frozen_worker(argv: list[str]) -> int:
    if not argv:
        return 1
    mode = argv[0].strip().lower()
    if mode == "--run-variant":
        if len(argv) < 2:
            return 2
        version = argv[1]
        rest = argv[2:]
        import variant_engine

        variant_engine.main_for(version, rest)
        return 0
    return 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0].startswith("--run-"):
        return _dispatch_frozen_worker(args)
    Launcher().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
