from __future__ import annotations

from bisect import bisect_left
from statistics import median


def default_payload() -> dict[str, object]:
    return {
        "version": "v1",
        "polyrhythm_overlays": [],
        "microtiming": {
            "sample_count": 0,
            "mean_offset_ms": 0.0,
            "std_offset_ms": 0.0,
            "ahead_ratio": 0.0,
            "behind_ratio": 0.0,
            "by_part": [],
        },
        "phrase_boundaries": [],
        "energy_prediction": {
            "horizon_ms": 1200,
            "point_count": 0,
            "max_predicted_lift": 0.0,
            "max_predicted_drop": 0.0,
            "points": [],
        },
    }


def _sorted_unique_ms(values: list[int]) -> list[int]:
    return sorted({int(value) for value in values if int(value) >= 0})


def _median_spacing(marks_ms: list[int]) -> float | None:
    if len(marks_ms) < 2:
        return None
    spans = [marks_ms[idx + 1] - marks_ms[idx] for idx in range(len(marks_ms) - 1)]
    spans = [span for span in spans if 25 <= span <= 3000]
    if not spans:
        return None
    return float(median(spans))


def _alignment_score(
    *,
    beat_ms: list[int],
    onset_ms: list[int],
    subdivision: int,
    tolerance_ms: float,
) -> tuple[float, int, int]:
    if subdivision <= 1 or len(beat_ms) < 2:
        return (0.0, 0, 0)
    clean_onsets = _sorted_unique_ms(onset_ms)
    if not clean_onsets:
        return (0.0, 0, 0)
    checks = 0
    matches = 0
    for idx in range(len(beat_ms) - 1):
        start = beat_ms[idx]
        end = beat_ms[idx + 1]
        span = end - start
        if span < 40:
            continue
        step = span / float(subdivision)
        for sub in range(1, subdivision):
            target = int(round(start + (sub * step)))
            checks += 1
            nearest_idx = bisect_left(clean_onsets, target)
            nearby: list[int] = []
            if nearest_idx > 0:
                nearby.append(clean_onsets[nearest_idx - 1])
            if nearest_idx < len(clean_onsets):
                nearby.append(clean_onsets[nearest_idx])
            if nearby and min(abs(hit - target) for hit in nearby) <= tolerance_ms:
                matches += 1
    if checks <= 0:
        return (0.0, 0, 0)
    return (matches / float(checks), matches, checks)


def detect_polyrhythm_overlays(
    *,
    beat_ms: list[int],
    onset_ms: list[int],
    candidate_ratios: tuple[tuple[int, int], ...] = ((3, 2), (4, 3), (5, 4)),
) -> list[dict[str, object]]:
    clean_beats = _sorted_unique_ms(beat_ms)
    clean_onsets = _sorted_unique_ms(onset_ms)
    beat_interval = _median_spacing(clean_beats)
    if beat_interval is None:
        return []
    tolerance = max(16.0, min(45.0, beat_interval * 0.07))
    overlays: list[dict[str, object]] = []
    for top, bottom in candidate_ratios:
        top_score, top_hits, top_checks = _alignment_score(
            beat_ms=clean_beats,
            onset_ms=clean_onsets,
            subdivision=int(top),
            tolerance_ms=tolerance,
        )
        bot_score, bot_hits, bot_checks = _alignment_score(
            beat_ms=clean_beats,
            onset_ms=clean_onsets,
            subdivision=int(bottom),
            tolerance_ms=tolerance,
        )
        base_confidence = min(top_score, bot_score)
        balance = 1.0 - min(1.0, abs(top_score - bot_score))
        confidence = base_confidence * (0.7 + (0.3 * balance))
        if confidence < 0.34:
            continue
        overlays.append(
            {
                "ratio": f"{top}:{bottom}",
                "confidence": round(float(confidence), 4),
                "subdivision_scores": {
                    str(top): round(float(top_score), 4),
                    str(bottom): round(float(bot_score), 4),
                },
                "hit_counts": {
                    str(top): {"hits": int(top_hits), "checks": int(top_checks)},
                    str(bottom): {"hits": int(bot_hits), "checks": int(bot_checks)},
                },
                "recommended_layer_split": {
                    "driver": "drums",
                    "support": "bass",
                },
            }
        )
    overlays.sort(key=lambda item: float(item.get("confidence", 0.0)), reverse=True)
    return overlays


