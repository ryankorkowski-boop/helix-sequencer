from __future__ import annotations


def detect_mapping_failures(*, source_density: float, target_density: float, has_submodel: bool, is_ac: bool, requires_pixels: bool) -> list[str]:
    failures: list[str] = []
    if source_density - target_density > 0.35:
        failures.append("density_mismatch")
    if requires_pixels and is_ac:
        failures.append("AC_pixel_mismatch")
    if not has_submodel and source_density >= 0.7:
        failures.append("missing_submodel")
    return failures
