from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from music.note_events import NoteEvent


@dataclass(frozen=True)
class MidiImportResult:
    events: list[NoteEvent]
    ticks_per_quarter: int
    tempo_events: list[tuple[int, int]]


def _read_exact(handle: BinaryIO, count: int) -> bytes:
    data = handle.read(count)
    if len(data) != count:
        raise ValueError("Unexpected end of MIDI file.")
    return data


def _read_u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "big")


def _read_u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


def _read_varlen(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    while True:
        if offset >= len(data):
            raise ValueError("Unterminated MIDI variable-length value.")
        byte = data[offset]
        offset += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            return value, offset


def _parse_track(data: bytes) -> tuple[list[tuple[int, int, int, int]], list[tuple[int, int]]]:
    """Return channel events `(tick, status, data1, data2)` and tempo events."""
    offset = 0
    tick = 0
    running_status: int | None = None
    channel_events: list[tuple[int, int, int, int]] = []
    tempos: list[tuple[int, int]] = []
    while offset < len(data):
        delta, offset = _read_varlen(data, offset)
        tick += delta
        status = data[offset]
        offset += 1
        if status == 0xFF:
            meta_type = data[offset]
            offset += 1
            length, offset = _read_varlen(data, offset)
            payload = data[offset : offset + length]
            offset += length
            if meta_type == 0x2F:
                break
            if meta_type == 0x51 and length == 3:
                tempos.append((tick, int.from_bytes(payload, "big")))
            running_status = None
            continue
        if status in {0xF0, 0xF7}:
            length, offset = _read_varlen(data, offset)
            offset += length
            running_status = None
            continue
        if status < 0x80:
            if running_status is None:
                raise ValueError("MIDI running status encountered before status byte.")
            offset -= 1
            status = running_status
        else:
            running_status = status
        event_type = status & 0xF0
        data_len = 1 if event_type in {0xC0, 0xD0} else 2
        data1 = data[offset]
        offset += 1
        data2 = data[offset] if data_len == 2 else 0
        offset += 1 if data_len == 2 else 0
        channel_events.append((tick, status, data1, data2))
    return channel_events, tempos


def _seconds_for_tick(tick: int, tempo_map: list[tuple[int, int]], ticks_per_quarter: int) -> float:
    tempo_map = sorted(tempo_map or [(0, 500000)], key=lambda item: item[0])
    if tempo_map[0][0] != 0:
        tempo_map.insert(0, (0, 500000))
    seconds = 0.0
    prev_tick = 0
    prev_tempo = tempo_map[0][1]
    for tempo_tick, tempo in tempo_map[1:]:
        if tick <= tempo_tick:
            break
        seconds += (tempo_tick - prev_tick) * (prev_tempo / 1_000_000.0) / ticks_per_quarter
        prev_tick = tempo_tick
        prev_tempo = tempo
    seconds += (tick - prev_tick) * (prev_tempo / 1_000_000.0) / ticks_per_quarter
    return seconds


def import_midi(path: Path | str) -> MidiImportResult:
    path = Path(path)
    with path.open("rb") as handle:
        if _read_exact(handle, 4) != b"MThd":
            raise ValueError("Not a Standard MIDI File.")
        header_len = int.from_bytes(_read_exact(handle, 4), "big")
        header = _read_exact(handle, header_len)
        if header_len < 6:
            raise ValueError("Invalid MIDI header.")
        track_count = _read_u16(header, 2)
        division = _read_u16(header, 4)
        if division & 0x8000:
            raise ValueError("SMPTE MIDI timing is not supported yet.")
        tracks: list[bytes] = []
        for _ in range(track_count):
            chunk = _read_exact(handle, 4)
            length = int.from_bytes(_read_exact(handle, 4), "big")
            data = _read_exact(handle, length)
            if chunk == b"MTrk":
                tracks.append(data)

    channel_events: list[tuple[int, int, int, int]] = []
    tempo_events: list[tuple[int, int]] = [(0, 500000)]
    for track in tracks:
        events, tempos = _parse_track(track)
        channel_events.extend(events)
        tempo_events.extend(tempos)
    tempo_events = sorted(set(tempo_events), key=lambda item: item[0])
    channel_events.sort(key=lambda item: item[0])

    active: dict[tuple[int, int], list[tuple[int, int]]] = {}
    notes: list[NoteEvent] = []
    for tick, status, data1, data2 in channel_events:
        event_type = status & 0xF0
        channel = status & 0x0F
        pitch = int(data1)
        velocity = int(data2)
        key = (channel, pitch)
        if event_type == 0x90 and velocity > 0:
            active.setdefault(key, []).append((tick, velocity))
        elif event_type in {0x80, 0x90}:
            starts = active.get(key) or []
            if not starts:
                continue
            start_tick, start_velocity = starts.pop(0)
            if not starts:
                active.pop(key, None)
            if tick <= start_tick:
                continue
            notes.append(
                NoteEvent(
                    start=_seconds_for_tick(start_tick, tempo_events, division),
                    end=_seconds_for_tick(tick, tempo_events, division),
                    pitch=pitch,
                    velocity=max(0.0, min(1.0, start_velocity / 127.0)),
                    channel=channel,
                    source="midi",
                    confidence=1.0,
                )
            )
    notes.sort(key=lambda item: (item.start, item.pitch, item.end))
    return MidiImportResult(events=notes, ticks_per_quarter=division, tempo_events=tempo_events)
