from __future__ import annotations

import argparse
from pathlib import Path

from core.wadena_spatial_propagation import PropagationProfile, compile_direction_propagation
from core.wadena_temporal_renderer import render_samples_at
from core.wadena_xsq_emitter import emit_wadena_xsq_sequence


def build_proof(output: Path) -> Path:
    profile = PropagationProfile(travel_s=0.55, decay_s=0.8, strength=1.0, spread=1.0)
    samples = compile_direction_propagation(
        direction="left_to_right",
        launch_s=1.0,
        duration_s=0.55 * 4 + 0.8,
        profile=profile,
    )
    # Use the graph's deterministic landmark order as a compact proof map.
    landmark_names = [sample.landmark for sample in samples]
    unique = tuple(dict.fromkeys(landmark_names))
    events = tuple(render_samples_at(samples, t) for t in (1.0, 1.55, 2.10, 2.65, 3.20))
    flat = tuple(event for frame in events for event in frame)
    channel_map = {name: f"WADENA_PROOF_{index + 1:03d}" for index, name in enumerate(unique)}
    sequence = emit_wadena_xsq_sequence(
        events=flat,
        landmark_channels=channel_map,
        sequence_name="WadenaPropagationProof",
        model_name="WADENA_AC",
        grid_ms=50,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(sequence.xml_text, encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(build_proof(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
