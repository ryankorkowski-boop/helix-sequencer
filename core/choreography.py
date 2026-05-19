from __future__ import annotations

from dataclasses import replace

from core.birdsong_generative import RenderEvent


ROLE_TOKENS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("drummer", ("drum", "kick", "snare", "tom", "cymbal")),
    ("guitar", ("guitar", "gtr")),
    ("bass", ("bass", "sub")),
    ("lead", ("sing", "singer", "face", "mouth", "vocal", "lead")),
    ("sparkle", ("star", "flake", "snow", "sparkle")),
)


class ChoreographyEngine:
    def __init__(self, model_names: list[str]) -> None:
        self.roles = {name: infer_role(name) for name in model_names}

    def transform_event(self, event: RenderEvent, phrase: object | None = None) -> RenderEvent:
        role = self.roles.get(event.model, infer_role(event.model))
        duration = max(1, int(event.end_ms - event.start_ms))
        effect = event.effect
        intensity = event.intensity

        if role == "drummer":
            duration = max(55, min(duration, 150))
            intensity = min(1.0, intensity * 1.12)
        elif role == "bass":
            duration = max(duration, 220)
            intensity = min(1.0, intensity * 1.06)
        elif role == "lead":
            duration = max(duration, 180)
            if event.effect == "On":
                effect = "Wave"
        elif role == "sparkle":
            duration = max(55, min(duration, 170))
            effect = "Twinkle" if event.effect == "On" else event.effect
            intensity = min(0.82, intensity)
        elif role == "guitar":
            duration = max(duration, 145)
            effect = "Wave" if event.effect in {"On", "Ramp"} else event.effect

        return replace(
            event,
            end_ms=event.start_ms + duration,
            effect=effect,
            intensity=max(0.0, min(1.0, intensity)),
        )


def infer_role(model_name: str) -> str:
    lower = str(model_name or "").lower()
    for role, tokens in ROLE_TOKENS:
        if any(token in lower for token in tokens):
            return role
    return "generic"
