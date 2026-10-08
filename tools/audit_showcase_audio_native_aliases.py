"""Prove native alias rendering instead of relying on schema/coverage scores."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import numpy as np

from models.showcase_flavors import build_flavor
from tools.build_helpers.ultimate_showcase_preview import read_fseq
from tools.showcase_audio_native import prepare_template,native_music_xsq


def audit(xlights:Path,output:Path)->dict:
    g=build_flavor('midnight_masquerade');after=output/'after';template=prepare_template(g,after)
    source_audio=Path(__file__).resolve().parents[1]/'evidence/showcase_audio/source/3-Frostbitten-Fingerboard-1-.mp3'
    shutil.copy2(source_audio,after/'song.mp3')
    raw=ET.parse(template);rows=raw.getroot().find('ElementEffects');rows.clear()
    target=next(m for m in g.models if m.name.endswith('CROWN_5'))
    layer=ET.SubElement(ET.SubElement(rows,'Element',{'name':target.name,'type':'model'}),'EffectLayer')
    for name,start,end,settings in [('Ramp',0,1000,''),('Single Strand',2000,3000,''),
        ('On',4000,5000,'E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100')]:
        ET.SubElement(layer,'Effect',{'name':name,'startTime':str(start),'endTime':str(end),'settings':settings})
    raw_path=output/'source.xsq';raw.write(raw_path)
    native_music_xsq(raw_path,after/'probe.xsq',g,after/'song.mp3',6)
    before=output/'before';shutil.copytree(after,before,dirs_exist_ok=True)
    root=ET.parse(before/'probe.xsq')
    for effect in root.getroot().findall('ElementEffects/Element/EffectLayer/Effect'):
        if effect.get('startTime')=='0':effect.set('name','Ramp')
        if effect.get('startTime')=='2000':effect.set('name','Single Strand')
    root.write(before/'probe.xsq')
    report={'schema':'helix.native_alias_probe.v1','target':target.name,'seconds':6,
        'purpose':'native effect-name/envelope test, not musical acceptance','stages':{}}
    for stage in ('before','after'):
        folder=output/stage
        with (folder/'native.log').open('w') as log:
            subprocess.run([str(xlights.resolve()),'--headless','-q','-s',str(folder.resolve()),'-od',str(folder.resolve()),str((folder/'probe.xsq').resolve())],
                stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'XL_NO_GPU_COMPUTE':'1'},check=True,timeout=120)
        frames,step=read_fseq(folder/'probe.fseq');values=frames[:,target.start-1:target.start-1+target.channels]
        result={}
        for name,start,end in [('Ramp',0,1000),('SingleStrand',2000,3000),('On',4000,5000)]:
            region=values[start//step:end//step]
            result[name]={'peak':int(region.max()),'active_frames':int(np.sum(region.max(axis=1)>0)),
                'frame_means':[round(float(x),4) for x in region.mean(axis=1)]}
        report['stages'][stage]=result
    old,new=report['stages']['before'],report['stages']['after']
    assert old['Ramp']['peak']==0 and new['Ramp']['peak']>0
    assert new['Ramp']['frame_means'][0]>new['Ramp']['frame_means'][-1]
    assert old['On']==new['On'] and old['SingleStrand']==new['SingleStrand']
    report['native_alias_recovery_verified']=True
    (output/'proof.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--xlights',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('outputs/showcase_audio_native_alias_probe'))
    args=parser.parse_args();report=audit(args.xlights,args.output)
    print(json.dumps({'native_alias_recovery_verified':report['native_alias_recovery_verified']}))


if __name__=='__main__':main()
