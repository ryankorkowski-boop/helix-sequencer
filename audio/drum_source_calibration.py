"""Recording-bound attack/body timbre calibration for unresolved candidates.

The five-family network does not identify which physical tom was played.
Compare original-source spectra with explicitly labelled recording exemplars
before the identity gate discards those attacks. This never creates attacks,
rotates toms, changes families, or implies human review beyond the given labels.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.ndimage import gaussian_filter1d

SCHEMA = "helix.drum_source_calibration.v1"
MIN_SIMILARITY = .65
MIN_MARGIN = .10


def source_timbre(samples, sample_rate, timestamp):
    """Separate unit-energy log-frequency attack and body spectra.

    Loudness cannot decide the class. Two windows retain both a noisy attack
    and a resonant body; a high partial alone cannot erase the rest of a hit.
    Timestamps remain the original network's grid (no waveform time shifting).
    """
    freqs = np.fft.rfftfreq(8192, 1 / sample_rate)
    edges = np.geomspace(40, 16000, 97)
    features = []
    for begin, end, weight in ((.002, .022, .35), (.022, .092, .65)):
        lo, hi = round((timestamp + begin) * sample_rate), round((timestamp + end) * sample_rate)
        segment = samples[lo:hi]
        if lo < 0 or hi > len(samples) or len(segment) < 2:
            raise ValueError("Source calibration window is outside the audio")
        power = abs(np.fft.rfft(segment * np.hanning(len(segment)), 8192)) ** 2
        bands = np.array([power[(freqs >= a) & (freqs < b)].sum()
                          for a, b in zip(edges[:-1], edges[1:])])
        bands = np.sqrt(gaussian_filter1d(bands, .7))
        norm = float(np.linalg.norm(bands))
        features.append(bands / norm * math.sqrt(weight) if norm > 1e-12 else bands * 0)
    return np.concatenate(features)


def apply_source_calibration(rows, audio_path, calibration_path):
    calibration = json.loads(Path(calibration_path).read_text(encoding="utf-8"))
    if calibration.get("schema") != SCHEMA:
        raise ValueError("Unsupported drum source calibration schema")
    digest = hashlib.sha256(Path(audio_path).read_bytes()).hexdigest()
    if calibration.get("audio_sha256") != digest:
        raise ValueError("Source calibration does not belong to this song")
    start, end = map(float, calibration["scope_seconds"])
    if not all(math.isfinite(t) for t in (start, end)) or not 0 <= start < end:
        raise ValueError("Invalid source calibration scope")
    samples, sr = sf.read(audio_path, dtype="float32", always_2d=True)
    samples = samples.mean(axis=1)
    if end > len(samples) / sr:
        raise ValueError("Source calibration scope is outside the audio")
    prototypes = []
    for exemplar in calibration["exemplars"]:
        family, tom = exemplar["drum_family"], exemplar.get("tom_class")
        if family != "tom" or tom not in {"high", "mid", "floor"}:
            raise ValueError("Source exemplar requires a supported family and explicit tom identity")
        timestamp = float(exemplar["timestamp"])
        if not math.isfinite(timestamp) or timestamp < 0 or not exemplar.get("label_source"):
            raise ValueError("Source exemplar needs finite timing and a label source")
        vector = source_timbre(samples, sr, timestamp)
        if np.linalg.norm(vector) < .99:
            raise ValueError("Source exemplar has insufficient audio")
        prototypes.append((family, tom, exemplar, vector))
    labels = {(family, tom) for family, tom, _, _ in prototypes}
    if not {("tom", t) for t in ("high", "mid", "floor")} <= labels:
        raise ValueError("Source calibration needs all three tom alternatives")
    updated, corrected = [], 0
    for row in rows:
        if (row["drum_family"] != "tom" or row.get("rejection_reason") != "unresolved_tom_identity"
                or row.get("tom_class") is not None or not start <= row["timestamp"] <= end):
            updated.append(row)
            continue
        vector = source_timbre(samples, sr, row["timestamp"])
        scores, closest = {}, {}
        for family, tom, exemplar, prototype in prototypes:
            label = family + (":" + tom if tom else "")
            score = float(np.clip(vector @ prototype, 0, 1))
            if score > scores.get(label, -1):
                scores[label], closest[label] = score, exemplar
        ordered = sorted(scores, key=scores.get, reverse=True)
        best = ordered[0]
        margin = scores[best] - scores[ordered[1]]
        accepted = scores[best] >= MIN_SIMILARITY and margin >= MIN_MARGIN
        decision = dict(accepted=accepted, scores=scores, best_label=best,
                        similarity=scores[best], margin=margin,
                        exemplar=closest[best],
                        confidence_method="source_spectral_cosine_similarity_not_probability",
                        original_family=row["drum_family"], original_tom_class=row.get("tom_class"),
                        original_confidence=row["confidence"], original_velocity=row["velocity"],
                        original_identity_method=row.get("evidence", {}).get("tom_identity_method"),
                        original_rejection_reason=row.get("rejection_reason"),
                        rejection_reason=None if accepted else "ambiguous_or_unmatched_source_timbre")
        evidence = dict(row.get("evidence", {}), source_calibration=decision)
        result = dict(row, evidence=evidence)
        if accepted:
            family, _, tom = best.partition(":")
            result.update(tom_class=tom, tom_class_confidence=round(scores[best], 6), rejection_reason=None)
            if tom:
                evidence["tom_identity_method"] = "source_timbre_exemplar_with_explicit_identity"
            corrected += 1
        updated.append(result)
    return updated, dict(source=str(calibration_path), audio_sha256=digest,
                         scope_seconds=[start, end], exemplars=calibration["exemplars"],
                         min_similarity=MIN_SIMILARITY, min_margin=MIN_MARGIN,
                         corrected_candidate_count=corrected,
                         review_status="source_inspected_inference_pending_user_listening")
