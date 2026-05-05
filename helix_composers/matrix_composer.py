from __future__ import annotations


def compose_matrix(intent_type: str, *, density_budget: float) -> dict[str, object]:
    if density_budget < 0.4:
        return {"composer": "matrix", "mode": "low_density_fallback", "surface": "large_text_or_face_support"}
    return {"composer": "matrix", "mode": "full_surface", "surface": "particles_or_waveform"}
