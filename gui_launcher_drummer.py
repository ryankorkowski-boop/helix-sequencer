from __future__ import annotations

import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from core.engine_profiles import ACTIVE_STYLE_VERSION
from core.operator_command import newest_canonical_xsq
from gui_launcher import HelixGui, ROOT


class HelixDrummerGui(HelixGui):
    """Helix GUI plus an optional Drummer V3 post-pass and a ground-truth preview."""

    def __init__(self) -> None:
        self.drummer_var = tk.BooleanVar(value=False)
        self.drummer_ground_truth_var = tk.BooleanVar(value=False)
        super().__init__()
        self.title("Helix Sequence Weaver - Helixville Control Center + Drummer V3")
        self._add_drummer_controls()

    def _add_drummer_controls(self) -> None:
        panel = ttk.LabelFrame(self, text="Drummer V3")
        panel.pack(fill=tk.X, padx=16, pady=(0, 8))

        ttk.Checkbutton(
            panel,
            text="After a successful build, inject Drummer V3 hits into the new XSQ",
            variable=self.drummer_var,
        ).pack(side=tk.LEFT, padx=8, pady=6)
        ttk.Checkbutton(panel, text="Ground-Truth Preview", variable=self.drummer_ground_truth_var).pack(side=tk.LEFT, padx=8, pady=6)
        ttk.Button(panel, text="Run Drummer V3 Test", command=self._run_drummer_ground_truth).pack(side=tk.RIGHT, padx=8, pady=6)

        note = ttk.Label(panel, text="Off by default. Injection edits the canonical XSQ in place on layer AUTO_Drummer_V3.")
        note.pack(side=tk.RIGHT, padx=8, pady=6)

    def _run_sequence(self) -> None:
        if self.drummer_ground_truth_var.get():
            self._run_drummer_ground_truth()
            return
        super()._run_sequence()

    def _run_subprocess(self, cmd: list[str]) -> None:
        super()._run_subprocess(cmd)
        if not self.drummer_var.get():
            return
        if str(self.status_label.cget("text")) != "Completed":
            return
        try:
            summary = inject_newest_sequence(cmd)
        except Exception as exc:
            self._log(f"Drummer V3 injection failed: {exc}")
            self.status_label.configure(text="Completed; drummer injection failed")
            messagebox.showerror("Drummer V3 injection failed", str(exc))
            return
        self._log(
            "Drummer V3 injection: "
            f"xsq={summary['output_xsq']} placements={summary['placement_count']}"
        )
        self.status_label.configure(text="Completed with Drummer V3")

    def _run_drummer_ground_truth(self) -> None:
        import subprocess
        import sys

        out = ROOT / "test_runs" / "gui_drummer_ground_truth"
        wav = out / "drummer_ground_truth.wav"
        events = out / "events.json"
        xsq = out / "HelixDrummerGroundTruth_8ch.xsq"

        commands = [
            [sys.executable, str(ROOT / "tools" / "generate_drummer_ground_truth.py"), "--wav", str(wav), "--events", str(events)],
            [sys.executable, str(ROOT / "tools" / "export_drummer_ground_truth_xsq.py"), "--output", str(xsq), "--duration", "20"],
            [sys.executable, "-m", "tools.render_xsq_skeleton_preview", str(xsq), "--width", "1280", "--height", "720", "--fps", "24", "--audio", str(wav)],
        ]

        self.status_label.configure(text="Drummer test running...")
        self._log("")
        self._log("Running Drummer V3 ground-truth validation...")
        self._log(f"Output: {out}")

        def worker() -> None:
            try:
                out.mkdir(parents=True, exist_ok=True)
                for command in commands:
                    self._log("$ " + " ".join(command))
                    process = subprocess.Popen(command, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    assert process.stdout is not None
                    for line in process.stdout:
                        self._log(line.rstrip())
                    rc = process.wait()
                    if rc != 0:
                        self.status_label.configure(text="Drummer test failed")
                        self._log(f"Drummer command failed with exit code {rc}.")
                        return
                mp4 = xsq.with_suffix(".mp4")
                self.status_label.configure(text="Drummer test complete")
                self._log(f"Drummer XSQ: {xsq}")
                self._log(f"Drummer MP4: {mp4}")
                messagebox.showinfo("Drummer V3 Complete", f"Ground-truth XSQ and MP4 preview created in:\n{out}")
            except Exception as exc:
                self.status_label.configure(text="Drummer test failed")
                self._log(f"Drummer test exception: {exc}")
                messagebox.showerror("Drummer V3 Failed", str(exc))

        threading.Thread(target=worker, daemon=True).start()


def _flag_value(cmd: list[str], flag: str) -> str:
    if flag not in cmd:
        return ""
    index = cmd.index(flag)
    if index + 1 >= len(cmd):
        return ""
    return cmd[index + 1]


def inject_newest_sequence(cmd: list[str]) -> dict[str, object]:
    from tools.integrate_drummer_v3_into_xsq import inject_drummer_v3

    audio = Path(_flag_value(cmd, "--audio"))
    output_dir = Path(_flag_value(cmd, "--output-dir"))
    if not audio.is_file():
        raise FileNotFoundError(f"Drummer injection needs the audio file: {audio}")
    if not output_dir.is_dir():
        raise FileNotFoundError(f"Drummer injection needs the output folder: {output_dir}")
    xsq = newest_canonical_xsq(output_dir, audio, ACTIVE_STYLE_VERSION)
    if xsq is None:
        raise FileNotFoundError(
            f"No {audio.stem},{ACTIVE_STYLE_VERSION} XSQ found in {output_dir}"
        )
    return inject_drummer_v3(xsq, xsq, audio)


def main() -> int:
    app = HelixDrummerGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