def _offsets_against_quant_grid(onset_ms: list[int], beat_ms: list[int], subdivisions: int = 4) -> list[tuple[int, float]]:
    clean_beats = _sorted_unique_ms(beat_ms)
    clean_onsets = _sorted_unique_ms(onset_ms)
    if len(clean_beats) < 2 or not clean_onsets:
        return []
    offsets: list[tuple[int, float]] = []
    for onset in clean_onsets:
        idx = bisect_left(clean_beats, onset)
        left_idx = max(0, idx - 1)
        if left_idx >= len(clean_beats) - 1:
            continue
        start = clean_beats[left_idx]
        end = clean_beats[left_idx + 1]
        span = end - start
        if span < 40:
            continue
        phase = (onset - start) / float(span)
        quantized = round(phase * subdivisions) / float(subdivisions)
        expected = start + (quantized * span)
        offset = float(onset - expected)
        max_offset = max(20.0, min(65.0, span * 0.16))
        if abs(offset) <= max_offset:
            offsets.append((onset, offset))
    return offsets


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def _std(values: list[float], center: float | None = None) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values) if center is None else float(center)
    variance = sum((value - mu) ** 2 for value in values) / float(len(values))
    return variance ** 0.5


def _part_offsets(parts: list[object], offset_points: list[tuple[int, float]]) -> list[dict[str, object]]:
    if not parts:
        return []
    out: list[dict[str, object]] = []
    for part in parts:
        start_ms = int(getattr(part, "start_ms", 0) or 0)
        end_ms = int(getattr(part, "end_ms", start_ms + 1) or (start_ms + 1))
        label = str(getattr(part, "label", "PART") or "PART")
        values = [offset for t_ms, offset in offset_points if start_ms <= t_ms < end_ms]
        if not values:
            out.append(
                {
                    "label": label,
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "sample_count": 0,
                    "mean_offset_ms": 0.0,
                    "std_offset_ms": 0.0,
                    "swing_strength_ms": 0.0,
                }
            )
            continue
        mean_offset = _mean(values)
        out.append(
            {
                "label": label,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "sample_count": len(values),
                "mean_offset_ms": round(float(mean_offset), 4),
                "std_offset_ms": round(float(_std(values, mean_offset)), 4),
                "swing_strength_ms": round(float(_mean([abs(value) for value in values])), 4),
            }
        )
    return out


def build_microtiming_profile(
    *,
    onset_ms: list[int],
    note_onset_ms: list[int],
    beat_ms: list[int],
    parts: list[object] | None = None,
) -> dict[str, object]:
    reference_onsets = note_onset_ms if note_onset_ms else onset_ms
    offset_points = _offsets_against_quant_grid(reference_onsets, beat_ms, subdivisions=4)
    values = [offset for _t_ms, offset in offset_points]
    mean_offset = _mean(values)
    ahead = sum(1 for value in values if value <= -1.0)
    behind = sum(1 for value in values if value >= 1.0)
    total = len(values)
    part_rows = _part_offsets(parts or [], offset_points)
    return {
        "sample_count": total,
        "mean_offset_ms": round(float(mean_offset), 4),
        "std_offset_ms": round(float(_std(values, mean_offset)), 4),
        "ahead_ratio": round(float(ahead / total), 4) if total else 0.0,
        "behind_ratio": round(float(behind / total), 4) if total else 0.0,
        "by_part": part_rows,
    }


def derive_phrase_boundaries(
    *,
    beat_ms: list[int],
    parts: list[object] | None = None,
    beats_per_phrase: int = 16,
) -> list[dict[str, object]]:
    clean_beats = _sorted_unique_ms(beat_ms)
    if len(clean_beats) < 2:
        return []
    phrase_size = max(4, int(beats_per_phrase))
    spans: list[dict[str, object]] = []
    idx = 0
    phrase_num = 1
    while idx < len(clean_beats) - 1:
        start_ms = clean_beats[idx]
        end_idx = min(len(clean_beats) - 1, idx + phrase_size)
        end_ms = clean_beats[end_idx]
        midpoint = int(round((start_ms + end_ms) / 2.0))
        label = ""
        if parts:
            for part in parts:
                part_start = int(getattr(part, "start_ms", 0) or 0)
                part_end = int(getattr(part, "end_ms", part_start + 1) or (part_start + 1))
                if part_start <= midpoint < part_end:
                    label = str(getattr(part, "label", "") or "")
                    break
        spans.append(
            {
                "index": phrase_num,
                "label": f"Phrase {phrase_num}",
                "part_hint": label,
                "start_ms": int(start_ms),
                "end_ms": int(max(start_ms + 1, end_ms)),
                "beat_count": int(max(1, end_idx - idx)),
            }
        )
        phrase_num += 1
        idx += phrase_size
    return spans


