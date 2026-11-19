"""Multi-input palette decisions: lyrics + tempo + intensity + sections + key.

``choose_palette`` turns measured song features into a base palette and one
palette per song section, with a written rationale for every decision. A
``strategy`` selects *how* the inputs are weighed, so sixteen panels driven by
the same song can legitimately differ (and the differences are explainable):

    lyric_semantic   lyric imagery anchors the hues (gold, snow, rainbow ...)
    key_mood         circle-of-fifths hue, major = warm/bright, minor = cool
    tempo_energy     tempo -> hue temperature, intensity -> saturation/value
    section_contrast every section jumps to a contrasting hue family
    complementary    lyric anchor + its complement, energy sets the accent
    triadic          key hue + 120/240 degrees
    analogous        narrow +/-30 degree family, sections move brightness only
    classic_christmas red/green/warm-white kept, energy picks gold/ice accents
    ice_crystal      cool whites/blues; lyric warmth may add one accent
    neon_club        high-chroma neons; fast tempo widens the spread
    monochrome_pulse single hue; sections and intensity change value only
    candy_stripe     red/white/pink; chorus energy adds mint

Inputs never need to be complete; missing ones are reported as such.
"""
from __future__ import annotations

import colorsys
import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np

STRATEGIES = (
    "lyric_semantic", "key_mood", "tempo_energy", "section_contrast", "complementary",
    "triadic", "analogous", "classic_christmas", "ice_crystal", "neon_club",
    "monochrome_pulse", "candy_stripe",
)

# Lyric imagery -> hue (degrees). Kept small and literal; matched on whole words.
LYRIC_HUES = {
    "gold": 45, "golden": 45, "tinsel": 50, "star": 52, "bells": 48, "bell": 48, "candle": 35,
    "fire": 15, "fireplace": 15, "warm": 30, "cookie": 32, "grill": 20, "comet": 200,
    "snow": 205, "snowman": 205, "ice": 195, "frost": 190, "cold": 200, "winter": 210, "blue": 220,
    "pink": 330, "rose": 345, "kiss": 340, "angel": 280, "secrets": 270, "purple": 280,
    "red": 0, "santa": 0, "candy": 350, "holly": 120, "tree": 125, "green": 125, "elf": 110,
    "elves": 110, "deer": 25, "swans": 50, "rainbow": -1, "lights": -1, "neon": -1,
    "tornado": 265, "spin": 265, "storm": 250, "night": 235, "boom": 10, "blink": 55,
}
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
PITCHES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


@dataclass
class SongFeatures:
    tempo_bpm: float | None = None
    intensity: float | None = None             # 0..1 overall loudness/energy
    sections: list[dict] = field(default_factory=list)  # {label,start_ms,end_ms,energy 0..1}
    lyrics: list[str] = field(default_factory=list)
    key: str | None = None                       # e.g. "A minor"


@dataclass
class PaletteDecision:
    strategy: str
    palette: tuple[str, ...]
    section_palettes: dict[str, tuple[str, ...]]
    rationale: list[str]
    inputs_used: dict[str, object]

    def for_section(self, label: str) -> tuple[str, ...]:
        return self.section_palettes.get(str(label), self.palette)


class SectionPalette(tuple):
    """A tuple palette that also knows its per-section variants."""

    decision: PaletteDecision

    def __new__(cls, decision: PaletteDecision):
        obj = super().__new__(cls, decision.palette)
        obj.decision = decision
        return obj

    def for_section(self, label):
        return self.decision.for_section(label)


def _hex(h: float, s: float, v: float) -> str:
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360.0, max(0, min(1, s)), max(0, min(1, v)))
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def estimate_key(y, sr) -> tuple[str, float]:
    """Krumhansl-Schmuckler key from mean chroma. Returns (name, correlation)."""
    import librosa
    chroma = librosa.feature.chroma_cqt(y=np.asarray(y, dtype=np.float32), sr=sr).mean(axis=1)
    best = ("C major", -2.0)
    for tonic in range(12):
        for name, profile in (("major", MAJOR), ("minor", MINOR)):
            r = float(np.corrcoef(chroma, np.roll(profile, tonic))[0, 1])
            if r > best[1]:
                best = (f"{PITCHES[tonic]} {name}", r)
    return best


