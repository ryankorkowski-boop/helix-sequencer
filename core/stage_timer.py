"""Record elapsed stage durations for run logs."""

from time import perf_counter


class StageTimer:
    def __init__(self, stage: str) -> None:
        self._started = self._stage_started = perf_counter()
        self._stage = stage
        self._elapsed: list[tuple[str, float]] = []

    def advance(self, stage: str) -> None:
        now = perf_counter()
        self._elapsed.append((self._stage, now - self._stage_started))
        self._stage = stage
        self._stage_started = now

    def summary(self) -> str:
        now = perf_counter()
        stages = [*self._elapsed, (self._stage, now - self._stage_started)]
        durations = ", ".join(f"{stage}={elapsed:.3f}s" for stage, elapsed in stages)
        return f"total={now - self._started:.3f}s ({durations})"
