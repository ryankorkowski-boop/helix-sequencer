from __future__ import annotations

import os
import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from PIL import Image, ImageTk

from core import engine_profiles

try:
    import imageio.v3 as iio
except Exception:
    iio = None

SW_HIDE = 0
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS

_AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".m4a", ".ogg")
_FEELS = ("balanced", "aggressive", "airy", "percussive")
_CHASE_STYLES = ("none", "left_to_right", "radial_out", "group_to_group", "random_walk", "wave")
_LAYERING_MODES = ("replace", "overlay_blend", "smart_layer", "additive")
_PALETTE_MODES = ("template", "christmas", "warm", "cool", "neon", "random", "workspace_match")
_VARIANT_COUNTS = ("1", "2", "3", "4", "5")

_LOGO_CANDIDATES = ("c82.png", "c82.ico")
_WORKING_VIDEO_CANDIDATES = (
    "helix_twist.mp4",
    "grok-video-9256730a-68a5-49ec-855c-ad156e1fa006.mp4",
)
_SNOWMAN_CONCEPT_ORDER = ("snowcap_swing", "aurora_echo", "candy_cabaret", "festival_of_frost")

_SAVED_XSQ_RE = re.compile(r"Saved:\s*(.+?\.xsq)\s*(?:\||$)", re.IGNORECASE)
_CREATED_MP4_RE = re.compile(r"Created\s+(.+?\.mp4)\s*$", re.IGNORECASE)


def _hide_console_window() -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)
    except Exception:
        pass


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            return Path(bundle_root)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _asset_roots(workspace: Path) -> list[Path]:
    roots: list[Path] = [_resource_root(), Path(sys.executable).resolve().parent, workspace, Path.home() / "Downloads"]
    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root.resolve()) if root.exists() else str(root)
        if key not in seen:
            seen.add(key)
            deduped.append(root)
    return deduped


def _find_asset(workspace: Path, names: tuple[str, ...]) -> Path | None:
    for root in _asset_roots(workspace):
        for name in names:
            candidate = root / name
            if candidate.exists():
                return candidate
    return None


def _default_template(workspace: Path) -> str:
    candidate = workspace / "template.xsq"
    if candidate.exists():
        return str(candidate)
    return ""


def _default_layout(workspace: Path) -> str:
    candidates = (
        workspace / "allmodels" / "xlights_rgbeffects.xml",
        workspace / "allmodels" / "xlights_rgbeffects.xbkp",
        workspace / "xlights_rgbeffects.xml",
        workspace / "xlights_rgbeffects.xbkp",
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return ""


def _default_audio(workspace: Path) -> str:
    for ext in _AUDIO_EXTENSIONS:
        matches = sorted(workspace.glob(f"*{ext}"))
        if matches:
            return str(matches[0])
    return ""


def _default_output_dir(workspace: Path) -> str:
    return str(workspace / "outputs")


def _snowman_gallery_path(workspace: Path) -> Path | None:
    candidate = workspace / "outputs" / "snowman_bands" / "gallery.html"
    if candidate.exists():
        return candidate
    return None


def _snowman_concept_paths(workspace: Path) -> list[Path]:
    concepts_dir = workspace / "outputs" / "snowman_bands"
    if not concepts_dir.exists():
        return []
    order_lookup = {stem: index for index, stem in enumerate(_SNOWMAN_CONCEPT_ORDER)}
    return sorted(
        (path for path in concepts_dir.glob("*.svg") if path.is_file()),
        key=lambda path: (order_lookup.get(path.stem, len(order_lookup)), path.stem),
    )


def _concept_title(path: Path) -> str:
    return path.stem.replace("_", " ").title()


def _describe_layout_choice(raw_path: str) -> tuple[str, str]:
    clean_path = raw_path.strip()
    if not clean_path:
        return "No layout selected yet. Pick the allmodels overlay to keep the base 256 AC channels untouched.", "#8f2c2c"

    layout_path = Path(clean_path)
    if not layout_path.exists():
        return "Selected layout file is missing. Re-pick the allmodels overlay before running.", "#8f2c2c"

    if "allmodels" in str(layout_path).lower():
        return (
            "Allmodels overlay ready. Your original 256 AC channels stay intact while extended props map around them.",
            "#1b6f50",
        )

    return (
        "Custom layout selected. Double-check that your added props stay off the original 256 AC channel footprint.",
        "#946b1d",
    )


def _runner_prefix() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable]
    project_root = Path(__file__).resolve().parent.parent
    return [sys.executable, str(project_root / "main.py")]


def _build_sequence_command(
    profile: str,
    template_path: str,
    audio_path: str,
    layout_path: str,
    output_dir: str,
    feel: str,
    *,
    keyboard_mix: str,
    flash_guard: str,
    spatial_awareness: str,
    chase_style: str,
    layering_mode: str,
    palette_mode: str,
    template_guidance: bool,
    auto_timing_tracks: bool,
    pixel_reactive: bool,
    polish_enabled: bool,
    workspace_history: bool,
    learn_from_my_xsqs: bool,
    variant_count: str,
    auto_shortlist: bool,
    ac_lights_only: bool,
) -> list[str]:
    cmd = _runner_prefix()
    cmd.extend(["--profile", profile, "--"])
    cmd.extend(["--no-prompt", "--single"])
    cmd.extend(["--template", template_path, "--audio", audio_path, "--feel", feel])
    if layout_path:
        cmd.extend(["--layout-file", layout_path])
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    cmd.extend(
        [
            "--keyboard-mix",
            keyboard_mix,
            "--flash-guard",
            flash_guard,
            "--spatial-awareness",
            spatial_awareness,
            "--chase-style",
            chase_style,
            "--layering-mode",
            layering_mode,
            "--palette-mode",
            palette_mode,
        ]
    )
    cmd.append("--template-guidance" if template_guidance else "--no-template-guidance")
    cmd.append("--auto-timing-tracks" if auto_timing_tracks else "--no-auto-timing-tracks")
    cmd.append("--pixel-reactive" if pixel_reactive else "--no-pixel-reactive")
    cmd.append("--polish" if polish_enabled else "--no-polish")
    cmd.append("--workspace-history" if workspace_history else "--no-workspace-history")
    cmd.extend(["--variants", variant_count])
    if auto_shortlist:
        cmd.append("--auto-shortlist")
    if learn_from_my_xsqs:
        cmd.append("--learn-from-my-xsqs")
    if ac_lights_only:
        cmd.append("--ac-lights-only")
    return cmd


