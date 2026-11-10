from __future__ import annotations

from dataclasses import dataclass, field

SNOWMAN_BAND_MEMBERS=("HX_SNOWMAN_BASSIST","HX_SNOWMAN_GUITARIST","HX_SNOWMAN_DRUMMER","HX_SNOWMAN_SINGER","HX_SNOWMAN_SINGER_FEMALE")
CACTUS_TUBEMAN_MODELS=("HX_CACTUS_BODY","HX_CACTUS_FACE","HX_TUBEMAN_BODY","HX_TUBEMAN_ARMS","HX_DJ_BOOTH")
FLOOR_PIANO_MODELS=("HX_FLOOR_PIANO_BASE","HX_FLOOR_PIANO_KEYS")
REINDEER_DANCE_MODELS=("HX_REINDEER_DANCE_BODY","HX_REINDEER_DANCE_LEGS")

@dataclass(frozen=True)
class HelixiaSubmodelDefinition:
    name:str; parent_model:str; category:str
@dataclass(frozen=True)
class HelixiaModelDefinition:
    name:str; category:str; submodels:tuple[str,...]=field(default_factory=tuple); exportable:bool=True
@dataclass(frozen=True)
class HelixiaGroupDefinition:
    name:str; members:tuple[str,...]
@dataclass(frozen=True)
class HelixiaPropDefinition:
    name:str; models:tuple[HelixiaModelDefinition,...]; submodels:tuple[HelixiaSubmodelDefinition,...]; groups:tuple[HelixiaGroupDefinition,...]

def _submodel_names(prop_name,suffixes): return tuple(f"{prop_name}_{suffix}" for suffix in suffixes)

def _build_snowman_member_structure(*,prop_name,instrument_suffixes):
    body_submodels=_submodel_names(prop_name,("ARMS","HEAD","TORSO")); instrument_submodels=_submodel_names(prop_name,instrument_suffixes)
    body_model=HelixiaModelDefinition(f"{prop_name}_BODY","body",body_submodels)
    instrument_model=HelixiaModelDefinition(f"{prop_name}_INSTRUMENT","instrument",instrument_submodels)
    submodels=tuple(HelixiaSubmodelDefinition(n,body_model.name,"body") for n in body_submodels)+tuple(HelixiaSubmodelDefinition(n,instrument_model.name,"instrument") for n in instrument_submodels)
    groups=(HelixiaGroupDefinition(prop_name,(body_model.name,instrument_model.name)),HelixiaGroupDefinition("HX_SNOWMAN_BAND",(prop_name,)),HelixiaGroupDefinition("HELIXIA_STAGE",("HX_SNOWMAN_BAND",)))
    return HelixiaPropDefinition(prop_name,(body_model,instrument_model),submodels,groups)

def build_snowman_bassist_structure(): return _build_snowman_member_structure(prop_name="HX_SNOWMAN_BASSIST",instrument_suffixes=("BASS_BODY","BASS_NECK","BASS_STRINGS","PLUCK_ZONE"))
def build_snowman_guitarist_structure(): return _build_snowman_member_structure(prop_name="HX_SNOWMAN_GUITARIST",instrument_suffixes=("GUITAR_BODY","GUITAR_NECK","GUITAR_STRINGS","STRUM_ZONE"))

def build_snowman_drummer_structure():
    # Exactly eight sequencing components: kick, snare, hi-hat, three toms, two cymbals.
    # Contacting-stick geometry belongs to each hit component; there are no stick channels.
    components=("KICK","SNARE","TOM_HIGH","TOM_MID","TOM_FLOOR","HI_HAT","CYMBAL_LEFT","CYMBAL_RIGHT")
    body=_submodel_names("HX_SNOWMAN_DRUMMER",("HEAD","FACE","HAT","HAT_BAND","SCARF","TORSO","BUTTONS","PLATFORM"))
    hits=_submodel_names("HX_SNOWMAN_DRUMMER",components)
    body_model=HelixiaModelDefinition("HX_SNOWMAN_DRUMMER_BODY","body",body)
    instrument_model=HelixiaModelDefinition("HX_SNOWMAN_DRUMMER_INSTRUMENT","instrument",hits)
    subs=tuple(HelixiaSubmodelDefinition(n,body_model.name,"body") for n in body)+tuple(HelixiaSubmodelDefinition(n,instrument_model.name,"drum_hit_component") for n in hits)
    groups=(HelixiaGroupDefinition("HX_SNOWMAN_DRUMMER",(body_model.name,instrument_model.name)),HelixiaGroupDefinition("HX_SNOWMAN_BAND",("HX_SNOWMAN_DRUMMER",)),HelixiaGroupDefinition("HELIXIA_STAGE",("HX_SNOWMAN_BAND",)))
    return HelixiaPropDefinition("HX_SNOWMAN_DRUMMER",(body_model,instrument_model),subs,groups)

