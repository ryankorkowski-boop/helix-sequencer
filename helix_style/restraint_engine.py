from __future__ import annotations


def prop_cooldown_ok(history: list[str], prop_name: str, cooldown: int = 2) -> bool:
    return history[-cooldown:].count(prop_name) == 0