def _build_preview_command(sequence_path: Path, layout_path: Path, audio_path: Path) -> list[str]:
    cmd = _runner_prefix()
    cmd.extend(
        [
            "--render-preview",
            str(sequence_path),
            "--layout",
            str(layout_path),
            "--audio",
            str(audio_path),
        ]
    )
    return cmd


def _load_photo(path: Path, max_size: tuple[int, int]) -> ImageTk.PhotoImage | None:
    try:
        image = Image.open(path).convert("RGBA")
        image.thumbnail(max_size, _RESAMPLE)
        return ImageTk.PhotoImage(image)
    except Exception:
        return None


def _theme_background_from_logo(path: Path | None, fallback: str = "#f3f7f5") -> str:
    if path is None:
        return fallback
    try:
        image = Image.open(path).convert("RGBA")
        image.thumbnail((96, 96), _RESAMPLE)
        pixels = list(image.getdata())
        opaque_pixels = [(r, g, b) for (r, g, b, a) in pixels if a >= 32]
        if not opaque_pixels:
            return fallback
        r = int(sum(px[0] for px in opaque_pixels) / len(opaque_pixels))
        g = int(sum(px[1] for px in opaque_pixels) / len(opaque_pixels))
        b = int(sum(px[2] for px in opaque_pixels) / len(opaque_pixels))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return fallback


def _load_working_frames(video_path: Path, max_size: tuple[int, int]) -> tuple[list[ImageTk.PhotoImage], int]:
    if iio is None:
        return [], 120
    try:
        metadata = iio.immeta(video_path)
        fps = float(metadata.get("fps", 12.0) or 12.0)
    except Exception:
        fps = 12.0

    target_fps = 12.0
    step = max(1, int(round(fps / target_fps)))
    delay_ms = max(45, int((1000.0 * step) / max(fps, 1.0)))

    frames: list[ImageTk.PhotoImage] = []
    try:
        for index, raw_frame in enumerate(iio.imiter(video_path)):
            if index % step != 0:
                continue
            frame_image = Image.fromarray(raw_frame).convert("RGBA")
            frame_image.thumbnail(max_size, _RESAMPLE)
            frames.append(ImageTk.PhotoImage(frame_image))
            if len(frames) >= 45:
                break
    except Exception:
        return [], delay_ms
    return frames, delay_ms


def _open_path(target: Path) -> None:
    if not target.exists():
        raise FileNotFoundError(target)
    if sys.platform.startswith("win") and hasattr(os, "startfile"):
        os.startfile(str(target))
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
        return
    subprocess.Popen(["xdg-open", str(target)])


class _FrameAnimator:
    def __init__(self, target_label: ttk.Label, frames: list[ImageTk.PhotoImage], delay_ms: int) -> None:
        self._label = target_label
        self._frames = frames
        self._delay_ms = max(delay_ms, 45)
        self._index = 0
        self._after_id: str | None = None
        self._running = False

    def start(self) -> None:
        if self._running or not self._frames:
            return
        self._running = True
        self._index = 0
        self._tick()

    def stop(self) -> None:
        self._running = False
        if self._after_id:
            self._label.after_cancel(self._after_id)
            self._after_id = None
        if self._frames:
            self._label.configure(image=self._frames[0])
            self._label.image = self._frames[0]

    def _tick(self) -> None:
        if not self._running or not self._frames:
            return
        frame = self._frames[self._index]
        self._label.configure(image=frame)
        self._label.image = frame
        self._index = (self._index + 1) % len(self._frames)
        self._after_id = self._label.after(self._delay_ms, self._tick)


