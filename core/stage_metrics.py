"""Opt-in wall-clock stages and process peak RSS; never part of sequence data.

Set HELIX_PROFILE_OUTPUT to a JSON path, or use capture_metrics(). Stage times
are inclusive (nested stages must not be summed). RSS is the process lifetime
high-water mark, not an allocation estimate or a per-stage delta.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
import json
import os
from pathlib import Path
import platform
import tempfile
from time import perf_counter
from typing import Callable, Iterator, ParamSpec, TypeVar
import warnings

P = ParamSpec("P")
T = TypeVar("T")


def peak_rss_bytes() -> int | None:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        api = ctypes.WinDLL("psapi", use_last_error=True).GetProcessMemoryInfo
        api.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        api.restype = wintypes.BOOL
        if api(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return int(counters.PeakWorkingSetSize)
        return None
    try:
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(rss if platform.system() == "Darwin" else rss * 1024)
    except (ImportError, OSError):
        return None


@dataclass
class StageMetrics:
    stages: dict[str, dict[str, float | int | None]] = field(default_factory=dict)
    success: bool = False
    started: float = field(default_factory=perf_counter)
    wall_seconds: float = 0.0
    peak_rss: int | None = None
    _phase: tuple[str, float] | None = None

    def record(self, name: str, elapsed: float) -> None:
        row = self.stages.setdefault(name, {"calls": 0, "wall_seconds": 0.0})
        row["calls"] += 1
        row["wall_seconds"] += elapsed

    def phase(self, name: str | None) -> None:
        now = perf_counter()
        if self._phase is not None:
            previous, started = self._phase
            self.record(previous, now - started)
        self._phase = (name, now) if name else None

    def to_dict(self) -> dict:
        return {
            "schema": "helix.stage_metrics.v1", "success": self.success,
            "python": platform.python_version(), "platform": platform.system(),
            "wall_seconds": self.wall_seconds, "peak_rss_bytes": self.peak_rss,
            "rss_scope": "process lifetime high-water mark",
            "timing_scope": "inclusive; nested stage durations overlap",
            "stages": self.stages,
        }

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                             prefix=".helix-metrics-", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(self.to_dict(), stream, indent=2, allow_nan=False)
                stream.write("\n")
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


_ACTIVE: ContextVar[StageMetrics | None] = ContextVar("helix_stage_metrics", default=None)


@contextmanager
def capture_metrics(output: Path | None = None) -> Iterator[StageMetrics]:
    """Nest safely; preserve exceptions, including SystemExit and interrupts."""
    existing = _ACTIVE.get()
    if existing is not None:
        yield existing
        return
    metrics = StageMetrics()
    token = _ACTIVE.set(metrics)
    try:
        yield metrics
        metrics.success = True
    finally:
        metrics.phase(None)
        metrics.wall_seconds = perf_counter() - metrics.started
        metrics.peak_rss = peak_rss_bytes()
        _ACTIVE.reset(token)
        if output is not None:
            try:
                metrics.write(output)
            except OSError as exc:
                warnings.warn(f"Could not save Helix stage metrics: {exc}", RuntimeWarning)


def phase(name: str | None) -> None:
    metrics = _ACTIVE.get()
    if metrics is not None:
        metrics.phase(name)


def timed_stage(name: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorate(function: Callable[P, T]) -> Callable[P, T]:
        @wraps(function)
        def run(*args: P.args, **kwargs: P.kwargs) -> T:
            metrics = _ACTIVE.get()
            if metrics is None:
                return function(*args, **kwargs)
            started = perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                metrics.record(name, perf_counter() - started)
        return run
    return decorate


def profile_run(function: Callable[P, T]) -> Callable[P, T]:
    @wraps(function)
    def run(*args: P.args, **kwargs: P.kwargs) -> T:
        output = os.environ.get("HELIX_PROFILE_OUTPUT")
        if not output or _ACTIVE.get() is not None:
            return function(*args, **kwargs)
        with capture_metrics(Path(output)):
            return function(*args, **kwargs)
    return run
