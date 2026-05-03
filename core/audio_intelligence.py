from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
import time
import subprocess
from bisect import bisect_left
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable
import xml.etree.ElementTree as ET

from core.lazy_imports import LazyModule, optional_import
from core import audio_trigger_routes
from core import feature_state
from core import band_sync
from core import model_parser as xmp
from core import spatial_scene
from core import vocal_emotion
from core import vocal_timeline as vt
from audio import drum_detection as drum_intel
from audio import instrument_detection
from music.note_events import midi_note_name

librosa = LazyModule("librosa")
np = LazyModule("numpy")


def _requests_module():
    return optional_import("requests")


def _soundfile_module():
    return optional_import("soundfile")


@dataclass
class LyricEvent:
    start_ms: int
    end_ms: int
    text: str
    confidence: float = 0.75


@dataclass
class BackgroundVocalEvent:
    start_ms: int
    end_ms: int
    confidence: float
    role: str
    source_reason: str
    energy: float
    performer_hint: str = ""


@dataclass
class StemAnalysis:
    source: str
    stems: dict[str, Path]
    bass_peaks_ms: list[int]
    vocal_peaks_ms: list[int]
    drum_kicks_ms: list[int]
    drum_snares_ms: list[int]
    drum_hats_ms: list[int]
    background_vocal_events: list[BackgroundVocalEvent] | None = None
    drum_event_streams: dict[str, list[object]] | None = None
    stem_features: dict[str, dict[str, object]] = field(default_factory=dict)
    confidence_summary: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class AudioAnalysisConfig:
    onset_sensitivity: float = 0.86
    beat_sensitivity: float = 0.78
    stem_event_sensitivity: float = 0.72
    pitch_confidence_min: float = 0.18
    vocal_confidence_min: float = 0.22
    background_vocal_confidence_min: float = 0.32
    drum_hit_confidence_min: float = 0.18
    stem_hit_confidence_min: float = 0.18
    section_change_sensitivity: float = 0.68
    spatial_frame_rate: int = 12
    max_candidate_events_per_second: int = 18
    smoothing_window_ms: int = 180

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TimedConfidenceEvent:
    time_ms: int
    confidence: float
    strength: float = 0.0
    label: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "time_ms": self.time_ms,
            "confidence": round(float(self.confidence), 4),
            "strength": round(float(self.strength), 4),
            "label": self.label,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class NoteEvent:
    timestamp_ms: int
    duration_ms: int
    pitch_hz: float
    midi_note: int
    note_name: str
    velocity: float
    confidence: float
    source_stem: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SongSection:
    start_ms: int
    end_ms: int
    section_type: str
    strength: float
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SpatialAudioFrame:
    time_ms: int
    x_feature: float
    y_feature: float
    z_feature: float
    color_hint: str
    motion_hint: str
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StyleFeatureSummary:
    likely_genre: str
    tempo_class: str
    rhythmic_intensity: float
    harmonic_complexity: float
    brightness: float
    density: float
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class AudioAnalysisResult:
    metadata: dict[str, object] = field(default_factory=dict)
    tempo_map: list[dict[str, object]] = field(default_factory=list)
    beat_events: list[TimedConfidenceEvent] = field(default_factory=list)
    onset_events: list[TimedConfidenceEvent] = field(default_factory=list)
    energy_curves: dict[str, object] = field(default_factory=dict)
    spectral_features: dict[str, object] = field(default_factory=dict)
    harmonic_percussive_features: dict[str, object] = field(default_factory=dict)
    note_events: list[NoteEvent] = field(default_factory=list)
    chord_key_estimates: dict[str, object] = field(default_factory=dict)
    stem_events: dict[str, object] = field(default_factory=dict)
    lyric_timeline: dict[str, object] = field(default_factory=dict)
    section_events: list[SongSection] = field(default_factory=list)
    part_hits: list[dict[str, object]] = field(default_factory=list)
    emotion_events: list[dict[str, object]] = field(default_factory=list)
    style_features: dict[str, object] = field(default_factory=dict)
    feature_state_frames: list[dict[str, object]] = field(default_factory=list)
    beat_feature_timeline: list[dict[str, object]] = field(default_factory=list)
    audio_reactive_actions: list[dict[str, object]] = field(default_factory=list)
    spatial_audio_frames: list[SpatialAudioFrame] = field(default_factory=list)
    confidence_scores: dict[str, float] = field(default_factory=dict)
    debug_summaries: dict[str, object] = field(default_factory=dict)
    raw_candidates: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "metadata": dict(self.metadata),
            "tempo_map": list(self.tempo_map),
            "beat_events": [event.to_dict() for event in self.beat_events],
            "onset_events": [event.to_dict() for event in self.onset_events],
            "energy_curves": dict(self.energy_curves),
            "spectral_features": dict(self.spectral_features),
            "harmonic_percussive_features": dict(self.harmonic_percussive_features),
            "note_events": [event.to_dict() for event in self.note_events],
            "chord_key_estimates": dict(self.chord_key_estimates),
            "stem_events": dict(self.stem_events),
            "lyric_timeline": dict(self.lyric_timeline),
            "section_events": [section.to_dict() for section in self.section_events],
            "part_hits": list(self.part_hits),
            "emotion_events": list(self.emotion_events),
            "style_features": dict(self.style_features),
            "feature_state_frames": list(self.feature_state_frames),
            "beat_feature_timeline": list(self.beat_feature_timeline),
            "audio_reactive_actions": list(self.audio_reactive_actions),
            "spatial_audio_frames": [frame.to_dict() for frame in self.spatial_audio_frames],
            "confidence_scores": dict(self.confidence_scores),
            "debug_summaries": dict(self.debug_summaries),
            "raw_candidates": dict(self.raw_candidates),
        }


def normalize_name(name: str) -> str:
    return " ".join((name or "").lower().replace("_", " ").replace("-", " ").split())


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_audio_analysis_config_path() -> Path:
    return _repo_root() / "config" / "audio_analysis_defaults.json"


def load_audio_analysis_config(path: Path | None = None) -> AudioAnalysisConfig:
    target = path or default_audio_analysis_config_path()
    config = AudioAnalysisConfig()
    if not target.exists():
        return config
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return config
    if not isinstance(payload, dict):
        return config
    source = config.to_dict()
    for key in source:
        if key in payload:
            source[key] = payload[key]
    return AudioAnalysisConfig(
        onset_sensitivity=float(source["onset_sensitivity"]),
        beat_sensitivity=float(source["beat_sensitivity"]),
        stem_event_sensitivity=float(source["stem_event_sensitivity"]),
        pitch_confidence_min=float(source["pitch_confidence_min"]),
        vocal_confidence_min=float(source["vocal_confidence_min"]),
        background_vocal_confidence_min=float(source["background_vocal_confidence_min"]),
        drum_hit_confidence_min=float(source["drum_hit_confidence_min"]),
        stem_hit_confidence_min=float(source["stem_hit_confidence_min"]),
        section_change_sensitivity=float(source["section_change_sensitivity"]),
        spatial_frame_rate=max(1, int(source["spatial_frame_rate"])),
        max_candidate_events_per_second=max(1, int(source["max_candidate_events_per_second"])),
        smoothing_window_ms=max(1, int(source["smoothing_window_ms"])),
    )


def _log(log_fn: Callable[[str], None] | None, text: str) -> None:
    if log_fn is not None:
        try:
            log_fn(text)
        except Exception:
            pass


def _ffmpeg_available() -> bool:
    return _ensure_ffmpeg_environment() is not None