def run_gui() -> int:
    _hide_console_window()

    workspace = Path.cwd()
    profiles = [profile.profile_id for profile in engine_profiles.available_profiles()] or ["master"]
    logo_path = _find_asset(workspace, _LOGO_CANDIDATES)
    theme_bg = _theme_background_from_logo(logo_path)

    root = tk.Tk()
    root.title("Helix Sequence Helper")
    root.geometry("1260x820")
    root.minsize(1100, 720)
    root.configure(bg=theme_bg)

    profile_var = tk.StringVar(value=profiles[0])
    feel_var = tk.StringVar(value="balanced")
    template_var = tk.StringVar(value=_default_template(workspace))
    audio_var = tk.StringVar(value=_default_audio(workspace))
    layout_var = tk.StringVar(value=_default_layout(workspace))
    output_var = tk.StringVar(value=_default_output_dir(workspace))
    status_var = tk.StringVar(value="Ready. Choose files and press Run.")
    render_mp4_var = tk.BooleanVar(value=True)
    keyboard_mix_var = tk.StringVar(value="1.0")
    flash_guard_var = tk.StringVar(value="0.80")
    spatial_awareness_var = tk.StringVar(value="0.0")
    chase_style_var = tk.StringVar(value="none")
    layering_mode_var = tk.StringVar(value="replace")
    palette_mode_var = tk.StringVar(value="template")
    template_guidance_var = tk.BooleanVar(value=True)
    auto_timing_tracks_var = tk.BooleanVar(value=True)
    pixel_reactive_var = tk.BooleanVar(value=True)
    polish_enabled_var = tk.BooleanVar(value=True)
    workspace_history_var = tk.BooleanVar(value=True)
    learn_from_my_xsqs_var = tk.BooleanVar(value=True)
    variant_count_var = tk.StringVar(value="5")
    auto_shortlist_var = tk.BooleanVar(value=True)
    ac_lights_only_var = tk.BooleanVar(value=False)

    helix_video_path = _find_asset(workspace, _WORKING_VIDEO_CANDIDATES)

    if logo_path:
        try:
            icon_image = tk.PhotoImage(file=str(logo_path))
            root.iconphoto(True, icon_image)
            root._logo_icon = icon_image
        except Exception:
            pass

    shell = tk.Frame(root, bg=theme_bg, padx=16, pady=14)
    shell.pack(fill=tk.BOTH, expand=True)
    shell.grid_columnconfigure(0, weight=5)
    shell.grid_columnconfigure(1, weight=4)
    shell.grid_rowconfigure(2, weight=4)
    shell.grid_rowconfigure(1, weight=3)

    header = tk.Frame(shell, bg=theme_bg)
    header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    header.grid_columnconfigure(0, weight=1)
    header.grid_columnconfigure(1, weight=0)

    tk.Label(
        header,
        text="Helix Sequence Helper",
        font=("Segoe UI Semibold", 25, "bold"),
        bg=theme_bg,
        fg="#0c5842",
    ).grid(row=0, column=0, sticky="w")
    tk.Label(
        header,
        text="Sequencing, Simplified.  |  Helix and Relax.",
        font=("Segoe UI", 11, "italic"),
        bg=theme_bg,
        fg="#1e6f56",
    ).grid(row=1, column=0, sticky="w")

    header_logo_label = tk.Label(header, bg=theme_bg)
    header_logo_label.grid(row=0, column=1, rowspan=2, sticky="e", padx=(10, 0))

    setup_panel = tk.Frame(
        shell,
        bg="#ffffff",
        padx=14,
        pady=14,
        highlightbackground="#b8d5c8",
        highlightthickness=1,
    )
    setup_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
    setup_panel.grid_columnconfigure(1, weight=1)

    media_panel = tk.Frame(
        shell,
        bg="#eaf5ef",
        padx=12,
        pady=12,
        highlightbackground="#b1d1c3",
        highlightthickness=1,
    )
    media_panel.grid(row=1, column=1, sticky="nsew")
    media_panel.grid_columnconfigure(0, weight=1)
    media_panel.grid_rowconfigure(1, weight=1)

    log_panel = tk.Frame(
        shell,
        bg="#ffffff",
        padx=12,
        pady=10,
        highlightbackground="#b8d5c8",
        highlightthickness=1,
    )
    log_panel.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
    log_panel.grid_columnconfigure(0, weight=1)
    log_panel.grid_rowconfigure(1, weight=1)

    tk.Label(setup_panel, text="Run Setup", bg="#ffffff", fg="#0d5f47", font=("Segoe UI", 15, "bold")).grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
    )

    controls: list[tk.Widget] = []
    readonly_combos: list[ttk.Combobox] = []

    def browse_file(target: tk.StringVar, title: str, file_types: list[tuple[str, str]]) -> None:
        selected = filedialog.askopenfilename(
            title=title,
            filetypes=file_types,
            initialdir=str(workspace),
        )
        if selected:
            target.set(selected)

    def browse_directory(target: tk.StringVar, title: str) -> None:
        selected = filedialog.askdirectory(title=title, initialdir=str(workspace))
        if selected:
            target.set(selected)

    def open_path_or_message(target: Path, title: str) -> None:
        try:
            _open_path(target)
        except Exception as exc:
            messagebox.showerror(title, f"Could not open:\n\n{target}\n\n{exc}")

    def _make_row(
        row: int,
        label: str,
        variable: tk.StringVar,
        browse_cmd: Callable[[], None],
        browse_text: str = "Browse",
    ) -> tuple[ttk.Entry, tk.Button]:
        tk.Label(setup_panel, text=label, bg="#ffffff", fg="#20483c", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=5
        )
        entry = ttk.Entry(setup_panel, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=5, padx=(8, 8))
        button = tk.Button(
            setup_panel,
            text=browse_text,
            command=browse_cmd,
            bg="#1f7f5f",
            fg="#ffffff",
            activebackground="#17694f",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=3,
        )
        button.grid(row=row, column=2, sticky="ew", pady=5)
        controls.extend([entry, button])
        return entry, button

    def _make_labeled_combo(
        parent: tk.Widget,
        row: int,
        column: int,
        label: str,
        variable: tk.StringVar,
        values: tuple[str, ...],
    ) -> ttk.Combobox:
        tk.Label(parent, text=label, bg=parent.cget("bg"), fg="#20483c", font=("Segoe UI", 9, "bold")).grid(
            row=row, column=column, sticky="w", pady=(4, 0), padx=(0 if column == 0 else 10, 0)
        )
        combo = ttk.Combobox(parent, textvariable=variable, values=list(values), state="readonly")
        combo.grid(row=row + 1, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0), pady=(2, 6))
        controls.append(combo)
        return combo

    def _make_labeled_entry(
        parent: tk.Widget,
        row: int,
        column: int,
        label: str,
        variable: tk.StringVar,
    ) -> ttk.Entry:
        tk.Label(parent, text=label, bg=parent.cget("bg"), fg="#20483c", font=("Segoe UI", 9, "bold")).grid(
            row=row, column=column, sticky="w", pady=(4, 0), padx=(0 if column == 0 else 10, 0)
        )
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row + 1, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0), pady=(2, 6))
        controls.append(entry)
        return entry

    tk.Label(setup_panel, text="Profile", bg="#ffffff", fg="#20483c", font=("Segoe UI", 10, "bold")).grid(
        row=1, column=0, sticky="w", pady=5
    )
    profile_combo = ttk.Combobox(setup_panel, textvariable=profile_var, values=profiles, state="readonly")
    profile_combo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5, padx=(8, 0))
    controls.append(profile_combo)
    readonly_combos.append(profile_combo)

    tk.Label(setup_panel, text="Feel", bg="#ffffff", fg="#20483c", font=("Segoe UI", 10, "bold")).grid(
        row=2, column=0, sticky="w", pady=5
    )
    feel_combo = ttk.Combobox(setup_panel, textvariable=feel_var, values=list(_FEELS), state="readonly")
    feel_combo.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5, padx=(8, 0))
    controls.append(feel_combo)
    readonly_combos.append(feel_combo)

    _make_row(
        3,
        "Template .xsq",
        template_var,
        lambda: browse_file(template_var, "Select template .xsq", [("xLights sequence", "*.xsq"), ("All files", "*.*")]),
    )
    _make_row(
        4,
        "Audio file",
        audio_var,
        lambda: browse_file(audio_var, "Select audio file", [("Audio files", "*.wav *.mp3 *.flac *.m4a *.ogg"), ("All files", "*.*")]),
    )
    _make_row(
        5,
        "Layout file",
        layout_var,
        lambda: browse_file(layout_var, "Select xLights layout", [("xLights layout", "*.xml *.xbkp"), ("All files", "*.*")]),
    )
    _make_row(
        6,
        "Output folder",
        output_var,
        lambda: browse_directory(output_var, "Select output folder"),
    )

    safety_note = tk.Label(
        setup_panel,
        text="Safe layout rule: use the allmodels layout so your original 256 AC channels stay untouched and new artistry lives around them on the overflow/null side.",
        bg="#ffffff",
        fg="#7b4e0b",
        wraplength=610,
        justify=tk.LEFT,
        font=("Segoe UI", 9, "italic"),
    )
    safety_note.grid(row=11, column=0, columnspan=3, sticky="w", pady=(8, 6))

    advanced_panel = tk.Frame(
        setup_panel,
        bg="#f7fbf8",
        padx=10,
        pady=10,
        highlightbackground="#d3e7dc",
        highlightthickness=1,
    )
    advanced_panel.grid(row=12, column=0, columnspan=3, sticky="ew", pady=(0, 8))
    advanced_panel.grid_columnconfigure(0, weight=1)
    advanced_panel.grid_columnconfigure(1, weight=1)
    advanced_panel.grid_columnconfigure(2, weight=1)
    tk.Label(
        advanced_panel,
        text="Advanced Choreography",
        bg="#f7fbf8",
        fg="#0d5f47",
        font=("Segoe UI", 11, "bold"),
    ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

    _make_labeled_entry(advanced_panel, 1, 0, "Keyboard Mix", keyboard_mix_var)
    _make_labeled_entry(advanced_panel, 1, 1, "Flash Guard", flash_guard_var)
    _make_labeled_entry(advanced_panel, 1, 2, "Spatial Awareness", spatial_awareness_var)
    readonly_combos.append(_make_labeled_combo(advanced_panel, 3, 0, "Chase Style", chase_style_var, _CHASE_STYLES))
    readonly_combos.append(_make_labeled_combo(advanced_panel, 3, 1, "Layering Mode", layering_mode_var, _LAYERING_MODES))
    readonly_combos.append(_make_labeled_combo(advanced_panel, 3, 2, "Palette Mode", palette_mode_var, _PALETTE_MODES))

    template_guidance_check = tk.Checkbutton(
        advanced_panel,
        text="Template Guidance",
        variable=template_guidance_var,
        onvalue=True,
        offvalue=False,
        bg="#f7fbf8",
        fg="#1d4f40",
        activebackground="#f7fbf8",
        font=("Segoe UI", 9),
    )
    template_guidance_check.grid(row=5, column=0, sticky="w", pady=(4, 0))
    controls.append(template_guidance_check)

    auto_timing_check = tk.Checkbutton(
        advanced_panel,
        text="Auto Timing Tracks",
        variable=auto_timing_tracks_var,
        onvalue=True,
        offvalue=False,
        bg="#f7fbf8",
        fg="#1d4f40",
        activebackground="#f7fbf8",
        font=("Segoe UI", 9),
    )
    auto_timing_check.grid(row=5, column=1, sticky="w", pady=(4, 0))
    controls.append(auto_timing_check)

    pixel_reactive_check = tk.Checkbutton(
        advanced_panel,
        text="Pixel Reactive",
        variable=pixel_reactive_var,
        onvalue=True,
        offvalue=False,
        bg="#f7fbf8",
        fg="#1d4f40",
        activebackground="#f7fbf8",
        font=("Segoe UI", 9),
    )
    pixel_reactive_check.grid(row=5, column=2, sticky="w", pady=(4, 0))
    controls.append(pixel_reactive_check)

    workspace_history_check = tk.Checkbutton(
        advanced_panel,
        text="Workspace History",
        variable=workspace_history_var,
        onvalue=True,
        offvalue=False,
        bg="#f7fbf8",
        fg="#1d4f40",
        activebackground="#f7fbf8",
        font=("Segoe UI", 9),
    )
    workspace_history_check.grid(row=6, column=0, sticky="w", pady=(4, 0))
    controls.append(workspace_history_check)

    ac_lights_only_check = tk.Checkbutton(
        advanced_panel,
        text="AC Lights Only",
        variable=ac_lights_only_var,
        onvalue=True,
        offvalue=False,
        bg="#f7fbf8",
        fg="#1d4f40",
        activebackground="#f7fbf8",
        font=("Segoe UI", 9),
    )
    ac_lights_only_check.grid(row=6, column=1, sticky="w", pady=(4, 0))
    controls.append(ac_lights_only_check)

    polish_enabled_check = tk.Checkbutton(
        advanced_panel,
        text="Deep Polish",
        variable=polish_enabled_var,
        onvalue=True,
        offvalue=False,
        bg="#f7fbf8",
        fg="#1d4f40",
        activebackground="#f7fbf8",
        font=("Segoe UI", 9),
    )
    polish_enabled_check.grid(row=6, column=2, sticky="w", pady=(4, 0))
    controls.append(polish_enabled_check)

    quality_panel = tk.Frame(
        advanced_panel,
        bg="#edf7f1",
        padx=10,
        pady=8,
        highlightbackground="#d3e7dc",
        highlightthickness=1,
    )
    quality_panel.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(8, 0))
    quality_panel.grid_columnconfigure(0, weight=1)
    quality_panel.grid_columnconfigure(1, weight=1)
    quality_panel.grid_columnconfigure(2, weight=1)

    tk.Label(
        quality_panel,
        text="Hero Render Stack",
        bg="#edf7f1",
        fg="#0d5f47",
        font=("Segoe UI", 10, "bold"),
    ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))

    tk.Label(
        quality_panel,
        text="Variant Count",
        bg="#edf7f1",
        fg="#20483c",
        font=("Segoe UI", 9, "bold"),
    ).grid(row=1, column=0, sticky="w")
    variant_count_combo = ttk.Combobox(quality_panel, textvariable=variant_count_var, values=list(_VARIANT_COUNTS), state="readonly")
    variant_count_combo.grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(2, 4))
    controls.append(variant_count_combo)
    readonly_combos.append(variant_count_combo)

    auto_shortlist_check = tk.Checkbutton(
        quality_panel,
        text="Auto Shortlist Winner",
        variable=auto_shortlist_var,
        onvalue=True,
        offvalue=False,
        bg="#edf7f1",
        fg="#1d4f40",
        activebackground="#edf7f1",
        font=("Segoe UI", 9),
    )
    auto_shortlist_check.grid(row=2, column=1, sticky="w", pady=(2, 4))
    controls.append(auto_shortlist_check)

    learn_from_my_xsqs_check = tk.Checkbutton(
        quality_panel,
        text="Learn From Saved XSQs",
        variable=learn_from_my_xsqs_var,
        onvalue=True,
        offvalue=False,
        bg="#edf7f1",
        fg="#1d4f40",
        activebackground="#edf7f1",
        font=("Segoe UI", 9),
    )
    learn_from_my_xsqs_check.grid(row=2, column=2, sticky="w", pady=(2, 4))
    controls.append(learn_from_my_xsqs_check)

    tk.Label(
        quality_panel,
        text="Default launcher target: deep polish, five runtime variants, and an auto-promoted winner while preserving the allmodels-safe layout path.",
        bg="#edf7f1",
        fg="#45695d",
        wraplength=560,
        justify=tk.LEFT,
        font=("Segoe UI", 8, "italic"),
    ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(2, 0))

    def sync_learning_toggle(*_args: object) -> None:
        enabled_state = tk.NORMAL if workspace_history_var.get() else tk.DISABLED
        learn_from_my_xsqs_check.configure(state=enabled_state)
        if enabled_state == tk.DISABLED:
            learn_from_my_xsqs_var.set(False)

    sync_learning_toggle()
    workspace_history_var.trace_add("write", sync_learning_toggle)

    render_mp4_check = tk.Checkbutton(
        setup_panel,
        text="Also render MP4 preview after sequence completes",
        variable=render_mp4_var,
        onvalue=True,
        offvalue=False,
        bg="#ffffff",
        fg="#1d4f40",
        activebackground="#ffffff",
        font=("Segoe UI", 10),
    )
    render_mp4_check.grid(row=9, column=0, columnspan=3, sticky="w", pady=(6, 6))
    controls.append(render_mp4_check)

    run_button = tk.Button(
        setup_panel,
        text="Run",
        bg="#0f8f5f",
        fg="#ffffff",
        activebackground="#0b734c",
        activeforeground="#ffffff",
        relief=tk.FLAT,
        font=("Segoe UI Semibold", 12, "bold"),
        padx=14,
        pady=8,
    )
    run_button.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(8, 6))
    controls.append(run_button)

    status_label = tk.Label(
        setup_panel,
        textvariable=status_var,
        bg="#ffffff",
        fg="#1b6f50",
        wraplength=600,
        justify=tk.LEFT,
        font=("Segoe UI", 10),
    )
    status_label.grid(row=8, column=0, columnspan=3, sticky="w", pady=(0, 4))

    tk.Label(media_panel, text="Showcase", bg=theme_bg, fg="#0c5f46", font=("Segoe UI", 13, "bold")).grid(
        row=0, column=0, sticky="w", pady=(0, 8)
    )

    showcase_tabs = ttk.Notebook(media_panel)
    showcase_tabs.grid(row=1, column=0, sticky="nsew")

    helix_tab = tk.Frame(showcase_tabs, bg=theme_bg, padx=14, pady=14)
    helix_tab.grid_columnconfigure(0, weight=1)
    helix_tab.grid_rowconfigure(1, weight=1)

    layout_tab = tk.Frame(showcase_tabs, bg=theme_bg, padx=14, pady=14)
    layout_tab.grid_columnconfigure(0, weight=1)

    showcase_tabs.add(helix_tab, text="Helix")
    showcase_tabs.add(layout_tab, text="Layout")

    tk.Label(helix_tab, text="Helix Activity", bg=theme_bg, fg="#0c5f46", font=("Segoe UI", 13, "bold")).grid(
        row=0, column=0, sticky="w", pady=(0, 8)
    )

    animation_card = tk.Frame(
        helix_tab,
        bg="#ffffff",
        padx=12,
        pady=12,
        highlightbackground="#d6e5ee",
        highlightthickness=1,
    )
    animation_card.grid(row=1, column=0, sticky="nsew")
    animation_card.grid_columnconfigure(0, weight=1)

    animation_label = tk.Label(animation_card, bg="#ffffff")
    animation_label.grid(row=0, column=0, sticky="n", pady=(0, 10))

    helix_progress_var = tk.StringVar(value="Idle. Configure files and press Run.")
    helix_progress_label = tk.Label(
        animation_card,
        textvariable=helix_progress_var,
        bg="#ffffff",
        fg="#245247",
        wraplength=360,
        justify=tk.LEFT,
        anchor="w",
        font=("Segoe UI", 10),
    )
    helix_progress_label.grid(row=1, column=0, sticky="ew")

    working_frames: list[ImageTk.PhotoImage] = []
    working_delay = 120
    if helix_video_path:
        working_frames, working_delay = _load_working_frames(helix_video_path, max_size=(380, 210))
    if working_frames:
        header_logo_label.configure(image=working_frames[0], text="")
        header_logo_label.image = working_frames[0]
        animation_label.configure(image=working_frames[0], text="")
        animation_label.image = working_frames[0]
    else:
        header_logo_photo = _load_photo(logo_path, (72, 72)) if logo_path else None
        if header_logo_photo:
            header_logo_label.configure(image=header_logo_photo, text="")
            header_logo_label.image = header_logo_photo
        else:
            header_logo_label.configure(text="H", fg="#0c5f46", font=("Segoe UI Semibold", 28, "bold"))
        animation_label.configure(text="Add helix_twist.mp4 to enable working animation.")

    animator = _FrameAnimator(animation_label, working_frames, working_delay)
    header_animator = _FrameAnimator(header_logo_label, working_frames, working_delay)

    tk.Label(
        layout_tab,
        text="Layout Tools",
        bg=theme_bg,
        fg="#0c5f46",
        font=("Segoe UI", 13, "bold"),
    ).grid(row=0, column=0, sticky="w")

    layout_summary_var = tk.StringVar()
    layout_path_var = tk.StringVar()

    layout_summary_label = tk.Label(
        layout_tab,
        textvariable=layout_summary_var,
        bg=theme_bg,
        fg="#31574c",
        wraplength=350,
        justify=tk.LEFT,
        font=("Segoe UI", 10),
    )
    layout_summary_label.grid(row=1, column=0, sticky="w", pady=(6, 12))

    layout_path_card = tk.Frame(
        layout_tab,
        bg="#ffffff",
        padx=12,
        pady=10,
        highlightbackground="#d6e5ee",
        highlightthickness=1,
    )
    layout_path_card.grid(row=2, column=0, sticky="ew")
    layout_path_card.grid_columnconfigure(0, weight=1)

    tk.Label(
        layout_path_card,
        text="Current layout path",
        bg="#ffffff",
        fg="#20483c",
        font=("Segoe UI", 10, "bold"),
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    tk.Label(
        layout_path_card,
        textvariable=layout_path_var,
        bg="#ffffff",
        fg="#2c4e44",
        wraplength=330,
        justify=tk.LEFT,
        anchor="w",
        font=("Segoe UI", 9),
    ).grid(row=1, column=0, sticky="w")

    layout_button_row = tk.Frame(layout_tab, bg=theme_bg)
    layout_button_row.grid(row=3, column=0, sticky="ew", pady=(12, 0))
    layout_button_row.grid_columnconfigure(0, weight=1)
    layout_button_row.grid_columnconfigure(1, weight=1)

    def open_selected_layout() -> None:
        selected = layout_var.get().strip()
        if not selected:
            messagebox.showinfo("Open layout", "Select a layout file first.")
            return
        open_path_or_message(Path(selected), "Open layout")

    def open_selected_layout_folder() -> None:
        selected = layout_var.get().strip()
        if not selected:
            messagebox.showinfo("Open layout folder", "Select a layout file first.")
            return
        open_path_or_message(Path(selected).resolve().parent, "Open layout folder")

    open_layout_button = tk.Button(
        layout_button_row,
        text="Open Layout",
        bg="#1f7f5f",
        fg="#ffffff",
        activebackground="#17694f",
        activeforeground="#ffffff",
        relief=tk.FLAT,
        padx=10,
        pady=5,
        command=open_selected_layout,
    )
    open_layout_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

    open_layout_folder_button = tk.Button(
        layout_button_row,
        text="Open Folder",
        bg="#d9eee3",
        fg="#1b5f4a",
        activebackground="#cbe6d9",
        relief=tk.FLAT,
        padx=10,
        pady=5,
        command=open_selected_layout_folder,
    )
    open_layout_folder_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    layout_tools_row = tk.Frame(layout_tab, bg=theme_bg)
    layout_tools_row.grid(row=4, column=0, sticky="ew", pady=(10, 0))
    layout_tools_row.grid_columnconfigure(0, weight=1)
    layout_tools_row.grid_columnconfigure(1, weight=1)

    generated_layout_path = workspace / "outputs" / "layouts" / "helixville_importable_3d" / "xlights_rgbeffects.xml"

    def run_assets_sync() -> None:
        if active_process is not None and active_process.poll() is None:
            messagebox.showinfo("Task running", "Wait for the current task to finish first.")
            return
        script_path = workspace / "tools" / "open_source_assets_sync.py"
        if not script_path.exists():
            messagebox.showerror("Missing tool", f"Could not find tool:\n\n{script_path}")
            return
        cmd = [
            sys.executable,
            str(script_path),
            "--output-root",
            "external/open_source_assets",
            "--manifest",
            "outputs/open_source/assets_manifest.json",
            "--max-files-per-repo",
            "80",
            "--repo-limit",
            "8",
        ]
        _disable_controls(True)
        status_label.configure(fg="#1b6f50")
        status_var.set("Syncing open-source assets...")
        _start_working("Syncing open-source assets...")
        add_log("Starting open-source asset sync with license gating.")
        if not _launch_process(cmd, "assets_sync"):
            _finish_error("Could not start open-source asset sync.")

    def run_helixville_layout_build() -> None:
        if active_process is not None and active_process.poll() is None:
            messagebox.showinfo("Task running", "Wait for the current task to finish first.")
            return
        script_path = workspace / "tools" / "build_helixville_layout.py"
        if not script_path.exists():
            messagebox.showerror("Missing tool", f"Could not find tool:\n\n{script_path}")
            return
        base_layout = layout_var.get().strip()
        if not base_layout:
            base_layout = _default_layout(workspace)
        if not base_layout or not Path(base_layout).exists():
            messagebox.showerror("Missing layout", "Pick a valid base layout before building Helixville 3D.")
            return
        cmd = [
            sys.executable,
            str(script_path),
            "--base-layout",
            str(base_layout),
            "--xmodel-root",
            "external/open_source_assets/models",
            "--output-layout",
            str(generated_layout_path),
            "--report",
            "outputs/layouts/helixville_importable_3d/layout_report.json",
        ]
        _disable_controls(True)
        status_label.configure(fg="#1b6f50")
        status_var.set("Building Helixville 3D layout...")
        _start_working("Building Helixville 3D layout...")
        add_log("Building Helixville importable 3D layout.")
        if not _launch_process(cmd, "helixville_layout"):
            _finish_error("Could not start Helixville 3D layout build.")

    sync_assets_button = tk.Button(
        layout_tools_row,
        text="1) Download Open-Source Assets",
        bg="#1f7f5f",
        fg="#ffffff",
        activebackground="#17694f",
        activeforeground="#ffffff",
        relief=tk.FLAT,
        padx=10,
        pady=5,
        command=run_assets_sync,
    )
    sync_assets_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
    controls.append(sync_assets_button)

    build_helixville_button = tk.Button(
        layout_tools_row,
        text="2) Build Helixville 3D Layout",
        bg="#d9eee3",
        fg="#1b5f4a",
        activebackground="#cbe6d9",
        relief=tk.FLAT,
        padx=10,
        pady=5,
        command=run_helixville_layout_build,
    )
    build_helixville_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))
    controls.append(build_helixville_button)

    tk.Label(
        layout_tab,
        text="Use step 1 first, then step 2. Step 2 creates an importable 3D test layout and auto-selects it here when done.",
        bg=theme_bg,
        fg="#4b6d62",
        wraplength=350,
        justify=tk.LEFT,
        font=("Segoe UI", 9, "italic"),
    ).grid(row=5, column=0, sticky="w", pady=(10, 0))

    def refresh_layout_panel(*_args: object) -> None:
        summary_text, summary_color = _describe_layout_choice(layout_var.get())
        layout_summary_var.set(summary_text)
        layout_summary_label.configure(fg=summary_color)

        raw_path = layout_var.get().strip()
        if raw_path:
            layout_path_var.set(raw_path)
        else:
            layout_path_var.set("No layout file selected.")

        enabled_state = tk.NORMAL if raw_path and Path(raw_path).exists() else tk.DISABLED
        open_layout_button.configure(state=enabled_state)
        open_layout_folder_button.configure(state=enabled_state)

    refresh_layout_panel()
    layout_var.trace_add("write", refresh_layout_panel)

    tk.Label(log_panel, text="Live Activity", bg="#ffffff", fg="#0c5f46", font=("Segoe UI", 13, "bold")).grid(
        row=0, column=0, sticky="w"
    )
    clear_log_button = tk.Button(
        log_panel,
        text="Clear Log",
        bg="#d9eee3",
        fg="#1b5f4a",
        activebackground="#cbe6d9",
        relief=tk.FLAT,
        padx=10,
        pady=2,
    )
    clear_log_button.grid(row=0, column=1, sticky="e")
    log_panel.grid_columnconfigure(1, weight=0)

    log_text = scrolledtext.ScrolledText(
        log_panel,
        wrap=tk.WORD,
        bg="#0f1418",
        fg="#d9f4e8",
        insertbackground="#d9f4e8",
        font=("Consolas", 9),
        height=16,
    )
    log_text.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
    log_text.configure(state=tk.DISABLED)

    active_process: subprocess.Popen[str] | None = None
    active_stage: str | None = None
    log_queue: queue.Queue[str] = queue.Queue()
    log_polling_active = False
    last_saved_sequence: Path | None = None
    last_created_mp4: Path | None = None
    current_output_dir: Path | None = None
    current_audio_path: Path | None = None
    current_layout_path: Path | None = None
    run_started_at: float | None = None

    def add_log(message: str) -> None:
        clean = message.strip()
        if not clean:
            return
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {clean}\n"
        log_text.configure(state=tk.NORMAL)
        log_text.insert(tk.END, line)
        log_text.see(tk.END)
        log_text.configure(state=tk.DISABLED)
        if clean:
            helix_progress_var.set(clean[:240])

    def _start_working(message: str) -> None:
        helix_progress_var.set(message)
        animator.start()
        header_animator.start()

    def _stop_working(message: str) -> None:
        animator.stop()
        header_animator.stop()
        helix_progress_var.set(message)

    def clear_log() -> None:
        log_text.configure(state=tk.NORMAL)
        log_text.delete("1.0", tk.END)
        log_text.configure(state=tk.DISABLED)

    def _disable_controls(disabled: bool) -> None:
        state = "disabled" if disabled else "normal"
        for control in controls:
            try:
                control.configure(state=state)
            except tk.TclError:
                pass
        if not disabled:
            for combo in readonly_combos:
                combo.configure(state="readonly")

    def _handle_stream_line(line: str) -> None:
        nonlocal last_saved_sequence, last_created_mp4
        add_log(line)

        saved_match = _SAVED_XSQ_RE.search(line)
        if saved_match:
            raw = saved_match.group(1).strip()
            candidate = Path(raw)
            if not candidate.is_absolute() and current_output_dir is not None:
                candidate = current_output_dir / candidate
            last_saved_sequence = candidate

        mp4_match = _CREATED_MP4_RE.search(line)
        if mp4_match:
            raw = mp4_match.group(1).strip()
            candidate = Path(raw)
            if not candidate.is_absolute() and current_output_dir is not None:
                candidate = current_output_dir / candidate
            last_created_mp4 = candidate

    def _reader_worker(proc: subprocess.Popen[str]) -> None:
        if proc.stdout is None:
            return
        try:
            for raw in proc.stdout:
                log_queue.put(raw.rstrip("\r\n"))
        except Exception as exc:
            log_queue.put(f"[reader-error] {exc}")
        finally:
            try:
                proc.stdout.close()
            except Exception:
                pass

    def _drain_log_queue() -> None:
        while True:
            try:
                line = log_queue.get_nowait()
            except queue.Empty:
                break
            _handle_stream_line(line)

    def _poll_log_queue() -> None:
        nonlocal log_polling_active
        _drain_log_queue()
        if active_process is not None and active_process.poll() is None:
            root.after(120, _poll_log_queue)
            return
        if not log_queue.empty():
            root.after(120, _poll_log_queue)
            return
        log_polling_active = False

    def _ensure_log_polling() -> None:
        nonlocal log_polling_active
        if log_polling_active:
            return
        log_polling_active = True
        root.after(80, _poll_log_queue)

    def _resolve_sequence_output() -> Path | None:
        if last_saved_sequence is not None and last_saved_sequence.exists():
            return last_saved_sequence
        if current_output_dir is None or not current_output_dir.exists():
            return None

        candidates: list[Path] = []
        if current_audio_path is not None:
            candidates = sorted(
                current_output_dir.glob(f"{current_audio_path.stem},*.xsq"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
        if not candidates:
            candidates = sorted(
                current_output_dir.glob("*.xsq"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
        if not candidates:
            return None
        if run_started_at is None:
            return candidates[0]
        recent = [path for path in candidates if path.stat().st_mtime >= run_started_at - 5]
        return recent[0] if recent else candidates[0]

    def _launch_process(cmd: list[str], stage: str, env_overrides: dict[str, str] | None = None) -> bool:
        nonlocal active_process, active_stage
        popen_args: dict[str, object] = {
            "cwd": str(workspace),
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "bufsize": 1,
        }
        if env_overrides:
            env = dict(os.environ)
            env.update(env_overrides)
            popen_args["env"] = env
        if sys.platform.startswith("win") and _CREATE_NO_WINDOW:
            popen_args["creationflags"] = _CREATE_NO_WINDOW
        try:
            active_process = subprocess.Popen(cmd, **popen_args)
        except Exception as exc:
            messagebox.showerror("Launch failed", f"Could not start process.\n\n{exc}")
            return False

        active_stage = stage
        threading.Thread(target=_reader_worker, args=(active_process,), daemon=True).start()
        _ensure_log_polling()
        add_log("------------------------------------------------------------")
        add_log(f"{stage.upper()} command: {' '.join(cmd)}")
        helix_progress_var.set(f"Running {stage}...")
        root.after(220, _monitor_process)
        return True

    def _finish_success(message: str, color: str = "#1b6f50") -> None:
        _stop_working(message)
        _disable_controls(False)
        status_label.configure(fg=color)
        status_var.set(message)

    def _finish_error(message: str) -> None:
        _stop_working(message)
        _disable_controls(False)
        status_label.configure(fg="#8f2c2c")
        status_var.set(message)
        messagebox.showerror("Run failed", message)

    def _monitor_process() -> None:
        nonlocal active_process, active_stage
        if active_process is None:
            return
        return_code = active_process.poll()
        if return_code is None:
            root.after(220, _monitor_process)
            return

        _drain_log_queue()
        finished_stage = active_stage or "task"
        active_process = None
        active_stage = None

        if return_code != 0:
            _finish_error(f"{finished_stage.capitalize()} exited with an error code ({return_code}).")
            return

        if finished_stage == "sequencing" and render_mp4_var.get():
            sequence_path = _resolve_sequence_output()
            if sequence_path is None:
                _finish_success("Sequence complete, but MP4 render was skipped (could not locate output .xsq).", color="#946b1d")
                return
            if current_layout_path is None or current_audio_path is None:
                _finish_success("Sequence complete. MP4 render skipped (missing layout/audio context).", color="#946b1d")
                return

            preview_cmd = _build_preview_command(sequence_path, current_layout_path, current_audio_path)
            status_label.configure(fg="#1b6f50")
            status_var.set("Sequence complete. Rendering MP4 preview...")
            helix_progress_var.set("Sequence complete. Rendering MP4 preview...")
            add_log(f"Detected sequence output: {sequence_path}")
            if not _launch_process(preview_cmd, "preview"):
                _finish_success("Sequence complete. MP4 render could not start.", color="#946b1d")
                return
            return

        if finished_stage == "preview":
            if last_created_mp4 is not None:
                _finish_success(f"Done. MP4 preview created: {last_created_mp4}")
            else:
                _finish_success("Done. MP4 preview render finished.")
            return
        if finished_stage == "assets_sync":
            _finish_success("Open-source asset sync complete.")
            return
        if finished_stage == "helixville_layout":
            if generated_layout_path.exists():
                layout_var.set(str(generated_layout_path))
                _finish_success(f"Helixville 3D layout built: {generated_layout_path}")
            else:
                _finish_success("Helixville layout build finished, but output file was not detected.", color="#946b1d")
            return

        _finish_success("Sequence complete.")

    def run_sequence() -> None:
        nonlocal current_output_dir, current_audio_path, current_layout_path, run_started_at
        nonlocal last_saved_sequence, last_created_mp4
        if active_process is not None and active_process.poll() is None:
            messagebox.showinfo("Already running", "A task is already running.")
            return

        template_path = Path(template_var.get().strip()) if template_var.get().strip() else None
        audio_path = Path(audio_var.get().strip()) if audio_var.get().strip() else None
        layout_path = Path(layout_var.get().strip()) if layout_var.get().strip() else None
        output_dir = Path(output_var.get().strip()) if output_var.get().strip() else Path(_default_output_dir(workspace))
        profile = profile_var.get().strip() or "master"
        feel = feel_var.get().strip() or "balanced"

        def _parse_float_field(label: str, raw: str, minimum: float, maximum: float) -> float:
            try:
                value = float(raw.strip())
            except Exception:
                raise ValueError(f"{label} must be a number.")
            if value < minimum or value > maximum:
                raise ValueError(f"{label} must be between {minimum:.2f} and {maximum:.2f}.")
            return value

        try:
            keyboard_mix = _parse_float_field("Keyboard Mix", keyboard_mix_var.get(), 0.0, 2.0)
            flash_guard = _parse_float_field("Flash Guard", flash_guard_var.get(), 0.0, 1.0)
            spatial_awareness = _parse_float_field("Spatial Awareness", spatial_awareness_var.get(), 0.0, 1.0)
            variant_count = int(variant_count_var.get().strip())
        except ValueError as exc:
            messagebox.showerror("Advanced settings error", str(exc))
            return
        except Exception:
            messagebox.showerror("Advanced settings error", "Variant Count must be a whole number.")
            return

        if variant_count < 1 or variant_count > 5:
            messagebox.showerror("Advanced settings error", "Variant Count must be between 1 and 5.")
            return

        if template_path is None or not template_path.exists():
            messagebox.showerror("Missing template", "Pick a valid template .xsq file.")
            return
        if audio_path is None or not audio_path.exists():
            messagebox.showerror("Missing audio", "Pick a valid audio file.")
            return
        if layout_path is None or not layout_path.exists():
            messagebox.showerror("Missing layout", "Pick a valid xLights layout .xml/.xbkp file.")
            return
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror("Output folder error", f"Could not create output folder:\n\n{exc}")
            return

        output_var.set(str(output_dir))
        command = _build_sequence_command(
            profile=profile,
            template_path=str(template_path),
            audio_path=str(audio_path),
            layout_path=str(layout_path),
            output_dir=str(output_dir),
            feel=feel,
            keyboard_mix=f"{keyboard_mix:.2f}",
            flash_guard=f"{flash_guard:.2f}",
            spatial_awareness=f"{spatial_awareness:.2f}",
            chase_style=chase_style_var.get().strip() or "none",
            layering_mode=layering_mode_var.get().strip() or "replace",
            palette_mode=palette_mode_var.get().strip() or "template",
            template_guidance=bool(template_guidance_var.get()),
            auto_timing_tracks=bool(auto_timing_tracks_var.get()),
            pixel_reactive=bool(pixel_reactive_var.get()),
            polish_enabled=bool(polish_enabled_var.get()),
            workspace_history=bool(workspace_history_var.get()),
            learn_from_my_xsqs=bool(learn_from_my_xsqs_var.get() and workspace_history_var.get()),
            variant_count=str(variant_count),
            auto_shortlist=bool(auto_shortlist_var.get()),
            ac_lights_only=bool(ac_lights_only_var.get()),
        )

        current_output_dir = output_dir
        current_audio_path = audio_path
        current_layout_path = layout_path
        run_started_at = time.time()
        last_saved_sequence = None
        last_created_mp4 = None

        _disable_controls(True)
        status_label.configure(fg="#1b6f50")
        status_var.set("Running sequencer...")
        _start_working("Running sequencer...")
        add_log("Starting sequence run...")
        add_log(
            "Hero render stack: "
            f"polish={int(bool(polish_enabled_var.get()))}, "
            f"variants={variant_count}, "
            f"shortlist={int(bool(auto_shortlist_var.get()))}, "
            f"learn_xsqs={int(bool(learn_from_my_xsqs_var.get() and workspace_history_var.get()))}"
        )
        if "allmodels" in str(layout_path).lower():
            add_log("Using allmodels overlay layout. Original 256 AC channels stay untouched; added props should ride around them.")
        else:
            add_log("WARNING: layout does not look like allmodels. Neighbor artistry may not trigger.")
        env_overrides = {"HELIX_USE_BASIC_PITCH": "1"}
        if not _launch_process(command, "sequencing", env_overrides=env_overrides):
            _finish_error("Could not start sequencer process.")

    def _on_close() -> None:
        nonlocal active_process
        if active_process is not None and active_process.poll() is None:
            should_stop = messagebox.askyesno(
                "Task running",
                "A process is still running. Stop it and close the app?",
            )
            if not should_stop:
                return
            try:
                active_process.terminate()
            except Exception:
                pass
        root.destroy()

    clear_log_button.configure(command=clear_log)
    run_button.configure(command=run_sequence)
    add_log("GUI started.")
    add_log("Default layout preference: allmodels/xlights_rgbeffects.xml when available.")

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()
    return 0
