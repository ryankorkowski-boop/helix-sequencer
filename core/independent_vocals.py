"""Evidence-gated, independent vocal activity for Helix singing performers.

This module consumes *already separated* mono PCM WAV stems. It never pretends
that a four-stem Demucs 'vocals.wav' contains two independent singers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import json
import math
import wave


@dataclass(frozen=True)
class VocalWindow:
    start_ms: int
    end_ms: int
    confidence: float


@dataclass(frozen=True)
class VocalTrack:
    performer: str
    source: str
    sha256: str
    sample_rate: int
    windows: tuple[VocalWindow, ...]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_mono_pcm(path: Path) -> tuple[int, "array.array"]:
    with wave.open(str(path), "rb") as wav:
        channels, width, rate, frames = (wav.getnchannels(), wav.getsampwidth(),
                                          wav.getframerate(), wav.getnframes())
        if channels != 1 or width != 2 or rate < 8000:
            raise ValueError(f"{path}: expected mono 16-bit PCM WAV at >= 8 kHz")
        import array
        samples = array.array("h")
        samples.frombytes(wav.readframes(frames))
        if __import__("sys").byteorder != "little":
            samples.byteswap()
    return rate, samples


def _stream_vocal_features(path: Path, *, hop_ms: int = 20,
                           fingerprint_budget: int = 50000,
                           fingerprint_stride: int | None = None) -> tuple[int, int, list[float], list[float]]:
    """Stream PCM once: small RMS envelope and bounded sparse fingerprint.

    The fingerprint samples fixed absolute positions, allowing correlations
    between separately streamed stems without retaining full-song PCM.
    """
    import array
    import sys
    with wave.open(str(path), "rb") as wav:
        channels, width, rate, frames = (wav.getnchannels(), wav.getsampwidth(),
                                          wav.getframerate(), wav.getnframes())
        if channels != 1 or width != 2 or rate < 8000:
            raise ValueError(f"{path}: expected mono 16-bit PCM WAV at >= 8 kHz")
        hop = max(1, round(rate * hop_ms / 1000))
        stride = fingerprint_stride or max(1, (frames + fingerprint_budget - 1) // fingerprint_budget)
        if stride < 1:
            raise ValueError("fingerprint_stride must be positive")
        energies: list[float] = []
        fingerprint: list[float] = []
        offset = 0
        while offset < frames:
            samples = array.array("h")
            samples.frombytes(wav.readframes(min(hop, frames - offset)))
            if sys.byteorder != "little":
                samples.byteswap()
            if not samples:
                break
            energies.append(math.sqrt(sum(x * x for x in samples) / len(samples)) / 32768.0)
            for j in range((-offset) % stride, len(samples), stride):
                fingerprint.append(float(samples[j]))
            offset += len(samples)
    return rate, frames, energies, fingerprint


def _activity_from_energies(energies: list[float], duration_ms: int, *,
                            hop_ms: int = 20, threshold_db: float = -34.0,
                            min_duration_ms: int = 100,
                            max_gap_ms: int = 80) -> tuple[VocalWindow, ...]:
    if not energies:
        return ()
    peak = max(energies)
    if peak < 1e-4:
        return ()
    floor = max(10 ** (threshold_db / 20), peak * 0.035)
    active = [e >= floor for e in energies]
    gap_frames = max(0, round(max_gap_ms / hop_ms))
    i = 0
    while i < len(active):
        if active[i]:
            i += 1
            continue
        j = i
        while j < len(active) and not active[j]:
            j += 1
        if i > 0 and j < len(active) and j - i <= gap_frames:
            active[i:j] = [True] * (j - i)
        i = j
    windows = []
    start = None
    for i, on in enumerate(active + [False]):
        if on and start is None:
            start = i
        elif not on and start is not None:
            a, b = start * hop_ms, min(duration_ms, i * hop_ms)
            if b - a >= min_duration_ms:
                strength = sum(energies[start:i]) / max(1, i - start)
                windows.append(VocalWindow(a, b, round(min(1.0, strength / max(peak, 1e-9)), 3)))
            start = None
    return tuple(windows)


def _activity(samples: "array.array", rate: int, *,
              hop_ms: int = 20, threshold_db: float = -34.0,
              min_duration_ms: int = 100, max_gap_ms: int = 80) -> tuple[VocalWindow, ...]:
    hop = max(1, round(rate * hop_ms / 1000))
    energies = []
    for start in range(0, len(samples), hop):
        block = samples[start:start + hop]
        energies.append(math.sqrt(sum(x * x for x in block) / len(block)) / 32768.0)
    if not energies:
        return ()
    peak = max(energies)
    if peak < 1e-4:
        return ()
    floor = max(10 ** (threshold_db / 20), peak * 0.035)
    active = [e >= floor for e in energies]
    gap_frames = max(0, round(max_gap_ms / hop_ms))
    i = 0
    while i < len(active):
        if active[i]:
            i += 1
            continue
        j = i
        while j < len(active) and not active[j]:
            j += 1
        if i > 0 and j < len(active) and j - i <= gap_frames:
            active[i:j] = [True] * (j - i)
        i = j
    windows = []
    start = None
    for i, on in enumerate(active + [False]):
        if on and start is None:
            start = i
        elif not on and start is not None:
            a, b = start * hop_ms, min(round(len(samples) * 1000 / rate), i * hop_ms)
            if b - a >= min_duration_ms:
                strength = sum(energies[start:i]) / max(1, i - start)
                windows.append(VocalWindow(a, b, round(min(1.0, strength / max(peak, 1e-9)), 3)))
            start = None
    return tuple(windows)


def analyze_independent_vocals(lead_path: str | Path, harmony_path: str | Path,
                               *, output_json: str | Path | None = None) -> dict:
    """Accept two separately sourced singer stems, reject duplicated vocal mixtures.

    A verified separation algorithm must create the two inputs upstream. The
    gate deliberately fails closed if two paths contain identical PCM.
    """
    lead_path, harmony_path = Path(lead_path), Path(harmony_path)
    # Use the same absolute sample indices for both singer fingerprints, even
    # when their WAV durations differ by the permitted 50 ms tolerance.
    with wave.open(str(lead_path), "rb") as lead_wav, wave.open(str(harmony_path), "rb") as harmony_wav:
        common_stride = max(1, (max(lead_wav.getnframes(), harmony_wav.getnframes()) + 49999) // 50000)
    lead_rate, lead_frames, lead_energies, lead_fingerprint = _stream_vocal_features(
        lead_path, fingerprint_stride=common_stride)
    harmony_rate, harmony_frames, harmony_energies, harmony_fingerprint = _stream_vocal_features(
        harmony_path, fingerprint_stride=common_stride)
    if lead_rate != harmony_rate:
        raise ValueError("Vocal stems have different sample rates; align/resample first")
    if abs(lead_frames - harmony_frames) > round(lead_rate * 0.05):
        raise ValueError("Vocal stems differ in duration by more than 50 ms")
    lead_sha = _file_sha256(lead_path)
    harmony_sha = _file_sha256(harmony_path)
    if lead_sha == harmony_sha:
        raise ValueError("Duplicate vocal stems: independent harmony not established")
    lead_windows = _activity_from_energies(lead_energies, round(lead_frames * 1000 / lead_rate))
    harmony_windows = _activity_from_energies(harmony_energies, round(harmony_frames * 1000 / harmony_rate))
    if not lead_windows:
        raise ValueError("Lead stem is silent; no lead singer can be verified")
    if not harmony_windows:
        raise ValueError("Harmony stem is silent; no second singer can be verified")
    dot = aa = bb = 0.0
    for a, b in zip(lead_fingerprint, harmony_fingerprint):
        dot += a * b
        aa += a * a
        bb += b * b
    corr = abs(dot) / math.sqrt(aa * bb) if aa > 0 and bb > 0 else 0.0
    if corr >= 0.995:
        raise ValueError("Vocal stems are near-identical (possibly gain-scaled copies)")
    tracks = (
        VocalTrack("lead_singer", str(lead_path), lead_sha, lead_rate, lead_windows),
        VocalTrack("harmony_singer", str(harmony_path), harmony_sha, harmony_rate,
                   harmony_windows),
    )
    result = {"schema": "helix.independent-vocals.v1", "status": "distinct_stem_inputs",
              "independence": "duplicate_rejection_only_not_voice_identity_proof",
              "tracks": [asdict(t) for t in tracks]}
    if output_json is not None:
        path = Path(output_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
