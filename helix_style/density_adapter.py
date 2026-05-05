from __future__ import annotations


def adapt_density(source_description: str, *, target: str) -> str:
    mapping = {
        "Dense matrix particles": "AC color pulses" if target == "ac" else "matrix particles",
        "Complex mega tree spiral": "broad bands or simple chase" if target == "ac" else "layered spiral",
        "Shader texture": "color wash + envelope" if target == "ac" else "shader texture",
    }
    return mapping.get(source_description, source_description)