def lyric_anchors(words: Iterable[str]) -> list[tuple[str, int, int]]:
    """Return (word, hue, count) sorted by frequency; hue -1 means 'multicolour'."""
    counts: dict[str, int] = {}
    for raw in words:
        w = re.sub(r"[^a-z]", "", str(raw).lower())
        if w in LYRIC_HUES:
            counts[w] = counts.get(w, 0) + 1
    return sorted(((w, LYRIC_HUES[w], c) for w, c in counts.items()), key=lambda t: (-t[2], t[0]))


def _key_hue(key: str | None) -> tuple[float, bool] | None:
    if not key:
        return None
    parts = key.split()
    if parts[0] not in PITCHES:
        return None
    fifths = (PITCHES.index(parts[0]) * 7) % 12  # circle-of-fifths position
    return fifths * 30.0, (len(parts) > 1 and parts[1].lower().startswith("min"))


def choose_palette(features: SongFeatures, strategy: str = "lyric_semantic", *, size: int = 3) -> PaletteDecision:
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown palette strategy {strategy!r}")
    why: list[str] = []
    tempo = features.tempo_bpm
    intensity = 0.6 if features.intensity is None else float(np.clip(features.intensity, 0, 1))
    if features.intensity is None:
        why.append("intensity unavailable: assumed 0.60")
    fast = None if tempo is None else float(np.clip((tempo - 70) / 100, 0, 1))  # 70->0, 170->1
    sat = 0.55 + 0.4 * intensity
    val = 0.70 + 0.30 * intensity
    anchors = lyric_anchors(features.lyrics)
    key = _key_hue(features.key)
    used = dict(tempo_bpm=tempo, intensity=round(intensity, 3), key=features.key,
                lyric_anchors=[a[0] for a in anchors[:5]], sections=len(features.sections))
    lyric_hue = next((h for _, h, _ in anchors if h >= 0), None)
    multicolour = any(h < 0 for _, h, _ in anchors[:4])

    if strategy == "lyric_semantic":
        hues = [h for _, h, _ in anchors if h >= 0][:size] or [0, 120, 45][:size]
        while len(hues) < size:
            hues.append(hues[-1] + 137.5)
        base = [_hex(h, sat, val) for h in hues]
        why.append(f"lyric imagery {[a[0] for a in anchors[:size]]} set hues {hues}")
    elif strategy == "key_mood":
        h, minor = key or (30.0, False)
        shift = -25 if minor else 15
        base = [_hex(h + shift, sat * (0.85 if minor else 1), val * (0.9 if minor else 1)),
                _hex(h + shift + 40, sat * 0.8, val), _hex(h + shift + 180, 0.25, 1.0)]
        why.append(f"key {features.key or 'unknown (C-equivalent)'}: hue {h:.0f}, {'minor -> cooler/darker' if minor else 'major -> warmer/brighter'}")
    elif strategy == "tempo_energy":
        f = 0.5 if fast is None else fast
        h = 220 - 200 * f  # slow = blue, fast = red/orange
        base = [_hex(h, sat, val), _hex(h + 30, sat * 0.9, val), _hex(h - 150, 0.9, 1.0)]
        why.append(f"tempo {tempo} BPM -> temperature {f:.2f} (hue {h:.0f}); intensity {intensity:.2f} -> sat {sat:.2f}")
    elif strategy == "section_contrast":
        h = lyric_hue if lyric_hue is not None else (key[0] if key else 0)
        base = [_hex(h, sat, val), _hex(h + 180, sat, val), _hex(h + 90, 0.3, 1)]
        why.append(f"anchor hue {h} with complementary contrast; sections rotate hue families")
    elif strategy == "complementary":
        h = lyric_hue if lyric_hue is not None else 45
        base = [_hex(h, sat, val), _hex(h + 180, sat, val), _hex(h, 0.15, 1.0)]
        why.append(f"lyric anchor hue {h} + complement {h + 180 % 360}")
    elif strategy == "triadic":
        h = key[0] if key else (lyric_hue or 0)
        base = [_hex(h + o, sat, val) for o in (0, 120, 240)]
        why.append(f"triad on key hue {h:.0f}")
    elif strategy == "analogous":
        h = lyric_hue if lyric_hue is not None else 200
        base = [_hex(h + o, sat, val) for o in (-30, 0, 30)]
        why.append(f"analogous +/-30 around {h}")
    elif strategy == "classic_christmas":
        accent = _hex(48, 0.75, 1.0) if intensity >= 0.5 else _hex(200, 0.35, 1.0)
        base = ["#FF2020", "#20E040", "#FFF1D0", accent]
        why.append(f"traditional red/green/warm-white; intensity {intensity:.2f} -> {'gold' if intensity >= .5 else 'ice'} accent")
    elif strategy == "ice_crystal":
        base = ["#E8F6FF", "#56C8FF", "#2A5BFF"]
        if lyric_hue is not None and (lyric_hue < 60 or lyric_hue > 300):
            base.append(_hex(lyric_hue, 0.7, 1.0))
            why.append(f"warm lyric anchor ({anchors[0][0]}) adds one accent")
        why.append("cool white/blue family")
    elif strategy == "neon_club":
        spread = 60 + 60 * (0.5 if fast is None else fast)
        h = 300 if lyric_hue is None else lyric_hue
        base = [_hex(h + o * spread, 1.0, 1.0) for o in range(size)]
        why.append(f"max-chroma neon, tempo spreads hues by {spread:.0f} degrees")
    elif strategy == "monochrome_pulse":
        h = key[0] if key else (lyric_hue or 280)
        base = [_hex(h, 0.9, 1.0), _hex(h, 0.75, 0.55), _hex(h, 0.25, 1.0)]
        why.append(f"single hue {h:.0f}; only brightness moves")
    else:  # candy_stripe
        base = ["#FF2848", "#FFFFFF", "#FF8CC6"]
        why.append("red/white/pink candy stripe")
    if multicolour and strategy in ("lyric_semantic", "neon_club", "section_contrast"):
        base.append(_hex((lyric_hue or 0) + 200, 1.0, 1.0))
        why.append("lyrics mention lights/rainbow/neon -> extra spectral accent")

    sections: dict[str, tuple[str, ...]] = {}
    for index, section in enumerate(features.sections):
        label = str(section.get("label", index))
        energy = float(np.clip(section.get("energy", intensity), 0, 1))
        cols = [colorsys.rgb_to_hsv(*(int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))) for c in base]
        out = []
        for j, (h, s, v) in enumerate(cols):
            h *= 360
            if strategy == "section_contrast":
                h += (index % 4) * 90
            elif strategy in ("monochrome_pulse", "analogous"):
                v = 0.35 + 0.65 * energy if j == 0 else v
            elif strategy == "tempo_energy":
                h -= 40 * (energy - 0.5)
            elif strategy in ("lyric_semantic", "complementary", "triadic", "key_mood", "neon_club"):
                h += 25 * (energy - 0.5) * (1 if j % 2 == 0 else -1)
            s = min(1, s * (0.75 + 0.5 * energy)) if strategy not in ("ice_crystal", "classic_christmas", "candy_stripe") else s
            v = min(1, max(0.25, v * (0.7 + 0.45 * energy)))
            out.append(_hex(h, s, v))
        if strategy == "classic_christmas" and energy < 0.35:
            out = out[:3]
        if strategy == "candy_stripe" and energy >= 0.7:
            out.append("#64FFB4")
        sections[label] = tuple(out)
    if features.sections:
        why.append(f"{len(features.sections)} sections recoloured by measured section energy")
    else:
        why.append("no section data: one palette for the whole song")
    return PaletteDecision(strategy, tuple(base), sections, why, used)


