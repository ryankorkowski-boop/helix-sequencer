"""Compile vocal cues only against existing native mouth definitions."""
from __future__ import annotations
from core.singing_face_discovery import SingingFace
from core.singing_face_routing import route_singing_faces
from xlights.xsq_writer import EffectTemplate


def face_template(cue: dict, faces: list[SingingFace], palette: str | None) -> EffectTemplate | None:
    target = str(cue.get("target_model", ""))
    mouth = str(cue.get("mouth_shape", "")).removeprefix("mouth_").upper()
    if mouth == "CLOSED":
        mouth = "REST"
    candidates = [face for face in faces if face.model == target]
    requested = cue.get("face_definition")
    # An explicitly selected definition must never silently animate a different face.
    if requested is not None:
        candidates = [face for face in candidates if face.name == requested]
    for face in candidates:
        mapped = route_singing_faces([face])[0:1]
        if not mapped or mouth not in mapped[0].phoneme_keys or any(char in face.name for char in (",", "=", "\n", "\r")):
            continue
        attribute = mapped[0].phoneme_keys[mouth]
        # xLights consumes the face's actual standard phoneme alias (e.g. AI).
        native_phoneme = attribute.replace("_", "-").split("-")[-1].upper()
        settings = (f"E_CHOICE_Faces_FaceDefinition={face.name},E_CHOICE_Faces_Phoneme={native_phoneme},"
                    "E_CHOICE_Faces_Eyes=Off,E_CHECKBOX_Faces_Outline=0,E_CHECKBOX_Faces_SuppressShimmer=1")
        return EffectTemplate(settings=settings, palette=palette)
    return None
