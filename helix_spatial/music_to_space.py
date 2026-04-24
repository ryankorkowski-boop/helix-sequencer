from __future__ import annotations


def map_music_features_to_space(*, bass_energy: float, centroid: float, vocal_energy: float) -> dict[str, float]:
    return {
        "ground_weight": round(max(0.0, min(1.0, bass_energy)), 4),
        "height_weight": round(max(0.0, min(1.0, centroid)), 4),
        "center_focus": round(max(0.0, min(1.0, vocal_energy)), 4),
    }
