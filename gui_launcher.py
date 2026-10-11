from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


ROOT = Path(__file__).resolve().parent


def _best_layout_file(folder: Path) -> Path:
    xbkp = folder / "xlights_rgbeffects.xbkp"
    if xbkp.exists():
        return xbkp
    return folder / "xlights_rgbeffects.xml"


class HelixGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Helix Sequence Weaver - Helixville Control Center")
        self.geometry("1060x760")
        self.minsize(960, 680)

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

        self.birdsong_var = tk.BooleanVar(value=True)
        self.birdsong_auto_var = tk.BooleanVar(value=True)
        self.birdsong_profile_var = tk.StringVar(value="canopy")
        self.birdsong_intensity_var = tk.DoubleVar(value=1.2)
        self.birdsong_min_conf_var = tk.DoubleVar(value=0.45)
        self.variants_var = tk.IntVar(value=4)
        self.output_mode_var = tk.StringVar(value="Original xLights colors")
        self.showcase_gate_var = tk.BooleanVar(value=False)
        self.spatial_accent_var = tk.BooleanVar(value=False)

        self._build_ui()
        self._apply_layout_preset()

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 6}
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, **pad)

        top = ttk.LabelFrame(frame, text="Show Context")
        top.pack(fill=tk.X, **pad)

        ttk.Label(top, text="Layout Preset").grid(row=0, column=0, sticky="w", **pad)
        preset_combo = ttk.Combobox(
            top,
            textvariable=self.layout_preset_var,
            values=list(self.layout_presets.keys()),
            state="readonly",
            width=20,
        )
        preset_combo.grid(row=0, column=1, sticky="w", **pad)
        preset_combo.bind("<<ComboboxSelected>>", lambda _event: self._apply_layout_preset())

        ttk.Button(top, text="Build/Refresh Helixville", command=self._build_helixville).grid(
            row=0, column=2, sticky="w", **pad
        )

        ttk.Label(top, text="Template XSQ").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(top, textvariable=self.template_var, width=86).grid(row=1, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(top, text="Browse", command=lambda: self._browse_file(self.template_var, [("XSQ", "*.xsq")])).grid(
            row=1, column=3, sticky="w", **pad
        )

        ttk.Label(top, text="Audio File").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(top, textvariable=self.audio_var, width=86).grid(row=2, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(top, text="Browse", command=lambda: self._browse_file(self.audio_var, [("Audio", "*.wav *.mp3 *.flac *.ogg *.m4a")])).grid(
            row=2, column=3,
            sticky="w",
            **pad,
        )

        ttk.Label(top, text="Layout File").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(top, textvariable=self.layout_var, width=86).grid(row=3, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(top, text="Browse", command=lambda: self._browse_file(self.layout_var, [("xLights Layout", "*.xml *.xbkp")])).grid(
            row=3, column=3, sticky="w", **pad
        )

        ttk.Label(top, text="Output Folder").grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(top, textvariable=self.output_var, width=86).grid(row=4, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(top, text="Browse", command=lambda: self._browse_folder(self.output_var)).grid(row=4, column=3, sticky="w", **pad)

        controls = ttk.LabelFrame(frame, text="Engine Controls")
        controls.pack(fill=tk.X, **pad)

        ttk.Label(controls, text="Profile").grid(row=0, column=0, sticky="w", **pad)
        ttk.Combobox(controls, textvariable=self.profile_var, values=["master"], width=12, state="readonly").grid(
            row=0, column=1, sticky="w", **pad
        )
        ttk.Label(controls, text="Variants").grid(row=0, column=2, sticky="w", **pad)
        ttk.Spinbox(controls, from_=1, to=8, textvariable=self.variants_var, width=6).grid(row=0, column=3, sticky="w", **pad)

        ttk.Checkbutton(controls, text="Vendor Bar", variable=self.vendor_bar_var).grid(row=1, column=0, sticky="w", **pad)
        ttk.Checkbutton(controls, text="Matrix Intelligence", variable=self.matrix_var).grid(row=1, column=1, sticky="w", **pad)
        ttk.Checkbutton(controls, text="Polish", variable=self.polish_var).grid(row=1, column=2, sticky="w", **pad)
        ttk.Checkbutton(controls, text="Auto Shortlist", variable=self.shortlist_var).grid(row=1, column=3, sticky="w", **pad)
        ttk.Checkbutton(controls, text="Learn From My XSQs", variable=self.learn_xsq_var).grid(row=1, column=4, sticky="w", **pad)

        output_options = ttk.LabelFrame(frame, text="Sequence Output / Controller Compatibility")
        output_options.pack(fill=tk.X, **pad)
        ttk.Label(output_options, text="Output Mode").grid(row=0, column=0, sticky="w", **pad)
        ttk.Combobox(
            output_options,
            textvariable=self.output_mode_var,
            values=[
                "Original xLights colors",
                "Neon musical color",
                "RGW AC - On effects only (Light-O-Rama)",
            ],
            width=44,
            state="readonly",
        ).grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(
            output_options,
            text="AC mode requires Single Color Red/Green/White models; never converts RGB pixels into AC circuits.",
            wraplength=690,
        ).grid(row=1, column=0, columnspan=4, sticky="w", **pad)

        ttk.Checkbutton(
            output_options, text="Strict showcase quality gate (abort weak RGB output)",
            variable=self.showcase_gate_var
        ).grid(row=2, column=0, columnspan=3, sticky="w", **pad)

        ttk.Checkbutton(
            output_options,
            text="Optional RGB chorus chase (left-to-right across RGB props)",
            variable=self.spatial_accent_var
        ).grid(row=3, column=0, columnspan=3, sticky="w", **pad)

        birdsong = ttk.LabelFrame(frame, text="Birdsong Engine")
        birdsong.pack(fill=tk.X, **pad)
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

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, **pad)
        self.run_button = ttk.Button(actions, text="Run Sequence Build", command=self._run_sequence)
        self.run_button.pack(side=tk.LEFT, padx=8, pady=6)
        ttk.Button(actions, text="Export legacy LOR LMS...", command=self._export_legacy_lms).pack(
            side=tk.LEFT, padx=8, pady=6
        )
        ttk.Button(actions, text="xLights render to FSEQ...", command=self._native_render_fseq).pack(
            side=tk.LEFT, padx=8, pady=6
        )
        ttk.Button(actions, text="FSEQ to pixel MP4...", command=self._fseq_preview).pack(
            side=tk.LEFT, padx=8, pady=6
        )
        self.status_label = ttk.Label(actions, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=8, pady=6)

        log_frame = ttk.LabelFrame(frame, text="Run Log")
        log_frame.pack(fill=tk.BOTH, expand=True, **pad)
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20, bg="#0e1013", fg="#d6deeb", insertbackground="#d6deeb")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

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
        self.update_idletasks()

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
        cmd = [sys.executable, str(ROOT / "tools" / "build_helixville_layout.py")]
        self._log("Building/refreshing helixville layout...")
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if result.stdout:
            self._log(result.stdout.strip())
        if result.returncode != 0:
            if result.stderr:
                self._log(result.stderr.strip())
            messagebox.showerror("Helixville Build Failed", "Could not build Helixville layout. Check log output.")
            return
        self.layout_preset_var.set("helixville")
        self._apply_layout_preset()
        messagebox.showinfo("Helixville Ready", "Helixville layout has been generated and selected.")

    def _launch_optional_export(self, cmd: list[str]) -> None:
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
            sys.executable, "-m", "tools.legacy_lms_export", source,
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
            sys.executable, "-m", "tools.validate_native_xlights",
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
            sys.executable, "-m", "tools.fseq_pixel_preview",
            fseq, "--layout", str(default_layout),
            "--output", destination
        ]
        audio = Path(self.audio_var.get().strip()) if self.audio_var.get().strip() else None
        if audio and audio.exists():
            cmd.extend(["--audio", str(audio)])
        self._log("Preview shows actual FSEQ channel colors with approximate model geometry.")
        self._launch_optional_export(cmd)

    def _run_sequence(self) -> None:
        if not self.audio_var.get().strip():
            messagebox.showwarning("Missing Audio", "Choose an audio file before running.")
            return
        if not Path(self.layout_var.get().strip()).exists():
            messagebox.showwarning("Missing Layout", "Layout file does not exist.")
            return
        if not Path(self.template_var.get().strip()).exists():
            messagebox.showwarning("Missing Template", "Template XSQ file does not exist.")
            return

        cmd = [
            sys.executable,
            str(ROOT / "main.py"),
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
            str(max(1, int(self.variants_var.get()))),
            "--no-prompt",
        ]

        output_mode = self.output_mode_var.get()
        if output_mode == "Neon musical color":
            cmd.extend(["--palette-mode", "neon"])
        elif output_mode == "RGW AC - On effects only (Light-O-Rama)":
            # Preflight hardware truth before running expensive audio analysis.
            try:
                from tools.ac_on_export import inventory_layout
                models, _, _ = inventory_layout(Path(self.layout_var.get().strip()))
            except (OSError, ValueError) as exc:
                messagebox.showerror("AC-only layout invalid", str(exc))
                return
            cmd.append("--helix-ac-on-only")
            self._log(
                f"AC output: {len(models)} explicit RGW single-color circuits; "
                "On-only XSQ plus per-sequence channel map. "
                "Confirm Light-O-Rama Unit ID / circuit mapping in xLights."
            )

        if self.showcase_gate_var.get() and output_mode != "RGW AC - On effects only (Light-O-Rama)":
            cmd.append("--helix-showcase-quality-gate")

        if self.spatial_accent_var.get() and output_mode == "Neon musical color":
            cmd.append("--helix-spatial-accent")

        if self.vendor_bar_var.get():
            cmd.append("--vendor-bar")
        if self.matrix_var.get():
            cmd.append("--matrix-intelligence")
        if self.polish_var.get():
            cmd.append("--polish")
        else:
            cmd.append("--no-polish")
        if self.shortlist_var.get():
            cmd.append("--auto-shortlist")
        if self.learn_xsq_var.get():
            cmd.append("--learn-from-my-xsqs")

        if self.birdsong_var.get():
            cmd.extend(
                [
                    "--birdsong",
                    "--birdsong-profile",
                    self.birdsong_profile_var.get().strip() or "wild",
                    "--birdsong-intensity",
                    f"{float(self.birdsong_intensity_var.get()):.2f}",
                    "--birdsong-min-confidence",
                    f"{float(self.birdsong_min_conf_var.get()):.2f}",
                ]
            )
            if self.birdsong_auto_var.get():
                cmd.append("--birdsong-auto")

        self.run_button.configure(state=tk.DISABLED)
        self.status_label.configure(text="Running...")
        self._log("")
        self._log("Running command:")
        self._log(" ".join(cmd))

        thread = threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True)
        thread.start()

    def _run_subprocess(self, cmd: list[str]) -> None:
        process = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert process.stdout is not None
        for line in process.stdout:
            self.after(0, self._log, line.rstrip())
        process.wait()
        rc = process.returncode
        def finish() -> None:
            if rc == 0:
                self._log("Process complete.")
                self.status_label.configure(text="Completed")
            else:
                self._log(f"Process failed with exit code {rc}.")
                self.status_label.configure(text="Failed")
            self.run_button.configure(state=tk.NORMAL)
        self.after(0, finish)


def main() -> int:
    app = HelixGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
