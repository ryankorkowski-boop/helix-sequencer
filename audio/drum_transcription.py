"""Auditable polyphonic drum transcription import, independent of model vendor.

A transcript is tied to the original song bytes. Each source event has a family;
unknown tom identities abstain instead of rotating physical drums. Model output
is evidence, never a human-reviewed annotation by implication.
"""
from pathlib import Path
import hashlib
import json
import math
from collections import Counter

from audio.drum_classification import DrumEvent

SCHEMA = "helix.drum_transcription.v1"
FAMILIES = {"kick", "snare", "hihat", "cymbal", "tom"}


def _validate_values(row):
    timestamp = float(row["timestamp"])
    confidence, velocity = float(row["confidence"]), float(row["velocity"])
    if not math.isfinite(timestamp) or timestamp < 0:
        raise ValueError("Invalid transcription timestamp")
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in (confidence, velocity)):
        raise ValueError("Invalid transcription confidence or velocity")
    return timestamp, confidence, velocity


def load_drum_transcription(path, audio_path, review_path=None, calibration_path=None):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA:
        raise ValueError("Unsupported drum transcription schema")
    digest = hashlib.sha256(Path(audio_path).read_bytes()).hexdigest()
    if payload.get("audio_sha256") != digest:
        raise ValueError("Drum transcription does not belong to this song")
    source = payload.get("provenance", {})
    if not source.get("engine"):
        raise ValueError("Drum transcription must name its source engine")
    rows, review = payload["events"], None
    # Calibration must never launder an invalid original score/time.
    for row in rows:
        _validate_values(row)
    if review_path is not None:
        from audio.drum_review import apply_tom_review
        rows, review = apply_tom_review(rows, digest, review_path)
    calibration = None
    if calibration_path is not None:
        from audio.drum_source_calibration import apply_source_calibration
        rows, calibration = apply_source_calibration(rows, audio_path, calibration_path)
    events, audit = [], []
    for index, row in enumerate(rows):
        timestamp, confidence, velocity = _validate_values(row)
        family, tom = row["drum_family"], row.get("tom_class")
        reason = row.get("rejection_reason")
        if family not in FAMILIES:
            reason = "unsupported_instrument"
        elif family == "tom" and tom not in {"high", "mid", "floor"}:
            reason = "unresolved_tom_identity"
        info = dict(row.get("evidence", {}))
        info.update(onset_index=index, transcription_source_index=row.get("source_onset_index", index),
                    analysis_engine=source["engine"], tom_class=tom,
                    tom_class_confidence=row.get("tom_class_confidence", confidence),
                    transcription_provenance=source)
        audit.append(dict(timestamp=timestamp, drum_family=family, confidence=confidence,
                          velocity=velocity, source_onset_index=index, primary=info,
                          contextual=None, attack_refinement=None,
                          body_class=family if family in {"kick", "snare", "tom"} else None,
                          metal_class=family if family in {"hihat", "cymbal"} else None,
                          rejection_reason=reason,
                          scheduler_decision="not_submitted" if reason else "pending",
                          physical_target=None))
        if reason is None:
            events.append(DrumEvent(timestamp, velocity, confidence, info, index,
                                    family, source["engine"]))
    events.sort(key=lambda e: (e.timestamp, e.drum_type))
    diagnostics = dict(analysis_engine=source["engine"], transcription_provenance=source,
                        audio_sha256=digest, review_status=payload.get("review_status", "unreviewed"),
                        rejection_counts=dict(Counter(r["rejection_reason"] for r in audit if r["rejection_reason"])),
                        onset_candidate_count=len(audit), typed_event_count=len(events),
                        onset_audit=audit)
    if review is not None:
        diagnostics["tom_review"] = review
    if calibration is not None:
        diagnostics["source_calibration"] = calibration
    return events, diagnostics
