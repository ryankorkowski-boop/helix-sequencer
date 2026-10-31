"""Master audio features, extracted without changing DSP or sample clocks.

The XSQ module still owns public Audio/profile settings and low-level timing
helpers. Reading them through base preserves runtime overrides by existing
callers. No import of the effect engine or layout-specific placement is needed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from importlib.util import find_spec
from importlib.metadata import PackageNotFoundError, version
import marshal
import os
import platform
from pathlib import Path
from core.lazy_imports import LazyModule
from core.stage_metrics import timed_stage
from xlights import xsq_writer as base

librosa = LazyModule("librosa")
np = LazyModule("numpy")


def _cache_parameters(kind: str, **parameters) -> dict:
    """Bind feature identity to DSP parameters, actual code and library versions."""
    implementation = hashlib.sha256()
    for module_name, path in (
            (__name__, Path(__file__)), (base.__name__, Path(base.__file__)),
            ("core.bounded_audio", Path(__file__).with_name("bounded_audio.py"))):
        try:
            code_bytes = path.read_bytes()
        except OSError:
            # Frozen/zip loaders retain bytecode even when no .py exists.
            spec = find_spec(module_name)
            code = spec.loader.get_code(module_name) if spec and hasattr(spec.loader, "get_code") else None
            if code is None:
                raise ValueError(f"Cannot fingerprint cached DSP module: {module_name}")
            code_bytes = marshal.dumps(code)
        implementation.update(module_name.encode() + b"\0" + code_bytes)
    libraries = {}
    for name in ("numpy", "librosa", "scipy", "numba", "llvmlite", "soundfile", "soxr", "audioread", "aubio"):
        try:
            libraries[name] = version(name)
        except PackageNotFoundError:
            libraries[name] = None
    return {"kind": kind, "implementation_sha256": implementation.hexdigest(),
            "libraries": libraries, "python": platform.python_version(),
            "platform": (platform.system(), platform.machine()), "hop": base.HOP_MS,
            "fast_pitch": base.USE_FAST_PITCH, **parameters}


def _validate_arrays(arrays, dimensions):
    if arrays.keys() != dimensions.keys():
        raise ValueError("Incomplete audio feature cache")
    for name, ndim in dimensions.items():
        value = arrays[name]
        if value.ndim != ndim or value.dtype.kind not in "fiu":
            raise ValueError(f"Invalid audio feature cache array: {name}")


@timed_stage("audio.load_features")
def analyze_audio(audio_path: Path) -> base.Audio:
    """Original feature pipeline; optional content-addressed reuse across runs.

    HELIX_AUDIO_CACHE_DIR opts in. Raw signal and reduced features retain exact
    dtypes, shapes, NaN pitch sentinels and sample clocks; no pickle is loaded.
    """
    cache_dir = os.environ.get("HELIX_AUDIO_CACHE_DIR")
    if not cache_dir:
        return _compute_audio(audio_path)
    from core.audio_analysis_cache import audio_cache_key, cached_arrays

    dimensions = {name: 1 for name in (
        "y", "onset_ms", "beat_ms", "times_s", "centroid", "rms01", "bass01", "vocal01", "pitch_hz")}
    dimensions.update(sr=0, dur_s=0)

    def compute():
        audio = _compute_audio(audio_path)
        return {name: np.asarray(getattr(audio, name)) for name in dimensions}

    def validate(arrays):
        _validate_arrays(arrays, dimensions)
        if arrays["sr"] <= 0 or not np.isfinite(arrays["dur_s"]) or arrays["dur_s"] < 0:
            raise ValueError("Invalid cached audio rate/duration")
        count = len(arrays["times_s"])
        if any(len(arrays[name]) != count for name in (
                "centroid", "rms01", "bass01", "vocal01", "pitch_hz")):
            raise ValueError("Cached feature clocks disagree")

    key = audio_cache_key(audio_path, _cache_parameters("master_audio_v1"))
    arrays = cached_arrays(cache_dir, key, compute, validate=validate)
    values = dict(arrays)
    values.update(sr=int(arrays["sr"]), dur_s=float(arrays["dur_s"]),
                  onset_ms=arrays["onset_ms"].tolist(), beat_ms=arrays["beat_ms"].tolist())
    return base.Audio(**values)


@timed_stage("audio.harmonic")
def analyze_harmonic(audio: base.Audio, *, audio_path: Path | None = None) -> HarmonicData:
    cache_dir = os.environ.get("HELIX_AUDIO_CACHE_DIR")
    if not cache_dir or audio_path is None:
        return _compute_harmonic(audio)
    from core.audio_analysis_cache import audio_cache_key, cached_arrays

    dimensions = {"times_s": 1, "cqt_mag": 2, "pitch_hz": 2, "pitch_mag": 2, "base_midi": 0}

    def compute():
        harmonic = _compute_harmonic(audio)
        return {name: np.asarray(getattr(harmonic, name)) for name in dimensions}

    def validate(arrays):
        _validate_arrays(arrays, dimensions)
        count = len(arrays["times_s"])
        # CQT resampling can retain an extra frame relative to the STFT pitch
        # grid. Keep both original shapes; consumers already handle that seam.
        if (arrays["cqt_mag"].shape != (60, count)
                or arrays["pitch_hz"].shape != arrays["pitch_mag"].shape):
            raise ValueError("Cached harmonic clocks disagree")

    # The file identifies the recording; the actual samples additionally guard
    # API callers that edit the in-memory audio before requesting harmonics.
    sample_sha = hashlib.sha256(memoryview(np.ascontiguousarray(audio.y)).cast("B")).hexdigest()
    key = audio_cache_key(audio_path, _cache_parameters(
        "master_harmonic_v1", sr=audio.sr, duration=audio.dur_s,
        sample_dtype=audio.y.dtype.str, sample_shape=audio.y.shape, sample_sha256=sample_sha))
    arrays = cached_arrays(cache_dir, key, compute, validate=validate)
    values = dict(arrays, base_midi=int(arrays["base_midi"]))
    return HarmonicData(**values)

@dataclass
class HarmonicData:
    times_s: np.ndarray
    cqt_mag: np.ndarray
    base_midi: int
    pitch_hz: np.ndarray
    pitch_mag: np.ndarray


@dataclass
class MultiBandAnalysis:
    sub_bass_marks: list[int]
    bass_marks: list[int]
    mid_marks: list[int]
    high_marks: list[int]
    spectral_flux_marks: list[int]
    loud_marks: list[int]
    quiet_windows: list[tuple[int, int]]
    dominance_marks: dict[str, list[int]]
    frame_times_s: np.ndarray | None = None
    spectral_centroid01: np.ndarray | None = None
    spectral_bandwidth01: np.ndarray | None = None
    spectral_contrast01: np.ndarray | None = None
    spectral_flatness01: np.ndarray | None = None
    spectral_flux01: np.ndarray | None = None
    mfcc_motion01: np.ndarray | None = None
    chroma_stability01: np.ndarray | None = None
    tonnetz_motion01: np.ndarray | None = None
    tempo_bpm: float = 0.0
    genre_hint: str = "unknown"
    mood_hint: str = "neutral"
    descriptor_summary: dict[str, float] = field(default_factory=dict)
    section_profiles: dict[str, dict[str, float | str]] = field(default_factory=dict)


def _compute_audio(audio_path: Path) -> base.Audio:
    base.log(f"Loading audio: {audio_path.name}")
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    dur = float(len(y) / sr)
    base.log(f"SR={sr} duration={dur:.2f}s")

    hop = base.HOP_MS
    magnitude = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    S = magnitude**2
    mel = librosa.feature.melspectrogram(S=S, sr=sr, n_mels=128, fmin=20, fmax=11025)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    times_s = librosa.frames_to_time(np.arange(mel.shape[1]), sr=sr, hop_length=hop)

    # onset_strength(y=...) and spectral_centroid(y=...) each decoded this
    # same frame grid through a fresh STFT. Preserve onset_strength's default
    # mel bank (different from the display's fmin=20 bank) and dB reference.
    onset_mel = librosa.feature.melspectrogram(S=S, sr=sr)
    onset_env = librosa.onset.onset_strength(
        S=librosa.power_to_db(onset_mel), sr=sr, hop_length=hop)
    if dur > 30:
        from core.bounded_audio import dominant_pitch
        # Each centroid/pitch frame is independent. Reduce it while its bounded
        # workspace is live, then free the full spectra before beat planning.
        centroid = np.empty(magnitude.shape[1], dtype=float)
        for start in range(0, len(centroid), 512):
            centroid[start:start+512] = librosa.feature.spectral_centroid(
                S=magnitude[:, start:start+512], sr=sr, hop_length=hop)[0]
        pitch_hz = (dominant_pitch(S, sr=sr, hop=hop,
                    fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"))
                    if base.USE_FAST_PITCH else np.full(len(times_s), np.nan))
        del magnitude, S, onset_mel
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, hop_length=hop,
        backtrack=False, units="frames",
        pre_max=3, post_max=3, pre_avg=3, post_avg=3,
        delta=0.08, wait=0
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop)
    onset_ms = [base.ms(t) for t in onset_times.tolist()]

    _, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop, units="frames")
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)
    beat_ms = [base.ms(t) for t in beat_times.tolist()]
    if base._aubio_module() is not None:
        try:
            beat_ms_aubio = base._aubio_beats(y, sr, hop)
            if len(beat_ms_aubio) >= 4:
                beat_ms = beat_ms_aubio
        except Exception:
            pass

    if dur <= 30:
        centroid = librosa.feature.spectral_centroid(S=magnitude, sr=sr, hop_length=hop)[0]
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms01 = base.norm01(rms)

    mel_freqs = librosa.mel_frequencies(n_mels=128, fmin=20, fmax=11025)
    bass_bins = np.where((mel_freqs >= 20) & (mel_freqs <= 180))[0]
    vocal_bins = np.where((mel_freqs >= 300) & (mel_freqs <= 3000))[0]
    bass_db = mel_db[bass_bins, :].mean(axis=0) if len(bass_bins) else mel_db.mean(axis=0)
    vocal_db = mel_db[vocal_bins, :].mean(axis=0) if len(vocal_bins) else mel_db.mean(axis=0)
    bass01 = base.norm01(bass_db)
    vocal01 = base.norm01(vocal_db)

    if dur > 30:
        pass  # Already reduced before releasing the full spectra above.
    elif base.USE_FAST_PITCH:
        mags = np.sqrt(S)
        pitches, pmags = librosa.piptrack(
            S=mags, sr=sr, hop_length=hop,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7")
        )
        pitch_hz = np.full((pitches.shape[1],), np.nan, dtype=float)
        columns = np.arange(pitches.shape[1])
        selected = pitches[np.argmax(pmags, axis=0), columns]
        pitch_hz[:] = np.where(selected > 0, selected, np.nan)
    else:
        pitch_hz = np.full((len(times_s),), np.nan, dtype=float)

    return base.Audio(sr=sr, y=y, dur_s=dur,
                 onset_ms=onset_ms, beat_ms=beat_ms,
                 times_s=np.asarray(times_s),
                 centroid=np.asarray(centroid),
                 rms01=np.asarray(rms01),
                 bass01=np.asarray(bass01),
                 vocal01=np.asarray(vocal01),
                 pitch_hz=np.asarray(pitch_hz))


def _compute_harmonic(audio: base.Audio) -> HarmonicData:
    from core.bounded_audio import hpss
    y_harm, percussive = hpss(audio.y, audio.sr)
    del percussive
    hop = base.HOP_MS
    cqt_mag = np.abs(
        librosa.cqt(
            y_harm,
            sr=audio.sr,
            hop_length=hop,
            fmin=librosa.note_to_hz("C2"),
            n_bins=60,
            bins_per_octave=12,
        )
    )
    # Supplement CQT with piptrack so polyphonic note picking can use true pitch bins too.
    stft_mag = np.abs(librosa.stft(y_harm, n_fft=2048, hop_length=hop))
    if audio.dur_s > 30:
        from core.bounded_audio import pitch_matrices
        pitch_hz, pitch_mag = pitch_matrices(stft_mag, sr=audio.sr, hop_length=hop, fmin=65.0, fmax=2800.0)
    else:
        pitch_hz, pitch_mag = librosa.piptrack(S=stft_mag, sr=audio.sr, hop_length=hop, fmin=65.0, fmax=2800.0)
    times_s = librosa.frames_to_time(np.arange(cqt_mag.shape[1]), sr=audio.sr, hop_length=hop)
    return HarmonicData(
        times_s=np.asarray(times_s),
        cqt_mag=np.asarray(cqt_mag),
        base_midi=36,
        pitch_hz=np.asarray(pitch_hz),
        pitch_mag=np.asarray(pitch_mag),
    )


def derive_dynamic_marks(audio: base.Audio) -> tuple[list[int], list[int], list[int]]:
    if audio.times_s.size == 0:
        return ([], [], [])
    energy_peaks = base.compress_times_ms(
        [base.ms(t) for t in base.peak_times(audio.times_s, audio.rms01, 0.09, 12)],
        base.scaled_gap(120),
    )
    rise_curve = np.clip(np.gradient(np.asarray(audio.rms01, dtype=float)), 0.0, None)
    fall_curve = np.clip(-np.gradient(np.asarray(audio.rms01, dtype=float)), 0.0, None)
    build_lifts = base.compress_times_ms(
        [base.ms(t) for t in base.peak_times(audio.times_s, rise_curve, 0.025, 10)],
        base.scaled_gap(110),
    )
    releases = base.compress_times_ms(
        [base.ms(t) for t in base.peak_times(audio.times_s, fall_curve, 0.025, 10)],
        base.scaled_gap(110),
    )
    return (energy_peaks, build_lifts, releases)


def _series_peak_marks(
    times_s: np.ndarray,
    series: np.ndarray,
    *,
    threshold: float,
    wait: int,
    gap_ms: int,
) -> list[int]:
    if times_s.size == 0 or series.size == 0:
        return []
    usable = min(len(times_s), len(series))
    if usable <= 0:
        return []
    ts = np.asarray(times_s[:usable], dtype=float)
    vals = np.asarray(series[:usable], dtype=float)
    if not np.isfinite(vals).any():
        return []
    norm = base.norm01(np.nan_to_num(vals, nan=0.0, posinf=0.0, neginf=0.0))
    marks = [base.ms(t) for t in base.peak_times(ts, norm, threshold, max(1, int(wait)))]
    return base.compress_times_ms(marks, max(10, int(gap_ms)))


def _quiet_windows_from_rms(
    times_s: np.ndarray,
    rms01: np.ndarray,
    *,
    threshold: float,
    min_window_ms: int,
) -> list[tuple[int, int]]:
    if times_s.size == 0 or rms01.size == 0:
        return []
    usable = min(len(times_s), len(rms01))
    if usable <= 1:
        return []
    ts = np.asarray(times_s[:usable], dtype=float)
    vals = np.asarray(rms01[:usable], dtype=float)
    windows: list[tuple[int, int]] = []
    start_idx: int | None = None
    for idx, value in enumerate(vals):
        if value <= threshold:
            if start_idx is None:
                start_idx = idx
        elif start_idx is not None:
            st = base.ms(ts[start_idx])
            en = base.ms(ts[max(start_idx + 1, idx)])
            if (en - st) >= min_window_ms:
                windows.append((st, en))
            start_idx = None
    if start_idx is not None:
        st = base.ms(ts[start_idx])
        en = base.ms(ts[-1])
        if (en - st) >= min_window_ms:
            windows.append((st, en))
    return windows


def _align_curve(values: np.ndarray, target_len: int) -> np.ndarray:
    if target_len <= 0:
        return np.asarray([], dtype=float)
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return np.zeros(target_len, dtype=float)
    if arr.size == target_len:
        return arr
    src = np.linspace(0.0, 1.0, num=arr.size, endpoint=True)
    dst = np.linspace(0.0, 1.0, num=target_len, endpoint=True)
    return np.interp(dst, src, arr)


def _marks_density_per_minute(marks: list[int], duration_s: float) -> float:
    if duration_s <= 0.0:
        return 0.0
    return float(len(marks)) / max(1e-6, duration_s / 60.0)


def estimate_tempo_bpm(beat_ms: list[int]) -> float:
    if len(beat_ms) < 2:
        return 0.0
    deltas = np.diff(np.asarray(beat_ms, dtype=float))
    if deltas.size == 0:
        return 0.0
    median_delta = float(np.median(deltas))
    if median_delta <= 1.0:
        return 0.0
    return float(base.clamp(60000.0 / median_delta, 45.0, 220.0))


def classify_mir_genre(summary: dict[str, float], *, tempo_bpm: float, rms_mean: float) -> str:
    bass_density = float(summary.get("bass_density", 0.0))
    sub_density = float(summary.get("sub_bass_density", 0.0))
    high_density = float(summary.get("high_density", 0.0))
    flux_density = float(summary.get("flux_density", 0.0))
    contrast_mean = float(summary.get("contrast_mean", 0.0))
    flatness_mean = float(summary.get("flatness_mean", 0.0))
    mfcc_motion_mean = float(summary.get("mfcc_motion_mean", 0.0))
    chroma_stability_mean = float(summary.get("chroma_stability_mean", 0.0))
    tonnetz_motion_mean = float(summary.get("tonnetz_motion_mean", 0.0))
    if tempo_bpm >= 124.0 and bass_density >= 48.0 and flux_density >= 60.0:
        return "edm"
    if flatness_mean >= 0.50 and contrast_mean >= 0.55 and tempo_bpm >= 92.0:
        return "rock"
    if sub_density >= 52.0 and high_density <= 34.0 and tempo_bpm < 108.0:
        return "hip_hop"
    if chroma_stability_mean >= 0.62 and mfcc_motion_mean <= 0.32 and flux_density <= 38.0:
        return "ambient"
    if tonnetz_motion_mean <= 0.22 and tempo_bpm < 92.0 and rms_mean <= 0.38:
        return "classical"
    return "pop"


def classify_mir_mood(summary: dict[str, float], *, rms_mean: float) -> str:
    centroid_mean = float(summary.get("centroid_mean", 0.0))
    flux_density = float(summary.get("flux_density", 0.0))
    chroma_stability_mean = float(summary.get("chroma_stability_mean", 0.0))
    tonnetz_motion_mean = float(summary.get("tonnetz_motion_mean", 0.0))
    arousal = base.clamp((0.50 * rms_mean) + (0.30 * min(1.0, flux_density / 95.0)) + (0.20 * centroid_mean), 0.0, 1.0)
    valence = base.clamp((0.55 * chroma_stability_mean) + (0.30 * (1.0 - tonnetz_motion_mean)) + (0.15 * centroid_mean), 0.0, 1.0)
    if arousal >= 0.74 and valence >= 0.52:
        return "uplifting"
    if arousal >= 0.74:
        return "intense"
    if arousal <= 0.34 and valence <= 0.44:
        return "brooding"
    if arousal <= 0.34:
        return "calm"
    return "balanced"


@timed_stage("audio.multiband")
def derive_multiband_analysis(audio: base.Audio) -> MultiBandAnalysis:
    if audio.y.size == 0 or audio.sr <= 0:
        return MultiBandAnalysis([], [], [], [], [], [], [], {})

    hop = max(1, int(base.HOP_MS))
    n_fft = 2048
    spectrum = np.abs(librosa.stft(audio.y, n_fft=n_fft, hop_length=hop)) ** 2
    if spectrum.size == 0:
        return MultiBandAnalysis([], [], [], [], [], [], [], {})
    frame_count = int(spectrum.shape[1])
    freqs = librosa.fft_frequencies(sr=audio.sr, n_fft=n_fft)
    frame_times = librosa.frames_to_time(np.arange(frame_count), sr=audio.sr, hop_length=hop)

    def band_env(low_hz: float, high_hz: float) -> np.ndarray:
        bins = np.where((freqs >= low_hz) & (freqs < high_hz))[0]
        if len(bins) == 0:
            return np.zeros(frame_count, dtype=float)
        raw = np.asarray(spectrum[bins, :].mean(axis=0), dtype=float)
        return base.norm01(raw)

    sub_env = band_env(20.0, 60.0)
    bass_env = band_env(60.0, 150.0)
    mid_env = band_env(150.0, 2000.0)
    high_env = band_env(2000.0, 12000.0)

    sub_marks = _series_peak_marks(frame_times, sub_env, threshold=0.46, wait=9, gap_ms=120)
    bass_marks = _series_peak_marks(frame_times, bass_env, threshold=0.42, wait=8, gap_ms=105)
    mid_marks = _series_peak_marks(frame_times, mid_env, threshold=0.38, wait=7, gap_ms=95)
    high_marks = _series_peak_marks(frame_times, high_env, threshold=0.34, wait=6, gap_ms=80)

    from core.bounded_audio import positive_flux, spectral_descriptors
    flux = positive_flux(spectrum)
    flux01 = base.norm01(np.nan_to_num(np.asarray(flux, dtype=float), nan=0.0, posinf=0.0, neginf=0.0))
    flux_marks = _series_peak_marks(frame_times, flux, threshold=0.40, wait=8, gap_ms=90)

    rms = np.asarray(audio.rms01, dtype=float)
    if rms.size >= 5:
        kernel = np.asarray([1.0, 2.0, 3.0, 2.0, 1.0], dtype=float)
        rms_smoothed = np.convolve(rms, kernel / np.sum(kernel), mode="same")
    else:
        rms_smoothed = rms
    loud_marks = _series_peak_marks(audio.times_s, rms_smoothed, threshold=0.72, wait=8, gap_ms=170)
    quiet_threshold = min(0.24, max(0.08, float(np.nanpercentile(rms if rms.size else np.asarray([0.1]), 22))))
    quiet_windows = _quiet_windows_from_rms(audio.times_s, rms, threshold=quiet_threshold, min_window_ms=360)

    stacks = np.vstack(
        [
            np.asarray(sub_env, dtype=float),
            np.asarray(bass_env, dtype=float),
            np.asarray(mid_env, dtype=float),
            np.asarray(high_env, dtype=float),
        ]
    )
    band_names = ("sub_bass", "bass", "mid", "high")
    dominance_marks: dict[str, list[int]] = {name: [] for name in band_names}
    if stacks.size:
        dominant_idx = np.argmax(stacks, axis=0)
        dominant_strength = np.max(stacks, axis=0)
        for idx, name in enumerate(band_names):
            marks = [base.ms(float(frame_times[i])) for i in range(len(frame_times)) if int(dominant_idx[i]) == idx and dominant_strength[i] >= 0.28]
            dominance_marks[name] = base.compress_times_ms(marks, base.scaled_gap(180))

    centroid, bandwidth, contrast, flatness = spectral_descriptors(spectrum, sr=audio.sr, power=True)
    centroid = _align_curve(centroid, frame_count)
    bandwidth = _align_curve(bandwidth, frame_count)
    contrast = np.asarray(contrast, dtype=float)
    contrast_curve = _align_curve(np.asarray(contrast.mean(axis=0), dtype=float), frame_count)
    flatness = _align_curve(flatness, frame_count)
    del spectrum

    mfcc_motion = np.zeros(frame_count, dtype=float)
    chroma_stability = np.zeros(frame_count, dtype=float)
    tonnetz_motion = np.zeros(frame_count, dtype=float)
    try:
        mfcc = np.asarray(librosa.feature.mfcc(y=audio.y, sr=audio.sr, hop_length=hop, n_mfcc=20), dtype=float)
        if mfcc.size:
            mfcc_delta = np.asarray(librosa.feature.delta(mfcc), dtype=float)
            mfcc_motion = _align_curve(np.mean(np.abs(mfcc_delta), axis=0), frame_count)
    except Exception:
        mfcc_motion = np.zeros(frame_count, dtype=float)
    try:
        options = {}
        if len(audio.y) > 30 * audio.sr:
            from core.bounded_audio import estimate_tuning
            options['tuning'] = estimate_tuning(audio.y, sr=audio.sr, bins_per_octave=36)
        chroma = np.asarray(librosa.feature.chroma_cqt(y=audio.y, sr=audio.sr, hop_length=hop, **options), dtype=float)
        if chroma.size:
            denom = np.sum(chroma, axis=0) + 1e-9
            chroma_stability = _align_curve(np.max(chroma, axis=0) / denom, frame_count)
            tonnetz = np.asarray(librosa.feature.tonnetz(chroma=chroma, sr=audio.sr), dtype=float)
            if tonnetz.size:
                tonnetz_delta = np.asarray(librosa.feature.delta(tonnetz), dtype=float)
                tonnetz_motion = _align_curve(np.mean(np.abs(tonnetz_delta), axis=0), frame_count)
    except Exception:
        chroma_stability = np.zeros(frame_count, dtype=float)
        tonnetz_motion = np.zeros(frame_count, dtype=float)

    centroid01 = base.norm01(np.nan_to_num(centroid, nan=0.0, posinf=0.0, neginf=0.0))
    bandwidth01 = base.norm01(np.nan_to_num(bandwidth, nan=0.0, posinf=0.0, neginf=0.0))
    contrast01 = base.norm01(np.nan_to_num(contrast_curve, nan=0.0, posinf=0.0, neginf=0.0))
    flatness01 = base.norm01(np.nan_to_num(flatness, nan=0.0, posinf=0.0, neginf=0.0))
    mfcc_motion01 = base.norm01(np.nan_to_num(mfcc_motion, nan=0.0, posinf=0.0, neginf=0.0))
    chroma_stability01 = base.norm01(np.nan_to_num(chroma_stability, nan=0.0, posinf=0.0, neginf=0.0))
    tonnetz_motion01 = base.norm01(np.nan_to_num(tonnetz_motion, nan=0.0, posinf=0.0, neginf=0.0))

    tempo_bpm = estimate_tempo_bpm(audio.beat_ms)
    duration_s = float(max(1e-6, audio.dur_s))
    descriptor_summary = {
        "centroid_mean": float(np.mean(centroid01)) if centroid01.size else 0.0,
        "bandwidth_mean": float(np.mean(bandwidth01)) if bandwidth01.size else 0.0,
        "contrast_mean": float(np.mean(contrast01)) if contrast01.size else 0.0,
        "flatness_mean": float(np.mean(flatness01)) if flatness01.size else 0.0,
        "mfcc_motion_mean": float(np.mean(mfcc_motion01)) if mfcc_motion01.size else 0.0,
        "chroma_stability_mean": float(np.mean(chroma_stability01)) if chroma_stability01.size else 0.0,
        "tonnetz_motion_mean": float(np.mean(tonnetz_motion01)) if tonnetz_motion01.size else 0.0,
        "flux_density": _marks_density_per_minute(flux_marks, duration_s),
        "sub_bass_density": _marks_density_per_minute(sub_marks, duration_s),
        "bass_density": _marks_density_per_minute(bass_marks, duration_s),
        "mid_density": _marks_density_per_minute(mid_marks, duration_s),
        "high_density": _marks_density_per_minute(high_marks, duration_s),
    }
    rms_mean = float(np.mean(np.asarray(audio.rms01, dtype=float))) if np.asarray(audio.rms01).size else 0.0
    genre_hint = classify_mir_genre(descriptor_summary, tempo_bpm=tempo_bpm, rms_mean=rms_mean)
    mood_hint = classify_mir_mood(descriptor_summary, rms_mean=rms_mean)

    return MultiBandAnalysis(
        sub_bass_marks=sub_marks,
        bass_marks=bass_marks,
        mid_marks=mid_marks,
        high_marks=high_marks,
        spectral_flux_marks=flux_marks,
        loud_marks=loud_marks,
        quiet_windows=quiet_windows,
        dominance_marks=dominance_marks,
        frame_times_s=np.asarray(frame_times, dtype=float),
        spectral_centroid01=np.asarray(centroid01, dtype=float),
        spectral_bandwidth01=np.asarray(bandwidth01, dtype=float),
        spectral_contrast01=np.asarray(contrast01, dtype=float),
        spectral_flatness01=np.asarray(flatness01, dtype=float),
        spectral_flux01=np.asarray(flux01, dtype=float),
        mfcc_motion01=np.asarray(mfcc_motion01, dtype=float),
        chroma_stability01=np.asarray(chroma_stability01, dtype=float),
        tonnetz_motion01=np.asarray(tonnetz_motion01, dtype=float),
        tempo_bpm=tempo_bpm,
        genre_hint=genre_hint,
        mood_hint=mood_hint,
        descriptor_summary=descriptor_summary,
    )

