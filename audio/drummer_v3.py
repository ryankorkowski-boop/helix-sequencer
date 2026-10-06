"""Canonical Drummer V3 HPSS typed-event analysis.

The production classifier lives here, never in the XSQ/export layer.
Legacy feature-only experiments remain archived for regression comparison.
"""
from pathlib import Path
import librosa
import numpy as np
from audio.drum_classification import DrumEvent as LegacyDrumEvent

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
        and low_centroid >= 225.0
        and low_mid >= low * 0.78
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
            and low_centroid >= 225.0
        ):
            body = "tom"
            tom_class = _tom_class_from_low_centroid(low_centroid)

    metal: str | None = None
    if high >= 0.46 and centroid >= 3500.0:
        sustained = decay_100ms >= 0.45 or decay_300ms >= 0.20
        if high >= 0.60 and sustained:
            metal = "cymbal"
        else:
            metal = "hihat"

    return body, metal, tom_class


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
    if y.size == 0:
        return [], {"analysis_engine": "v3_hpss_onset_classifier", "typed_event_count": 0}
    hop = max(128, int(round(sr * 0.01)))
    n_fft = max(1024, 2 ** int(np.ceil(np.log2(max(1024, int(sr * 0.046))))))

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
        timestamp = float(frame * hop / sr)
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
        "sample_rate": int(sr),
        "frame_rate": round(sr / hop, 3),
        "onset_candidate_count": int(len(onset_frames)),
        "accepted_onset_count": int(accepted_onsets),
        "typed_event_count": int(len(typed)),
        "event_types": counts,
        "tom_classes": tom_counts,
        "rejected_low_percussive_quality": int(rejected_quality),
        "rejected_weak_local_support": int(rejected_support),
        "rejected_unclassified": int(rejected_unclassified),
        "used_hpss_percussive_evidence": True,
        "min_percussive_ratio": 0.36,
        "percussive_ratio_p10": round(float(np.percentile(drum_quality, 10)), 4) if len(drum_quality) else 0.0,
        "percussive_ratio_median": round(float(np.median(drum_quality)), 4) if len(drum_quality) else 0.0,
        "percussive_ratio_p90": round(float(np.percentile(drum_quality, 90)), 4) if len(drum_quality) else 0.0,
    }
    return typed, diagnostics
