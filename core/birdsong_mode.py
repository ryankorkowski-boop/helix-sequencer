from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import wave

from core.lazy_imports import LazyModule


np = LazyModule("numpy")


@dataclass(frozen=True)
class BirdsongMetrics:
    duration_s: float
    low_ratio: float
    mid_ratio: float
    high_ratio: float
    flux_density: float
    chirp_density: float


@dataclass(frozen=True)
class BirdsongTaskPreset:
    name: str
    profile: str
    description: str
    runtime_args: list[str]
    phase: str
    target_xsq_name: str


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def analyze_audio(audio_path: Path) -> BirdsongMetrics:
    with wave.open(str(audio_path), "rb") as reader:
        frame_count = reader.getnframes()
        sample_rate = float(reader.getframerate() or 44100)
        channels = int(reader.getnchannels() or 1)
        sample_width = int(reader.getsampwidth() or 2)
        raw = reader.readframes(frame_count)

    if sample_width != 2:
        raise RuntimeError(f"Unsupported WAV sample width for birdsong analysis: {sample_width}")

    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    if channels > 1:
        pcm = pcm.reshape(-1, channels).mean(axis=1)
    signal = pcm / 32768.0
    duration_s = max(0.001, float(len(signal)) / sample_rate)

    frame = 2048
    hop = 1024
    if len(signal) < frame:
        signal = np.pad(signal, (0, frame - len(signal)))

    window = np.hanning(frame).astype(np.float32)
    spectra: list[np.ndarray] = []
    for start in range(0, len(signal) - frame + 1, hop):
        chunk = signal[start : start + frame] * window
        spec = np.abs(np.fft.rfft(chunk)).astype(np.float32)
        spectra.append(spec)

    if not spectra:
        return BirdsongMetrics(duration_s=duration_s, low_ratio=0.33, mid_ratio=0.33, high_ratio=0.34, flux_density=0.0, chirp_density=0.0)

    stack = np.stack(spectra)
    freqs = np.fft.rfftfreq(frame, d=1.0 / sample_rate)
    low_band = stack[:, freqs < 500.0].sum(axis=1)
    mid_band = stack[:, (freqs >= 500.0) & (freqs < 2500.0)].sum(axis=1)
    high_band = stack[:, freqs >= 2500.0].sum(axis=1)
    total = low_band + mid_band + high_band + 1e-9

    low_ratio = float(low_band.mean() / total.mean())
    mid_ratio = float(mid_band.mean() / total.mean())
    high_ratio = float(high_band.mean() / total.mean())
    high_frame_ratio = high_band / total
    chirp_density = float(np.mean(high_frame_ratio >= 0.34))

    if stack.shape[0] < 2:
        flux_density = 0.0
    else:
        norm = stack / np.maximum(1e-9, stack.sum(axis=1, keepdims=True))
        deltas = np.diff(norm, axis=0)
        flux = np.maximum(deltas, 0.0).sum(axis=1)
        flux_density = float(np.mean(flux) * 40.0)

    return BirdsongMetrics(
        duration_s=duration_s,
        low_ratio=_clip01(low_ratio),
        mid_ratio=_clip01(mid_ratio),
        high_ratio=_clip01(high_ratio),
        flux_density=max(0.0, flux_density),
        chirp_density=_clip01(chirp_density),
    )


def _birdsong_runtime_args(metrics: BirdsongMetrics) -> list[str]:
    percussive_bias = _clip01(metrics.low_ratio + (metrics.flux_density / 40.0))
    melody_bias = _clip01((metrics.high_ratio * 0.8) + (metrics.chirp_density * 0.6))
    feel = "percussive" if percussive_bias >= 0.58 else "balanced"
    chase_style = "wave" if melody_bias >= 0.48 else "group_to_group"
    palette_mode = "cool" if metrics.high_ratio >= 0.36 else "christmas"
    return [
        "--feel",
        feel,
        "--density",
        f"{1.02 + (metrics.flux_density * 0.0025):.3f}",
        "--speed",
        f"{1.08 + (metrics.chirp_density * 0.38):.3f}",
        "--randomness",
        f"{0.06 + (metrics.high_ratio * 0.10):.3f}",
        "--melody-density",
        f"{1.25 + (melody_bias * 0.45):.3f}",
        "--bass-bias",
        f"{1.12 + (metrics.low_ratio * 0.62):.3f}",
        "--darkness",
        f"{0.82 - (metrics.high_ratio * 0.18):.3f}",
        "--flash-guard",
        f"{0.78 + (metrics.low_ratio * 0.12):.3f}",
        "--keyboard-mix",
        f"{1.08 + (melody_bias * 0.22):.3f}",
        "--spatial-awareness",
        f"{0.26 + (melody_bias * 0.38):.3f}",
        "--chase-style",
        chase_style,
        "--layering-mode",
        "smart_layer",
        "--palette-mode",
        palette_mode,
        "--polish",
        "--variants",
        "1",
        "--auto-shortlist",
    ]


