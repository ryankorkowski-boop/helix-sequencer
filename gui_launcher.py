from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


from core.helix_version import TITLE, VERSION
from gui_lightshow import SequencingLightShow

ROOT = Path(__file__).resolve().parent


def _best_layout_file(folder: Path) -> Path:
    xbkp = folder / "xlights_rgbeffects.xbkp"
    if xbkp.exists():
        return xbkp
    return folder / "xlights_rgbeffects.xml"


class HelixGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(TITLE)
        self.geometry("1060x760")
        self.minsize(960, 680)
        self.configure(bg="#091020")
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#101b30")
        style.configure("TLabelframe", background="#101b30", foreground="#5de5ef")
        style.configure("TLabelframe.Label", background="#101b30", foreground="#5de5ef")
        style.configure("TLabel", background="#101b30", foreground="#e7f1ff")

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

        self._ui_events = queue.Queue()
        self._build_ui()
        self._apply_layout_preset()
        self.after(80, self._drain_ui_events)

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 6}
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, **pad)

        top = ttk.LabelFrame(frame, text="Show Context")
        top.pack(fill=tk.X, **pad)

        ttk.Label(top, text=TITLE).grid(row=0, column=0, columnspan=2, sticky="w", **pad)
        ttk.Button(top, text="About", command=self._show_about).grid(row=0, column=2, sticky="w", **pad)
        ttk.Button(top, text="Instructions", command=self._show_instructions).grid(row=0, column=3, sticky="w", **pad)

        ttk.Label(top, text="Layout Preset").grid(row=1, column=0, sticky="w", **pad)
        preset_combo = ttk.Combobox(
            top,
            textvariable=self.layout_preset_var,
            values=list(self.layout_presets.keys()),
            state="readonly",
            width=20,
        )
        preset_combo.grid(row=1, column=1, sticky="w", **pad)
        preset_combo.bind("<<ComboboxSelected>>", lambda _event: self._apply_layout_preset())

        ttk.Button(top, text="Build/Refresh Helixville", command=self._build_helixville).grid(
            row=1, column=2, sticky="w", **pad
        )

        ttk.Label(top, text="Template XSQ").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(top, textvariable=self.template_var, width=86).grid(row=2, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(top, text="Browse", command=lambda: self._browse_file(self.template_var, [("XSQ", "*.xsq")])).grid(
            row=2, column=3, sticky="w", **pad
        )

        ttk.Label(top, text="Audio File").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(top, textvariable=self.audio_var, width=86).grid(row=3, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(top, text="Browse", command=lambda: self._browse_file(self.audio_var, [("Audio", "*.wav *.mp3 *.flac *.ogg *.m4a")])).grid(
            row=3, column=3,
            sticky="w",
            **pad,
        )

        ttk.Label(top, text="Layout File").grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(top, textvariable=self.layout_var, width=86).grid(row=4, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(top, text="Browse", command=lambda: self._browse_file(self.layout_var, [("xLights Layout", "*.xml *.xbkp")])).grid(
            row=4, column=3, sticky="w", **pad
        )

        ttk.Label(top, text="Output Folder").grid(row=5, column=0, sticky="w", **pad)
        ttk.Entry(top, textvariable=self.output_var, width=86).grid(row=5, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(top, text="Browse", command=lambda: self._browse_folder(self.output_var)).grid(row=5, column=3, sticky="w", **pad)

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

        legal = ttk.LabelFrame(frame, text="Legal / Licensing")
        legal.pack(fill=tk.X, **pad)
        ttk.Label(legal, text="Helix Sequencer: PolyForm Noncommercial 1.0.0 | Free for qualifying noncommercial use; commercial use requires a separate license.", wraplength=900).pack(anchor="w", padx=8, pady=4)
        ttk.Button(legal, text="Donate to Helix", command=lambda: self._open_donation("helix")).pack(side=tk.LEFT, padx=8, pady=4)
        ttk.Button(legal, text="Donate to xLights", command=lambda: self._open_donation("xlights")).pack(side=tk.LEFT, padx=8, pady=4)
        ttk.Button(legal, text="View License", command=lambda: webbrowser.open("https://polyformproject.org/licenses/noncommercial/1.0.0/")).pack(side=tk.LEFT, padx=8, pady=4)
        ttk.Button(legal, text="Third-Party Licenses", command=lambda: webbrowser.open((ROOT / "THIRD_PARTY_LICENSES.md").as_uri())).pack(side=tk.LEFT, padx=8, pady=4)

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, **pad)
        self.run_button = ttk.Button(actions, text="Run Sequence Build", command=self._run_sequence)
        self.run_button.pack(side=tk.LEFT, padx=8, pady=6)
        self.status_label = ttk.Label(actions, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=8, pady=6)
        ttk.Label(actions, text="Animation").pack(side=tk.LEFT, padx=(16, 4))
        self.animation_scene = tk.StringVar(value="Combined")
        ttk.Combobox(actions, textvariable=self.animation_scene, values=["Combined", "Arches", "Mega tree"], state="readonly", width=12).pack(side=tk.LEFT)
        self.light_show = SequencingLightShow(frame)
        self.light_show.pack(fill=tk.X, padx=8, pady=(0, 6))
        self.animation_scene.trace_add("write", lambda *_: self.light_show.set_scene(self.animation_scene.get()))

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

    def _drain_ui_events(self) -> None:
        try:
            while True:
                kind, payload = self._ui_events.get_nowait()
                if kind == "log":
                    self._log(payload)
                elif kind == "done":
                    self.status_label.configure(text=payload)
                    self.light_show.set_running(False)
                    self.run_button.configure(state=tk.NORMAL)
        except queue.Empty:
            pass
        self.after(80, self._drain_ui_events)

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

    def _open_donation(self, key: str) -> None:
        try:
            links = json.loads((ROOT / "config" / "support_links.json").read_text(encoding="utf-8"))
            webbrowser.open(links[key])
        except (OSError, KeyError, ValueError) as error:
            messagebox.showerror("Donation link unavailable", str(error))

    def _show_instructions(self) -> None:
        instructions = ROOT / "android" / "app" / "src" / "main" / "assets" / "helix_instructions.txt"
        if not instructions.exists():
            messagebox.showinfo("Instructions", "See the included README.md for setup and usage instructions.")
            return
        window = tk.Toplevel(self)
        window.title("Helix Instructions")
        window.geometry("720x560")
        viewer = tk.Text(window, wrap=tk.WORD, bg="#101b30", fg="#e7f1ff")
        viewer.pack(fill=tk.BOTH, expand=True)
        viewer.insert("1.0", instructions.read_text(encoding="utf-8"))
        viewer.configure(state=tk.DISABLED)

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About Helix",
            (
                f"{TITLE}\n\n"
                f"Version {VERSION}.\n\n"
                "Section colors are written into the sequence palette table. "
                "White is reserved for strobe, twinkle, shimmer, snowflake, and sparkle."
            ),
        )

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
        self.light_show.set_running(True)
        self._log("")
        self._log("Running command:")
        self._log(" ".join(cmd))

        thread = threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True)
        thread.start()

    def _run_subprocess(self, cmd: list[str]) -> None:
        try:
            process = subprocess.Popen(
                cmd, cwd=str(ROOT), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True,
            )
            assert process.stdout is not None
            for line in process.stdout:
                self._ui_events.put(("log", line.rstrip()))
            rc = process.wait()
            self._ui_events.put(("log", "Run complete." if rc == 0 else f"Run failed with exit code {rc}."))
            self._ui_events.put(("done", "Completed" if rc == 0 else "Failed"))
        except Exception as exc:
            self._ui_events.put(("log", f"Sequence process failed: {exc}"))
            self._ui_events.put(("done", "Failed"))


def main() -> int:
    app = HelixGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
