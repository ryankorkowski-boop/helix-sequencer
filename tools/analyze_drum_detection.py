#!/usr/bin/env python3
"""Run Helix drum detection and emit measurable classification diagnostics."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from audio.drum_detection import detect_drum_event_streams_from_file
from core.audio_intelligence import build_stem_analysis


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _summarize_streams(
    streams: dict[str, list[object]],
    *,
    audio: Path,
    analysis_mode: str,
    stem_source: str,
    stems: dict[str, Path] | None = None,
) -> dict[str, object]:
    class_counts: Counter[str] = Counter()
    stream_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    confidence: dict[str, list[float]] = defaultdict(list)
    detector_agreement: list[float] = []
    detector_onset: list[float] = []
    detector_flux: list[float] = []
    support_counts: list[float] = []
    events: list[dict[str, object]] = []
    clusters: dict[str, set[str]] = defaultdict(set)

    for stream, items in streams.items():
        stream_counts[stream] += len(items)
        for event in items:
            drum_type = str(getattr(event, "drum_type", "drum_bus"))
            score = float(getattr(event, "confidence", 0.0) or 0.0)
            source = str(getattr(event, "source", "unknown"))
            features = dict(getattr(event, "frequency_band_info", {}) or {})
            timestamp = float(getattr(event, "timestamp", 0.0) or 0.0)
            cluster_id = getattr(event, "cluster_id", None)

            class_counts[drum_type] += 1
            source_counts[source] += 1
            confidence[drum_type].append(score)
            detector_agreement.append(float(features.get("detector_agreement", 0.0) or 0.0))
            detector_onset.append(float(features.get("detector_onset", 0.0) or 0.0))
            detector_flux.append(float(features.get("detector_spectral_flux", 0.0) or 0.0))
            support_counts.append(float(features.get("family_support_count", 0.0) or 0.0))

            cluster_key = str(cluster_id) if cluster_id is not None else f"t:{timestamp:.4f}"
            clusters[cluster_key].add(drum_type)

            family_scores = {
                key.removeprefix("score_"): round(float(value), 4)
                for key, value in features.items()
                if key.startswith("score_")
            }
            events.append(
                {
                    "timestamp": round(timestamp, 6),
                    "timestamp_ms": int(round(timestamp * 1000.0)),
                    "source_stream": stream,
                    "classified_type": drum_type,
                    "confidence": round(score, 4),
                    "source": source,
                    "cluster_id": cluster_id,
                    "detectors": {
                        "onset": float(features.get("detector_onset", 0.0) or 0.0),
                        "spectral_flux": float(features.get("detector_spectral_flux", 0.0) or 0.0),
                        "agreement": float(features.get("detector_agreement", 0.0) or 0.0),
                    },
                    "family_support_count": int(round(float(features.get("family_support_count", 0.0) or 0.0))),
                    "family_scores": family_scores,
                }
            )

    events.sort(key=lambda x: (int(x["timestamp_ms"]), str(x["classified_type"])))
    total = len(events)
    bus_count = int(class_counts.get("drum_bus", 0))
    multi_hit_clusters = sum(1 for types in clusters.values() if len(types) > 1)
    agreement_two = sum(1 for value in detector_agreement if value >= 2.0)
    agreement_one = sum(1 for value in detector_agreement if 1.0 <= value < 2.0)

    summary = {
        "audio": str(audio),
        "analysis_mode": analysis_mode,
        "stem_source": stem_source,
        "stems": {name: str(path) for name, path in sorted((stems or {}).items())},
        "candidate_events": total,
        "class_counts": dict(sorted(class_counts.items())),
        "stream_counts": dict(sorted(stream_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "typed_event_fraction": round((total - bus_count) / total, 4) if total else 0.0,
        "drum_bus_fraction": round(bus_count / total, 4) if total else 0.0,
        "confidence": {
            key: {
                "count": len(values),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "mean": _mean(values),
            }
            for key, values in sorted(confidence.items())
            if values
        },
        "detector_evidence": {
            "both_detectors": agreement_two,
            "single_detector": agreement_one,
            "mean_agreement": _mean(detector_agreement),
            "mean_onset_vote": _mean(detector_onset),
            "mean_spectral_flux_vote": _mean(detector_flux),
        },
        "multi_hit_clusters": multi_hit_clusters,
        "cluster_count": len(clusters),
        "mean_family_support_count": _mean(support_counts),
        "events": events,
    }
    return summary


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("audio", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--use-stems",
        action="store_true",
        help="Run the production stem-analysis path and classify the isolated drums stem when available.",
    )
    p.add_argument(
        "--stem-cache",
        type=Path,
        default=Path("test_runs/stem_cache"),
        help="Cache directory used by the stem-analysis path.",
    )
    args = p.parse_args()

    if args.use_stems:
        analysis = build_stem_analysis(
            audio_path=args.audio,
            use_moises=False,
            api_key=None,
            cache_dir=args.stem_cache,
        )
        streams = analysis.drum_event_streams or {}
        summary = _summarize_streams(
            streams,
            audio=args.audio,
            analysis_mode="stem",
            stem_source=analysis.source,
            stems=analysis.stems,
        )
    else:
        streams = detect_drum_event_streams_from_file(args.audio, source_label="direct:mix")
        summary = _summarize_streams(
            streams,
            audio=args.audio,
            analysis_mode="direct_mix",
            stem_source="direct",
            stems={},
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    keys = (
        "audio",
        "analysis_mode",
        "stem_source",
        "candidate_events",
        "class_counts",
        "typed_event_fraction",
        "drum_bus_fraction",
        "detector_evidence",
        "multi_hit_clusters",
    )
    print(json.dumps({key: summary[key] for key in keys}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
