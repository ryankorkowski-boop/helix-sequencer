from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

from core.energy_model import EnergyCurve, build_energy_curve


CANONICAL_SECTION_LABELS = (
    "intro",
    "verse",
    "pre-chorus",
    "chorus",
    "post-chorus",
    "bridge",
    "breakdown",
    "buildup",
    "drop",
    "outro",
)


_LABEL_ALIASES = {
    "intro": "intro",
    "verse": "verse",
    "prechorus": "pre-chorus",
    "pre_chorus": "pre-chorus",
    "pre-chorus": "pre-chorus",
    "chorus": "chorus",
    "postchorus": "post-chorus",
    "post_chorus": "post-chorus",
    "post-chorus": "post-chorus",
    "bridge": "bridge",
    "break": "breakdown",
    "breakdown": "breakdown",
    "build": "buildup",
    "buildup": "buildup",
    "build_up": "buildup",
    "drop": "drop",
    "outro": "outro",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    if out != out:
        return default
    return out


def _normalize_label(label: str) -> str:
    key = str(label or "").strip().lower().replace(" ", "_")
    return _LABEL_ALIASES.get(key, "")


@dataclass(frozen=True)
class SongSection:
    label: str
    start_ms: int
    end_ms: int
    energy: float
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SongStructureTimeline:
    sections: tuple[SongSection, ...]
    energy_curve: EnergyCurve

    def section_for_time(self, t_ms: int) -> SongSection | None:
        for section in self.sections:
            if section.start_ms <= int(t_ms) < section.end_ms:
                return section
        return self.sections[-1] if self.sections else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "helix.song_structure.v1",
            "allowed_labels": list(CANONICAL_SECTION_LABELS),
            "sections": [section.to_dict() for section in self.sections],
            "energy_curve": self.energy_curve.to_dict(),
        }


def _duration_ms(audio: Any, beat_ms: Sequence[int], sections: Sequence[Any] | None) -> int:
    dur = int(round(_safe_float(getattr(audio, "dur_s", 0.0)) * 1000.0))
    if dur > 0:
        return dur
    if sections:
        return max(int(getattr(section, "end_ms", 0) or 0) for section in sections)
    if beat_ms:
        return max(int(value) for value in beat_ms) + 1000
    return 1000


def _fallback_sections(song_length_ms: int, beat_ms: Sequence[int]) -> list[tuple[str, int, int]]:
    if not beat_ms:
        spans = [
            ("intro", 0, int(song_length_ms * 0.12)),
            ("verse", int(song_length_ms * 0.12), int(song_length_ms * 0.42)),
            ("chorus", int(song_length_ms * 0.42), int(song_length_ms * 0.68)),
            ("bridge", int(song_length_ms * 0.68), int(song_length_ms * 0.84)),
            ("outro", int(song_length_ms * 0.84), song_length_ms),
        ]
        return [(label, start, max(start + 1, end)) for label, start, end in spans if end > start]
    clean = sorted({int(value) for value in beat_ms if int(value) >= 0})
    beats_per_section = 32
    out: list[tuple[str, int, int]] = []
    idx = 0
    while idx < len(clean) - 1:
        start = clean[idx]
        end_idx = min(len(clean) - 1, idx + beats_per_section)
        end = clean[end_idx]
        out.append(("", start, max(start + 1, end)))
        idx = end_idx
    if not out:
        out.append(("", 0, song_length_ms))
    if out[-1][2] < song_length_ms:
        label, start, _end = out[-1]
        out[-1] = (label, start, song_length_ms)
    return out


def _candidate_sections(sections: Sequence[Any] | None, song_length_ms: int, beat_ms: Sequence[int]) -> list[tuple[str, int, int]]:
    if not sections:
        return _fallback_sections(song_length_ms, beat_ms)
    out: list[tuple[str, int, int]] = []
    for section in sections:
        start = max(0, int(getattr(section, "start_ms", 0) or 0))
        end = max(start + 1, int(getattr(section, "end_ms", start + 1) or (start + 1)))
        label = _normalize_label(str(getattr(section, "label", "") or ""))
        out.append((label, start, min(song_length_ms, end)))
    out.sort(key=lambda item: (item[1], item[2], item[0]))
    return out


def _classify(index: int, total: int, explicit_label: str, energy: float, prev_energy: float, next_energy: float, max_energy: float, seen_chorus: bool) -> tuple[str, float]:
    if explicit_label in CANONICAL_SECTION_LABELS:
        return explicit_label, 0.92
    if index == 0 and energy <= max(0.62, max_energy * 0.78):
        return "intro", 0.72
    if index == total - 1:
        return "outro", 0.74
    rising = next_energy - prev_energy
    falling = prev_energy - next_energy
    if energy >= max(0.78, max_energy * 0.92):
        return ("drop" if rising >= 0.08 else "chorus"), 0.78
    if rising >= 0.18 and next_energy >= max(0.64, energy + 0.12):
        return ("buildup" if next_energy >= 0.78 else "pre-chorus"), 0.76
    if seen_chorus and falling >= 0.18 and energy <= 0.46:
        return "breakdown", 0.70
    if seen_chorus and index >= max(1, int(total * 0.55)) and energy < max_energy * 0.75:
        return "bridge", 0.68
    if seen_chorus and prev_energy >= max_energy * 0.82 and energy >= 0.52:
        return "post-chorus", 0.66
    if energy >= 0.58:
        return "chorus", 0.62
    return "verse", 0.64


def detect_song_structure(
    *,
    audio: Any,
    beat_ms: Sequence[int],
    onset_ms: Sequence[int] | None = None,
    multiband: Any | None = None,
    sections: Sequence[Any] | None = None,
    energy_curve: EnergyCurve | None = None,
) -> SongStructureTimeline:
    curve = energy_curve or build_energy_curve(audio=audio, beat_ms=beat_ms, onset_ms=onset_ms, multiband=multiband)
    song_length_ms = _duration_ms(audio, beat_ms, sections)
    candidates = _candidate_sections(sections, song_length_ms, beat_ms)
    energies = [curve.energy_between(start, end) for _label, start, end in candidates]
    max_energy = max(energies) if energies else 0.0
    out: list[SongSection] = []
    seen_chorus = False
    for idx, (explicit_label, start, end) in enumerate(candidates):
        energy = energies[idx] if idx < len(energies) else curve.energy_between(start, end)
        prev_energy = energies[idx - 1] if idx > 0 else energy
        next_energy = energies[idx + 1] if idx + 1 < len(energies) else energy
        label, confidence = _classify(idx, len(candidates), explicit_label, energy, prev_energy, next_energy, max_energy, seen_chorus)
        seen_chorus = seen_chorus or label in {"chorus", "drop"}
        out.append(
            SongSection(
                label=label,
                start_ms=int(start),
                end_ms=int(end),
                energy=round(float(energy), 4),
                confidence=round(float(confidence), 4),
                metadata={
                    "source_label": explicit_label,
                    "position": round(float(idx / max(1, len(candidates) - 1)), 4),
                    "macro_ramp": round(float(next_energy - prev_energy), 4),
                },
            )
        )
    return SongStructureTimeline(sections=tuple(out), energy_curve=curve)