def _as_float_list(values: object) -> list[float]:
    try:
        return [float(item) for item in values]  # type: ignore[arg-type]
    except Exception:
        return []


def build_energy_prediction(
    *,
    audio,
    horizon_ms: int = 1200,
    step_ms: int = 180,
    max_points: int = 220,
) -> dict[str, object]:
    points = _as_float_list(getattr(audio, "times_s", []))
    rms = _as_float_list(getattr(audio, "rms01", []))
    if not points or not rms or len(points) != len(rms):
        return {
            "horizon_ms": int(horizon_ms),
            "point_count": 0,
            "max_predicted_lift": 0.0,
            "max_predicted_drop": 0.0,
            "points": [],
        }
    if len(points) < 2:
        current = rms[0]
        return {
            "horizon_ms": int(horizon_ms),
            "point_count": 1,
            "max_predicted_lift": 0.0,
            "max_predicted_drop": 0.0,
            "points": [
                {
                    "t_ms": int(round(points[0] * 1000.0)),
                    "current": round(float(current), 4),
                    "predicted_peak": round(float(current), 4),
                    "predicted_lift": 0.0,
                }
            ],
        }
    dt_ms = max(1.0, median([(points[idx + 1] - points[idx]) * 1000.0 for idx in range(len(points) - 1)]))
    lookahead = max(1, int(round(horizon_ms / dt_ms)))
    step = max(1, int(round(step_ms / dt_ms)))
    rows: list[dict[str, object]] = []
    for idx in range(0, len(points), step):
        end_idx = min(len(points), idx + lookahead + 1)
        window = rms[idx:end_idx]
        if not window:
            continue
        current = float(rms[idx])
        predicted_peak = float(max(window))
        predicted_floor = float(min(window))
        rows.append(
            {
                "t_ms": int(round(points[idx] * 1000.0)),
                "current": round(current, 4),
                "predicted_peak": round(predicted_peak, 4),
                "predicted_lift": round(predicted_peak - current, 4),
                "predicted_drop": round(predicted_floor - current, 4),
            }
        )
        if len(rows) >= max_points:
            break
    max_lift = max((float(row.get("predicted_lift", 0.0)) for row in rows), default=0.0)
    max_drop = min((float(row.get("predicted_drop", 0.0)) for row in rows), default=0.0)
    return {
        "horizon_ms": int(horizon_ms),
        "point_count": len(rows),
        "max_predicted_lift": round(max_lift, 4),
        "max_predicted_drop": round(max_drop, 4),
        "points": rows,
    }


def build_rhythm_intelligence(
    *,
    beat_ms: list[int],
    onset_ms: list[int],
    note_onset_ms: list[int],
    parts: list[object],
    audio,
) -> dict[str, object]:
    payload = default_payload()
    clean_beats = _sorted_unique_ms(beat_ms)
    clean_onsets = _sorted_unique_ms(onset_ms)
    clean_notes = _sorted_unique_ms(note_onset_ms) if note_onset_ms else clean_onsets
    if len(clean_beats) < 2:
        payload["energy_prediction"] = build_energy_prediction(audio=audio)
        return payload
    payload["polyrhythm_overlays"] = detect_polyrhythm_overlays(
        beat_ms=clean_beats,
        onset_ms=(clean_notes if clean_notes else clean_onsets),
    )
    payload["microtiming"] = build_microtiming_profile(
        onset_ms=clean_onsets,
        note_onset_ms=clean_notes,
        beat_ms=clean_beats,
        parts=parts,
    )
    payload["phrase_boundaries"] = derive_phrase_boundaries(
        beat_ms=clean_beats,
        parts=parts,
    )
    payload["energy_prediction"] = build_energy_prediction(audio=audio)
    return payload

