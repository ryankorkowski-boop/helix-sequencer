"""Discover native xLights singing-face definitions without relying on model names.

Read-only scanner: never changes imported layout XML or channel mappings.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class SingingFace:
    model: str
    name: str
    type: str
    mappings: dict[str, str]
    source: str


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1].lower()


def _scan_root(root: ET.Element, source: str) -> list[SingingFace]:
    found: list[SingingFace] = []
    seen: set[tuple[str, str, str]] = set()
    for model in root.iter():
        if _tag(model) not in {"model", "custommodel"}:
            continue
        model_name = model.get("name") or model.get("Name") or ""
        if not model_name:
            continue
        for child in model.iter():
            if _tag(child) not in {"faceinfo", "face"}:
                continue
            name = child.get("Name") or child.get("name") or "Default"
            kind = child.get("Type") or child.get("type") or ""
            mappings = {
                key: value for key, value in child.attrib.items()
                if key.lower() not in {"name", "type"} and value.strip()
            }
            if not mappings:
                continue
            key = (model_name, name, source)
            if key in seen:
                continue
            seen.add(key)
            found.append(SingingFace(model_name, name, kind, mappings, source))
    return found


def detect_singing_faces(layout_path: str | Path, *, include_external: bool = True) -> list[SingingFace]:
    """Discover embedded face definitions and optional adjacent .xmodel assets.

    XML is read only; external models are searched only in the layout directory.
    """
    path = Path(layout_path)
    root = ET.parse(path).getroot()
    found = _scan_root(root, str(path))
    if include_external:
        for candidate in sorted(path.parent.glob("*.xmodel")):
            try:
                found.extend(_scan_root(ET.parse(candidate).getroot(), str(candidate)))
            except (ET.ParseError, OSError):
                continue
    return found


def singing_face_summary(layout_path: str | Path) -> dict:
    faces = detect_singing_faces(layout_path)
    models = sorted({face.model for face in faces})
    return {
        "singing_model_count": len(models),
        "singing_models": models,
        "face_definition_count": len(faces),
        "faces": [
            {"model": face.model, "name": face.name, "type": face.type,
             "mappings": face.mappings, "source": face.source}
            for face in faces
        ],
    }
