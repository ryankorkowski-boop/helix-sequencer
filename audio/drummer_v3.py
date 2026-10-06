"""Canonical Drummer V3 HPSS typed-event analysis.

The production classifier lives here, never in the XSQ/export layer.
Legacy feature-only experiments remain archived for regression comparison.
"""
from pathlib import Path
import librosa
import numpy as np
from audio.drum_classification import DrumEvent as LegacyDrumEvent

ANALYSIS_SAMPLE_RATE = 44100
ANALYSIS_HOP_LENGTH = 441
ANALYSIS_N_FFT = 2048
MIN_ATTACK_CONTRAST = 1.05


def _tom_class_from_low_centroid(low_centroid_hz: float) -> str:
    """Map an accepted tom onset to the physical HIGH/MID/FLOOR drum."""
    if low_centroid_hz >= 380.0:
        return "high"
    if low_centroid_hz >= 275.0:
        return "mid"
    return "floor"


def _classify_onset(
    *,
    low_ratio: float,
    low_mid_ratio: float,
    mid_ratio: float,
    high_ratio: float,
    centroid_hz: float,
    low_centroid_hz: float,
    decay_100ms: float,
    decay_300ms: float,
) -> tuple[str | None, str | None, str | None]:
    """Return (body, metal, tom_class) for one proven percussive onset.

    The classifier is deliberately sparse.  One onset may contain one body hit
    (kick/snare/tom) and one metal hit (hat/cymbal), which preserves real
    simultaneous kick+hat or snare+hat playing without turning one transient
    into three unrelated drums.
    """
    low = float(low_ratio)
    low_mid = float(low_mid_ratio)
    mid = float(mid_ratio)
    high = float(high_ratio)
    centroid = float(centroid_hz)
    low_centroid = float(low_centroid_hz)

    body: str | None = None
    tom_class: str | None = None

    # Tuned to the isolated HPSS percussive spectrum, not the full mix.
    # A tom has a substantial 180-700 Hz body and a higher low-band centroid
    # than a bass-drum fundamental.  Give that explicit signature precedence.
    tom_signature = (
        low_mid >= 0.28
        and high <= 0.43
        and centroid <= 4300.0
        and low_mid >= low * 0.72
        and (
            low_centroid >= 185.0
            or (centroid >= 450.0 and low <= 0.58)
        )
    )
    if tom_signature:
        body = "tom"
        tom_class = _tom_class_from_low_centroid(low_centroid)
    else:
        kick_score = (2.20 * low) + (0.55 * low_mid) + (0.12 * mid) - (0.35 * high)
        snare_score = (1.65 * mid) + (0.35 * high) + (0.25 * low_mid) - (0.35 * low)

        if low >= 0.18 and low_centroid <= 225.0 and kick_score >= 0.35:
            body = "kick"
        elif mid >= 0.22 and centroid <= 6500.0 and snare_score >= 0.42:
            body = "snare"
        elif (
            low_mid >= 0.22
            and high <= 0.45
            and centroid <= 4300.0
            and low_centroid >= 185.0
        ):
            body = "tom"
            tom_class = _tom_class_from_low_centroid(low_centroid)

    metal: str | None = None
    if high >= 0.46 and centroid >= 3500.0:
        sustained = decay_100ms >= 0.50 and decay_300ms >= 0.16
        if high >= 0.60 and sustained:
            metal = "cymbal"
        else:
            metal = "hihat"

    return body, metal, tom_class


