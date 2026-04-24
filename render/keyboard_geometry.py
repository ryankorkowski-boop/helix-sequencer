from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


BLACK_PITCH_CLASSES = {1, 3, 6, 8, 10}
WHITE_PITCH_CLASSES = {0, 2, 4, 5, 7, 9, 11}


@dataclass(frozen=True)
class PianoKey:
    pitch: int
    note_name: str
    is_black: bool
    x: float
    y: float
    width: float
    height: float
    white_index: int | None
    key_index: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class KeyboardGeometry:
    note_range_start: int
    note_range_end: int
    show_sharps_flats: bool
    orientation: str
    keys: list[PianoKey]

    @property
    def pitch_to_key(self) -> dict[int, PianoKey]:
        return {key.pitch: key for key in self.keys}

    def key_for_pitch(self, pitch: int) -> PianoKey | None:
        return self.pitch_to_key.get(int(pitch))

    def to_dict(self) -> dict[str, object]:
        return {
            "note_range_start": self.note_range_start,
            "note_range_end": self.note_range_end,
            "show_sharps_flats": self.show_sharps_flats,
            "orientation": self.orientation,
            "keys": [key.to_dict() for key in self.keys],
        }


NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def midi_note_name(pitch: int) -> str:
    pitch_i = int(pitch)
    return f"{NOTE_NAMES[pitch_i % 12]}{(pitch_i // 12) - 1}"


def is_black_key(pitch: int) -> bool:
    return int(pitch) % 12 in BLACK_PITCH_CLASSES


def _rotate_for_orientation(key: PianoKey, orientation: str) -> PianoKey:
    if orientation == "horizontal":
        return key
    return PianoKey(
        pitch=key.pitch,
        note_name=key.note_name,
        is_black=key.is_black,
        x=key.y,
        y=key.x,
        width=key.height,
        height=key.width,
        white_index=key.white_index,
        key_index=key.key_index,
    )


def generate_keyboard_geometry(
    note_range_start: int = 21,
    note_range_end: int = 108,
    *,
    show_sharps_flats: bool = True,
    orientation: str = "horizontal",
) -> KeyboardGeometry:
    if note_range_end < note_range_start:
        raise ValueError("note_range_end must be >= note_range_start.")
    orientation = orientation if orientation in {"horizontal", "vertical"} else "horizontal"
    pitches = list(range(int(note_range_start), int(note_range_end) + 1))
    white_pitches = [pitch for pitch in pitches if not is_black_key(pitch)]
    white_count = max(1, len(white_pitches))
    white_width = 1.0 / white_count
    white_position: dict[int, int] = {}
    white_idx = 0
    for pitch in pitches:
        if not is_black_key(pitch):
            white_position[pitch] = white_idx
            white_idx += 1

    keys: list[PianoKey] = []
    visible_pitches: Iterable[int] = pitches if show_sharps_flats else white_pitches
    for key_idx, pitch in enumerate(visible_pitches):
        black = is_black_key(pitch)
        if black:
            previous_whites = sum(1 for candidate in white_pitches if candidate < pitch)
            x = max(0.0, min(1.0 - (white_width * 0.58), (previous_whites * white_width) - (white_width * 0.29)))
            key = PianoKey(
                pitch=pitch,
                note_name=midi_note_name(pitch),
                is_black=True,
                x=x,
                y=0.0,
                width=white_width * 0.58,
                height=0.62,
                white_index=None,
                key_index=key_idx,
            )
        else:
            idx = white_position[pitch]
            key = PianoKey(
                pitch=pitch,
                note_name=midi_note_name(pitch),
                is_black=False,
                x=idx * white_width,
                y=0.0,
                width=white_width,
                height=1.0,
                white_index=idx,
                key_index=key_idx,
            )
        keys.append(_rotate_for_orientation(key, orientation))
    return KeyboardGeometry(
        note_range_start=int(note_range_start),
        note_range_end=int(note_range_end),
        show_sharps_flats=bool(show_sharps_flats),
        orientation=orientation,
        keys=keys,
    )