def build_snowman_singer_structure(): return _build_snowman_member_structure(prop_name="HX_SNOWMAN_SINGER",instrument_suffixes=("MICROPHONE","MIC_STAND"))
def build_snowman_singer_female_structure(): return _build_snowman_member_structure(prop_name="HX_SNOWMAN_SINGER_FEMALE",instrument_suffixes=("MICROPHONE","MIC_STAND"))
def build_snowman_band_structures(): return (build_snowman_bassist_structure(),build_snowman_guitarist_structure(),build_snowman_drummer_structure(),build_snowman_singer_structure(),build_snowman_singer_female_structure())
def build_snowman_band_group_definitions(): return tuple(p.groups[0] for p in build_snowman_band_structures())+(HelixiaGroupDefinition("HX_SNOWMAN_BAND",SNOWMAN_BAND_MEMBERS),HelixiaGroupDefinition("HELIXIA_STAGE",("HX_SNOWMAN_BAND",)))

def build_cactus_tubeman_dj_structure():
    ms={"HX_CACTUS_BODY":("HX_CACTUS_BODY_CORE","HX_CACTUS_LEFT_ARM","HX_CACTUS_RIGHT_ARM"),"HX_CACTUS_FACE":("HX_CACTUS_FACE_EYES","HX_CACTUS_FACE_MOUTH"),"HX_TUBEMAN_BODY":("HX_TUBEMAN_BODY_CORE","HX_TUBEMAN_HEAD"),"HX_TUBEMAN_ARMS":("HX_TUBEMAN_LEFT_ARM","HX_TUBEMAN_RIGHT_ARM"),"HX_DJ_BOOTH":("HX_DJ_BOOTH_FRONT","HX_DJ_BOOTH_DECKS","HX_DJ_BOOTH_SPEAKERS")}; cats={"HX_CACTUS_BODY":"character_body","HX_CACTUS_FACE":"face","HX_TUBEMAN_BODY":"character_body","HX_TUBEMAN_ARMS":"arms","HX_DJ_BOOTH":"stage_prop"}
    models=tuple(HelixiaModelDefinition(m,cats[m],ms[m]) for m in CACTUS_TUBEMAN_MODELS); subs=tuple(HelixiaSubmodelDefinition(s,m,cats[m]) for m in CACTUS_TUBEMAN_MODELS for s in ms[m]); groups=(HelixiaGroupDefinition("HX_CACTUS_TUBEMAN_GROUP",CACTUS_TUBEMAN_MODELS),HelixiaGroupDefinition("HELIXIA_STAGE",("HX_CACTUS_TUBEMAN_GROUP",)))
    return HelixiaPropDefinition("HX_CACTUS_TUBEMAN_GROUP",models,subs,groups)