def _refine_attack_sample(
    y: np.ndarray,
    sr: int,
    coarse_sample: int,
) -> tuple[int, float]:
    """Refine a 10 ms onset frame to the waveform attack and reject release edges."""
    back = int(round(sr * 0.030))
    forward = int(round(sr * 0.040))
    lo = max(0, int(coarse_sample) - back)
    hi = min(len(y), int(coarse_sample) + forward)
    segment = np.asarray(y[lo:hi], dtype=float)
    if segment.size < 16:
        return int(coarse_sample), 1.0

    smooth = max(3, int(round(sr * 0.003)))
    power = np.convolve(segment * segment, np.ones(smooth) / smooth, mode="same")
    envelope = np.sqrt(np.maximum(power, 0.0))
    rise = np.diff(envelope, prepend=envelope[0])
    edge = max(smooth // 2 + 1, int(round(sr * 0.008)))
    if rise.size <= (2 * edge + 2):
        return int(coarse_sample), 1.0
    rise[:edge] = 0.0
    rise[-edge:] = 0.0
    peak_index = int(np.argmax(rise))

    span = max(2, int(round(sr * 0.006)))
    before = envelope[max(edge, peak_index - span):peak_index]
    after = envelope[peak_index:min(len(envelope) - edge, peak_index + span)]
    if before.size == 0 or after.size == 0:
        return int(coarse_sample), 1.0
    attack_contrast = float(np.median(after)) / max(float(np.median(before)), 1e-8)

    baseline_lo = max(edge, peak_index - int(round(sr * 0.015)))
    baseline_hi = max(baseline_lo + 1, peak_index - int(round(sr * 0.004)))
    baseline = float(np.median(envelope[baseline_lo:baseline_hi]))
    local_peak = float(np.max(after))
    threshold = baseline + (0.12 * max(0.0, local_peak - baseline))
    search_lo = max(edge, peak_index - int(round(sr * 0.012)))
    crossings = np.flatnonzero(envelope[search_lo:peak_index + 1] >= threshold)
    onset_index = search_lo + int(crossings[0]) if crossings.size else peak_index
    return lo + onset_index, attack_contrast


def analyze_drummer_audio(audio_path: Path) -> tuple[list[LegacyDrumEvent], dict[str, object]]:
    """Detect drummer hits from one conservative HPSS percussive-onset stream.

    This replaces the previous independent-family detector, which could either
    double-classify one transient across several drums or reject an entire real
    song because its spectral-flatness scale was mismatched.  Full-mix audio
    never originates a hit: every accepted onset must first pass an exact-frame
    HPSS percussive-ratio gate.
    """
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    return analyze_drummer_samples(y, sr)


def analyze_drummer_samples(y: np.ndarray, sr: int, *, onset_delta: float = 0.06) -> tuple[list[LegacyDrumEvent], dict[str, object]]:
    """Canonical typed-event detector, shared by file and in-memory callers."""
    y = np.asarray(y, dtype=np.float32).reshape(-1)
    if sr <= 0:
        raise ValueError("Sample rate must be positive")
    source_sr = int(sr)
    if y.size == 0:
        return [], {
            "analysis_engine": "v3_hpss_onset_classifier",
            "source_sample_rate": source_sr,
            "analysis_sample_rate": ANALYSIS_SAMPLE_RATE,
            "typed_event_count": 0,
        }
    if source_sr != ANALYSIS_SAMPLE_RATE:
        y = librosa.resample(
            y,
            orig_sr=source_sr,
            target_sr=ANALYSIS_SAMPLE_RATE,
        ).astype(np.float32, copy=False)
    sr = ANALYSIS_SAMPLE_RATE
    hop = ANALYSIS_HOP_LENGTH
    n_fft = ANALYSIS_N_FFT

    harmonic, percussive = librosa.effects.hpss(y, margin=2.0)
    p_stft = np.abs(
        librosa.stft(percussive, n_fft=n_fft, hop_length=hop, center=True)
    )
    h_rms = librosa.feature.rms(
        y=harmonic,
        frame_length=n_fft,
        hop_length=hop,
        center=True,
    )[0]
    p_rms = librosa.feature.rms(
        y=percussive,
        frame_length=n_fft,
        hop_length=hop,
        center=True,
    )[0]
    full_rms = librosa.feature.rms(
        y=y,
        frame_length=n_fft,
        hop_length=hop,
        center=True,
    )[0]
    onset_env = librosa.onset.onset_strength(
        y=percussive,
        sr=sr,
        hop_length=hop,
    )

    n = min(
        p_stft.shape[1],
        len(h_rms),
        len(p_rms),
        len(full_rms),
        len(onset_env),
    )
    p_stft = p_stft[:, :n]
    h_rms = h_rms[:n]
    p_rms = p_rms[:n]
    full_rms = full_rms[:n]
    onset_env = onset_env[:n]

    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    def band_sum(low_hz: float, high_hz: float) -> np.ndarray:
        mask = (freqs >= low_hz) & (freqs < high_hz)
        if not np.any(mask):
            return np.zeros(n, dtype=float)
        return np.sum(p_stft[mask], axis=0)

    low = band_sum(30, 180)
    low_mid = band_sum(180, 700)
    mid = band_sum(700, 2500)
    high = band_sum(2500, min(sr / 2, 14000))
    total = np.maximum(low + low_mid + mid + high, 1e-9)
    low_ratio = low / total
    low_mid_ratio = low_mid / total
    mid_ratio = mid / total
    high_ratio = high / total

    centroid = librosa.feature.spectral_centroid(S=p_stft, sr=sr)[0][:n]
    low_mask = (freqs >= 30) & (freqs < 700)
    low_total = np.sum(p_stft[low_mask], axis=0)
    low_centroid = np.sum(
        freqs[low_mask, None] * p_stft[low_mask],
        axis=0,
    ) / np.maximum(low_total, 1e-9)

    flatness = librosa.feature.spectral_flatness(S=p_stft)[0][:n]
    drum_quality = p_rms / np.maximum(p_rms + h_rms, 1e-9)

    onset_frames = np.asarray(
        librosa.onset.onset_detect(
            onset_envelope=onset_env,
            sr=sr,
            hop_length=hop,
            backtrack=False,
            delta=onset_delta,
            wait=3,
        ),
        dtype=int,
    )
    onset_scale = max(float(np.percentile(onset_env, 99.5)), 1e-9)

    typed: list[LegacyDrumEvent] = []
    rejected_quality = 0
    rejected_support = 0
    rejected_unclassified = 0
    rejected_release_edge = 0
    accepted_onsets = 0

    for onset_index, frame in enumerate(onset_frames):
        frame = int(frame)
        if frame < 0 or frame >= n:
            continue

        # Critical false-positive guard: use the exact onset frame.  Taking the
        # maximum from neighbouring frames admitted guitar/piano attacks whose
        # adjacent HPSS frame happened to look percussive.
        quality = float(drum_quality[frame])
        if quality < 0.36:
            rejected_quality += 1
            continue

        local_lo = max(0, frame - 8)
        local_hi = min(n, frame + 9)
        if float(full_rms[frame]) < float(np.median(full_rms[local_lo:local_hi])):
            rejected_support += 1
            continue

        refined_sample, attack_contrast = _refine_attack_sample(y, sr, frame * hop)
        if attack_contrast < MIN_ATTACK_CONTRAST:
            rejected_release_edge += 1
            continue

        attack = float(np.mean(p_rms[frame:min(n, frame + 3)]))
        tail_100 = (
            float(np.mean(p_rms[min(n, frame + 5):min(n, frame + 12)]))
            if frame + 5 < n
            else 0.0
        )
        tail_300 = (
            float(np.mean(p_rms[min(n, frame + 15):min(n, frame + 35)]))
            if frame + 15 < n
            else 0.0
        )
        decay_100 = tail_100 / max(attack, 1e-9)
        decay_300 = tail_300 / max(attack, 1e-9)

        body, metal, tom_class = _classify_onset(
            low_ratio=float(low_ratio[frame]),
            low_mid_ratio=float(low_mid_ratio[frame]),
            mid_ratio=float(mid_ratio[frame]),
            high_ratio=float(high_ratio[frame]),
            centroid_hz=float(centroid[frame]),
            low_centroid_hz=float(low_centroid[frame]),
            decay_100ms=decay_100,
            decay_300ms=decay_300,
        )
        if body is None and metal is None:
            rejected_unclassified += 1
            continue

        accepted_onsets += 1
        coarse_timestamp = float(frame * hop / sr)
        timestamp = float(refined_sample / sr)
        onset_strength = min(1.0, float(onset_env[frame]) / onset_scale)
        confidence = max(
            0.36,
            min(1.0, (quality * 0.72) + (onset_strength * 0.28)),
        )
        velocity = max(
            0.22,
            min(1.0, (quality * 0.62) + (onset_strength * 0.38)),
        )

        common_info: dict[str, object] = {
            "analysis_engine": "v3_hpss_onset_classifier",
            "event_frame": float(frame),
            "coarse_timestamp_ms": round(coarse_timestamp * 1000.0, 3),
            "refined_attack_sample": int(refined_sample),
            "attack_contrast": round(float(attack_contrast), 4),
            "timing_refinement_ms": round((timestamp - coarse_timestamp) * 1000.0, 3),
            "percussive_ratio": round(quality, 4),
            "percussive_flatness": round(float(flatness[frame]), 6),
            "low_ratio": round(float(low_ratio[frame]), 4),
            "low_mid_ratio": round(float(low_mid_ratio[frame]), 4),
            "mid_ratio": round(float(mid_ratio[frame]), 4),
            "high_ratio": round(float(high_ratio[frame]), 4),
            "centroid_hz": round(float(centroid[frame]), 2),
            "low_centroid_hz": round(float(low_centroid[frame]), 2),
            "decay_100ms": round(float(decay_100), 4),
            "decay_300ms": round(float(decay_300), 4),
        }

        def append_event(drum_type: str, *, tom: str | None = None) -> None:
            info = dict(common_info)
            if tom is not None:
                info["tom_class"] = tom
                info["tom_class_confidence"] = round(confidence, 4)
            typed.append(
                LegacyDrumEvent(
                    timestamp=round(timestamp, 4),
                    velocity=round(velocity, 3),
                    confidence=round(confidence, 3),
                    frequency_band_info=info,
                    cluster_id=onset_index,
                    drum_type=drum_type,
                    source="v3_hpss_onset_classifier",
                )
            )

        if body is not None:
            append_event(body, tom=tom_class if body == "tom" else None)
        if metal is not None:
            append_event(metal)

    counts = {
        kind: sum(1 for event in typed if event.drum_type == kind)
        for kind in ("kick", "snare", "tom", "hihat", "cymbal")
    }
    tom_counts = {
        tom: sum(
            1
            for event in typed
            if event.drum_type == "tom"
            and event.frequency_band_info.get("tom_class") == tom
        )
        for tom in ("high", "mid", "floor")
    }

    diagnostics: dict[str, object] = {
        "analysis_engine": "v3_hpss_onset_classifier",
        "source_sample_rate": source_sr,
        "sample_rate": int(sr),
        "analysis_sample_rate": int(sr),
        "analysis_hop_length": int(hop),
        "analysis_n_fft": int(n_fft),
        "analysis_window_ms": round((n_fft / sr) * 1000.0, 3),
        "timing_refinement": "waveform_attack",
        "min_attack_contrast": MIN_ATTACK_CONTRAST,
        "frame_rate": round(sr / hop, 3),
        "onset_candidate_count": int(len(onset_frames)),
        "accepted_onset_count": int(accepted_onsets),
        "typed_event_count": int(len(typed)),
        "event_types": counts,
        "tom_classes": tom_counts,
        "rejected_low_percussive_quality": int(rejected_quality),
        "rejected_weak_local_support": int(rejected_support),
        "rejected_unclassified": int(rejected_unclassified),
        "rejected_release_edge": int(rejected_release_edge),
        "used_hpss_percussive_evidence": True,
        "min_percussive_ratio": 0.36,
        "percussive_ratio_p10": round(float(np.percentile(drum_quality, 10)), 4) if len(drum_quality) else 0.0,
        "percussive_ratio_median": round(float(np.median(drum_quality)), 4) if len(drum_quality) else 0.0,
        "percussive_ratio_p90": round(float(np.percentile(drum_quality, 90)), 4) if len(drum_quality) else 0.0,
    }
    return typed, diagnostics
