"""Decorative, low-cost Tk animation; not an xLights output preview."""
import math
import time
import tkinter as tk


class SequencingLightShow(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=110, bg="#091020", highlightthickness=0, **kwargs)
        self.running = False
        self.scene = "Combined"
        self._started = 0.0
        self._timer = None
        self.bind("<Configure>", lambda _event: self._draw())

    def set_scene(self, scene):
        self.scene = scene
        self._draw()

    def set_running(self, running):
        self.running = bool(running)
        if self._timer is not None:
            self.after_cancel(self._timer)
            self._timer = None
        if self.running:
            self._started = time.monotonic()
        self._draw()

    def destroy(self):
        if self._timer is not None:
            self.after_cancel(self._timer)
            self._timer = None
        super().destroy()

    def _draw(self):
        self.delete("all")
        w, h = max(self.winfo_width(), 1), max(self.winfo_height(), 1)
        phase = time.monotonic() - self._started if self.running else 0
        if self.scene in ("Combined", "Arches"):
            for arch in range(5):
                center = w * (.12 + .12 * arch)
                for i in range(31):
                    t = math.pi * i / 30
                    x = center + w * .075 * math.cos(t)
                    y = h * (.83 - .53 * math.sin(t))
                    chase = ((i / 30 + arch * .19 - phase * .55) % 1)
                    color = "#e25dff" if abs(chase - .5) < .14 else "#326a9c"
                    self.create_oval(x-2, y-2, x+2, y+2, fill=color, outline="")
        if self.scene in ("Combined", "Mega tree"):
            center = w * (.82 if self.scene == "Combined" else .5)
            radius = w * (.14 if self.scene == "Combined" else .28)
            colors = ("#29e7ed", "#e35bff", "#fbbf24", "#3af9a5")
            for i in range(100):
                t = i / 99
                angle = t * math.pi * 10 + phase * 1.6
                x = center + radius * t * math.cos(angle)
                y = h * (.1 + .75 * t)
                self.create_oval(x-2, y-2, x+2, y+2, fill=colors[(i//10)%4], outline="")
        if self.running and self.winfo_exists():
            self._timer = self.after(80, self._draw)
