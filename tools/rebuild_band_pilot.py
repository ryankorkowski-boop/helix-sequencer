"""Rebuild only band geometry/export from an authenticated existing analysis.

No second analysis, remade soundtrack, inferred notes or copied vocal lane.
The output remains a diagnostic until source and visual acceptance pass.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from models.ultimate_showcase import Garden
from models.canonical_native_band import add_band,visual_identity
from tools.native_source_pose_band import stage_native_cast
from tools.phoneme_vocal_export import static_materials,export
from tools.canonical_band_cues import export_instruments,export_drums,refresh_models
from tools.build_snowman_ensemble import NativeSequence
from tools.build_helpers.ultimate_showcase import write_layout
from tools.phoneme_source import digest,EXPECTED_SHA256
from xlights.xml_io import materialize_native_effect_tables


def rebuild(source,output):
    source,output=Path(source),Path(output)
    original=json.loads((source/'run_manifest.json').read_text())
    audio=source/'media/Phoneme_Test_Hook.mp3'
    if digest(audio)!=EXPECTED_SHA256 or original['audio_sha256']!=EXPECTED_SHA256:
        raise ValueError('Original source identity mismatch')
    plans=list((source/'sequence').glob('*.snowman_band.json'))
    if len(plans)!=1:raise ValueError('Exactly one retained production plan is required')
    if output.exists():raise FileExistsError(output)
    g=Garden(title='Helix recovery band diagnostic',slug='Recovery_Band_Pilot')
    add_band(g);stage_native_cast(g.models);static_materials(g)
    write_layout(g,output,include_demo=False,export_all_custom=True)
    (output/'media').mkdir();shutil.copyfile(audio,output/'media/Phoneme_Test_Hook.mp3')
    (output/'sequence').mkdir();shutil.copyfile(plans[0],output/'sequence'/plans[0].name)
    sequence=NativeSequence(g,34.88,'media/Phoneme_Test_Hook.mp3','Recovery band diagnostic')
    sequence.root.find('head/sequenceDuration').text='34.880'
    plan=json.loads(plans[0].read_text())
    instruments=export_instruments(sequence.root,g,plan)
    instruments['drummer']=export_drums(sequence.root,g,plan)
    layout=output/'xlights_rgbeffects.xml';refresh_models(g,layout)
    vocals=export(sequence.root,layout,g)
    materialize_native_effect_tables(sequence.root)
    sequence.write(output/'Phoneme_Test_Hook_Helix.xsq')
    tree=ET.parse(layout)
    for camera in tree.findall('./Viewpoints/*'):
        for key,value in dict(angleX='8',angleY='0',distance='-65',pany='-18',panz='-75').items():camera.set(key,value)
    tree.write(layout,encoding='utf-8',xml_declaration=True)
    root=Path(__file__).resolve().parents[1]
    manifest=dict(schema='helix.run_manifest.v1',warnings=[],status='band_export_generated',
        audio_sha256=EXPECTED_SHA256,source_audio_sha256=EXPECTED_SHA256,
        source_analysis_sha256=digest(plans[0]),analysis_reused_without_modification=True,
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        source_worktree_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()),
        visual_identity=visual_identity(),owner_approved_geometry=False,
        source_module_sha256={str(p.relative_to(root)):digest(p) for p in [
            root/'models/readable_band_scene.py',root/'models/final_band_native.py',
            root/'models/canonical_native_band.py',Path(__file__),root/'tools/phoneme_vocal_export.py']})
    for name,report in [('run_manifest.json',manifest),('instrument_export.json',instruments),
                        ('vocal_lane_diagnostic.json',vocals)]:
        (output/name).write_text(json.dumps(report,indent=2)+'\n')
    return output/'Phoneme_Test_Hook_Helix.xsq'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(rebuild(a.source,a.output))
