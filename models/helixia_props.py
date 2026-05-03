from __future__ import annotations

from dataclasses import dataclass, field


SNOWMAN_BAND_MEMBERS = (
    "HX_SNOWMAN_BASSIST",
    "HX_SNOWMAN_GUITARIST",
    "HX_SNOWMAN_DRUMMER",
    "HX_SNOWMAN_SINGER",
    "HX_SNOWMAN_SINGER_FEMALE",
)

CACTUS_TUBEMAN_MODELS = (
    "HX_CACTUS_BODY",
    "HX_CACTUS_FACE",
    "HX_TUBEMAN_BODY",
    "HX_TUBEMAN_ARMS",
    "HX_DJ_BOOTH",
)


@dataclass(frozen=True)
class HelixiaSubmodelDefinition:
    name: str
    parent_model: str
    category: str


@dataclass(frozen=True)
class HelixiaModelDefinition:
    name: str
    category: str
    submodels: tuple[str, ...] = field(default_factory=tuple)
    exportable: bool = True


@dataclass(frozen=True)
class HelixiaGroupDefinition:
    name: str
    members: tuple[str, ...]


@dataclass(frozen=True)
class HelixiaPropDefinition:
    name: str
    models: tuple[HelixiaModelDefinition, ...]
    submodels: tuple[HelixiaSubmodelDefinition, ...]
    groups: tuple[HelixiaGroupDefinition, ...]


def _submodel_names(prop_name: str, suffixes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"{prop_name}_{suffix}" for suffix in suffixes)


def _build_snowman_member_structure(
    *,
    prop_name: str,
    instrument_suffixes: tuple[str, ...],
) -> HelixiaPropDefinition:
    body_submodels = _submodel_names(prop_name, ("ARMS", "HEAD", "TORSO"))
    instrument_submodels = _submodel_names(prop_name, instrument_suffixes)
    body_model = HelixiaModelDefinition(
        name=f"{prop_name}_BODY",
        category="body",
        submodels=body_submodels,
    )
    instrument_model = HelixiaModelDefinition(
        name=f"{prop_name}_INSTRUMENT",
        category="instrument",
        submodels=instrument_submodels,
    )
    submodels = tuple(
        HelixiaSubmodelDefinition(name=name, parent_model=body_model.name, category="body")
        for name in body_submodels
    ) + tuple(
        HelixiaSubmodelDefinition(name=name, parent_model=instrument_model.name, category="instrument")
        for name in instrument_submodels
    )
    groups = (
        HelixiaGroupDefinition(
            name=prop_name,
            members=(body_model.name, instrument_model.name),
        ),
        HelixiaGroupDefinition(
            name="HX_SNOWMAN_BAND",
            members=(prop_name,),
        ),
        HelixiaGroupDefinition(
            name="HELIXIA_STAGE",
            members=("HX_SNOWMAN_BAND",),
        ),
    )
    return HelixiaPropDefinition(
        name=prop_name,
        models=(body_model, instrument_model),
        submodels=submodels,
        groups=groups,
    )


def build_snowman_bassist_structure() -> HelixiaPropDefinition:
    return _build_snowman_member_structure(
        prop_name="HX_SNOWMAN_BASSIST",
        instrument_suffixes=("BASS_BODY", "BASS_NECK", "BASS_STRINGS", "PLUCK_ZONE"),
    )


def build_snowman_guitarist_structure() -> HelixiaPropDefinition:
    return _build_snowman_member_structure(
        prop_name="HX_SNOWMAN_GUITARIST",
        instrument_suffixes=("GUITAR_BODY", "GUITAR_NECK", "GUITAR_STRINGS", "STRUM_ZONE"),
    )


def build_snowman_drummer_structure() -> HelixiaPropDefinition:
    return _build_snowman_member_structure(
        prop_name="HX_SNOWMAN_DRUMMER",
        instrument_suffixes=("KICK", "SNARE", "TOM", "CYMBALS", "HI_HAT", "STICKS"),
    )


def build_snowman_singer_structure() -> HelixiaPropDefinition:
    return _build_snowman_member_structure(
        prop_name="HX_SNOWMAN_SINGER",
        instrument_suffixes=("MICROPHONE", "MIC_STAND"),
    )


def build_snowman_singer_female_structure() -> HelixiaPropDefinition:
    return _build_snowman_member_structure(
        prop_name="HX_SNOWMAN_SINGER_FEMALE",
        instrument_suffixes=("MICROPHONE", "MIC_STAND"),
    )