def _legacy_plus_runtime_args(metrics: BirdsongMetrics) -> list[str]:
    return [
        "--feel",
        "balanced",
        "--density",
        f"{0.96 + (metrics.low_ratio * 0.18):.3f}",
        "--speed",
        f"{0.96 + (metrics.high_ratio * 0.14):.3f}",
        "--randomness",
        f"{0.03 + (metrics.chirp_density * 0.08):.3f}",
        "--melody-density",
        f"{1.08 + (metrics.high_ratio * 0.28):.3f}",
        "--bass-bias",
        f"{1.18 + (metrics.low_ratio * 0.54):.3f}",
        "--darkness",
        f"{1.02 - (metrics.high_ratio * 0.09):.3f}",
        "--flash-guard",
        "0.84",
        "--keyboard-mix",
        "0.98",
        "--spatial-awareness",
        "0.14",
        "--chase-style",
        "left_to_right",
        "--layering-mode",
        "replace",
        "--palette-mode",
        "template",
        "--polish",
        "--variants",
        "1",
        "--auto-shortlist",
    ]


def _heavy_logic_runtime_args(metrics: BirdsongMetrics) -> list[str]:
    energy_bias = _clip01((metrics.low_ratio * 0.65) + (metrics.flux_density / 45.0))
    return [
        "--feel",
        "aggressive",
        "--density",
        f"{1.22 + (energy_bias * 0.18):.3f}",
        "--speed",
        f"{1.24 + (metrics.chirp_density * 0.20):.3f}",
        "--randomness",
        f"{0.08 + (metrics.high_ratio * 0.14):.3f}",
        "--melody-density",
        f"{1.36 + (metrics.high_ratio * 0.30):.3f}",
        "--bass-bias",
        f"{1.36 + (metrics.low_ratio * 0.74):.3f}",
        "--darkness",
        f"{0.74 - (metrics.high_ratio * 0.12):.3f}",
        "--flash-guard",
        "0.68",
        "--keyboard-mix",
        "1.24",
        "--spatial-awareness",
        "0.52",
        "--chase-style",
        "group_to_group",
        "--layering-mode",
        "additive",
        "--palette-mode",
        "neon",
        "--polish",
        "--variants",
        "1",
        "--auto-shortlist",
    ]


def default_task_presets(audio_path: Path) -> list[BirdsongTaskPreset]:
    metrics = analyze_audio(audio_path)
    return [
        BirdsongTaskPreset(
            name="birdmap",
            profile="master",
            description="Birdsong-centric mapping and runtime routing.",
            runtime_args=_birdsong_runtime_args(metrics),
            phase="allmodels",
            target_xsq_name="birdmap.xsq",
        ),
        BirdsongTaskPreset(
            name="legacyplusbirdinputlegacyoutput",
            profile="v27.1",
            description="Legacy sequencing profile with birdsong-informed input tuning.",
            runtime_args=_legacy_plus_runtime_args(metrics),
            phase="allmodels",
            target_xsq_name="legacyplusbirdinputlegacyoutput.xsq",
        ),
        BirdsongTaskPreset(
            name="heavylogicwhatever",
            profile="master",
            description="Heavy logic stress run with aggressive layering and motion.",
            runtime_args=_heavy_logic_runtime_args(metrics),
            phase="allmodels",
            target_xsq_name="heavylogicwhatever.xsq",
        ),
        BirdsongTaskPreset(
            name="helixville3d_balancedbird",
            profile="master",
            description="3D Helixville balanced birdsong mapping pass.",
            runtime_args=_birdsong_runtime_args(metrics),
            phase="helixville_3d",
            target_xsq_name="helixville3d_balancedbird.xsq",
        ),
        BirdsongTaskPreset(
            name="helixville3d_percussivelegacyblend",
            profile="v27.2",
            description="3D Helixville percussive legacy-leaning blend run.",
            runtime_args=_legacy_plus_runtime_args(metrics),
            phase="helixville_3d",
            target_xsq_name="helixville3d_percussivelegacyblend.xsq",
        ),
    ]
