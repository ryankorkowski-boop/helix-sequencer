from __future__ import annotations


def migration_hints(source_role: str, target_role: str) -> list[str]:
    hints = []
    if source_role != target_role:
        hints.append(f"Map {source_role} intent into nearest {target_role} proxy.")
    return hints or ["Direct role mapping is available."]