def song_features_from_plan(plan: dict, *, words: Sequence[str] = (), key: str | None = None,
                            intensity: float | None = None) -> SongFeatures:
    """Collect tempo + per-label section energy from a Helix snowman_band plan.

    Cue ``section`` labels are upper-case part names (VERSE, CHORUS ...), so
    energies of repeated parts are averaged under one label.
    """
    tempo = (plan.get("debug") or {}).get("tempo_bpm")
    parts = ((plan.get("global_timeline") or {}).get("song_parts") or [])
    energy: dict[str, list[float]] = {}
    for part in parts:
        label = str(part.get("name") or part.get("label") or "").upper()
        if not label or part.get("energy_level") is None:
            continue
        energy.setdefault(label, []).append(float(part["energy_level"]))
    sections = [dict(label=k, energy=float(np.mean(v))) for k, v in energy.items()]
    if intensity is None and parts:
        durations = [max(0.0, float(p.get("end_time", 0)) - float(p.get("start_time", 0))) for p in parts]
        levels = [float(p.get("energy_level", 0) or 0) for p in parts]
        if sum(durations) > 0:
            intensity = float(np.average(levels, weights=durations))
    return SongFeatures(tempo_bpm=None if tempo is None else float(tempo), intensity=intensity,
                        sections=sections, lyrics=list(words), key=key)