def build_snowman_band_structures() -> tuple[HelixiaPropDefinition, ...]:
    return (
        build_snowman_bassist_structure(),
        build_snowman_guitarist_structure(),
        build_snowman_drummer_structure(),
        build_snowman_singer_structure(),
        build_snowman_singer_female_structure(),
    )


def build_snowman_band_group_definitions() -> tuple[HelixiaGroupDefinition, ...]:
    member_groups = tuple(prop.groups[0] for prop in build_snowman_band_structures())
    return member_groups + (
        HelixiaGroupDefinition(
            name="HX_SNOWMAN_BAND",
            members=SNOWMAN_BAND_MEMBERS,
        ),
        HelixiaGroupDefinition(
            name="HELIXIA_STAGE",
            members=("HX_SNOWMAN_BAND",),
        ),
    )


def build_cactus_tubeman_dj_structure() -> HelixiaPropDefinition:
    model_submodels = {
        "HX_CACTUS_BODY": ("HX_CACTUS_BODY_CORE", "HX_CACTUS_LEFT_ARM", "HX_CACTUS_RIGHT_ARM"),
        "HX_CACTUS_FACE": ("HX_CACTUS_FACE_EYES", "HX_CACTUS_FACE_MOUTH"),
        "HX_TUBEMAN_BODY": ("HX_TUBEMAN_BODY_CORE", "HX_TUBEMAN_HEAD"),
        "HX_TUBEMAN_ARMS": ("HX_TUBEMAN_LEFT_ARM", "HX_TUBEMAN_RIGHT_ARM"),
        "HX_DJ_BOOTH": ("HX_DJ_BOOTH_FRONT", "HX_DJ_BOOTH_DECKS", "HX_DJ_BOOTH_SPEAKERS"),
    }
    model_categories = {
        "HX_CACTUS_BODY": "character_body",
        "HX_CACTUS_FACE": "face",
        "HX_TUBEMAN_BODY": "character_body",
        "HX_TUBEMAN_ARMS": "arms",
        "HX_DJ_BOOTH": "stage_prop",
    }
    models = tuple(
        HelixiaModelDefinition(
            name=model_name,
            category=model_categories[model_name],
            submodels=model_submodels[model_name],
        )
        for model_name in CACTUS_TUBEMAN_MODELS
    )
    submodels = tuple(
        HelixiaSubmodelDefinition(
            name=submodel_name,
            parent_model=model_name,
            category=model_categories[model_name],
        )
        for model_name in CACTUS_TUBEMAN_MODELS
        for submodel_name in model_submodels[model_name]
    )
    groups = (
        HelixiaGroupDefinition(
            name="HX_CACTUS_TUBEMAN_GROUP",
            members=CACTUS_TUBEMAN_MODELS,
        ),
        HelixiaGroupDefinition(
            name="HELIXIA_STAGE",
            members=("HX_CACTUS_TUBEMAN_GROUP",),
        ),
    )
    return HelixiaPropDefinition(
        name="HX_CACTUS_TUBEMAN_GROUP",
        models=models,
        submodels=submodels,
        groups=groups,
    )


def model_definition_to_dict(model: HelixiaModelDefinition) -> dict[str, object]:
    return {
        "name": model.name,
        "category": model.category,
        "submodels": list(model.submodels),
        "exportable": bool(model.exportable),
    }


def submodel_definition_to_dict(submodel: HelixiaSubmodelDefinition) -> dict[str, object]:
    return {
        "name": submodel.name,
        "parent_model": submodel.parent_model,
        "category": submodel.category,
    }


def group_definition_to_dict(group: HelixiaGroupDefinition) -> dict[str, object]:
    return {
        "name": group.name,
        "members": list(group.members),
    }


def prop_definition_to_dict(prop: HelixiaPropDefinition) -> dict[str, object]:
    return {
        "name": prop.name,
        "models": [model_definition_to_dict(model) for model in prop.models],
        "submodels": [submodel_definition_to_dict(submodel) for submodel in prop.submodels],
        "groups": [group_definition_to_dict(group) for group in prop.groups],
    }


def build_snowman_band_export_catalog() -> dict[str, object]:
    props = build_snowman_band_structures()
    groups = build_snowman_band_group_definitions()
    return {
        "schema": "helixia.props.catalog.v1",
        "catalog_id": "HX_SNOWMAN_BAND",
        "scope": "structure_only",
        "implementation_boundary": {
            "layout_generation": False,
            "layout_xml_modification": False,
            "sequencing": False,
            "timing": False,
            "audio": False,
            "animation": False,
        },
        "props": [prop_definition_to_dict(prop) for prop in props],
        "groups": [group_definition_to_dict(group) for group in groups],
    }
