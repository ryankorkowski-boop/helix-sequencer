"""Reproducible blind comparison scoring for Helix vs vendor/community sequences.

Scores are supplied by human reviewers; this tool does not manufacture ratings.
Input JSON: {"entries":[{"id":"...", "kind":"helix|vendor|community",
"reviewer":"...", "scores":{"synchronization":0..5, "choreography":0..5,
"performance":0..5,"compatibility":0..5,"import":0..5}}]}.
"""
from __future__ import annotations
import argparse
import json
from collections import defaultdict
from pathlib import Path

WEIGHTS = {"synchronization":30, "choreography":25, "performance":20,
           "compatibility":15, "import":10}
KINDS = {"helix", "vendor", "community"}


def score_entries(entries):
    results = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("kind") not in KINDS:
            raise ValueError("Each entry needs a recognized kind")
        identifier = entry.get("id")
        reviewer = entry.get("reviewer")
        if not isinstance(identifier, str) or not identifier.strip() or not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("Each entry needs nonempty id and reviewer")
        identity = (identifier, reviewer)
        if identity in seen:
            raise ValueError("Duplicate reviewer/item rating")
        seen.add(identity)
        scores = entry.get("scores")
        if not isinstance(scores, dict) or set(scores) != set(WEIGHTS):
            raise ValueError("All five categories are required")
        for name, value in scores.items():
            if type(value) not in (int, float) or not 0 <= value <= 5:
                raise ValueError(f"Invalid score for {name}: expected 0..5")
        total = sum(scores[name] * weight for name, weight in WEIGHTS.items()) / 5
        results.append({"id": identifier, "kind": entry["kind"],
                        "reviewer": reviewer, "score_100": round(total, 3)})
    return results


def summarize(entries):
    rows = score_entries(entries)
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["id"], row["kind"])].append(row["score_100"])
    return {"weights": WEIGHTS, "individual": rows,
            "items": [{"id": key[0], "kind": key[1], "review_count": len(values),
                       "mean_score_100": round(sum(values) / len(values), 3)}
                      for key, values in sorted(grouped.items())]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        parser.error("Expected JSON object containing entries list")
    report = json.dumps(summarize(payload["entries"]), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
