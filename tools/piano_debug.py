from __future__ import annotations

import argparse
import json
from pathlib import Path

from effects.piano_effect import PianoEffectConfig, build_piano_effect_plan, load_note_events


def main() -> int:
    parser = argparse.ArgumentParser(description="Debug Helix piano effect note timelines and frame data.")
    parser.add_argument("midi", nargs="?", help="Optional MIDI file to inspect.")
    parser.add_argument("--mode", choices=("true_piano", "bars"), default="true_piano")
    parser.add_argument("--range-start", type=int, default=21)
    parser.add_argument("--range-end", type=int, default=108)
    parser.add_argument("--out", default="", help="Optional JSON output path.")
    args = parser.parse_args()
    events = load_note_events(
        midi_path=Path(args.midi) if args.midi else None,
        note_range_start=args.range_start,
        note_range_end=args.range_end,
    )
    frame_times = [event.start for event in events[:24]]
    config = PianoEffectConfig(mode=args.mode, note_range_start=args.range_start, note_range_end=args.range_end)
    plan = build_piano_effect_plan(events, config, frame_times=frame_times)
    text = json.dumps(plan["debug"], indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
