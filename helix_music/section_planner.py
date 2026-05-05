from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SongSection:
    name: str
    start_time: float
    end_time: float
    energy_level: float
    density_budget: float
    brightness_budget: float
    recommended_prop_coverage: str
    palette_hint: str
    motif_role: str
    transition_in: str
    transition_out: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_song_sections(duration_seconds: float, tempo_class: str = "medium") -> list[SongSection]:
    duration = max(20.0, float(duration_seconds))
    marks = [0.0, duration * 0.16, duration * 0.40, duration * 0.58, duration * 0.76, duration * 0.90, duration]
    names = ["intro", "verse", "pre_chorus", "chorus", "bridge", "final_chorus"]
    sections: list[SongSection] = []
    defaults = {
        "intro": (0.22, 0.18, "localized", "tease", "fade_in", "lift"),
        "verse": (0.38, 0.34, "localized", "support", "steady", "build"),
        "pre_chorus": (0.58, 0.54, "widening", "build", "rise", "release"),
        "chorus": (0.82, 0.78, "full_layout", "hero", "impact", "settle"),
        "bridge": (0.46, 0.42, "contrast", "contrast", "reset", "lift"),
        "final_chorus": (0.9, 0.86, "full_layout", "hero_return", "reimpact", "resolve"),
    }
    palette_hints = {
        "intro": "cool_tease",
        "verse": "vocal_support",
        "pre_chorus": "saturated_rise",
        "chorus": "full_color_lift",
        "bridge": "contrast_palette",
        "final_chorus": "max_lift_with_control",
    }
    for idx, name in enumerate(names):
        density_budget, brightness_budget, coverage, motif_role, transition_in, transition_out = defaults[name]
        if tempo_class == "fast" and name in {"pre_chorus", "chorus", "final_chorus"}:
            density_budget = min(1.0, density_budget + 0.06)
        sections.append(
            SongSection(
                name=name,
                start_time=round(marks[idx], 3),
                end_time=round(marks[idx + 1], 3),
                energy_level=round((density_budget + brightness_budget) * 0.5, 3),
                density_budget=round(density_budget, 3),
                brightness_budget=round(brightness_budget, 3),
                recommended_prop_coverage=coverage,
                palette_hint=palette_hints[name],
                motif_role=motif_role,
                transition_in=transition_in,
                transition_out=transition_out,
            )
        )
    sections.append(
        SongSection(
            name="outro",
            start_time=round(duration * 0.96, 3),
            end_time=round(duration, 3),
            energy_level=0.24,
            density_budget=0.18,
            brightness_budget=0.16,
            recommended_prop_coverage="localized",
            palette_hint="fade_resolve",
            motif_role="resolve",
            transition_in="echo",
            transition_out="fade_out",
        )
    )
    return sections