def _resolve_ffmpeg_exe() -> Path | None:
    env_path = os.environ.get("IMAGEIO_FFMPEG_EXE", "").strip()
    if env_path and Path(env_path).exists():
        return Path(env_path)
    which_path = shutil.which("ffmpeg")
    if which_path:
        return Path(which_path)
    try:
        import imageio_ffmpeg  # type: ignore
    except Exception:
        return None
    try:
        exe = Path(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        return None
    return exe if exe.exists() else None


def _ensure_ffmpeg_environment() -> Path | None:
    resolved = _resolve_ffmpeg_exe()
    if resolved is None or not resolved.exists():
        return None
    ffmpeg_exe = resolved
    if resolved.name.lower() != "ffmpeg.exe":
        alias_dir = Path(tempfile.gettempdir()) / "dream_sequence_weaver" / "ffmpeg"
        alias_dir.mkdir(parents=True, exist_ok=True)
        alias_path = alias_dir / "ffmpeg.exe"
        try:
            needs_copy = True
            if alias_path.exists():
                needs_copy = alias_path.stat().st_size != resolved.stat().st_size
            if needs_copy:
                shutil.copyfile(resolved, alias_path)
            ffmpeg_exe = alias_path
        except Exception:
            ffmpeg_exe = resolved
    os.environ["IMAGEIO_FFMPEG_EXE"] = str(ffmpeg_exe)
    ffmpeg_dir = str(ffmpeg_exe.parent)
    current_path = os.environ.get("PATH", "")
    path_parts = current_path.split(os.pathsep) if current_path else []
    if ffmpeg_dir not in path_parts:
        os.environ["PATH"] = ffmpeg_dir + (os.pathsep + current_path if current_path else "")
    return ffmpeg_exe


def _write_audio(path: Path, y: np.ndarray, sr: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf = _soundfile_module()
    if sf is None:
        raise RuntimeError("soundfile is required for stem export but is not installed.")
    sf.write(str(path), np.asarray(y, dtype=np.float32), sr, subtype="PCM_16")


def _compress_ms(values: list[int], min_gap_ms: int) -> list[int]:
    if not values:
        return []
    values = sorted(int(v) for v in values)
    out = [values[0]]
    last = values[0]
    for value in values[1:]:
        if value - last >= min_gap_ms:
            out.append(value)
            last = value
    return out


def _peak_times_ms(times_s: np.ndarray, env: np.ndarray, threshold: float, wait: int) -> list[int]:
    if env.size == 0 or times_s.size == 0:
        return []
    peaks = librosa.util.peak_pick(env, pre_max=2, post_max=2, pre_avg=4, post_avg=4, delta=threshold, wait=max(1, wait))
    out: list[int] = []
    for idx in peaks:
        if 0 <= idx < len(times_s):
            out.append(int(round(float(times_s[idx]) * 1000.0)))
    return out


def _clip_audio(y: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(y, dtype=np.float32), -1.0, 1.0)


def _local_stem_separation(audio_path: Path, out_dir: Path, log_fn: Callable[[str], None] | None) -> dict[str, Path]:
    """Fallback local stem splitting using harmonic/percussive + frequency masking."""
    _log(log_fn, "Stem split: using local fallback separation.")
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    y = np.asarray(y, dtype=np.float32)
    harm, perc = librosa.effects.hpss(y)

    n_fft = 2048
    hop = 512
    harm_stft = librosa.stft(harm, n_fft=n_fft, hop_length=hop)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    freq_col = freqs.reshape(-1, 1)

    bass_mask = freq_col <= 220.0
    vocal_mask = (freq_col > 220.0) & (freq_col <= 4200.0)

    bass_stft = harm_stft * bass_mask
    vocal_stft = harm_stft * vocal_mask
    bass = librosa.istft(bass_stft, hop_length=hop, length=len(y))
    vocals = librosa.istft(vocal_stft, hop_length=hop, length=len(y))
    drums = perc
    other = y - (0.62 * vocals + 0.68 * drums + 0.70 * bass)

    stems = {
        "vocals": out_dir / f"{audio_path.stem}.vocals.wav",
        "drums": out_dir / f"{audio_path.stem}.drums.wav",
        "bass": out_dir / f"{audio_path.stem}.bass.wav",
        "other": out_dir / f"{audio_path.stem}.other.wav",
    }
    _write_audio(stems["vocals"], _clip_audio(vocals), sr)
    _write_audio(stems["drums"], _clip_audio(drums), sr)
    _write_audio(stems["bass"], _clip_audio(bass), sr)
    _write_audio(stems["other"], _clip_audio(other), sr)
    return stems


def _try_demucs_stem_separation(
    audio_path: Path,
    out_dir: Path,
    log_fn: Callable[[str], None] | None,
) -> dict[str, Path] | None:
    demucs_exe = shutil.which("demucs")
    if not demucs_exe:
        return None
    _log(log_fn, "Stem split: attempting local Demucs separation.")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            demucs_exe,
            "-n",
            "htdemucs",
            "-o",
            str(out_dir),
            str(audio_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception as exc:
        _log(log_fn, f"Demucs split failed, falling back: {exc}")
        return None

    track_dir: Path | None = None
    for model_dir in sorted(out_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        candidate = model_dir / audio_path.stem
        if candidate.exists():
            track_dir = candidate
            break
    if track_dir is None:
        return None

    stems = {
        "vocals": track_dir / "vocals.wav",
        "drums": track_dir / "drums.wav",
        "bass": track_dir / "bass.wav",
        "other": track_dir / "other.wav",
    }
    if not stems["vocals"].exists():
        return None
    _log(log_fn, f"Demucs: stems ready ({', '.join(sorted(stems))}).")
    return stems


def _collect_urls(obj: object) -> list[str]:
    urls: list[str] = []
    if isinstance(obj, dict):
        for value in obj.values():
            urls.extend(_collect_urls(value))
    elif isinstance(obj, list):
        for value in obj:
            urls.extend(_collect_urls(value))
    elif isinstance(obj, str):
        if obj.startswith("http://") or obj.startswith("https://"):
            urls.append(obj)
    return urls


def _find_value(data: object, keys: tuple[str, ...]) -> str | None:
    if isinstance(data, dict):
        for key, value in data.items():
            key_norm = str(key).lower()
            if any(token in key_norm for token in keys) and isinstance(value, str):
                return value
            nested = _find_value(value, keys)
            if nested:
                return nested
    elif isinstance(data, list):
        for item in data:
            nested = _find_value(item, keys)
            if nested:
                return nested
    return None


def _http_json(method: str, url: str, **kwargs) -> dict | None:
    requests = _requests_module()
    if requests is None:
        return None
    resp = requests.request(method, url, timeout=90, **kwargs)
    if resp.status_code >= 400:
        return None
    try:
        return resp.json()
    except Exception:
        return None


def _try_moises_stem_separation(
    audio_path: Path,
    out_dir: Path,
    api_key: str,
    log_fn: Callable[[str], None] | None,
) -> dict[str, Path] | None:
    """
    Best-effort Moises API integration using requests.
    The API surface can vary by account tier/version, so this tries common endpoint patterns.
    """
    requests = _requests_module()
    if requests is None:
        _log(log_fn, "Moises: requests is not installed, cannot call API.")
        return None
    if not api_key.strip():
        return None

    base_url = os.environ.get("MOISES_API_BASE", "https://developer-api.moises.ai/api").rstrip("/")
    headers = {"Authorization": f"Bearer {api_key.strip()}"}
    _log(log_fn, f"Moises: contacting {base_url} for stem separation.")

    upload_json = None
    for endpoint in ("/upload", "/v1/upload", "/uploads"):
        upload_json = _http_json("POST", f"{base_url}{endpoint}", headers=headers, json={"filename": audio_path.name})
        if upload_json:
            break
    if not upload_json:
        _log(log_fn, "Moises: upload URL request failed.")
        return None

    upload_url = _find_value(upload_json, ("uploadurl", "upload_url", "url"))
    source_url = _find_value(upload_json, ("downloadurl", "download_url", "sourceurl", "source_url", "fileurl", "file_url"))
    if not upload_url or not source_url:
        _log(log_fn, "Moises: upload response did not include upload/download URLs.")
        return None

    with audio_path.open("rb") as handle:
        upload_resp = requests.put(upload_url, data=handle, timeout=180)
    if upload_resp.status_code >= 400:
        _log(log_fn, f"Moises: upload failed with status {upload_resp.status_code}.")
        return None

    job_json = None
    payloads = [
        {"inputUrl": source_url, "workflow": "stems"},
        {"sourceUrl": source_url, "type": "stems"},
        {"audioUrl": source_url, "jobType": "stems"},
    ]
    for endpoint in ("/jobs", "/v1/jobs", "/process", "/workflow"):
        for payload in payloads:
            job_json = _http_json("POST", f"{base_url}{endpoint}", headers=headers, json=payload)
            if job_json:
                break
        if job_json:
            break
    if not job_json:
        _log(log_fn, "Moises: job submission failed.")
        return None

    job_id = _find_value(job_json, ("jobid", "job_id", "id", "taskid", "task_id"))
    if not job_id:
        _log(log_fn, "Moises: job id not found in response.")
        return None

    _log(log_fn, f"Moises: job submitted ({job_id}), waiting for completion...")
    result_json: dict | None = None
    for _ in range(90):
        time.sleep(2.0)
        for endpoint in (f"/jobs/{job_id}", f"/v1/jobs/{job_id}", f"/tasks/{job_id}", f"/process/{job_id}"):
            state = _http_json("GET", f"{base_url}{endpoint}", headers=headers)
            if state:
                result_json = state
                break
        if not result_json:
            continue
        state_text = json.dumps(result_json).lower()
        if "completed" in state_text or "success" in state_text or "succeeded" in state_text:
            break
        if "failed" in state_text or "error" in state_text:
            _log(log_fn, "Moises: stem job failed according to status response.")
            return None

    if not result_json:
        _log(log_fn, "Moises: job polling timed out.")
        return None

    urls = _collect_urls(result_json)
    typed_urls: dict[str, str] = {}
    for url in urls:
        low = url.lower()
        if "voc" in low and "vocals" not in typed_urls:
            typed_urls["vocals"] = url
        elif "drum" in low and "drums" not in typed_urls:
            typed_urls["drums"] = url
        elif "bass" in low and "bass" not in typed_urls:
            typed_urls["bass"] = url
        elif "other" in low and "other" not in typed_urls:
            typed_urls["other"] = url
    if len(typed_urls) < 2:
        _log(log_fn, "Moises: completed job did not return enough labeled stem URLs.")
        return None

    stems: dict[str, Path] = {}
    for stem_name, url in typed_urls.items():
        out_path = out_dir / f"{audio_path.stem}.moises.{stem_name}.wav"
        resp = requests.get(url, timeout=180)
        if resp.status_code >= 400:
            continue
        out_path.write_bytes(resp.content)
        stems[stem_name] = out_path
    if len(stems) < 2:
        _log(log_fn, "Moises: stem downloads failed.")
        return None
    _log(log_fn, f"Moises: downloaded stems ({', '.join(sorted(stems))}).")
    return stems


def _analyze_drum_events(path: Path) -> tuple[list[int], list[int], list[int]]:
    y, sr = librosa.load(str(path), sr=None, mono=True)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, backtrack=False)
    times = librosa.frames_to_time(frames, sr=sr)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    cent_times = librosa.frames_to_time(np.arange(len(cent)), sr=sr)
    hats: list[int] = []
    snares: list[int] = []
    kicks: list[int] = []
    for ts in times:
        idx = int(np.searchsorted(cent_times, ts))
        idx = max(0, min(len(cent) - 1, idx))
        c = float(cent[idx]) if len(cent) else 0.0
        ms = int(round(ts * 1000.0))
        if c >= 4200:
            hats.append(ms)
        elif c >= 1800:
            snares.append(ms)
        else:
            kicks.append(ms)
    return _compress_ms(kicks, 40), _compress_ms(snares, 32), _compress_ms(hats, 24)


def _analyze_peak_events(path: Path, kind: str) -> list[int]:
    y, sr = librosa.load(str(path), sr=None, mono=True)
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    if kind == "bass":
        threshold = float(np.quantile(rms, 0.78)) if rms.size else 0.0
        wait = 7
        gap = 70
    else:
        threshold = float(np.quantile(rms, 0.70)) if rms.size else 0.0
        wait = 9
        gap = 95
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    peaks = _peak_times_ms(np.asarray(times), np.asarray(rms), threshold=max(0.01, threshold * 0.20), wait=wait)
    return _compress_ms(peaks, gap)


def _group_background_vocal_scores(
    times_ms: list[int],
    scores: list[float],
    energies: list[float],
    *,
    threshold: float = 0.56,
    min_duration_ms: int = 140,
    max_gap_ms: int = 180,
) -> list[BackgroundVocalEvent]:
    events: list[BackgroundVocalEvent] = []
    active_start: int | None = None
    last_ms = 0
    score_bucket: list[float] = []
    energy_bucket: list[float] = []

    def flush(end_ms: int) -> None:
        nonlocal active_start, score_bucket, energy_bucket
        if active_start is None:
            return
        duration = max(0, end_ms - active_start)
        if duration >= min_duration_ms and score_bucket:
            confidence = max(0.0, min(1.0, sum(score_bucket) / len(score_bucket)))
            energy = max(0.0, min(1.0, sum(energy_bucket) / max(1, len(energy_bucket))))
            role = "group_chant" if confidence >= 0.78 and energy >= 0.72 else "harmony"
            events.append(
                BackgroundVocalEvent(
                    start_ms=active_start,
                    end_ms=max(active_start + min_duration_ms, end_ms),
                    confidence=round(confidence, 3),
                    role=role,
                    source_reason="vocal_stem_harmony_classifier",
                    energy=round(energy, 3),
                    performer_hint="guitarist,bassist" if role == "harmony" else "all_vocalists",
                )
            )
        active_start = None
        score_bucket = []
        energy_bucket = []

    for ms, score, energy in zip(times_ms, scores, energies):
        if score >= threshold:
            if active_start is None or (last_ms and ms - last_ms > max_gap_ms):
                flush(last_ms)
                active_start = ms
            score_bucket.append(float(score))
            energy_bucket.append(float(energy))
            last_ms = ms
        else:
            if active_start is not None and ms - last_ms > max_gap_ms:
                flush(last_ms)
    flush(last_ms)
    return events


def _classify_background_vocals(path: Path, log_fn: Callable[[str], None] | None = None) -> list[BackgroundVocalEvent]:
    """Classify harmony/background vocals from the selected vocal stem.

    This is a deterministic feature classifier, not a lyric heuristic: it looks
    for sustained vocal energy with simultaneous pitch/chroma spread, which is a
    practical signal for harmonies and gang vocals when only a mixed vocal stem
    is available.
    """
    try:
        y, sr = librosa.load(str(path), sr=None, mono=True)
        y = np.asarray(y, dtype=np.float32)
        if y.size < max(2048, int(sr * 0.2)):
            return []
        hop = 512
        harm, _ = librosa.effects.hpss(y)
        rms = librosa.feature.rms(y=harm, hop_length=hop)[0]
        if not rms.size or float(np.max(rms)) <= 0.0:
            return []
        rms01 = np.asarray(rms, dtype=float) / max(float(np.max(rms)), 1e-9)
        stft_mag = np.abs(librosa.stft(harm, n_fft=2048, hop_length=hop))
        pitch_hz, pitch_mag = librosa.piptrack(S=stft_mag, sr=sr, hop_length=hop, fmin=110.0, fmax=2200.0)
        if pitch_mag.size:
            frame_thresholds = np.quantile(pitch_mag, 0.92, axis=0)
            pitch_counts = np.sum(pitch_mag > np.maximum(frame_thresholds, 1e-8), axis=0)
            multi_pitch01 = np.clip((pitch_counts - 1.0) / 3.0, 0.0, 1.0)
        else:
            multi_pitch01 = np.zeros_like(rms01)
        chroma = librosa.feature.chroma_stft(S=stft_mag, sr=sr, hop_length=hop)
        chroma_sum = np.sum(chroma, axis=0) + 1e-9
        chroma_prob = chroma / chroma_sum
        chroma_entropy = -np.sum(chroma_prob * np.log2(chroma_prob + 1e-9), axis=0) / np.log2(12.0)
        size = min(len(rms01), len(multi_pitch01), len(chroma_entropy))
        if size <= 0:
            return []
        scores = np.clip((0.46 * rms01[:size]) + (0.36 * multi_pitch01[:size]) + (0.18 * chroma_entropy[:size]), 0.0, 1.0)
        times = librosa.frames_to_time(np.arange(size), sr=sr, hop_length=hop)
        events = _group_background_vocal_scores(
            [int(round(float(t) * 1000.0)) for t in times],
            [float(v) for v in scores],
            [float(v) for v in rms01[:size]],
        )
        if events:
            _log(log_fn, f"Background vocal classifier: {len(events)} harmony/group windows.")
        return events
    except Exception as exc:
        _log(log_fn, f"Background vocal classifier skipped: {exc}")
        return []


def _summarize_stem_file(
    path: Path,
    *,
    stem_name: str,
    sensitivity: float,
    max_events_per_second: int,
) -> dict[str, object]:
    if not path.exists():
        return {
            "stem_name": stem_name,
            "energy_curve": [],
            "onset_events": [],
            "dominant_frequency_bands": {},
            "confidence": 0.0,
            "notable_events": [],
        }
    y, sr = librosa.load(str(path), sr=None, mono=True)
    y = np.asarray(y, dtype=np.float32)
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    frames = librosa.util.peak_pick(
        onset_env if onset_env.size else np.asarray([], dtype=float),
        pre_max=1,
        post_max=1,
        pre_avg=2,
        post_avg=2,
        delta=max(0.01, (1.0 - sensitivity) * 0.06),
        wait=1,
    ) if onset_env.size else np.asarray([], dtype=int)
    limit = max(1, int(max_events_per_second * max(1.0, len(y) / max(1.0, float(sr))) * 0.2))
    times_s = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    total = max(1e-9, float(np.sum(np.abs(librosa.stft(y, n_fft=2048, hop_length=hop)))))
    spec = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low = float(np.sum(spec[(freqs >= 20) & (freqs < 250)])) / total
    mid = float(np.sum(spec[(freqs >= 250) & (freqs < 2500)])) / total
    high = float(np.sum(spec[(freqs >= 2500) & (freqs <= min(sr / 2, 12000))])) / total
    onset_events: list[dict[str, object]] = []
    norm = float(np.max(onset_env)) if onset_env.size else 0.0
    for frame in list(frames[:limit]):
        idx = int(frame)
        strength = float(onset_env[idx]) / max(1e-9, norm)
        onset_events.append(
            {
                "time_ms": int(round(float(librosa.frames_to_time(idx, sr=sr, hop_length=hop)) * 1000.0)),
                "confidence": round(_clamp01(strength), 4),
                "strength": round(_clamp01(strength), 4),
            }
        )
    energy_curve = [
        {"time_ms": int(round(float(ts) * 1000.0)), "value": round(_clamp01(float(value) / max(1e-9, float(np.max(rms) if rms.size else 1.0))), 4)}
        for ts, value in zip(times_s[: min(len(times_s), 96)], rms[:96])
    ]
    notable = sorted(onset_events, key=lambda item: (-float(item["strength"]), int(item["time_ms"])))[:12]
    confidence = round(_clamp01((0.45 * (len(onset_events) > 0)) + (0.30 * max(low, mid, high)) + (0.25 * (float(np.mean(rms)) if rms.size else 0.0))), 4)
    return {
        "stem_name": stem_name,
        "energy_curve": energy_curve,
        "onset_events": onset_events,
        "dominant_frequency_bands": {"low": round(low, 4), "mid": round(mid, 4), "high": round(high, 4)},
        "confidence": confidence,
        "notable_events": notable,
    }


def build_stem_analysis(
    audio_path: Path,
    use_moises: bool,
    api_key: str | None,
    cache_dir: Path,
    config: AudioAnalysisConfig | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> StemAnalysis:
    """Build stems and per-stem timing cues used by the sequencer engine."""
    settings = config or load_audio_analysis_config()
    if not audio_path.exists():
        _log(log_fn, f"Audio analysis skipped; file does not exist: {audio_path}")
        return StemAnalysis(
            source="direct",
            stems={},
            bass_peaks_ms=[],
            vocal_peaks_ms=[],
            drum_kicks_ms=[],
            drum_snares_ms=[],
            drum_hats_ms=[],
            background_vocal_events=[],
            drum_event_streams={},
            stem_features={},
            confidence_summary={},
        )

    stem_dir = cache_dir / audio_path.stem
    stem_dir.mkdir(parents=True, exist_ok=True)

    stems: dict[str, Path] | None = None
    source = "local"
    if use_moises:
        stems = _try_moises_stem_separation(audio_path, stem_dir, api_key or "", log_fn)
        if stems:
            source = "moises"
    if not stems:
        stems = _try_demucs_stem_separation(audio_path, stem_dir, log_fn)
        if stems:
            source = "demucs"
    if not stems:
        try:
            stems = _local_stem_separation(audio_path, stem_dir, log_fn)
            source = "local"
        except Exception as exc:
            _log(log_fn, f"Stem split fallback failed, using direct audio analysis only: {exc}")
            stems = {}
            source = "direct"

    drum_src = stems.get("drums") or audio_path
    bass_src = stems.get("bass") or audio_path
    vocal_src = stems.get("vocals") or audio_path
    kicks, snares, hats = _analyze_drum_events(drum_src)
    drum_event_streams = drum_intel.detect_drum_event_streams_from_file(drum_src, log_fn=log_fn)
    bass_peaks = _analyze_peak_events(bass_src, "bass")
    vocal_peaks = _analyze_peak_events(vocal_src, "vocals")
    background_vocal_events = _classify_background_vocals(vocal_src, log_fn)
    stem_features = {
        name: _summarize_stem_file(
            path,
            stem_name=name,
            sensitivity=settings.stem_event_sensitivity,
            max_events_per_second=settings.max_candidate_events_per_second,
        )
        for name, path in stems.items()
    }
    confidence_summary = {
        name: float(details.get("confidence", 0.0) or 0.0)
        for name, details in stem_features.items()
    }
    return StemAnalysis(
        source=source,
        stems=stems,
        bass_peaks_ms=bass_peaks,
        vocal_peaks_ms=vocal_peaks,
        drum_kicks_ms=kicks,
        drum_snares_ms=snares,
        drum_hats_ms=hats,
        background_vocal_events=background_vocal_events,
        drum_event_streams=drum_event_streams,
        stem_features=stem_features,
        confidence_summary=confidence_summary,
    )


def _try_whisper_lyrics(audio_path: Path, log_fn: Callable[[str], None] | None = None) -> list[LyricEvent]:
    try:
        import whisper  # type: ignore
    except Exception:
        _log(log_fn, "Lyrics: Whisper package unavailable.")
        return []

    ffmpeg_exe = _ensure_ffmpeg_environment()
    if ffmpeg_exe is None:
        _log(log_fn, "Lyrics: Whisper skipped because ffmpeg was not found in this build.")
        return []
    _log(log_fn, f"Lyrics: Whisper using ffmpeg at {ffmpeg_exe}")

    try:
        model = whisper.load_model("tiny")
        result = model.transcribe(str(audio_path), fp16=False, word_timestamps=True)
    except Exception as exc:
        _log(log_fn, f"Lyrics: Whisper transcription failed: {exc}")
        return []

    events: list[LyricEvent] = []
    segments = result.get("segments", []) if isinstance(result, dict) else []
    for seg in segments:
        words = seg.get("words", []) if isinstance(seg, dict) else []
        if words:
            for word in words:
                text = str(word.get("word", "")).strip()
                if not text:
                    continue
                st = int(round(float(word.get("start", 0.0) or 0.0) * 1000.0))
                en = int(round(float(word.get("end", 0.0) or 0.0) * 1000.0))
                if en <= st:
                    en = st + 80
                confidence = float(word.get("probability", word.get("confidence", 0.78)) or 0.78)
                events.append(LyricEvent(start_ms=st, end_ms=en, text=text, confidence=max(0.0, min(1.0, confidence))))
        else:
            text = str(seg.get("text", "")).strip()
            if not text:
                continue
            st = int(round(float(seg.get("start", 0.0) or 0.0) * 1000.0))
            en = int(round(float(seg.get("end", 0.0) or 0.0) * 1000.0))
            if en <= st:
                en = st + 150
            events.append(LyricEvent(start_ms=st, end_ms=en, text=text, confidence=0.62))
    return events


def _try_moises_lyrics(
    audio_path: Path,
    api_key: str,
    log_fn: Callable[[str], None] | None = None,
) -> list[LyricEvent]:
    requests = _requests_module()
    if requests is None or not api_key.strip():
        return []
    base_url = os.environ.get("MOISES_API_BASE", "https://developer-api.moises.ai/api").rstrip("/")
    headers = {"Authorization": f"Bearer {api_key.strip()}"}
    payload = {"audioFileName": audio_path.name}
    result = None
    for endpoint in ("/lyrics/transcribe", "/v1/lyrics/transcribe", "/transcribe", "/v1/transcriptions"):
        result = _http_json("POST", f"{base_url}{endpoint}", headers=headers, json=payload)
        if result:
            break
    if not result:
        _log(log_fn, "Moises lyrics: endpoint request failed.")
        return []

    events: list[LyricEvent] = []
    queue: list[object] = [result]
    while queue:
        current = queue.pop(0)
        if isinstance(current, dict):
            text = current.get("text")
            start = current.get("start") or current.get("startTime") or current.get("start_ms")
            end = current.get("end") or current.get("endTime") or current.get("end_ms")
            if isinstance(text, str) and start is not None and end is not None:
                try:
                    st = int(round(float(start) * (1000.0 if float(start) < 10000 else 1.0)))
                    en = int(round(float(end) * (1000.0 if float(end) < 10000 else 1.0)))
                except Exception:
                    st, en = 0, 0
                if en > st and text.strip():
                    conf = current.get("confidence") or current.get("score") or 0.76
                    try:
                        confidence = max(0.0, min(1.0, float(conf)))
                    except Exception:
                        confidence = 0.76
                    events.append(LyricEvent(start_ms=st, end_ms=en, text=text.strip(), confidence=confidence))
            queue.extend(current.values())
        elif isinstance(current, list):
            queue.extend(current)
    return events


def extract_lyrics_events(
    audio_path: Path,
    use_moises: bool,
    api_key: str | None,
    log_fn: Callable[[str], None] | None = None,
) -> list[LyricEvent]:
    """Try Moises lyrics first (when enabled/key present), then Whisper fallback."""
    events: list[LyricEvent] = []
    if use_moises and api_key:
        _log(log_fn, "Lyrics: attempting Moises transcription.")
        events = _try_moises_lyrics(audio_path, api_key, log_fn)
    if not events:
        _log(log_fn, "Lyrics: using Whisper fallback transcription.")
        events = _try_whisper_lyrics(audio_path, log_fn)
    if events:
        events.sort(key=lambda e: (e.start_ms, e.end_ms))
    return events


def extract_lyric_timeline(
    audio_path: Path,
    use_moises: bool,
    api_key: str | None,
    vocal_peaks_ms: list[int] | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> vt.LyricTimeline:
    """Return Helix's structured lyric timeline with word and phoneme timing.

    This keeps the working Moises/Whisper pathway while adding a deterministic
    word-to-phoneme fallback for xLights-style Faces export.
    """
    events = extract_lyrics_events(audio_path, use_moises, api_key, log_fn)
    timeline = vt.build_lyric_timeline(events, vocal_peaks_ms or [])
    if not events and vocal_peaks_ms:
        _log(log_fn, "Lyrics: no transcript found; using vocal-energy mouth fallback.")
    return timeline


def parse_layout_coordinates(layout_path: Path, available_names: list[str]) -> dict[str, tuple[float, float]]:
    """Parse xLights layout model centers (x,y) for spatial chase routing."""
    if not layout_path.exists():
        return {}
    try:
        scene = spatial_scene.load_scene(layout_path)
        return scene.projected_coordinate_map(available_names)
    except Exception:
        tree = ET.parse(layout_path)
        root = tree.getroot()
        available_map = {normalize_name(name): name for name in available_names}
        out: dict[str, tuple[float, float]] = {}

        model_root = root.find(".//models")
        if model_root is not None:
            for model in model_root.findall("model"):
                name = (model.attrib.get("name") or "").strip()
                if not name:
                    continue
                key = normalize_name(name)
                actual = available_map.get(key)
                if not actual:
                    continue
                try:
                    x = float(model.attrib.get("WorldPosX", "0") or 0)
                    y = float(model.attrib.get("WorldPosY", "0") or 0)
                    dx = float(model.attrib.get("X2", "0") or 0)
                    dy = float(model.attrib.get("Y2", "0") or 0)
                except Exception:
                    continue
                out[actual] = (x + (dx * 0.5), y + (dy * 0.5))

        group_root = root.find(".//modelGroups")
        if group_root is not None:
            for group in group_root.findall("modelGroup"):
                name = (group.attrib.get("name") or "").strip()
                if not name:
                    continue
                key = normalize_name(name)
                actual = available_map.get(key)
                if not actual or actual in out:
                    continue
                try:
                    x = float(group.attrib.get("centrex", "0") or 0)
                    y = float(group.attrib.get("centrey", "0") or 0)
                except Exception:
                    continue
                out[actual] = (x, y)

        return out


def nearest_mark_distance_ms(target_ms: int, marks: list[int]) -> int | None:
    if not marks:
        return None
    ordered = sorted(int(mark) for mark in marks)
    idx = bisect_left(ordered, int(target_ms))
    candidates: list[int] = []
    if idx < len(ordered):
        candidates.append(abs(ordered[idx] - int(target_ms)))
    if idx > 0:
        candidates.append(abs(ordered[idx - 1] - int(target_ms)))
    return min(candidates) if candidates else None


def proximity_confidence(target_ms: int, marks: list[int], window_ms: int, floor: float = 0.0) -> float:
    distance = nearest_mark_distance_ms(target_ms, marks)
    if distance is None:
        return float(np.clip(floor, 0.0, 1.0))
    if window_ms <= 0:
        return 1.0 if distance == 0 else float(np.clip(floor, 0.0, 1.0))
    score = 1.0 - min(1.0, float(distance) / float(window_ms))
    return float(np.clip(max(floor, score), 0.0, 1.0))


def ordered_spatial_path(
    models: list[str],
    coords: dict[str, tuple[float, float]],
    chase_style: str,
    rng,
) -> list[str]:
    if not models:
        return []
    usable = [name for name in models if name in coords]
    if len(usable) < 2:
        return models[:]
    style = chase_style.strip().lower()
    if style in {"none", ""}:
        return models[:]

    if style == "left_to_right":
        return sorted(usable, key=lambda name: (coords[name][0], coords[name][1], name.lower()))

    if style == "top_to_bottom":
        return sorted(usable, key=lambda name: (coords[name][1], coords[name][0], name.lower()))

    if style == "radial_out":
        xs = [coords[name][0] for name in usable]
        ys = [coords[name][1] for name in usable]
        cx = float(np.mean(xs))
        cy = float(np.mean(ys))
        return sorted(usable, key=lambda name: ((coords[name][0] - cx) ** 2 + (coords[name][1] - cy) ** 2, name.lower()))

    if style == "group_to_group":
        quadrants: dict[int, list[str]] = {0: [], 1: [], 2: [], 3: []}
        xs = [coords[name][0] for name in usable]
        ys = [coords[name][1] for name in usable]
        cx = float(np.mean(xs))
        cy = float(np.mean(ys))
        for name in usable:
            x, y = coords[name]
            q = 0
            if x >= cx and y >= cy:
                q = 1
            elif x < cx and y >= cy:
                q = 2
            elif x < cx and y < cy:
                q = 3
            quadrants[q].append(name)
        ordered: list[str] = []
        for q in (0, 1, 2, 3):
            ordered.extend(sorted(quadrants[q], key=lambda nm: nm.lower()))
        return ordered if ordered else usable

    if style == "random_walk":
        remaining = usable[:]
        start = rng.choice(remaining)
        walk = [start]
        remaining.remove(start)
        while remaining:
            cur = walk[-1]
            cx, cy = coords[cur]
            nxt = min(remaining, key=lambda name: ((coords[name][0] - cx) ** 2 + (coords[name][1] - cy) ** 2))
            walk.append(nxt)
            remaining.remove(nxt)
        return walk

    if style == "wave":
        xs = [coords[name][0] for name in usable]
        min_x, max_x = min(xs), max(xs)
        span = max(0.001, max_x - min_x)
        return sorted(
            usable,
            key=lambda name: (
                coords[name][0],
                np.sin(((coords[name][0] - min_x) / span) * np.pi * 2.0) + coords[name][1] * 0.04,
                name.lower(),
            ),
        )

    return usable


def _event_cap(limit_per_second: int, duration_s: float) -> int:
    return max(1, int(max(1, limit_per_second) * max(1.0, duration_s)))


def _scalar_float(value: object, default: float = 0.0) -> float:
    try:
        if hasattr(value, "item"):
            return float(value.item())
        return float(value)
    except Exception:
        try:
            seq = list(value)  # type: ignore[arg-type]
            return float(seq[0]) if seq else default
        except Exception:
            return default


def _peak_pick_candidates(values: np.ndarray, *, sensitivity: float, wait: int, limit: int) -> list[int]:
    if values.size == 0:
        return []
    peaks = librosa.util.peak_pick(
        values,
        pre_max=1,
        post_max=1,
        pre_avg=2,
        post_avg=2,
        delta=max(0.01, (1.0 - float(sensitivity)) * 0.08),
        wait=max(1, wait),
    )
    return [int(item) for item in list(peaks[:limit])]


def _timed_events_from_frames(
    frames: list[int],
    frame_times_s: np.ndarray,
    strengths: np.ndarray,
    *,
    label: str,
) -> list[TimedConfidenceEvent]:
    if not frames or frame_times_s.size == 0:
        return []
    top = float(np.max(strengths)) if strengths.size else 0.0
    out: list[TimedConfidenceEvent] = []
    for frame in frames:
        if frame < 0 or frame >= len(frame_times_s):
            continue
        strength = float(strengths[frame]) if frame < len(strengths) else 0.0
        confidence = _clamp01(strength / max(1e-9, top))
        out.append(
            TimedConfidenceEvent(
                time_ms=int(round(float(frame_times_s[frame]) * 1000.0)),
                confidence=round(confidence, 4),
                strength=round(confidence, 4),
                label=label,
            )
        )
    return out


def _estimate_syncopation(onsets_ms: list[int], beats_ms: list[int]) -> float:
    if not onsets_ms or len(beats_ms) < 2:
        return 0.0
    offbeats = 0
    for onset in onsets_ms:
        nearest = nearest_mark_distance_ms(onset, beats_ms)
        if nearest is not None and 60 <= nearest <= 220:
            offbeats += 1
    return round(_clamp01(offbeats / max(1, len(onsets_ms))), 4)


def _tempo_class(tempo_bpm: float) -> str:
    if tempo_bpm <= 0:
        return "unknown"
    if tempo_bpm < 86:
        return "slow"
    if tempo_bpm < 118:
        return "medium"
    if tempo_bpm < 150:
        return "fast"
    return "very_fast"


def _extract_note_candidates(
    y: np.ndarray,
    sr: int,
    *,
    source_stem: str,
    config: AudioAnalysisConfig,
) -> tuple[list[NoteEvent], list[dict[str, object]]]:
    harm, _ = librosa.effects.hpss(y)
    hop = 512
    stft_mag = np.abs(librosa.stft(harm, n_fft=2048, hop_length=hop))
    pitch_hz, pitch_mag = librosa.piptrack(S=stft_mag, sr=sr, hop_length=hop, fmin=40.0, fmax=2400.0)
    frame_times_s = librosa.frames_to_time(np.arange(stft_mag.shape[1]), sr=sr, hop_length=hop)
    raw_candidates: list[dict[str, object]] = []
    note_events: list[NoteEvent] = []
    active: dict[int, dict[str, float]] = {}
    for frame_idx in range(stft_mag.shape[1]):
        mags = pitch_mag[:, frame_idx]
        if mags.size == 0:
            continue
        best_idx = int(np.argmax(mags))
        best_hz = float(pitch_hz[best_idx, frame_idx])
        best_mag = float(mags[best_idx])
        max_mag = float(np.max(pitch_mag)) if pitch_mag.size else 0.0
        confidence = _clamp01(best_mag / max(1e-9, max_mag))
        if best_hz <= 0.0:
            continue
        midi = int(round(float(librosa.hz_to_midi(best_hz))))
        time_ms = int(round(float(frame_times_s[frame_idx]) * 1000.0))
        raw_candidates.append(
            {
                "time_ms": time_ms,
                "pitch_hz": round(best_hz, 3),
                "midi_note": midi,
                "confidence": round(confidence, 4),
                "source_stem": source_stem,
            }
        )
        if confidence < config.pitch_confidence_min:
            continue
        current = active.get(midi)
        if current is None:
            active[midi] = {"start_ms": time_ms, "last_ms": time_ms, "velocity": confidence, "pitch_hz": best_hz, "confidence": confidence}
            continue
        if time_ms - int(current["last_ms"]) <= max(90, config.smoothing_window_ms):
            current["last_ms"] = time_ms
            current["velocity"] = max(float(current["velocity"]), confidence)
            current["confidence"] = max(float(current["confidence"]), confidence)
            current["pitch_hz"] = (float(current["pitch_hz"]) + best_hz) * 0.5
        else:
            note_events.append(
                NoteEvent(
                    timestamp_ms=int(current["start_ms"]),
                    duration_ms=max(80, int(current["last_ms"]) - int(current["start_ms"]) + 80),
                    pitch_hz=round(float(current["pitch_hz"]), 3),
                    midi_note=midi,
                    note_name=midi_note_name(midi),
                    velocity=round(_clamp01(float(current["velocity"])), 4),
                    confidence=round(_clamp01(float(current["confidence"])), 4),
                    source_stem=source_stem,
                )
            )
            active[midi] = {"start_ms": time_ms, "last_ms": time_ms, "velocity": confidence, "pitch_hz": best_hz, "confidence": confidence}
    for midi, current in active.items():
        note_events.append(
            NoteEvent(
                timestamp_ms=int(current["start_ms"]),
                duration_ms=max(80, int(current["last_ms"]) - int(current["start_ms"]) + 80),
                pitch_hz=round(float(current["pitch_hz"]), 3),
                midi_note=int(midi),
                note_name=midi_note_name(int(midi)),
                velocity=round(_clamp01(float(current["velocity"])), 4),
                confidence=round(_clamp01(float(current["confidence"])), 4),
                source_stem=source_stem,
            )
        )
    note_events.sort(key=lambda item: (item.timestamp_ms, item.midi_note, item.duration_ms))
    return note_events, raw_candidates


def _build_feature_state_payload(
    *,
    energy: object,
    centroid: object,
    tempo_bpm: float,
    sample_rate: int,
    hop_length: int,
) -> tuple[list[dict[str, object]], float]:
    fps = float(sample_rate) / float(hop_length) if sample_rate > 0 and hop_length > 0 else 40.0
    frames = feature_state.build_feature_state_sequence(
        {
            "energy": [float(item) for item in list(energy)],
            "centroid": [float(item) for item in list(centroid)],
            "tempo": float(tempo_bpm),
        },
        fps=fps,
    )
    return feature_state.serialize_feature_state_sequence(frames), fps


def _build_beat_feature_timeline(
    beat_events: list[TimedConfidenceEvent],
    feature_frames: list[dict[str, object]],
    *,
    fps: float,
) -> list[dict[str, object]]:
    if fps <= 0.0 or not beat_events or not feature_frames:
        return []
    timeline: list[dict[str, object]] = []
    last_index = len(feature_frames) - 1
    for event in beat_events:
        frame_index = max(0, min(last_index, int(round((float(event.time_ms) / 1000.0) * fps))))
        frame = feature_frames[frame_index]
        timeline.append(
            {
                "time_ms": int(event.time_ms),
                "frame_index": int(frame.get("frame_index", frame_index) or frame_index),
                "downbeat": bool(event.metadata.get("downbeat", False)),
                "energy": round(float(frame.get("energy", 0.0) or 0.0), 4),
                "energy_smooth": round(float(frame.get("energy_smooth", 0.0) or 0.0), 4),
                "onset": round(float(frame.get("onset", 0.0) or 0.0), 4),
                "brightness": round(float(frame.get("centroid", 0.0) or 0.0), 3),
                "low": round(float(frame.get("low", 0.0) or 0.0), 4),
                "mid": round(float(frame.get("mid", 0.0) or 0.0), 4),
                "high": round(float(frame.get("high", 0.0) or 0.0), 4),
                "beat_phase": round(float(frame.get("beat_phase", 0.0) or 0.0), 4),
            }
        )
    return timeline


def map_note_event_to_prop(
    note_event: NoteEvent,
    *,
    prop_count: int,
    note_range_start: int = 36,
    note_range_end: int = 96,
) -> dict[str, object]:
    span = max(1, int(note_range_end) - int(note_range_start))
    normalized = _clamp01((int(note_event.midi_note) - int(note_range_start)) / span)
    prop_index = min(max(0, int(round(normalized * max(0, prop_count - 1)))), max(0, prop_count - 1))
    return {
        "prop_index": prop_index,
        "brightness": round(_clamp01(note_event.velocity), 4),
        "sustain_ms": int(note_event.duration_ms),
        "note_name": note_event.note_name,
        "midi_note": int(note_event.midi_note),
    }


def _estimate_key_and_chords(chroma: np.ndarray, frame_times_s: np.ndarray) -> dict[str, object]:
    if chroma.size == 0:
        return {"key": "unknown", "confidence": 0.0, "chords": []}
    chroma_mean = np.mean(chroma, axis=1)
    key_index = int(np.argmax(chroma_mean))
    key_name = midi_note_name(60 + key_index)[:-1]
    confidence = _clamp01(float(np.max(chroma_mean)) / max(1e-9, float(np.sum(chroma_mean))))
    chords: list[dict[str, object]] = []
    sample_count = min(chroma.shape[1], 32)
    if sample_count:
        step = max(1, chroma.shape[1] // sample_count)
        for idx in range(0, chroma.shape[1], step):
            frame = chroma[:, idx]
            top = list(np.argsort(frame)[-3:])
            tones = [midi_note_name(60 + int(note))[:-1] for note in sorted(top)]
            chords.append(
                {
                    "time_ms": int(round(float(frame_times_s[min(idx, len(frame_times_s) - 1)]) * 1000.0)),
                    "tones": tones,
                }
            )
    return {"key": key_name, "confidence": round(confidence, 4), "chords": chords[:32]}


def _detect_song_sections(
    duration_ms: int,
    energy_curve: list[float],
    frame_times_s: np.ndarray,
    *,
    sensitivity: float,
) -> list[SongSection]:
    if duration_ms <= 0:
        return []
    if not energy_curve:
        return [SongSection(0, duration_ms, "verse", 0.4, 0.3, "duration_fallback")]
    size = len(energy_curve)
    thirds = [0, max(1, size // 3), max(2, (size * 2) // 3), size]
    labels = ["intro", "verse", "chorus"]
    sections: list[SongSection] = []
    for idx in range(3):
        start_idx = thirds[idx]
        end_idx = thirds[idx + 1] if idx + 1 < len(thirds) else size
        if end_idx <= start_idx:
            continue
        window = energy_curve[start_idx:end_idx]
        start_ms = int(round(float(frame_times_s[min(start_idx, len(frame_times_s) - 1)]) * 1000.0))
        end_ms = int(round(float(frame_times_s[min(end_idx - 1, len(frame_times_s) - 1)]) * 1000.0)) + 1
        label = labels[idx]
        avg_energy = float(sum(window) / max(1, len(window)))
        if idx == 2 and avg_energy >= max(0.64, sensitivity * 0.7):
            label = "drop" if avg_energy >= 0.82 else "chorus"
        sections.append(
            SongSection(
                start_ms=start_ms,
                end_ms=max(start_ms + 1, end_ms),
                section_type=label,
                strength=round(_clamp01(avg_energy), 4),
                confidence=0.38 if label == "intro" else 0.52,
                reason="energy_curve_fallback",
            )
        )
    if sections and sections[-1].end_ms < duration_ms:
        sections.append(
            SongSection(
                start_ms=sections[-1].end_ms,
                end_ms=duration_ms,
                section_type="outro",
                strength=0.3,
                confidence=0.36,
                reason="tail_fill",
            )
        )
    return sections


def _build_spatial_audio_frames(
    *,
    frame_times_s: np.ndarray,
    pitch_candidates: list[dict[str, object]],
    rms01: np.ndarray,
    mfcc: np.ndarray,
    centroid01: np.ndarray,
    config: AudioAnalysisConfig,
) -> tuple[list[SpatialAudioFrame], dict[str, object]]:
    if frame_times_s.size == 0:
        return [], {"projection_method": "manual_axes", "cluster_count": 0}
    pitch_by_frame: dict[int, float] = {}
    for item in pitch_candidates:
        frame_idx = int(round((int(item["time_ms"]) / 1000.0) * max(1, config.spatial_frame_rate)))
        pitch_by_frame[frame_idx] = max(float(item.get("confidence", 0.0) or 0.0), pitch_by_frame.get(frame_idx, 0.0))
    sample_step = max(1, int(round(len(frame_times_s) / max(1, int(frame_times_s[-1] * config.spatial_frame_rate) or 1))))
    frames: list[SpatialAudioFrame] = []
    raw_vectors: list[list[float]] = []
    for idx in range(0, len(frame_times_s), sample_step):
        x_feature = pitch_by_frame.get(idx, float(centroid01[idx]) if idx < len(centroid01) else 0.0)
        y_feature = float(rms01[idx]) if idx < len(rms01) else 0.0
        z_feature = float(np.mean(np.abs(mfcc[:, idx]))) if mfcc.size and idx < mfcc.shape[1] else 0.0
        raw_vectors.append([x_feature, y_feature, z_feature])
    projection_method = "manual_axes"
    if len(raw_vectors) >= 3:
        try:
            matrix = np.asarray(raw_vectors, dtype=float)
            centered = matrix - np.mean(matrix, axis=0)
            _, _, vh = np.linalg.svd(centered, full_matrices=False)
            reduced = centered @ vh[:3].T
            raw_vectors = reduced.tolist()
            projection_method = "pca"
        except Exception:
            projection_method = "manual_axes"
    for idx, vector in enumerate(raw_vectors):
        time_ms = int(round(float(frame_times_s[min(idx * sample_step, len(frame_times_s) - 1)]) * 1000.0))
        y_feature = _clamp01(vector[1])
        color_hint = "warm" if y_feature >= 0.66 else "cool" if y_feature <= 0.34 else "neutral"
        motion_hint = "surge" if y_feature >= 0.78 else "glide" if y_feature <= 0.32 else "pulse"
        confidence = _clamp01((abs(vector[0]) + abs(vector[1]) + abs(vector[2])) / 3.0)
        frames.append(
            SpatialAudioFrame(
                time_ms=time_ms,
                x_feature=round(_clamp01(abs(vector[0])), 4),
                y_feature=round(_clamp01(abs(vector[1])), 4),
                z_feature=round(_clamp01(abs(vector[2])), 4),
                color_hint=color_hint,
                motion_hint=motion_hint,
                confidence=round(confidence, 4),
            )
        )
    return frames, {"projection_method": projection_method, "cluster_count": min(6, max(1, len(frames) // 8 if frames else 0))}


def _section_texture_signature(mfcc: np.ndarray, part: object, sr: int, hop: int) -> float:
    if not getattr(mfcc, "size", 0):
        return 0.0
    start_idx = max(0, int(float(getattr(part, "start_time", 0.0) or 0.0) * sr / hop))
    end_idx = max(start_idx + 1, int(float(getattr(part, "end_time", 0.0) or 0.0) * sr / hop))
    end_idx = min(end_idx, mfcc.shape[1])
    if end_idx <= start_idx:
        return 0.0
    window = np.abs(mfcc[:, start_idx:end_idx])
    if not window.size:
        return 0.0
    return round(float(np.mean(window)), 4)


def analyze_audio_file(
    audio_path: Path,
    *,
    use_moises: bool = False,
    api_key: str | None = None,
    cache_dir: Path | None = None,
    config: AudioAnalysisConfig | None = None,
    layout_path: Path | None = None,
    provided_parts: list[object] | None = None,
    enable_lyrics: bool = True,
    log_fn: Callable[[str], None] | None = None,
) -> AudioAnalysisResult:
    settings = config or load_audio_analysis_config()
    cache_root = cache_dir or (_repo_root() / "build" / "audio_analysis_cache")
    if not audio_path.exists():
        return AudioAnalysisResult(
            metadata={"audio_path": str(audio_path), "exists": False, "config": settings.to_dict()},
            debug_summaries={"fallback": "missing_audio_file"},
        )

    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    y = np.asarray(y, dtype=np.float32).reshape(-1)
    duration_s = float(len(y) / max(1, sr))
    hop = 512
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    frame_times_s = librosa.frames_to_time(np.arange(len(onset_env)), sr=sr, hop_length=hop)
    duration_ms = int(round(duration_s * 1000.0))
    onset_limit = _event_cap(settings.max_candidate_events_per_second, duration_s)
    onset_frames = _peak_pick_candidates(onset_env, sensitivity=settings.onset_sensitivity, wait=1, limit=onset_limit)
    onset_events = _timed_events_from_frames(onset_frames, frame_times_s, onset_env, label="onset")

    try:
        tempo_bpm, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop, units="frames")
        beat_frame_list = [int(item) for item in list(np.asarray(beat_frames).reshape(-1))]
    except Exception:
        tempo_bpm, beat_frame_list = 0.0, []
    beat_events = _timed_events_from_frames(beat_frame_list, frame_times_s, onset_env, label="beat")
    for idx, event in enumerate(beat_events):
        if idx % 4 == 0:
            event.metadata["downbeat"] = True
    tempo_map: list[dict[str, object]] = []
    for idx, event in enumerate(beat_events):
        local_bpm = _scalar_float(tempo_bpm) if idx == 0 or idx >= len(beat_events) - 1 else (60000.0 / max(1, beat_events[idx + 1].time_ms - event.time_ms))
        tempo_map.append({"time_ms": event.time_ms, "bpm": round(local_bpm, 3), "confidence": event.confidence, "downbeat": bool(event.metadata.get("downbeat", False))})

    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms01 = rms / max(1e-9, float(np.max(rms) if rms.size else 1.0))
    loudness = librosa.amplitude_to_db(np.maximum(rms, 1e-8), ref=np.max) if rms.size else np.asarray([], dtype=float)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=hop)[0]
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=hop)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop)[0]
    zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop)[0]
    mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=13)
    mfcc_delta = librosa.feature.delta(mfcc) if mfcc.size else np.asarray([], dtype=float)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop)
    harm, perc = librosa.effects.hpss(y)
    perc_onset = librosa.onset.onset_strength(y=perc, sr=sr, hop_length=hop)
    harmonic_change = np.abs(np.diff(np.mean(chroma, axis=0))) if chroma.size else np.asarray([], dtype=float)
    brightness01 = centroid / max(1e-9, float(np.max(centroid) if centroid.size else 1.0))
    feature_state_frames, feature_state_fps = _build_feature_state_payload(
        energy=rms01,
        centroid=centroid,
        tempo_bpm=_scalar_float(tempo_bpm),
        sample_rate=int(sr),
        hop_length=hop,
    )
    beat_feature_timeline = _build_beat_feature_timeline(
        beat_events,
        feature_state_frames,
        fps=feature_state_fps,
    )
    audio_reactive_actions = audio_trigger_routes.build_audio_reactive_actions(beat_feature_timeline)
    audio_reactive_summary = audio_trigger_routes.build_audio_reactive_summary(audio_reactive_actions)

    stem = build_stem_analysis(audio_path, use_moises, api_key, cache_root, config=settings, log_fn=log_fn)
    lyric_timeline = (
        extract_lyric_timeline(audio_path, use_moises, api_key, stem.vocal_peaks_ms, log_fn=log_fn)
        if enable_lyrics
        else vt.build_lyric_timeline([], stem.vocal_peaks_ms)
    )
    note_events, raw_pitch = _extract_note_candidates(harm, sr, source_stem="mix_harmonic", config=settings)
    if stem.stems.get("bass") and stem.stems["bass"].exists():
        bass_y, bass_sr = librosa.load(str(stem.stems["bass"]), sr=None, mono=True)
        bass_notes, bass_pitch = _extract_note_candidates(np.asarray(bass_y, dtype=np.float32), int(bass_sr), source_stem="bass", config=settings)
        note_events.extend(bass_notes)
        raw_pitch.extend(bass_pitch)
    note_events.sort(key=lambda item: (item.timestamp_ms, item.midi_note, item.duration_ms))

    sections = _detect_song_sections(duration_ms, [float(item) for item in list(rms01)], frame_times_s, sensitivity=settings.section_change_sensitivity)
    raw_parts = provided_parts or [
        type("HeuristicPart", (), {"label": section.section_type, "start_ms": section.start_ms, "end_ms": section.end_ms, "energy": section.strength})()
        for section in sections
    ]
    song_parts = vt.build_song_parts(raw_parts, stem.vocal_peaks_ms, stem.bass_peaks_ms, stem.drum_kicks_ms + stem.drum_snares_ms + stem.drum_hats_ms)
    build_lifts = [event.time_ms for event in onset_events if event.confidence >= 0.72 and event.strength >= 0.72]
    releases = [event.time_ms for event in beat_events if event.metadata.get("downbeat") and event.confidence >= 0.52]
    part_hits = [vt.as_plain_dict(hit) for hit in vt.detect_part_hits(song_parts, lyric_timeline, vocal_peaks_ms=stem.vocal_peaks_ms, build_lifts_ms=build_lifts, releases_ms=releases)]
    emotion_payload = vocal_emotion.build_vocal_emotion_timeline(
        lyric_timeline=lyric_timeline,
        song_parts=song_parts,
        vocal_peaks_ms=stem.vocal_peaks_ms,
        multiband=type(
            "MultiBandProxy",
            (),
            {
                "frame_times_s": frame_times_s,
                "spectral_centroid01": brightness01,
                "mfcc_motion01": np.mean(np.abs(mfcc_delta), axis=0) if getattr(mfcc_delta, "size", 0) else np.zeros_like(rms01),
                "pitch_motion01": np.clip(np.abs(np.diff(np.pad(np.asarray([item.pitch_hz for item in note_events[: len(frame_times_s)]], dtype=float) if note_events else np.zeros(len(frame_times_s)), (0, max(0, len(frame_times_s) - len(note_events))), constant_values=0.0))), 0.0, 1.0)[: len(frame_times_s)],
            },
        )(),
    )
    style_summary = StyleFeatureSummary(
        likely_genre=str("unknown"),
        tempo_class=_tempo_class(_scalar_float(tempo_bpm)),
        rhythmic_intensity=round(_clamp01(float(np.mean(perc_onset)) / max(1e-9, float(np.max(perc_onset) if perc_onset.size else 1.0))), 4),
        harmonic_complexity=round(_clamp01(float(np.mean(np.std(chroma, axis=0))) if chroma.size else 0.0), 4),
        brightness=round(_clamp01(float(np.mean(brightness01)) if len(brightness01) else 0.0), 4),
        density=round(_clamp01(len(onset_events) / max(1, settings.max_candidate_events_per_second * max(1.0, duration_s))), 4),
        confidence=0.54,
    )
    spatial_frames, spatial_debug = _build_spatial_audio_frames(
        frame_times_s=frame_times_s,
        pitch_candidates=raw_pitch,
        rms01=np.asarray(rms01, dtype=float),
        mfcc=np.asarray(mfcc, dtype=float),
        centroid01=np.asarray(brightness01, dtype=float),
        config=settings,
    )
    guitar_events, guitar_debug = instrument_detection.derive_guitar_events(note_events, onset_ms=[item.time_ms for item in onset_events], beat_ms=[item.time_ms for item in beat_events])
    bass_events, bass_debug = instrument_detection.derive_bass_events(stem.bass_peaks_ms, note_events, beat_ms=[item.time_ms for item in beat_events])
    timeline = band_sync.build_global_music_timeline(
        parts=song_parts,
        beat_ms=[item.time_ms for item in beat_events],
        onset_ms=[item.time_ms for item in onset_events],
        vocal_peaks=stem.vocal_peaks_ms,
        bass_peaks=stem.bass_peaks_ms,
        drum_event_streams=stem.drum_event_streams,
        note_events=note_events,
        background_vocal_events=stem.background_vocal_events,
        song_length_ms=duration_ms,
    )
    chord_key = _estimate_key_and_chords(chroma, frame_times_s)
    metadata = {
        "audio_path": str(audio_path),
        "sample_rate": int(sr),
        "duration_ms": duration_ms,
        "analysis_schema": "helix.audio_analysis.v1",
        "feature_state_fps": round(float(feature_state_fps), 6),
        "config": settings.to_dict(),
        "layout_path": str(layout_path) if layout_path else "",
    }
    if layout_path:
        metadata["layout_coordinate_count"] = len(parse_layout_coordinates(layout_path, []))
    return AudioAnalysisResult(
        metadata=metadata,
        tempo_map=tempo_map,
        beat_events=beat_events,
        onset_events=onset_events,
        energy_curves={
            "rms": [round(float(item), 4) for item in list(rms01[:256])],
            "loudness_db": [round(float(item), 4) for item in list(loudness[:256])],
            "attack_profile": [round(float(max(0.0, rms01[idx] - (rms01[idx - 1] if idx else 0.0))), 4) for idx in range(min(len(rms01), 256))],
            "release_profile": [round(float(max(0.0, (rms01[idx - 1] if idx else 0.0) - rms01[idx])), 4) for idx in range(min(len(rms01), 256))],
            "phrase_energy": [{"section": part.name, "energy": part.energy_level, "confidence": part.confidence} for part in song_parts],
            "build_drop_markers": [{"time_ms": int(round(float(hit.get("timestamp", 0.0)) * 1000.0)), "hit_type": hit["hit_type"], "confidence": hit["confidence"]} for hit in part_hits if hit["hit_type"] in {"drop_hit", "energy_swell_peak", "chorus_start"}],
        },
        spectral_features={
            "spectral_centroid": [round(float(item), 3) for item in list(centroid[:256])],
            "spectral_bandwidth": [round(float(item), 3) for item in list(bandwidth[:256])],
            "spectral_contrast": [[round(float(value), 4) for value in row[:128]] for row in contrast[: min(contrast.shape[0], 6)]],
            "spectral_rolloff": [round(float(item), 3) for item in list(rolloff[:256])],
            "zero_crossing_rate": [round(float(item), 4) for item in list(zcr[:256])],
            "brightness_estimate": [round(float(item), 4) for item in list(brightness01[:256])],
            "mfcc": [[round(float(value), 4) for value in row[:128]] for row in mfcc[: min(mfcc.shape[0], 13)]],
            "delta_mfcc": [[round(float(value), 4) for value in row[:128]] for row in mfcc_delta[: min(getattr(mfcc_delta, "shape", [0])[0], 13)]] if getattr(mfcc_delta, "size", 0) else [],
            "timbre_clusters": [{"cluster_id": idx, "centroid": round(float(np.mean(np.abs(row))), 4)} for idx, row in enumerate(mfcc[: min(mfcc.shape[0], 4)])],
            "texture_signatures": [{"section": part.name, "texture": _section_texture_signature(mfcc, part, sr, hop)} for part in song_parts],
        },
        harmonic_percussive_features={
            "harmonic_energy_ratio": round(float(np.sum(np.abs(harm))) / max(1e-9, float(np.sum(np.abs(y)))), 4),
            "percussive_energy_ratio": round(float(np.sum(np.abs(perc))) / max(1e-9, float(np.sum(np.abs(y)))), 4),
            "percussive_onset_stream": [event.to_dict() for event in _timed_events_from_frames(_peak_pick_candidates(perc_onset, sensitivity=settings.onset_sensitivity, wait=1, limit=onset_limit), frame_times_s, perc_onset, label="percussive_onset")],
            "transient_sharpness": round(float(np.mean(np.maximum(0.0, np.diff(np.pad(np.asarray(perc_onset, dtype=float), (1, 0), constant_values=0.0))))) if perc_onset.size else 0.0, 4),
            "decay_profile": round(float(np.mean(np.maximum(0.0, np.diff(np.pad(np.asarray(rms01, dtype=float)[::-1], (1, 0), constant_values=0.0))))) if len(rms01) else 0.0, 4),
            "chroma": [[round(float(value), 4) for value in row[:128]] for row in chroma[: min(chroma.shape[0], 12)]],
            "harmonic_change_points": [int(round(float(frame_times_s[idx + 1]) * 1000.0)) for idx, value in enumerate(harmonic_change[:64]) if float(value) >= np.quantile(harmonic_change, 0.78) if harmonic_change.size],
        },
        note_events=note_events,
        chord_key_estimates=chord_key,
        stem_events={
            "source": stem.source,
            "stems": {name: str(path) for name, path in stem.stems.items()},
            "legacy_marks": {
                "bass_peaks_ms": list(stem.bass_peaks_ms),
                "vocal_peaks_ms": list(stem.vocal_peaks_ms),
                "drum_kicks_ms": list(stem.drum_kicks_ms),
                "drum_snares_ms": list(stem.drum_snares_ms),
                "drum_hats_ms": list(stem.drum_hats_ms),
            },
            "per_stem": stem.stem_features,
            "background_vocal_events": [asdict(event) for event in list(stem.background_vocal_events or [])],
            "drum_event_streams": {key: [event.to_dict() for event in value] for key, value in (stem.drum_event_streams or {}).items()},
            "instrument_events": {
                "guitar": [event.to_dict() for event in guitar_events],
                "bass": [event.to_dict() for event in bass_events],
            },
        },
        lyric_timeline=vt.as_plain_dict(lyric_timeline),
        section_events=sections,
        part_hits=part_hits,
        emotion_events=list(emotion_payload.get("events", []) or []),
        style_features=style_summary.to_dict(),
        feature_state_frames=feature_state_frames,
        beat_feature_timeline=beat_feature_timeline,
        audio_reactive_actions=audio_reactive_actions,
        spatial_audio_frames=spatial_frames,
        confidence_scores={
            "tempo": round(_clamp01((len(beat_events) / max(1, duration_s * 1.5)) * 0.5 + (_scalar_float(tempo_bpm) > 0) * 0.3), 4),
            "onsets": round(_clamp01(sum(event.confidence for event in onset_events) / max(1, len(onset_events))), 4),
            "pitch": round(_clamp01(sum(event.confidence for event in note_events) / max(1, len(note_events))), 4),
            "lyrics": round(float(lyric_timeline.confidence_summary.get("average_confidence", 0.0) or 0.0), 4),
            "sections": round(sum(section.confidence for section in sections) / max(1, len(sections)), 4),
            "stems": round(sum(float(value) for value in stem.confidence_summary.values()) / max(1, len(stem.confidence_summary)), 4) if stem.confidence_summary else 0.0,
        },
        debug_summaries={
            "raw_candidate_counts": {"onsets": len(onset_frames), "beats": len(beat_events), "pitch_candidates": len(raw_pitch), "notes": len(note_events)},
            "timeline_segments": [asdict(item) for item in timeline[:32]],
            "feature_state": {"frames": len(feature_state_frames), "beat_timeline_entries": len(beat_feature_timeline)},
            "audio_reactive": audio_reactive_summary,
            "instrument_debug": {"guitar": guitar_debug, "bass": bass_debug},
            "emotion_debug": dict(emotion_payload.get("debug", {}) or {}),
            "spatial_debug": spatial_debug,
        },
        raw_candidates={
            "onset_frames": list(onset_frames),
            "onset_strength": [round(float(item), 4) for item in list(onset_env[:256])],
            "beat_frames": list(beat_frame_list),
            "pitch_candidates": raw_pitch[:512],
        },
    )


def export_audio_analysis_result(result: AudioAnalysisResult, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "audio_analysis.json"
    json_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    timeline_csv = output_dir / "audio_timeline.csv"
    with timeline_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["type", "time_ms", "confidence", "strength", "label"])
        for event in result.beat_events:
            writer.writerow(["beat", event.time_ms, event.confidence, event.strength, event.label])
        for event in result.onset_events:
            writer.writerow(["onset", event.time_ms, event.confidence, event.strength, event.label])
        for event in result.part_hits:
            writer.writerow(["part_hit", int(event.get("start_ms", 0) or 0), float(event.get("confidence", 0.0) or 0.0), float(event.get("strength", 0.0) or 0.0), str(event.get("hit_type", ""))])
    spatial_csv = output_dir / "spatial_frames.csv"
    with spatial_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_ms", "x_feature", "y_feature", "z_feature", "color_hint", "motion_hint", "confidence"])
        for frame in result.spatial_audio_frames:
            writer.writerow([frame.time_ms, frame.x_feature, frame.y_feature, frame.z_feature, frame.color_hint, frame.motion_hint, frame.confidence])
    feature_state_csv = output_dir / "feature_state.csv"
    with feature_state_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frame_index", "time_s", "energy", "energy_smooth", "onset", "centroid", "low", "mid", "high", "beat_phase"])
        for frame in result.feature_state_frames:
            writer.writerow(
                [
                    frame.get("frame_index", 0),
                    frame.get("time_s", 0.0),
                    frame.get("energy", 0.0),
                    frame.get("energy_smooth", 0.0),
                    frame.get("onset", 0.0),
                    frame.get("centroid", 0.0),
                    frame.get("low", 0.0),
                    frame.get("mid", 0.0),
                    frame.get("high", 0.0),
                    frame.get("beat_phase", 0.0),
                ]
            )
    audio_reactive_csv = output_dir / "audio_reactive_actions.csv"
    with audio_reactive_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_ms", "effect", "family", "target_hint", "motion_hint", "color_hint", "density", "priority", "route", "reason"])
        for action in result.audio_reactive_actions:
            writer.writerow(
                [
                    action.get("time_ms", 0),
                    action.get("effect", ""),
                    action.get("family", ""),
                    action.get("target_hint", ""),
                    action.get("motion_hint", ""),
                    action.get("color_hint", ""),
                    action.get("density", 0.0),
                    action.get("priority", 0),
                    action.get("route", ""),
                    action.get("reason", ""),
                ]
            )
    return {
        "json": str(json_path),
        "timeline_csv": str(timeline_csv),
        "spatial_csv": str(spatial_csv),
        "feature_state_csv": str(feature_state_csv),
        "audio_reactive_csv": str(audio_reactive_csv),
    }
