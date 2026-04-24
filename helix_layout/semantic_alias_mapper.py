from __future__ import annotations


ALIASES = {
    "mega tree": "mega_tree",
    "megatree": "mega_tree",
    "pixel tree": "mega_tree",
    "arch row": "arches",
    "leaping arches": "arches",
    "panel": "matrix",
    "screen": "matrix",
    "topper": "star",
    "starburst": "star",
    "snowflake": "spinner",
    "fan": "spinner",
    "coro face": "singing_face",
    "face": "singing_face",
    "eaves": "roofline",
    "outline": "roofline",
    "small tree": "mini_tree",
    "yard tree": "mini_tree",
}


def semantic_alias(value: str) -> str:
    normalized = " ".join((value or "").lower().replace("_", " ").replace("-", " ").split())
    return ALIASES.get(normalized, normalized.replace(" ", "_"))
