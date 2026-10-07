"""Historical transient behavior ported to the current eight-target drummer.

The b27e8d77 candidate grid, HPSS, spectral bands, decay features and principal
family classifier are the behavioral reference. Rejected #217 is archived for
forensic comparison. Context-window consensus and full-mix attack relocation
are deliberately absent: they removed real mixed-song hits.
"""
from dataclasses import dataclass
from pathlib import Path
import librosa
import numpy as np
from audio.drum_classification import DrumEvent, DrumClassifierThresholds, classify_drum_hit

ANALYSIS_HOP_LENGTH = 512
ANALYSIS_N_FFT = 2048
ANALYSIS_ENGINE = "v3_historical_hpss_onset_classifier"


@dataclass(frozen=True)
class DrumDetectionConfig:
    onset_delta: float = 0.045
    onset_wait: int = 1
    min_gap_ms: int = 22
    low_confidence_min: float = 0.34
    cluster_gap_ms: int = 95
    prefer_recall: bool = True
    min_percussive_ratio: float = 0.16
    entrance_anchor_ratio: float = 0.40
    entrance_search_seconds: float = 30.0
    entrance_support_seconds: float = 1.4
    entrance_preroll_seconds: float = 0.08


def _norm01(values):
    top = float(np.max(np.abs(values))) if len(values) else 0.0
    return values / top if top > 1e-9 else np.zeros_like(values)


def _tom_class_from_spectrum(spectrum, freqs):
    """Use an actual resolved body peak, not event order or kit coverage.

    Abstain when the 80–700 Hz body has no prominent resolved resonance.
    Pitch bins are ordered by physical pitch; this is a relative pitch estimate,
    not a claim to know the recording's kit tuning.
    """
    mask = (freqs >= 80) & (freqs < 700)
    band = np.asarray(spectrum[mask], dtype=float)
    hz = freqs[mask]
    if not len(band) or float(band.sum()) <= 1e-9:
        return None, 0.0, None
    peak = int(np.argmax(band))
    spacing = float(hz[1]-hz[0])
    radius = max(1,round(20/spacing))
    concentration = float(band[max(0,peak-radius):min(len(band),peak+radius+1)].sum() / band.sum())
    prominence = float(band[peak] / max(np.median(band), 1e-9))
    pitch = float(hz[peak])
    if concentration < 0.10 or prominence < 4.0 or pitch < 110:
        return None, concentration, pitch
    name = "high" if pitch >= 400 else "mid" if pitch >= 250 else "floor"
    return name, concentration, pitch


def analyze_drummer_audio(audio_path: Path):
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    return analyze_drummer_samples(y, sr)


