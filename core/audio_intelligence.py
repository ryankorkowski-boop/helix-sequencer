from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import xml.etree.ElementTree as ET

from core.lazy_imports import LazyModule, optional_import
from core import model_parser as xmp

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


@dataclass
class StemAnalysis:
    source: str
    stems: dict[str, Path]
    bass_peaks_ms: list[int]
    vocal_peaks_ms: list[int]
    drum_kicks_ms: list[int]
    drum_snares_ms: list[int]
    drum_hats_ms: list[int]


def normalize_name(name: str) -> str:
    return " ".join((name or "").lower().replace("_", " ").replace("-", " ").split())


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


def build_stem_analysis(
    audio_path: Path,
    use_moises: bool,
    api_key: str | None,
    cache_dir: Path,
    log_fn: Callable[[str], None] | None = None,
) -> StemAnalysis:
    """Build stems and per-stem timing cues used by the sequencer engine."""
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
    bass_peaks = _analyze_peak_events(bass_src, "bass")
    vocal_peaks = _analyze_peak_events(vocal_src, "vocals")
    return StemAnalysis(
        source=source,
        stems=stems,
        bass_peaks_ms=bass_peaks,
        vocal_peaks_ms=vocal_peaks,
        drum_kicks_ms=kicks,
        drum_snares_ms=snares,
        drum_hats_ms=hats,
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
                events.append(LyricEvent(start_ms=st, end_ms=en, text=text))
        else:
            text = str(seg.get("text", "")).strip()
            if not text:
                continue
            st = int(round(float(seg.get("start", 0.0) or 0.0) * 1000.0))
            en = int(round(float(seg.get("end", 0.0) or 0.0) * 1000.0))
            if en <= st:
                en = st + 150
            events.append(LyricEvent(start_ms=st, end_ms=en, text=text))
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
                    events.append(LyricEvent(start_ms=st, end_ms=en, text=text.strip()))
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


def parse_layout_coordinates(layout_path: Path, available_names: list[str]) -> dict[str, tuple[float, float]]:
    """Parse xLights layout model centers (x,y) for spatial chase routing."""
    if not layout_path.exists():
        return {}
    try:
        parsed = xmp.parse_layout(layout_path)
        return parsed.coordinate_map(available_names)
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
