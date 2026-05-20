from __future__ import annotations

from dataclasses import dataclass

from core.birdsong_feature_state import FeatureState


BIRDSONG_MOTIFS: tuple[str, ...] = (
    "wave_sweep",
    "spiral",
    "pulse_cascade",
    "orbit",
    "sparkle_field",
)

BIRDSONG_DIRECTIONS: tuple[str, ...] = (
    "left_to_right",
    "right_to_left",
    "center_out",
    "bottom_up",
    "top_down",
)


@dataclass(frozen=True)
class Phrase:
    start_time: float
    duration: float
    motif: str
    direction: str
    energy_anchor: float

    @property
    def end_time(self) -> float:
        return round(self.start_time + self.duration, 6)


def choose_motif(state: FeatureState, phrase_index: int = 0) -> str:
    low, mid, high = state.band_balance
    if high >= 0.45:
        options = ("sparkle_field", "spiral")
    elif low >= 0.45:
        options = ("pulse_cascade", "wave_sweep")
    elif mid >= 0.45:
        options = ("wave_sweep", "orbit")
    elif state.onset >= 0.7:
        options = ("pulse_cascade", "sparkle_field")
    else:
        options = BIRDSONG_MOTIFS
    return options[phrase_index % len(options)]


def choose_direction(state: FeatureState, phrase_index: int = 0) -> str:
    if state.low >= max(state.mid, state.high):
        options = ("center_out", "bottom_up")
    elif state.high >= max(state.low, state.mid):
        options = ("top_down", "left_to_right")
    else:
        options = ("left_to_right", "right_to_left")
    return options[phrase_index % len(options)]


class PhraseEngine:
    def __init__(
        self,
        *,
        bpm: float = 120.0,
        min_duration: float = 2.0,
        max_duration: float = 8.0,
        onset_threshold: float = 0.72,
        energy_shift_threshold: float = 0.22,
    ) -> None:
        if bpm <= 0:
            raise ValueError("bpm must be > 0")
        self.bpm = float(bpm)
        self.min_duration = float(min_duration)
        self.max_duration = float(max_duration)
        self.onset_threshold = float(onset_threshold)
        self.energy_shift_threshold = float(energy_shift_threshold)
        self.current_phrase: Phrase | None = None
        self.phrase_index = 0

    def phrase_duration(self) -> float:
        two_bars = (60.0 / self.bpm) * 8.0
        return round(max(self.min_duration, min(self.max_duration, two_bars)), 6)

    def should_start_phrase(self, time: float, state: FeatureState) -> bool:
        if self.current_phrase is None:
            return True
        age = time - self.current_phrase.start_time
        if time >= self.current_phrase.end_time:
            return True
        if age >= self.min_duration and state.onset >= self.onset_threshold:
            return True
        return age >= self.min_duration and abs(state.energy_smooth - self.current_phrase.energy_anchor) >= self.energy_shift_threshold

    def update(self, time: float, state: FeatureState) -> Phrase:
        if self.should_start_phrase(time, state):
            self.current_phrase = Phrase(
                start_time=round(float(time), 6),
                duration=self.phrase_duration(),
                motif=choose_motif(state, self.phrase_index),
                direction=choose_direction(state, self.phrase_index),
                energy_anchor=state.energy_smooth,
            )
            self.phrase_index += 1
        assert self.current_phrase is not None
        return self.current_phrase
