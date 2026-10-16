"""Original deterministic, audio-derived section budgets; no RNG or IO."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Section:
    id: str
    start_ms: int
    end_ms: int
    energy: float
    energy_budget: float
    density_cap: float
    palette: tuple[str, ...]
    allowed_families: tuple[str, ...]
    marker: str


@dataclass(frozen=True)
class SectionPlan:
    duration_ms: int
    sections: tuple[Section, ...]
    intentional_restraint: tuple[tuple[int, int], ...]
    energy_curve: tuple[tuple[int, float], ...]
    warnings: tuple[str, ...] = ()

    def at(self, time_ms: int) -> Section | None:
        return next((s for s in self.sections
                     if s.start_ms <= time_ms < s.end_ms), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "helix.section_composer.v1",
            "analysis": "chroma_mfcc_self_similarity",
            "duration_ms": self.duration_ms,
            "sections": [asdict(s) for s in self.sections],
            "intentional_restraint": [
                {"start_ms": a, "end_ms": b}
                for a, b in self.intentional_restraint],
            "energy": [{"time_ms": t, "value": v}
                       for t, v in self.energy_curve],
            "warnings": list(self.warnings) + budget_warnings(self.sections),
        }


def budget_warnings(sections: tuple[Section, ...]) -> list[str]:
    """Warn when later/higher energy fails to exceed an earlier budget."""
    return [f"energy_budget_order:{a.id}:{b.id}"
            for i, a in enumerate(sections) for b in sections[i + 1:]
            if b.energy > a.energy + 1e-6
            and b.energy_budget <= a.energy_budget]


def compose_sections(samples: Any, sample_rate: int, *,
                     minimum_ms: int = 4000) -> SectionPlan:
    """Use bounded chroma/MFCC self-similarity novelty, then assign budgets.

    Imports are lazy so a default-off engine run does no additional analysis.
    Minimum-length sections cover the complete signal without gaps/overlap;
    shorter clips become one section. No semantic verse/chorus claim is made.
    """
    import librosa
    import numpy as np

    y = np.asarray(samples, dtype=float)
    if (y.ndim != 1 or not y.size or not np.isfinite(y).all()
            or sample_rate <= 0 or minimum_ms < 500):
        raise ValueError("Need finite mono audio, positive rate, min >=500ms")
    duration = round(len(y) / sample_rate * 1000)
    if duration <= 0:
        raise ValueError("Audio is shorter than one millisecond")
    if sample_rate != 22050:
        y = librosa.resample(y, orig_sr=sample_rate, target_sr=22050)
    rate, hop = 22050, 512
    spectrum = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop)) ** 2
    chroma = librosa.feature.chroma_stft(
        S=spectrum, sr=rate, hop_length=hop, tuning=0)
    mel = librosa.feature.melspectrogram(S=spectrum, sr=rate, n_mels=40)
    mfcc = librosa.feature.mfcc(
        S=librosa.power_to_db(mel, ref=1.0), n_mfcc=13)
    # <=2048 pooled frames bounds the self-similarity matrix to 32 MiB.
    frame_ms = max(500, math.ceil(duration / 2048))
    times = list(range(0, duration, frame_ms))
    frame_times = np.arange(spectrum.shape[1]) * hop / rate * 1000
    descriptors, rms, hues = [], [], []
    for start in times:
        end = min(duration, start + frame_ms)
        mask = (frame_times >= start) & (frame_times < end)
        index = min(spectrum.shape[1] - 1,
                    round(start / 1000 * rate / hop))
        c = chroma[:, mask].mean(axis=1) if mask.any() else chroma[:, index]
        m = mfcc[:, mask].mean(axis=1) if mask.any() else mfcc[:, index]
        descriptors.append(np.concatenate((c, m)))
        hues.append(int(np.argmax(c)))
        segment = y[round(start / 1000 * rate):round(end / 1000 * rate)]
        rms.append(float(np.sqrt(np.mean(segment ** 2))))
    matrix = np.asarray(descriptors)
    c = matrix[:, :12]
    m = matrix[:, 12:]
    m = np.clip((m - np.median(m, axis=0))
                / np.maximum(np.std(m, axis=0), 1e-6), -3, 3)
    c = c / np.maximum(np.linalg.norm(c, axis=1, keepdims=True), 1e-9)
    m = m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-9)
    vectors = np.concatenate((c * .65, m * .35), axis=1)
    vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True),
                          1e-9)
    similarity = vectors @ vectors.T
    radius = max(1, math.ceil(minimum_ms / frame_ms / 2))
    novelty = np.zeros(len(times))
    for index in range(1, len(times)):
        left, right = max(0, index - radius), min(len(times), index + radius)
        novelty[index] = max(0, float(
            (similarity[left:index, left:index].mean()
             + similarity[index:right, index:right].mean()) / 2
            - similarity[left:index, index:right].mean()))
    threshold = max(.12, float(
        np.median(novelty)
        + np.median(abs(novelty - np.median(novelty)))))
    peaks = [i for i in range(1, len(times) - 1)
             if novelty[i] >= threshold
             and novelty[i] > novelty[i - 1]
             and novelty[i] >= novelty[i + 1]]
    cuts = [0, duration]
    for index in sorted(peaks, key=lambda i: (-novelty[i], i)):
        time_ms = times[index]
        if all(abs(time_ms - cut) >= minimum_ms for cut in cuts):
            cuts.append(time_ms)
    cuts.sort()
    peak_rms = max(rms)
    energy = [round(v / peak_rms, 6) if peak_rms > 1e-8 else 0.0
              for v in rms]
    palette = ("#3366ff", "#00c8c8", "#ff6600", "#cc33ff")
    sections: list[Section] = []
    for index, (start, end) in enumerate(zip(cuts, cuts[1:])):
        indices = [i for i, t in enumerate(times) if start <= t < end]
        level = round(sum(energy[i] for i in indices) / len(indices), 6)
        budget = round(.1 + .9 * level, 6) if level > 0 else 0.0
        previous = sections[-1].energy if sections else level
        marker = ("build" if level > previous + .15 else
                  "drop" if level < previous - .15 else "steady")
        hue = hues[indices[0]]
        families = (("base", "motion") if level < .45
                    else ("base", "motion", "texture", "accent"))
        sections.append(Section(
            f"section_{index:03d}_{start:08d}", start, end, level,
            budget, budget, (palette[hue % 4], "#ffffff"), families, marker))
    # Intentional restraint is tied to near-absolute silence, not quiet verses.
    silent = [(t, min(duration, t + frame_ms))
              for t, value in zip(times, rms) if value <= 1e-7]
    restraint: list[tuple[int, int]] = []
    for start, end in silent:
        if restraint and restraint[-1][1] == start:
            restraint[-1] = (restraint[-1][0], end)
        else:
            restraint.append((start, end))
    curve = tuple((min(duration, t + frame_ms // 2), e)
                  for t, e in zip(times, energy))
    curve = ((0, energy[0]), *curve, (duration, energy[-1]))
    warnings: tuple[str, ...] = (
        ("short_audio_single_section",) if duration < minimum_ms else ())
    if peak_rms <= 1e-8:
        warnings += ("silent_audio",)
    return SectionPlan(duration, tuple(sections), tuple(restraint),
                       tuple(curve), warnings)
