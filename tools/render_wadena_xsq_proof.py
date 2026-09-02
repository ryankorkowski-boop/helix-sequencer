from __future__ import annotations

import argparse
from pathlib import Path

from core.wadena_spatial_propagation import PropagationProfile, compile_direction_propagation
from core.wadena_temporal_renderer import compile_ac_safe_events
from core.wadena_xsq_emitter import emit_wadena_xsq_sequence


def build_proof(output: Path) -> Path:
    profile = PropagationProfile(
        launch_s=1.0,
        travel_s=0.55,
        attack_s=0.05,
        decay_s=0.8,
        hop_decay=1.0,
    )
    samples = compile_direction_propagation(
        direction="left_to_right",
        strength=1.0,
        profile=profile,
    )
    events = compile_ac_safe_events(samples, effect="Ramp")
    unique = tuple(dict.fromkeys(event.landmark for event in events))
    channel_map = {
        name: f"WADENA_PROOF_{index + 1:03d}"
        for index, name in enumerate(unique)
    }
    sequence = emit_wadena_xsq_sequence(
        events=events,
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
