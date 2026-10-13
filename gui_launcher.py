from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def _python_command(mode: str, script: Path) -> list[str]:
    if getattr(sys, "frozen", False):
        return [str(Path(sys.executable).resolve().with_name("HelixCLI.exe")), mode]
    return [sys.executable, str(script)]


TOOL_MODES = {
    "tools.legacy_lms_export": "--helix-legacy-lms-export",
    "tools.validate_native_xlights": "--helix-native-render",
    "tools.fseq_pixel_preview": "--helix-fseq-preview",
}


def _module_command(module: str) -> list[str]:
    if module not in TOOL_MODES:
        raise ValueError("Unsupported GUI tool")
    if getattr(sys, "frozen", False):
        return [str(Path(sys.executable).resolve().with_name("HelixCLI.exe")), TOOL_MODES[module]]
    return [sys.executable, "-m", module]


def _best_layout_file(folder: Path) -> Path:
    xbkp = folder / "xlights_rgbeffects.xbkp"
    if xbkp.exists():
        return xbkp
    return folder / "xlights_rgbeffects.xml"


class HelixGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Helix Sequence Weaver - Helixville Control Center")
        self.geometry("1140x850")
        self.minsize(1040, 740)

        self.layout_presets = {
            "GP's House": _best_layout_file(ROOT),
            "allmodels": _best_layout_file(ROOT / "allmodels"),
            "helixville": _best_layout_file(ROOT / "helixville"),
            "Custom": Path(""),
        }

        self.profile_var = tk.StringVar(value="master")
        self.layout_preset_var = tk.StringVar(value="GP's House")
        self.template_var = tk.StringVar(value=str(ROOT / "template.xsq"))
        self.audio_var = tk.StringVar(value="")
        self.layout_var = tk.StringVar(value=str(self.layout_presets["GP's House"]))
        self.output_var = tk.StringVar(value=str(ROOT / "outputs"))

        self.vendor_bar_var = tk.BooleanVar(value=True)
        self.matrix_var = tk.BooleanVar(value=True)
        self.polish_var = tk.BooleanVar(value=True)
        self.shortlist_var = tk.BooleanVar(value=True)
        self.learn_xsq_var = tk.BooleanVar(value=True)
        self.lor_compatible_var = tk.BooleanVar(value=False)
        self.sequence_mode_var = tk.StringVar(value="xLights")
        self.lor_source_var = tk.StringVar(value="")
        self.model_routing_var = tk.StringVar(value="")
        self.generate_mp4_var = tk.BooleanVar(value=True)
        self.preview_seconds_var = tk.IntVar(value=30)

        self.birdsong_var = tk.BooleanVar(value=True)
        self.birdsong_auto_var = tk.BooleanVar(value=True)
        self.birdsong_profile_var = tk.StringVar(value="canopy")
        self.birdsong_intensity_var = tk.DoubleVar(value=1.2)
        self.birdsong_min_conf_var = tk.DoubleVar(value=0.45)
        self.variants_var = tk.IntVar(value=4)

        self._events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.palette_mode_var = tk.StringVar(value="Default colors")
        self.showcase_gate_var = tk.BooleanVar(value=False)
        self.spatial_accent_var = tk.BooleanVar(value=False)
        self.ac_on_only_var = tk.BooleanVar(value=False)
        self._busy = False
        self._building_layout = False
        self._build_ui()
        self._apply_layout_preset()
        self._update_mode_ui()
        self.lor_compatible_var.trace_add("write", lambda *_a: self._update_mode_ui())
        self.ac_on_only_var.trace_add("write", lambda *_a: self._update_mode_ui())
        self.after(100, self._drain_events)

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, **pad)

        top = ttk.LabelFrame(frame, text="Show Context")
        top.pack(fill=tk.X, **pad)

        ttk.Label(top, text="Sequencer Mode").grid(row=0, column=0, sticky="w", **pad)
        ttk.Combobox(
            top, textvariable=self.sequence_mode_var,
            values=["xLights", "Light-O-Rama"],
            state="readonly", width=20,
        ).grid(row=0, column=1, sticky="w", **pad)
        self.sequence_mode_var.trace_add("write", lambda *_a: self._update_mode_ui())

        ttk.Label(top, text="Layout Preset").grid(row=1, column=0, sticky="w", **pad)
        preset_combo = ttk.Combobox(
            top,
            textvariable=self.layout_preset_var,
            values=list(self.layout_presets.keys()),
            state="readonly",
            width=20,
        )
        preset_combo.grid(row=1, column=1, sticky="w", **pad)
        self._layout_preset_combo = preset_combo
        preset_combo.bind("<<ComboboxSelected>>", lambda _event: self._apply_layout_preset())

        ttk.Button(top, text="Build/Refresh Helixville", command=self._build_helixville).grid(
            row=1, column=2, sticky="w", **pad
        )

        ttk.Label(top, text="Template XSQ").grid(row=2, column=0, sticky="w", **pad)
        self.template_entry = ttk.Entry(top, textvariable=self.template_var, width=86)
        self.template_entry.grid(row=2, column=1, columnspan=2, sticky="we", **pad)
        self.template_browse = ttk.Button(top, text="Browse", command=lambda: self._browse_file(self.template_var, [("XSQ", "*.xsq")]))
        self.template_browse.grid(row=2, column=3, sticky="w", **pad)

        ttk.Label(top, text="Audio File").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(top, textvariable=self.audio_var, width=86).grid(row=3, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(top, text="Browse", command=lambda: self._browse_file(self.audio_var, [("Audio", "*.wav *.mp3 *.flac *.ogg *.m4a")])).grid(
            row=3, column=3,
            sticky="w",
            **pad,
        )

        ttk.Label(top, text="Layout File").grid(row=4, column=0, sticky="w", **pad)
        self.layout_entry = ttk.Entry(top, textvariable=self.layout_var, width=86)
        self.layout_entry.grid(row=4, column=1, columnspan=2, sticky="we", **pad)
        self.layout_browse = ttk.Button(top, text="Browse", command=lambda: self._browse_file(self.layout_var, [("xLights Layout", "*.xml *.xbkp")]))
        self.layout_browse.grid(row=4, column=3, sticky="w", **pad)

        ttk.Label(top, text="Output Folder").grid(row=5, column=0, sticky="w", **pad)
        ttk.Entry(top, textvariable=self.output_var, width=86).grid(row=5, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(top, text="Browse", command=lambda: self._browse_folder(self.output_var)).grid(row=5, column=3, sticky="w", **pad)

        ttk.Label(top, text="LOR Channel Layout (.lms)").grid(row=6, column=0, sticky="w", **pad)
        self.lor_source_entry = ttk.Entry(top, textvariable=self.lor_source_var, width=86)
        self.lor_source_entry.grid(row=6, column=1, columnspan=2, sticky="we", **pad)
        self.lor_source_browse = ttk.Button(
            top, text="Browse", command=lambda: self._browse_file(
                self.lor_source_var, [("Legacy LOR sequence", "*.lms")]
            )
        )
        self.lor_source_browse.grid(row=6, column=3, sticky="w", **pad)
        ttk.Label(
            top,
            text="LOR mode reads channels and Unit/Circuit mapping from your existing LMS. "
                 "Modern .loredit is not yet supported; import/upgrade the exported LMS in LOR.",
            wraplength=840,
        ).grid(row=7, column=0, columnspan=4, sticky="w", **pad)

        controls = ttk.LabelFrame(frame, text="Engine Controls")
        controls.pack(fill=tk.X, **pad)

        ttk.Label(controls, text="Profile").grid(row=0, column=0, sticky="w", **pad)
        ttk.Combobox(controls, textvariable=self.profile_var, values=["master"], width=12, state="readonly").grid(
            row=0, column=1, sticky="w", **pad
        )
        ttk.Label(controls, text="Variants").grid(row=0, column=2, sticky="w", **pad)
        ttk.Spinbox(controls, from_=1, to=8, textvariable=self.variants_var, width=6).grid(row=0, column=3, sticky="w", **pad)

        ttk.Checkbutton(controls, text="Vendor Bar", variable=self.vendor_bar_var).grid(row=1, column=0, sticky="w", **pad)
        self.matrix_button=ttk.Checkbutton(controls,text="Matrix Intelligence",variable=self.matrix_var)
        self.matrix_button.grid(row=1,column=1,sticky="w",**pad)
        ttk.Checkbutton(controls, text="Polish", variable=self.polish_var).grid(row=1, column=2, sticky="w", **pad)
        ttk.Checkbutton(controls, text="Auto Shortlist", variable=self.shortlist_var).grid(row=1, column=3, sticky="w", **pad)
        ttk.Checkbutton(controls, text="Learn From My XSQs", variable=self.learn_xsq_var).grid(row=1, column=4, sticky="w", **pad)

        self.lor_compat_button = ttk.Checkbutton(
            controls,
            text="AC-compatible effects (xLights mode, for external LOR conversion)",
            variable=self.lor_compatible_var,
        )
        self.lor_compat_button.grid(row=2, column=0, columnspan=5, sticky="w", **pad)
        ttk.Checkbutton(
            controls, text="Generate MP4 preview with every sequence",
            variable=self.generate_mp4_var,
        ).grid(row=3, column=0, columnspan=3, sticky="w", **pad)
        ttk.Label(controls, text="Preview seconds").grid(row=3, column=3, sticky="w", **pad)
        ttk.Spinbox(
            controls, from_=1, to=600, increment=5,
            textvariable=self.preview_seconds_var, width=6,
        ).grid(row=3, column=4, sticky="w", **pad)

        birdsong = ttk.LabelFrame(frame, text="Birdsong Engine")
        birdsong.pack(fill=tk.X, **pad)
        self.birdsong_frame=birdsong
        ttk.Checkbutton(birdsong, text="Enable Birdsong", variable=self.birdsong_var).grid(row=0, column=0, sticky="w", **pad)
        ttk.Checkbutton(birdsong, text="Auto Enable By Confidence", variable=self.birdsong_auto_var).grid(
            row=0, column=1, sticky="w", **pad
        )
        ttk.Label(birdsong, text="Profile").grid(row=0, column=2, sticky="w", **pad)
        ttk.Combobox(
            birdsong,
            textvariable=self.birdsong_profile_var,
            values=["wild", "canopy", "ambient", "dawn"],
            width=10,
            state="readonly",
        ).grid(row=0, column=3, sticky="w", **pad)
        ttk.Label(birdsong, text="Intensity").grid(row=0, column=4, sticky="w", **pad)
        ttk.Spinbox(birdsong, from_=0.2, to=2.4, increment=0.1, textvariable=self.birdsong_intensity_var, width=8).grid(
            row=0, column=5, sticky="w", **pad
        )
        ttk.Label(birdsong, text="Min Confidence").grid(row=0, column=6, sticky="w", **pad)
        ttk.Spinbox(birdsong, from_=0.0, to=1.0, increment=0.05, textvariable=self.birdsong_min_conf_var, width=8).grid(
            row=0, column=7, sticky="w", **pad
        )

        render_tools = ttk.LabelFrame(frame, text="Color and playback")
        render_tools.pack(fill=tk.X, **pad)
        ttk.Label(render_tools, text="Colors").grid(row=0, column=0, **pad)
        self.palette_combo = ttk.Combobox(render_tools, textvariable=self.palette_mode_var,
            values=["Default colors", "Musical neon palettes"], state="readonly", width=23)
        self.palette_combo.grid(row=0, column=1, **pad)
        self.spatial_button = ttk.Checkbutton(render_tools, text="RGB chorus chase", variable=self.spatial_accent_var)
        self.spatial_button.grid(row=0, column=2, **pad)
        self.quality_button = ttk.Checkbutton(render_tools, text="Strict quality check", variable=self.showcase_gate_var)
        self.quality_button.grid(row=0, column=3, **pad)
        self.ac_on_button = ttk.Checkbutton(render_tools, text="RGW AC On only", variable=self.ac_on_only_var)
        self.ac_on_button.grid(row=0, column=4, **pad)
        self.native_buttons = []
        for column,(label,callback) in enumerate([("Render in xLights",self._native_render_fseq),
            ("Preview rendered FSEQ",self._fseq_preview),("Export existing AC XSQ to LMS",self._export_legacy_lms)]):
            button=ttk.Button(render_tools,text=label,command=callback)
            button.grid(row=1,column=column,columnspan=1,**pad);self.native_buttons.append(button)

        ttk.Label(top, text="Model routing (optional)").grid(row=8,column=0,sticky="w",**pad)
        self.routing_entry=ttk.Entry(top,textvariable=self.model_routing_var,width=86)
        self.routing_entry.grid(row=8,column=1,columnspan=2,sticky="we",**pad)
        self.routing_browse=ttk.Button(top,text="Browse",command=lambda:self._browse_file(self.model_routing_var,[("Model role mapping","*.json")]))
        self.routing_browse.grid(row=8,column=3,**pad)

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, **pad)
        self.run_button = ttk.Button(actions, text="Run Sequence Build", command=self._run_sequence)
        self.run_button.pack(side=tk.LEFT, padx=8, pady=6)
        ttk.Button(actions, text="Phone Remote", command=self._open_phone_remote).pack(side=tk.LEFT, padx=8, pady=6)
        self.status_label = ttk.Label(actions, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=8, pady=6)

        log_frame = ttk.LabelFrame(frame, text="Run Log")
        log_frame.pack(fill=tk.BOTH, expand=True, **pad)
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10, bg="#0e1013", fg="#d6deeb", insertbackground="#d6deeb")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _open_phone_remote(self) -> None:
        from tools.desktop_remote_gui import open_phone_link
        open_phone_link(self, ROOT)

    def _update_mode_ui(self) -> None:
        lor = self.sequence_mode_var.get() == "Light-O-Rama"
        for item in (
            self.template_entry, self.template_browse, self.layout_entry,
            self.layout_browse, self._layout_preset_combo, self.lor_compat_button,
            self.routing_entry, self.routing_browse
        ):
            item.configure(state="disabled" if lor else (
                "readonly" if item is self._layout_preset_combo else "normal"
            ))
        rgb_disabled = lor or self.lor_compatible_var.get() or self.ac_on_only_var.get()
        self.palette_combo.configure(state="disabled" if rgb_disabled else "readonly")
        self.matrix_button.configure(state="disabled" if rgb_disabled else "normal")
        for item in self.birdsong_frame.winfo_children():
            item.configure(state="disabled" if rgb_disabled else "readonly" if isinstance(item,ttk.Combobox) else "normal")
        for item in (self.spatial_button,self.quality_button):
            item.configure(state="disabled" if rgb_disabled else "normal")
        self.ac_on_button.configure(state="disabled" if lor or self.lor_compatible_var.get() else "normal")
        for item in self.native_buttons:
            item.configure(state="disabled" if lor else "normal")
        for item in (self.lor_source_entry, self.lor_source_browse):
            item.configure(state="normal" if lor else "disabled")

    def _drain_events(self) -> None:
        """Process worker results on Tk's main thread (never call Tk from a worker)."""
        try:
            for _ in range(100):
                kind, payload = self._events.get_nowait()
                if kind == "log":
                    self._log(str(payload))
                elif kind == "run_done":
                    if payload == 0:
                        self._log("Run complete.")
                        self.status_label.configure(text="Completed")
                    else:
                        self._log(f"Run failed with exit code {payload}.")
                        self.status_label.configure(text="Failed")
                    self._busy = False
                    self.run_button.configure(state=tk.NORMAL)
                    if self._building_layout:
                        if payload == 0:
                            self.layout_preset_var.set("helixville")
                            self._apply_layout_preset()
                        self._building_layout = False
                elif kind == "run_error":
                    self._log(f"Unable to launch Helix: {payload}")
                    self.status_label.configure(text="Failed")
                    self._busy = False
                    self._building_layout = False
                    self.run_button.configure(state=tk.NORMAL)
        except queue.Empty:
            pass
        self.after(100, self._drain_events)

    def _launch_optional_export(self, cmd: list[str]) -> None:
        if self._busy:
            return
        self._busy = True
        self.run_button.configure(state=tk.DISABLED)
        self.status_label.configure(text="Exporting...")
        self._log("Running: " + " ".join(cmd))
        threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True).start()

    def _export_legacy_lms(self) -> None:
        source = filedialog.askopenfilename(
            title="Choose Helix AC-only On XSQ", filetypes=[("xLights XSQ", "*.xsq")]
        )
        if not source:
            return
        proposed = Path(source).with_suffix(".ac_channel_map.csv")
        channel_map = str(proposed) if proposed.exists() else filedialog.askopenfilename(
            title="Choose CSV with verified LOR Unit ID and Circuit mapping",
            filetypes=[("Channel mapping CSV", "*.csv")]
        )
        if not channel_map:
            return
        destination = filedialog.asksaveasfilename(
            title="Save legacy Light-O-Rama LMS",
            defaultextension=".lms", filetypes=[("Legacy LOR sequence", "*.lms")],
            initialfile=Path(source).stem + ".lms"
        )
        if not destination:
            return
        if not messagebox.askokcancel(
            "Verify AC controller wiring",
            "This writes legacy .lms, NOT S5/S6 .loredit. "
            "All LOR Unit/Circuit assignments must be filled in the CSV and "
            "verified against actual controllers before playback. Continue?"
        ):
            return
        self._launch_optional_export([
            *_module_command("tools.legacy_lms_export"), source,
            "--channel-map", channel_map, "--output", destination
        ])

    def _native_render_fseq(self) -> None:
        source = filedialog.askopenfilename(
            title="Choose XSQ to render in installed xLights",
            filetypes=[("xLights XSQ", "*.xsq")]
        )
        if not source:
            return
        executable = filedialog.askopenfilename(
            title="Choose installed xLights executable",
            filetypes=[("xLights program", "*.exe"), ("All files", "*")]
        )
        if not executable:
            return
        show_dir = filedialog.askdirectory(title="Choose xLights show directory")
        if not show_dir:
            return
        out_dir = filedialog.askdirectory(title="Choose directory to keep rendered FSEQ")
        if not out_dir:
            return
        self._launch_optional_export([
            *_module_command("tools.validate_native_xlights"),
            source, "--show-dir", show_dir,
            "--xlights-exe", executable, "--output-dir", out_dir
        ])

    def _fseq_preview(self) -> None:
        fseq = filedialog.askopenfilename(
            title="Choose real FSEQ rendered by xLights",
            filetypes=[("Falcon/xLights sequence", "*.fseq")]
        )
        if not fseq:
            return
        default_layout = Path(self.layout_var.get().strip())
        if not default_layout.exists():
            messagebox.showerror("Missing layout", "Choose your original xLights layout first")
            return
        destination = filedialog.asksaveasfilename(
            title="Save real pixel preview MP4", defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4")], initialfile=Path(fseq).stem + ".mp4"
        )
        if not destination:
            return
        cmd = [
            *_module_command("tools.fseq_pixel_preview"),
            fseq, "--layout", str(default_layout),
            "--output", destination
        ]
        audio = Path(self.audio_var.get().strip()) if self.audio_var.get().strip() else None
        if audio and audio.exists():
            cmd.extend(["--audio", str(audio)])
        self._log("Preview shows actual FSEQ channel colors with approximate model geometry.")
        self._launch_optional_export(cmd)

    def _browse_file(self, target_var: tk.StringVar, filetypes: list[tuple[str, str]]) -> None:
        selected = filedialog.askopenfilename(initialdir=str(ROOT), filetypes=filetypes)
        if selected:
            target_var.set(selected)

    def _browse_folder(self, target_var: tk.StringVar) -> None:
        selected = filedialog.askdirectory(initialdir=str(ROOT))
        if selected:
            target_var.set(selected)

    def _log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _apply_layout_preset(self) -> None:
        preset = self.layout_preset_var.get()
        if preset == "Custom":
            return
        selected = self.layout_presets.get(preset, Path(""))
        if selected:
            self.layout_var.set(str(selected))
            if preset == "helixville":
                self.output_var.set(str(ROOT / "helixville" / "outputs"))
            elif preset == "allmodels":
                self.output_var.set(str(ROOT / "allmodels" / "outputs"))
            else:
                self.output_var.set(str(ROOT / "outputs"))

    def _build_helixville(self) -> None:
        source = ROOT / "allmodels" / "xlights_rgbeffects.xml"
        if not source.exists():
            source = ROOT / "xlights_rgbeffects.xml"
        if not source.exists():
            messagebox.showerror("Missing Layout", "No bundled source layout was found.")
            return
        cmd = [
            *_python_command("--helix-build-helixville", ROOT / "tools" / "build_helixville_layout.py"),
            "--source-layout", str(source),
            "--gps-layout", str(ROOT / "xlights_rgbeffects.xml"),
            "--output-dir", str(ROOT / "helixville"),
        ]
        self._log("Building/refreshing helixville layout...")
        if self._busy:
            return
        self._building_layout = True
        self._launch_optional_export(cmd)

    def _run_sequence(self) -> None:
        if self._busy:
            return
        lor_mode = self.sequence_mode_var.get() == "Light-O-Rama"
        rgb_enabled = not (lor_mode or self.lor_compatible_var.get() or self.ac_on_only_var.get())
        try:
            variants = int(self.variants_var.get())
            intensity = float(self.birdsong_intensity_var.get()) if rgb_enabled and self.birdsong_var.get() else 1.2
            confidence = float(self.birdsong_min_conf_var.get()) if rgb_enabled and self.birdsong_var.get() else .45
            if not 1 <= variants <= 8 or not 0 <= intensity <= 5 or not 0 <= confidence <= 1:
                raise ValueError("out of range")
        except (tk.TclError, ValueError):
            messagebox.showwarning("Invalid Settings", "Use 1–8 variants, intensity 0–5, and confidence 0–1.")
            return
        if not Path(self.audio_var.get().strip()).is_file():
            messagebox.showwarning("Missing Audio", "Choose an audio file before running.")
            return
        lor_mode = self.sequence_mode_var.get() == "Light-O-Rama"
        if lor_mode:
            if not Path(self.lor_source_var.get().strip()).is_file():
                messagebox.showwarning(
                    "Missing LOR Layout",
                    "Choose an existing legacy .lms sequence with your real LOR channels."
                )
                return
        else:
            if not Path(self.layout_var.get().strip()).exists():
                messagebox.showwarning("Missing Layout", "Layout file does not exist.")
                return
            if not Path(self.template_var.get().strip()).exists():
                messagebox.showwarning("Missing Template", "Template XSQ file does not exist.")
                return

        cmd = [
            *_python_command("--helix-cli", ROOT / "main.py"),
            "--profile",
            self.profile_var.get().strip() or "master",
            "--",
            "--template",
            self.template_var.get().strip(),
            "--audio",
            self.audio_var.get().strip(),
            "--layout-file",
            self.layout_var.get().strip(),
            "--output-dir",
            self.output_var.get().strip(),
            "--variants",
            str(variants),
            "--no-prompt",
        ]

        if not lor_mode and self.model_routing_var.get().strip():
            routing=Path(self.model_routing_var.get().strip())
            if not routing.is_file():
                messagebox.showwarning("Missing Model Routing", "Choose an existing model role mapping file.")
                return
            cmd.extend(["--model-overrides-file",str(routing)])
        if lor_mode:
            cmd.extend([
                "--helix-lor-source-lms", self.lor_source_var.get().strip(),
                "--ac-lights-only", "--no-pixel-reactive",
                "--no-matrix-intelligence", "--no-effects-orchestrator",
            ])
            self._log(
                "Light-O-Rama mode: using Unit/Circuit mapping from the supplied LMS; "
                "writing a new LMS and simulated channel-layout MP4."
            )
        elif self.lor_compatible_var.get():
            cmd.extend([
                "--ac-lights-only", "--no-pixel-reactive",
                "--no-matrix-intelligence", "--no-effects-orchestrator",
            ])
            self._log(
                "xLights AC compatible: output XSQ; optionally convert to LOR in xLights."
            )
        if not lor_mode and not self.lor_compatible_var.get():
            if not self.ac_on_only_var.get() and self.palette_mode_var.get() == "Musical neon palettes":
                cmd.extend(["--palette-mode", "neon"])
            if not self.ac_on_only_var.get() and self.spatial_accent_var.get():
                cmd.append("--helix-spatial-accent")
            if not self.ac_on_only_var.get() and self.showcase_gate_var.get():
                cmd.append("--helix-showcase-quality-gate")
            if self.ac_on_only_var.get():
                cmd.append("--helix-ac-on-only")

        if self.generate_mp4_var.get():
            try:
                seconds = int(self.preview_seconds_var.get())
            except (tk.TclError, ValueError):
                messagebox.showwarning("Invalid Preview Duration", "Enter 1–600 seconds")
                return
            if not 1 <= seconds <= 600:
                messagebox.showwarning("Invalid Preview Duration", "Enter 1–600 seconds")
                return
            cmd.extend(["--helix-preview-mp4", "--helix-preview-seconds", str(seconds)])
        if self.vendor_bar_var.get():
            cmd.append("--vendor-bar")
        if self.matrix_var.get() and rgb_enabled:
            cmd.append("--matrix-intelligence")
        if self.polish_var.get():
            cmd.append("--polish")
        else:
            cmd.append("--no-polish")
        if self.shortlist_var.get():
            cmd.append("--auto-shortlist")
        if self.learn_xsq_var.get():
            cmd.append("--learn-from-my-xsqs")

        if self.birdsong_var.get() and rgb_enabled:
            cmd.extend(
                [
                    "--birdsong",
                    "--birdsong-profile",
                    self.birdsong_profile_var.get().strip() or "wild",
                    "--birdsong-intensity",
                    f"{intensity:.2f}",
                    "--birdsong-min-confidence",
                    f"{confidence:.2f}",
                ]
            )
            if self.birdsong_auto_var.get():
                cmd.append("--birdsong-auto")

        self.run_button.configure(state=tk.DISABLED)
        self._busy = True
        self.status_label.configure(text="Running...")
        self._log("")
        self._log("Running command:")
        self._log(" ".join(cmd))

        thread = threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True)
        thread.start()

    def _run_subprocess(self, cmd: list[str]) -> None:
        try:
            with subprocess.Popen(
                cmd,
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                bufsize=1,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if getattr(sys, "frozen", False) else 0,
            ) as process:
                assert process.stdout is not None
                for line in process.stdout:
                    self._events.put(("log", line.rstrip()))
                rc = process.wait()
            self._events.put(("run_done", rc))
        except OSError as exc:
            self._events.put(("run_error", str(exc)))


def main() -> int:
    app = HelixGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