def build_floor_piano_structure():
    keys=tuple(f"HX_FLOOR_PIANO_KEY_{i:02d}" for i in range(1,25)); ms={"HX_FLOOR_PIANO_BASE":("HX_FLOOR_PIANO_BASE_FRAME","HX_FLOOR_PIANO_BASE_LEFT_EDGE","HX_FLOOR_PIANO_BASE_RIGHT_EDGE"),"HX_FLOOR_PIANO_KEYS":keys}; cats={"HX_FLOOR_PIANO_BASE":"stage_prop","HX_FLOOR_PIANO_KEYS":"keyboard"}; models=tuple(HelixiaModelDefinition(m,cats[m],ms[m]) for m in FLOOR_PIANO_MODELS); subs=tuple(HelixiaSubmodelDefinition(s,m,cats[m]) for m in FLOOR_PIANO_MODELS for s in ms[m]); groups=(HelixiaGroupDefinition("HX_FLOOR_PIANO",FLOOR_PIANO_MODELS),HelixiaGroupDefinition("HX_FLOOR_PIANO_KEY_GROUP",keys),HelixiaGroupDefinition("HELIXIA_STAGE",("HX_FLOOR_PIANO",)))
    return HelixiaPropDefinition("HX_FLOOR_PIANO",models,subs,groups)

def build_reindeer_dance_structure():
    ms={"HX_REINDEER_DANCE_BODY":("HX_REINDEER_DANCE_HEAD","HX_REINDEER_DANCE_TORSO","HX_REINDEER_DANCE_TAIL"),"HX_REINDEER_DANCE_LEGS":("HX_REINDEER_DANCE_FRONT_LEFT_LEG","HX_REINDEER_DANCE_FRONT_RIGHT_LEG","HX_REINDEER_DANCE_REAR_LEFT_LEG","HX_REINDEER_DANCE_REAR_RIGHT_LEG")}; cats={"HX_REINDEER_DANCE_BODY":"character_body","HX_REINDEER_DANCE_LEGS":"legs"}; models=tuple(HelixiaModelDefinition(m,cats[m],ms[m]) for m in REINDEER_DANCE_MODELS); subs=tuple(HelixiaSubmodelDefinition(s,m,cats[m]) for m in REINDEER_DANCE_MODELS for s in ms[m]); groups=(HelixiaGroupDefinition("HX_REINDEER_DANCE",REINDEER_DANCE_MODELS),HelixiaGroupDefinition("HELIXIA_STAGE",("HX_REINDEER_DANCE",)))
    return HelixiaPropDefinition("HX_REINDEER_DANCE",models,subs,groups)

def build_all_helixia_prop_structures(): return (*build_snowman_band_structures(),build_cactus_tubeman_dj_structure(),build_floor_piano_structure(),build_reindeer_dance_structure())
def model_definition_to_dict(model): return {"name":model.name,"category":model.category,"submodels":list(model.submodels),"exportable":bool(model.exportable)}
def submodel_definition_to_dict(submodel): return {"name":submodel.name,"parent_model":submodel.parent_model,"category":submodel.category}
def group_definition_to_dict(group): return {"name":group.name,"members":list(group.members)}
def prop_definition_to_dict(prop): return {"name":prop.name,"models":[model_definition_to_dict(m) for m in prop.models],"submodels":[submodel_definition_to_dict(s) for s in prop.submodels],"groups":[group_definition_to_dict(g) for g in prop.groups]}
def build_snowman_band_export_catalog():
    props=build_snowman_band_structures(); groups=build_snowman_band_group_definitions(); return {"schema":"helixia.props.catalog.v1","catalog_id":"HX_SNOWMAN_BAND","scope":"structure_only","implementation_boundary":{"layout_generation":False,"layout_xml_modification":False,"sequencing":False,"timing":False,"audio":False,"animation":False},"props":[prop_definition_to_dict(p) for p in props],"groups":[group_definition_to_dict(g) for g in groups]}
def build_all_helixia_props_export_catalog():
    props=build_all_helixia_prop_structures(); gb={}
    for prop in props:
        for group in prop.groups:
            if group.name in gb: gb[group.name]=HelixiaGroupDefinition(group.name,tuple(dict.fromkeys((*gb[group.name].members,*group.members))))
            else: gb[group.name]=group
    return {"schema":"helixia.props.catalog.v1","catalog_id":"HELIXIA_PROPS_V1","scope":"structure_only","implementation_boundary":{"layout_generation":False,"layout_xml_modification":False,"sequencing":False,"timing":False,"audio":False,"animation":False},"props":[prop_definition_to_dict(p) for p in props],"groups":[group_definition_to_dict(g) for g in gb.values()]}
