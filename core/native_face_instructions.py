"""Compile vocal cues only against existing native mouth definitions."""
from __future__ import annotations
from core.singing_face_discovery import SingingFace
from core.singing_face_routing import route_singing_faces
from xlights.xsq_writer import EffectTemplate


def exclusive_face_targets(layout) -> set[str]:
    """Opt-in canonical mouths cannot also receive decorative whole-face FX."""
    if layout is None:
        return set()
    models = getattr(layout, 'models', {})
    roots = {name for name, model in models.items()
             if not getattr(model, 'is_submodel', False)
             and getattr(model, 'raw_attrs', {}).get('HelixPhonemeOwnership') == 'exclusive'}
    reserved = set(roots)
    reserved.update(name for name, model in models.items()
                    if getattr(model, 'parent_name', None) in roots
                    and name.rsplit('/', 1)[-1].upper().startswith('MOUTH_'))
    # A whole-face group effect would light the same protected mouth nodes.
    changed = True
    while changed:
        changed = False
        for name, group in getattr(layout, 'groups', {}).items():
            if name not in reserved and set(group.models) & reserved:
                reserved.add(name)
                changed = True
    return reserved


def face_template(cue: dict, faces: list[SingingFace], palette: str | None) -> EffectTemplate | None:
    target = str(cue.get("target_model", ""))
    mouth = str(cue.get("mouth_shape", "")).removeprefix("mouth_").upper()
    if mouth == "CLOSED":
        mouth = "REST"
    candidates = [face for face in faces if face.model == target]
    requested = cue.get("face_definition")
    if cue.get("face_definition_origin") == "generated_style_hint":
        # Planner style labels are not imported faceInfo names. Bind only an
        # unambiguous real definition on this same singer. Explicit selections
        # (including absent names) retain the strict b418efe behavior below.
        definitions = {face.name for face in candidates}
        if len(definitions) != 1:
            return None
        requested = next(iter(definitions))
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
        if native_phoneme in {'REST', 'ETC'}:
            native_phoneme = native_phoneme.lower()
        settings = (f"E_CHOICE_Faces_FaceDefinition={face.name},E_CHOICE_Faces_Phoneme={native_phoneme},"
                    "E_CHOICE_Faces_Eyes=Off,E_CHECKBOX_Faces_Outline=0,E_CHECKBOX_Faces_SuppressShimmer=1")
        return EffectTemplate(settings=settings, palette=palette)
    return None
