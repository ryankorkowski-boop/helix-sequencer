from __future__ import annotations


def compose_ac_moment(intent_type: str) -> dict[str, object]:
    return {"composer": "ac", "intent_type": intent_type, "effect_family": "pulse" if "pulse" in intent_type else "wash"}