def analyze_drummer_samples(y, sr, *, onset_delta=None, config=None):
    config = config or DrumDetectionConfig()
    y = np.asarray(y, dtype=np.float32).reshape(-1)
    if sr <= 0:
        raise ValueError("Sample rate must be positive")
    hop, n_fft = ANALYSIS_HOP_LENGTH, ANALYSIS_N_FFT
    diagnostics = dict(analysis_engine=ANALYSIS_ENGINE, source_sample_rate=int(sr),
                       analysis_sample_rate=int(sr), sample_rate=int(sr),
                       analysis_hop_length=hop, analysis_n_fft=n_fft,
                       hpss_margin=1.0, onset_delta=config.onset_delta if onset_delta is None else onset_delta,
                       onset_wait=config.onset_wait, timing_refinement="none_detected_transient_grid",
                       used_hpss_percussive_evidence=True, min_percussive_ratio=config.min_percussive_ratio,
                       context_n_fft=None, onset_audit=[], typed_event_count=0)
    if not len(y):
        return [], diagnostics
    harmonic, perc = librosa.effects.hpss(y)
    onset_env = librosa.onset.onset_strength(y=perc, sr=sr, hop_length=hop)
    frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr,
                                      hop_length=hop, backtrack=False,
                                      delta=diagnostics["onset_delta"], wait=max(1, config.onset_wait))
    if not len(frames) and config.prefer_recall:
        frames = librosa.util.peak_pick(_norm01(onset_env), pre_max=1, post_max=1,
                                       pre_avg=2, post_avg=2, delta=0.025, wait=1)
    stft = np.abs(librosa.stft(perc, n_fft=n_fft, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    rms = librosa.feature.rms(y=perc, hop_length=hop)[0]
    h_rms = librosa.feature.rms(y=harmonic, hop_length=hop)[0]
    rms01, onset01 = _norm01(rms), _norm01(onset_env)
    centroids = librosa.feature.spectral_centroid(S=stft, sr=sr)[0]
    spreads = librosa.feature.spectral_bandwidth(S=stft, sr=sr)[0]
    flatness = librosa.feature.spectral_flatness(S=stft)[0]
    raw, audit = [], diagnostics["onset_audit"]
    cluster, previous_ms = -1, None
    for onset_index, frame in enumerate(sorted(set(int(f) for f in frames if int(f) < stft.shape[1]))):
        spectrum = stft[:, frame]
        total = float(spectrum.sum()) + 1e-9
        def band(lo, hi):
            return float(spectrum[(freqs >= lo) & (freqs < hi)].sum())
        low_mask = (freqs >= 20) & (freqs < 700)
        low_centroid = float((freqs[low_mask] * spectrum[low_mask]).sum() / max(spectrum[low_mask].sum(), 1e-9))
        attack = rms01[frame:min(len(rms01), frame+2)]
        tail = rms01[min(len(rms01), frame+4):min(len(rms01), frame+10)]
        decay = float(np.mean(tail)) / max(float(np.mean(attack)), 1e-6) if len(tail) and len(attack) else 0.0
        current = float(onset01[frame])
        sharp = max(0.0, current - (float(onset01[frame-1]) if frame else 0.0))
        # These overlapping bands and normalization exactly match b27e8d77.
        features = dict(low_ratio=band(20,250)/total, mid_low_ratio=band(160,700)/total,
                        mid_ratio=band(700,2500)/total, high_ratio=band(2500,min(sr/2,14000))/total,
                        centroid_hz=float(centroids[frame]), low_centroid_hz=low_centroid,
                        spectral_spread01=min(1.0,float(spreads[frame])/(sr/2)),
                        transient_sharpness=min(1.0,sharp), decay_profile=min(1.0,decay))
        kind, confidence = classify_drum_hit(features, DrumClassifierThresholds(low_confidence_min=config.low_confidence_min))
        # The historical kick test includes frequencies up to 250 Hz. A tonal
        # tom body can satisfy it. Require strong 160–700 Hz dominance and very
        # little metal energy before resolving that overlap as a tom.
        if kind == "kick" and features["mid_low_ratio"] >= features["low_ratio"]*0.72 and features["low_centroid_hz"] >= 185 and features["high_ratio"] < 0.08:
            kind = "tom"

        timestamp = float(frame*hop/sr)
        ms = round(timestamp*1000)
        if previous_ms is None or ms-previous_ms > config.cluster_gap_ms:
            cluster += 1
        previous_ms = ms
        velocity = round(max(.08,min(1.0,float(rms01[frame])*.65+current*.35)),3)
        quality = float(rms[frame]/max(rms[frame]+h_rms[frame],1e-9))
        info = {k:round(float(v),4) for k,v in features.items()}
        info.update(analysis_engine=ANALYSIS_ENGINE, event_frame=frame, onset_index=onset_index,
                    coarse_timestamp_ms=round(timestamp*1000,3), timing_refinement_ms=0.0,
                    percussive_ratio=quality, percussive_flatness=float(flatness[frame]))
        # Detect a literal cutoff using the original waveform. This gate does
        # not relocate an onset or demand attack contrast in a busy full mix.
        sample = int(frame*hop)
        before = y[max(0,sample-round(.018*sr)):max(0,sample-round(.008*sr))]
        after = y[min(len(y),sample+round(.005*sr)):min(len(y),sample+round(.015*sr))]
        cutoff = bool(len(before) and len(after) and np.mean(after**2) < np.mean(before**2)*0.01)
        info["waveform_cutoff"] = cutoff
        reason = "ambiguous_bus" if kind == "drum_bus" else None
        if cutoff:
            reason = "waveform_cutoff"

        if quality < config.min_percussive_ratio:
            reason = "harmonic_dominated"
        if kind == "tom":
            # A tom identity needs a resolved post-attack resonance. The
            # centered onset window includes the attack smear, so measure the
            # body in the source here: HPSS attenuates sustained tom partials.
            # This does not change candidate timing/classification.
            lo = max(0, int((timestamp-.005)*sr))
            body_samples = y[lo:min(len(y),lo+round(.080*sr))]
            body_spectrum = np.abs(np.fft.rfft(body_samples*np.hanning(len(body_samples)),n=8192))
            # Subtract preceding sustained bass/guitar resonance before naming
            # a tom. A loud continuing note is not the struck drum's pitch.
            pre_end = max(0,lo-round(.030*sr))
            pre_samples = y[max(0,pre_end-len(body_samples)):pre_end]
            if len(pre_samples):
                background = np.abs(np.fft.rfft(pre_samples*np.hanning(len(pre_samples)),n=8192))
                body_spectrum = np.maximum(0.0,body_spectrum-background)
            body_freqs = np.fft.rfftfreq(8192,1/sr)
            tom, tom_confidence, pitch = _tom_class_from_spectrum(body_spectrum,body_freqs)
            info.update(tom_class=tom, tom_class_confidence=tom_confidence,
                        tom_peak_hz=pitch, tom_class_evidence="new_post_attack_resonance_above_preceding_mix_after_hpss_family")
            if tom is None and reason is None:
                reason = "unresolved_tom_pitch"
        row = dict(timestamp=round(timestamp,4), drum_family=kind, confidence=confidence,
                   velocity=velocity, source_onset_index=onset_index, primary=info,
                   contextual=None, attack_refinement=None, body_class=kind if kind in ("kick","snare","tom") else None,
                   metal_class=kind if kind in ("hihat","cymbal") else None,
                   rejection_reason=reason, scheduler_decision="not_submitted" if reason else "pending",
                   physical_target=None)
        audit.append(row)
        if reason is None:
            raw.append(DrumEvent(round(timestamp,4),velocity,confidence,info,cluster,kind,ANALYSIS_ENGINE))

    # A strong body attack supported by another typed transient establishes an
    # entrance. This replaces repeated whole-song vetoes; soft later hits survive.
    # No absolute song timestamps, beat-generated hits, or target quotas are used.
    entrance = None
    for event in raw:
        if event.timestamp > config.entrance_search_seconds:
            break
        if event.drum_type not in ("kick","snare","tom") or event.frequency_band_info["percussive_ratio"] < config.entrance_anchor_ratio:
            continue
        if any(0 < other.timestamp-event.timestamp <= config.entrance_support_seconds for other in raw):
            entrance = max(0.0,event.timestamp-config.entrance_preroll_seconds)
            break
    eligible = [e for e in raw if entrance is None or e.timestamp >= entrance]
    eligible_indices = {e.frequency_band_info["onset_index"] for e in eligible}
    for row in audit:
        if row["rejection_reason"] is None and row["source_onset_index"] not in eligible_indices:
            row.update(rejection_reason="before_supported_drum_entrance",scheduler_decision="not_submitted")
    compressed = []
    for event in eligible:
        if compressed and event.drum_type == compressed[-1].drum_type and event.timestamp_ms-compressed[-1].timestamp_ms < config.min_gap_ms:
            previous = compressed[-1]
            loser = previous if event.velocity>previous.velocity else event
            if loser is previous:
                compressed[-1] = event
            audit[loser.frequency_band_info["onset_index"]].update(rejection_reason="same_family_compression",scheduler_decision="not_submitted")
        else:
            compressed.append(event)
    from collections import Counter
    diagnostics.update(onset_candidate_count=len(audit), accepted_onset_count=len(compressed),
                       typed_event_count=len(compressed), event_types=dict(Counter(e.drum_type for e in compressed)),
                       tom_classes=dict(Counter(e.frequency_band_info["tom_class"] for e in compressed if e.drum_type=="tom")),
                       rejection_counts=dict(Counter(r["rejection_reason"] for r in audit if r["rejection_reason"])),
                       entrance_timestamp=entrance, min_gap_ms=config.min_gap_ms)
    return compressed, diagnostics
