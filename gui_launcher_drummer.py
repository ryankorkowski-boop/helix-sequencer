from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from gui_launcher import HelixGui, ROOT


class HelixDrummerGui(HelixGui):
    """Helix GUI with the current Drummer V3 ground-truth tools exposed."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Helix Sequence Weaver - Helixville Control Center + Drummer V3")
        self._add_drummer_controls()

    def _add_drummer_controls(self) -> None:
        panel = ttk.LabelFrame(self, text="Drummer V3")
        panel.pack(fill=tk.X, padx=16, pady=(0, 8))

        ttk.Label(
            panel,
            text="Validate the latest 8-channel Drummer V3 ground truth and render an audio-muxed MP4 preview.",
        ).pack(side=tk.LEFT, padx=8, pady=6)
        ttk.Button(
            panel,
            text="Run Drummer V3 Ground Truth",
            command=self._run_drummer_ground_truth,
        ).pack(side=tk.RIGHT, padx=8, pady=6)

    def _run_drummer_ground_truth(self) -> None:
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
                    process = subprocess.Popen(
                        command,
                        cwd=str(ROOT),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )
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
                messagebox.showinfo(
                    "Drummer V3 Complete",
                    f"Ground-truth XSQ and MP4 preview created in:\n{out}",
                )
            except Exception as exc:
                self.status_label.configure(text="Drummer test failed")
                self._log(f"Drummer test exception: {exc}")
                messagebox.showerror("Drummer V3 Failed", str(exc))

        threading.Thread(target=worker, daemon=True).start()


def main() -> int:
    app = HelixDrummerGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
