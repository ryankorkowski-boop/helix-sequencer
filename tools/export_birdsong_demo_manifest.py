from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from core.birdsong_behavior_planner import EffectIntent, plan_effect_intent
from core.birdsong_feature_state import FeatureState
from core.birdsong_intent_manifest import write_intent_manifest
from core.birdsong_phrase_engine import PhraseEngine


def demo_feature_at(time: float, duration: float) -> dict[str, object]:
    phase = max(0.0, min(1.0, time / max(duration, 0.001)))
    if phase < 0.25:
        return {"energy": 0.35 + phase, "onset": 0.75 if time == 0 else 0.2, "bands": (0.6, 0.3, 0.1), "beat_phase": phase}
    if phase < 0.50:
        return {"energy": 0.65, "onset": 0.8 if abs(time - 5.0) < 0.001 else 0.25, "bands": (0.2, 0.65, 0.15), "beat_phase": phase}
    if phase < 0.75:
        return {"energy": 0.8, "onset": 0.85 if abs(time - 10.0) < 0.001 else 0.35, "bands": (0.15, 0.25, 0.6), "beat_phase": phase}
    return {"energy": 0.55, "onset": 0.7 if abs(time - 15.0) < 0.001 else 0.2, "bands": (0.3, 0.45, 0.25), "beat_phase": phase}


def build_birdsong_demo_intents(*, duration_seconds: float = 20.0, step_seconds: float = 1.0, bpm: float = 120.0) -> tuple[EffectIntent, ...]:
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")
    if step_seconds <= 0:
        raise ValueError("step_seconds must be > 0")

    state = FeatureState(smoothing_alpha=0.35)
    phrase_engine = PhraseEngine(bpm=bpm)
    intents: list[EffectIntent] = []
    recent_effects: list[str] = []
    previous_effect: str | None = None

    steps = int(duration_seconds / step_seconds)
    for index in range(steps):
        time = round(index * step_seconds, 6)
        state.update(demo_feature_at(time, duration_seconds))
        phrase = phrase_engine.update(time, state)
        intent = plan_effect_intent(
            state=state,
            phrase=phrase,
            time=time,
            recent_effects=tuple(recent_effects[-4:]),
            previous_effect=previous_effect,
        )
        if intent is None:
            continue
        intents.append(intent)
        recent_effects.append(intent.effect_name)
        previous_effect = intent.effect_name

    return tuple(intents)


def export_birdsong_demo_manifest(output: Path, *, duration_seconds: float = 20.0, step_seconds: float = 1.0, bpm: float = 120.0) -> Path:
    intents = build_birdsong_demo_intents(duration_seconds=duration_seconds, step_seconds=step_seconds, bpm=bpm)
    return write_intent_manifest(output, intents, title=f"BirdsongDemo{int(duration_seconds)}s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a deterministic 20-second Birdsong Engine demo intent manifest.")
    parser.add_argument("--output", type=Path, default=Path("test_runs/birdsong_demo/birdsong_intents.json"))
    parser.add_argument("--duration-seconds", type=float, default=20.0)
    parser.add_argument("--step-seconds", type=float, default=1.0)
    parser.add_argument("--bpm", type=float, default=120.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = export_birdsong_demo_manifest(
        args.output,
        duration_seconds=args.duration_seconds,
        step_seconds=args.step_seconds,
        bpm=args.bpm,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
