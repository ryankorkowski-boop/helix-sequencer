"""Sparse, source-bound tom identity reviews; never synthesize musical attacks."""
import json
import math
from pathlib import Path

SCHEMA = "helix.drum_review.v1"


def apply_tom_review(rows, audio_sha256, path):
    review = json.loads(Path(path).read_text(encoding="utf-8"))
    if review.get("schema") != SCHEMA:
        raise ValueError("Unsupported drum review schema")
    if review.get("audio_sha256") != audio_sha256:
        raise ValueError("Drum review does not belong to this song")
    resolved, used = {}, set()
    for annotation in review["annotations"]:
        timestamp = float(annotation["timestamp"])
        tolerance = float(annotation["tolerance_ms"]) / 1000
        if (not math.isfinite(timestamp) or timestamp < 0
                or not math.isfinite(tolerance) or not 0 < tolerance <= .1):
            raise ValueError("Invalid drum review timing or tolerance")
        if annotation.get("drum_family") != "tom" or annotation.get("tom_class") not in {"high", "mid", "floor"}:
            raise ValueError("Drum review requires an explicit tom class")
        if not annotation.get("label_source"):
            raise ValueError("Drum review must identify its label source")
        matches = [i for i, row in enumerate(rows) if row["drum_family"] == "tom"
                   and abs(float(row["timestamp"]) - timestamp) <= tolerance + 1e-9]
        if len(matches) != 1 or matches[0] in used:
            raise ValueError("Drum review must uniquely match an existing tom attack")
        index = matches[0]
        if rows[index].get("rejection_reason") not in {None, "unresolved_tom_identity"}:
            raise ValueError("Drum review cannot bypass other rejection gates")
        used.add(index)
        resolved[index] = annotation
    updated = []
    for i, row in enumerate(rows):
        if i not in resolved:
            updated.append(row)
            continue
        annotation = resolved[i]
        evidence = dict(row.get("evidence", {}))
        evidence["tom_review"] = dict(annotation,
            original_tom_class=row.get("tom_class"),
            original_rejection_reason=row.get("rejection_reason"),
            original_identity_method=evidence.get("tom_identity_method"))
        evidence["tom_identity_method"] = "source_bound_reviewed_annotation"
        updated.append(dict(row, tom_class=annotation["tom_class"],
                            rejection_reason=None, evidence=evidence))
    return updated, dict(source=str(path), annotations=review["annotations"],
                         resolved_event_count=len(resolved),
                         review_status="partial_source_bound_tom_review")
