from __future__ import annotations

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

_LOGO_CANDIDATES = ("c82.png", "app_icon.ico")
_MASCOT_CANDIDATES = (
    "helixmascot.jpg",
    "helixmascot.jpeg",
    "helixmascot.png",
    "c82fa187-9965-42cc-a906-b1802b2f0c97 (3).jpg",
)
_WORKING_VIDEO_CANDIDATES = (
    "helix_twist.mp4",
    "grok-video-9256730a-68a5-49ec-855c-ad156e1fa006.mp4",
)

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
) -> list[str]:
    cmd = _runner_prefix()
    cmd.extend(["--profile", profile, "--"])
    cmd.extend(["--no-prompt", "--single"])
    cmd.extend(["--template", template_path, "--audio", audio_path, "--feel", feel])
    if layout_path:
        cmd.extend(["--layout-file", layout_path])
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
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

    root = tk.Tk()
    root.title("Helix Sequence Helper")
    root.geometry("1240x790")
    root.minsize(1060, 700)
    root.configure(bg="#f3f7f5")

    profile_var = tk.StringVar(value=profiles[0])
    feel_var = tk.StringVar(value="balanced")
    template_var = tk.StringVar(value=_default_template(workspace))
    audio_var = tk.StringVar(value=_default_audio(workspace))
    layout_var = tk.StringVar(value=_default_layout(workspace))
    output_var = tk.StringVar(value=_default_output_dir(workspace))
    status_var = tk.StringVar(value="Ready. Choose files and press Run.")
    render_mp4_var = tk.BooleanVar(value=True)

    logo_path = _find_asset(workspace, _LOGO_CANDIDATES)
    mascot_path = _find_asset(workspace, _MASCOT_CANDIDATES)
    helix_video_path = _find_asset(workspace, _WORKING_VIDEO_CANDIDATES)

    if logo_path:
        try:
            icon_image = tk.PhotoImage(file=str(logo_path))
            root.iconphoto(True, icon_image)
            root._logo_icon = icon_image
        except Exception:
            pass

    shell = tk.Frame(root, bg="#f3f7f5", padx=16, pady=14)
    shell.pack(fill=tk.BOTH, expand=True)
    shell.grid_columnconfigure(0, weight=5)
    shell.grid_columnconfigure(1, weight=4)
    shell.grid_rowconfigure(2, weight=4)
    shell.grid_rowconfigure(1, weight=3)

    header = tk.Frame(shell, bg="#f3f7f5")
    header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    header.grid_columnconfigure(1, weight=1)

    logo_photo = _load_photo(logo_path, (62, 62)) if logo_path else None
    if logo_photo:
        logo_label = tk.Label(header, image=logo_photo, bg="#f3f7f5")
        logo_label.image = logo_photo
        logo_label.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 10))

    tk.Label(
        header,
        text="Helix Sequence Helper",
        font=("Segoe UI Semibold", 25, "bold"),
        bg="#f3f7f5",
        fg="#0c5842",
    ).grid(row=0, column=1, sticky="w")
    tk.Label(
        header,
        text="Sequencing, Simplified.  |  Helix and Relax.",
        font=("Segoe UI", 11, "italic"),
        bg="#f3f7f5",
        fg="#1e6f56",
    ).grid(row=1, column=1, sticky="w")

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

    tk.Label(setup_panel, text="Profile", bg="#ffffff", fg="#20483c", font=("Segoe UI", 10, "bold")).grid(
        row=1, column=0, sticky="w", pady=5
    )
    profile_combo = ttk.Combobox(setup_panel, textvariable=profile_var, values=profiles, state="readonly")
    profile_combo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5, padx=(8, 0))
    controls.append(profile_combo)

    tk.Label(setup_panel, text="Feel", bg="#ffffff", fg="#20483c", font=("Segoe UI", 10, "bold")).grid(
        row=2, column=0, sticky="w", pady=5
    )
    feel_combo = ttk.Combobox(setup_panel, textvariable=feel_var, values=list(_FEELS), state="readonly")
    feel_combo.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5, padx=(8, 0))
    controls.append(feel_combo)

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
    render_mp4_check.grid(row=7, column=0, columnspan=3, sticky="w", pady=(8, 8))
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
    run_button.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(4, 8))
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
    status_label.grid(row=9, column=0, columnspan=3, sticky="w")

    tk.Label(media_panel, text="Working Visual", bg="#eaf5ef", fg="#0c5f46", font=("Segoe UI", 13, "bold")).grid(
        row=0, column=0, sticky="w", pady=(0, 8)
    )

    mascot_photo = _load_photo(mascot_path, (380, 260)) if mascot_path else None
    mascot_label = tk.Label(media_panel, bg="#eaf5ef")
    mascot_label.grid(row=1, column=0, sticky="n")
    if mascot_photo:
        mascot_label.configure(image=mascot_photo)
        mascot_label.image = mascot_photo
    else:
        mascot_label.configure(text="Add helixmascot.jpg to show mascot art.", fg="#386b5a", font=("Segoe UI", 10))

    animation_label = ttk.Label(media_panel, anchor=tk.CENTER)
    animation_label.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    animation_label.configure(text="Animation plays while work is active.")

    working_frames: list[ImageTk.PhotoImage] = []
    working_delay = 120
    if helix_video_path:
        working_frames, working_delay = _load_working_frames(helix_video_path, max_size=(380, 210))
    if working_frames:
        animation_label.configure(image=working_frames[0], text="")
        animation_label.image = working_frames[0]
    else:
        animation_label.configure(text="Add helix_twist.mp4 to enable working animation.")

    animator = _FrameAnimator(animation_label, working_frames, working_delay)

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
            profile_combo.configure(state="readonly")
            feel_combo.configure(state="readonly")

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

    def _launch_process(cmd: list[str], stage: str) -> bool:
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
        root.after(220, _monitor_process)
        return True

    def _finish_success(message: str, color: str = "#1b6f50") -> None:
        animator.stop()
        _disable_controls(False)
        status_label.configure(fg=color)
        status_var.set(message)

    def _finish_error(message: str) -> None:
        animator.stop()
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
        animator.start()
        add_log("Starting sequence run...")
        if "allmodels" not in str(layout_path).lower():
            add_log("WARNING: layout does not look like allmodels. Neighbor artistry may not trigger.")
        if not _launch_process(command, "sequencing"):
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
