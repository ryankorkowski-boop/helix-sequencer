from __future__ import annotations


def palette_for_emotion(emotion: str) -> list[str]:
    palettes = {
        "bright": ["#FFD166", "#F72585", "#4CC9F0"],
        "dark": ["#1D3557", "#457B9D", "#A8DADC"],
        "dramatic": ["#D90429", "#2B2D42", "#EDF2F4"],
        "calm": ["#86E3CE", "#D0F4DE", "#F8FFE5"],
    }
    return palettes.get(emotion, ["#FFFFFF", "#AAAAAA", "#333333"])
