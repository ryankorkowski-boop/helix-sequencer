from __future__ import annotations


def enforce_intent_restraint(intents: list[dict[str, object]], *, max_full_density: int = 2) -> list[dict[str, object]]:
    restrained: list[dict[str, object]] = []
    full_count = 0
    for item in intents:
        updated = dict(item)
        if str(updated.get("density_level", "")) == "full":
            full_count += 1
            if full_count > max_full_density:
                updated["density_level"] = "medium"
                updated["brightness_strategy"] = "restrained_after_peak"
        restrained.append(updated)
    return restrained
