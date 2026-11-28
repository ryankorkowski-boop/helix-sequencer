"""Compile distinct district arrangements from one retained Helix analysis."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import time
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import numpy as np

from core.native_face_instructions import face_template
from core.output_provenance import sha256
from core.singing_face_discovery import detect_singing_faces
from models.ultimate_showcase import Sculpture
from tools.build_helpers.ultimate_showcase import model_xml
from tools.build_snowman_ensemble import NativeSequence
from tools.canonical_band_cues import export_drums, export_instruments
from tools.layout_bench.run_bench import canonical_xsq
from tools.phoneme_vocal_export import export as export_qualified_faces, static_materials
from tools.source_spatial_direction import export_model, onset_index
from xlights.xml_io import materialize_native_effect_tables
from xlights.xsq_writer import add_effect

from .export import canonical_band, native_xyz, write_xml


ROLE_DEFAULTS = {
    "Arch": "keyboardist", "Star": "drummer", "Spinner": "drummer",
    "Mega_Tree": "bassist", "Monumental_Mega_Tree": "bassist",
    "Tower_Tree": "bassist", "Spiral_Tree": "guitarist", "Matrix": "keyboardist",
    "Lantern": "guitarist", "Pathway": "keyboardist", "Roofline": "guitarist",
    "Window": "guitarist", "Fountain": "keyboardist", "Pillar": "bassist",
}
DISTRICT_ROLES = {
    "Grand": {"Spinner": "keyboardist", "Window": "guitarist", "Pillar": "bassist"},
    "Modern": {"Star": "keyboardist", "Roofline": "bassist"},
    "Gothic": {"Spires": "bassist", "Tracery": "keyboardist", "Window": "keyboardist"},
    "Jungle": {"Gill": "guitarist", "Flower": "keyboardist", "Vine": "bassist",
               "Mushroom": "guitarist", "Spinner": "keyboardist"},
    "Motor": {"Wheel": "drummer", "Vehicle": "bassist", "Headlight": "guitarist",
              "Float": "keyboardist", "Spiral_Tree": "bassist"},
    "Arena": {"Truss": "drummer", "Stagefloor": "bassist", "Performance_Riser": "guitarist"},
    "Nexus": {"Double_Helix": "guitarist", "Helix_Rung": "keyboardist", "Elevated_Track": "bassist"},
}
AXIS = {"Grand": 0, "Modern": 0, "Gothic": 1, "Jungle": 2, "Motor": 2, "Arena": 0, "Nexus": 1}


def park_models(manifest, positions):
    banks=defaultdict(list)
    models=[]
    for row in manifest["models"]:
        if row["model"].startswith("HX_INFINITY_SNOW_"):
            continue
        district,family=row["district"],row["family"]
        role=DISTRICT_ROLES[district].get(family,ROLE_DEFAULTS.get(family,"bassist"))
        start=(row["first_channel"]-1)//3
        points=native_xyz(positions[start:start+row["nodes"]])
        zone=district.upper()+"_SPATIAL"
        details={"musical_role":role,"advanced_spatial_routing":True,
                 "spatial_direction":-1 if district in ("Modern","Motor","Gothic") else 1,
                 "spatial_phase":{"Modern":.18,"Jungle":.32,"Gothic":.13,"Nexus":.47}.get(district,0),
                 "source_display_floor":.2}
        if family in ("Spiral_Tree","Double_Helix","Elevated_Track"):
            details["spatial_axis"]="spiral"
        elif family in ("Pillar","Spires","Truss","Roofline","Arch","Vehicle","Mushroom","Vine","Pathway"):
            details["spatial_axis"]="xyz"[AXIS[district]]
            if family in ("Pillar","Spires","Vine"):
                details["spatial_axis"]="y"
            elif family in ("Roofline","Vehicle","Arch"):
                details["spatial_axis"]="xyz"[int(np.argmax(np.ptp(points,axis=0)))]
        display="Matrix" if family=="Matrix" else "Poly Line"
        model=Sculpture(row["model"],display,zone,district,{},points,[],
                        details=details,start=row["first_channel"])
        banks[(district,family)].append((model,points.mean(axis=0)))
        models.append(model)
    for (district,family),bank in banks.items():
        axis=AXIS[district]
        if district=="Grand":
            # Read the symmetrical estate from the entrance out through both wings.
            key=lambda entry: (abs(entry[1][0]+88),entry[1][0],entry[0].name)
        elif district=="Nexus":
            key=lambda entry: (np.arctan2(entry[1][2],entry[1][0]),entry[1][1],entry[0].name)
        else:
            key=lambda entry: (entry[1][axis],entry[0].name)
        for rank,(model,_) in enumerate(sorted(bank,key=key)):
            model.details.update(source_route_bank=f"{district}_{family}",source_route_rank=rank,
                                 source_route_count=len(bank))
    return models


def add_faces(sequence, band, plan, layout):
    faces=detect_singing_faces(layout)
    singers={m.name:m for m in band if m.details["review_role"]=="lead"}
    counts=Counter({name:0 for name in singers})
    cue_layers={}
    for cue in plan.get("xlights_translation",{}).get("sequence_effect_instructions",[]):
        name=cue.get("target_model")
        if name not in singers:
            continue
        # The retained plan owns attribution and abstention. Consume only
        # literal mouth instructions for the corresponding physical singer.
        template=face_template(cue,faces,"C_BUTTON_Palette1=#FFA6B6,C_CHECKBOX_Palette1=1")
        if template is None:
            continue
        start=max(0,int(cue["start_ms"]))
        end=min(sequence.duration,int(cue["end_ms"]))
        if end<=start:
            continue
        if name not in cue_layers:
            cue_layers[name]=ET.SubElement(sequence.elements[name],"EffectLayer")
        add_effect(cue_layers[name],start,end,"Faces",template)
        counts[name]+=1
    return dict(counts)


def arrange(show, master_folder, audio, output, *, vocal_fixture=None):
    start=time.perf_counter()
    manifest=json.loads((show/"scene_manifest.json").read_text())
    master=canonical_xsq(master_folder,audio.stem)
    if master is None:
        candidates=[p for folder in sorted(master_folder.glob("beta/*"))
                    if (p:=canonical_xsq(folder,audio.stem)) is not None]
        master=candidates[-1] if candidates else None
    if master is None:
        raise ValueError(f"Master sequence missing for {audio.name}")
    plan_path=master.with_name(master.stem+".snowman_band.json")
    plan=json.loads(plan_path.read_text())
    duration=float(ET.parse(master).findtext("./head/sequenceDuration"))
    layout_path=show/"xlights_rgbeffects.xml"
    tree=ET.parse(layout_path)
    layout=tree.getroot()
    models=layout.find("models")
    groups=layout.find("modelGroups")
    for node in list(models):
        if node.get("name").startswith("HX_INFINITY_SNOW_"):
            models.remove(node)
    for node in list(groups):
        if node.get("name").startswith("HX_SNOWMAN_"):
            groups.remove(node)
    with np.load(show/"rgb_bindings.npz",allow_pickle=False) as data:
        props=park_models(manifest,data["positions"])
    band=[model for model,_,_ in canonical_band(models,groups,show/"assets",manifest["park_nodes"]*3+1)]
    static_materials(SimpleNamespace(models=band))
    garden=SimpleNamespace(models=props+band)
    sequence=NativeSequence(garden,duration,audio.name,"Helix Infinity")
    sequence.root.find("head/comment").text="Infinity district choreography routed from the retained Helix production analysis."
    routing_notes=defaultdict(lambda:Counter())
    # District banks never convert an onset into a synchronous park-wide cue.
    park_plan={"cues":{role:[dict(cue,synchronized_accent=False) for cue in plan["cues"].get(role,[])]
                       for role in ("bassist","drummer","guitarist","keyboardist")}}
    shared_onsets={role:onset_index(cues) for role,cues in park_plan["cues"].items()}
    by_name={node.get("name"):node for node in models}
    for model in props:
        district=model.details["source_route_bank"].split("_",1)[0]
        palette=["#"+color for color in manifest["districts"][district]["palette_srgb"]]
        result=export_model(sequence,model,park_plan,{},palette,shared_onsets=shared_onsets)
        if result["output_events"]:
            routing_notes[district][result["role"]]+=result["output_events"]
        node=by_name[model.name]
        for submodel in model_xml(model).findall("subModel"):
            node.append(submodel)
    # Staging light uses only authored static material submodels, excluding
    # every animated mouth, contact pose, instrument surface and strike lane.
    instruments=export_instruments(sequence.root,SimpleNamespace(models=band),plan,qualified_keyboard=True)
    drums=export_drums(sequence.root,SimpleNamespace(models=band),plan)
    parents={row.get("name"):row for row in sequence.root.findall("ElementEffects/Element")}
    for model in band:
        sequence.elements[model.name]=parents[model.name]
        for part in model.submodels:
            if part.startswith("STATIC_RGB_"):
                sequence.effect(model,part,0,sequence.duration,"#"+part.removeprefix("STATIC_RGB_"),
                                68 if model.details["review_role"]=="drummer" else 78)
        index=list(models).index(by_name[model.name])
        models.remove(by_name[model.name])
        models.insert(index,model_xml(model))
    output.mkdir(parents=True,exist_ok=True)
    routed_layout=output/"xlights_rgbeffects.xml"
    write_xml(routed_layout,layout)
    audio_hash=sha256(audio)
    if vocal_fixture is None:
        singer_counts=add_faces(sequence,band,plan,routed_layout)
        vocal_evidence={"lead_effects":singer_counts,"independent_vocals_verified":False,
                        "harmony_status":"Abstained without qualified independent vocal source"}
    else:
        qualification=json.loads((vocal_fixture/"diagnostic.json").read_text())
        if qualification.get("verification_state")!="VERIFIED":
            raise ValueError("An independent harmony lane requires a source-qualified vocal fixture")
        vocal_evidence=export_qualified_faces(sequence.root,routed_layout,SimpleNamespace(models=band),
                                             fixture=vocal_fixture,expected_sha256=audio_hash,source_audio=audio)
    materialize_native_effect_tables(sequence.root)
    sequence.write(output/f"{audio.stem}, Infinity Districts.xsq")
    receipt={"owner_approved":False,"audio_sha256":audio_hash,"master_xsq_sha256":sha256(master),
             "source_plan_sha256":sha256(plan_path),"district_effects_by_role":routing_notes,
             "drummer":drums,"instrument_routing":instruments,"vocal_evidence":vocal_evidence,"seconds":round(time.perf_counter()-start,3)}
    (output/"district_routing.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("show","master","audio","output"):
        parser.add_argument(name,type=Path)
    parser.add_argument("--vocal-fixture",type=Path)
    args=parser.parse_args()
    print(json.dumps(arrange(args.show,args.master,args.audio,args.output,vocal_fixture=args.vocal_fixture),indent=2))
