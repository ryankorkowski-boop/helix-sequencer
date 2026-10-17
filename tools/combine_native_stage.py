"""Combine generated Helix scenery and a source-matched seven-performer stage.

Edits native XML inputs only; xLights must render fresh channel/video output.
"""
from pathlib import Path
import argparse,copy,json,shutil,math
import xml.etree.ElementTree as ET
from tools.audio_excerpt import digest


def combine(scenery:Path,band:Path,output:Path,scale=2.8):
    scenery,band,output=scenery.resolve(),band.resolve(),output.resolve()
    if output.exists():raise FileExistsError(output)
    if not math.isfinite(scale) or scale<=0:raise ValueError('Stage scale must be positive and finite')
    band_layout=ET.parse(band/'xlights_rgbeffects.xml').getroot()
    expected={'HX_SNOW_'+r for r in ['DRUMMER','BASS','GUITAR','PIANO','XYLOPHONE','LEAD','HARMONY']}
    band_models=band_layout.findall('./models/model')
    if len(band_models)!=7 or {m.get('name') for m in band_models}!=expected:raise ValueError('Expected the seven-performer native RGB band')
    if digest(scenery/'audio.wav')!=digest(band/'media/audio.wav'):raise ValueError('Scenery and band must use identical original excerpts')
    shutil.copytree(scenery,output,ignore=shutil.ignore_patterns('*.fseq','*.mp4','*.log','native.json','engine_raw.xsq'))
    layout=ET.parse(output/'xlights_rgbeffects.xml');models=layout.getroot().find('models');source_models=list(models)
    old={m.get('name') for m in source_models if m.get('name','').startswith(('REVIEW_SNOW','REVIEW_ROCK'))}
    if old:offset=min(int(m.get('StartChannel'))-1 for m in source_models if m.get('name') in old)
    else:
        import struct
        offset=struct.unpack_from('<I',(scenery/'performance.fseq').read_bytes(),10)[0]
    for m in list(models):
        if m.get('name') in old:models.remove(m)
    assert all(int(m.get('StartChannel'))<=offset for m in models)
    removed_groups=set()
    for group in list(layout.getroot().find('modelGroups')):
        members=[x for x in group.get('models','').split(',') if x.split('/')[0] not in old]
        if members:group.set('models',','.join(members))
        else:removed_groups.add(group.get('name'));layout.getroot().find('modelGroups').remove(group)
    (output/'models').mkdir(exist_ok=True)
    for original in band_layout.findall('./models/model'):
        m=copy.deepcopy(original);m.set('StartChannel',str(int(m.get('StartChannel'))+offset))
        for axis in 'XYZ':
            value=float(m.get('WorldPos'+axis));value=value*scale if axis!='Z' else (value-75)*scale+150
            m.set('WorldPos'+axis,str(value));m.set('Scale'+axis,str(float(m.get('Scale'+axis))*scale))
        models.append(m);standalone=copy.deepcopy(m);standalone.tag='custommodel';ET.ElementTree(standalone).write(output/'models'/(m.get('name')+'.xmodel'),encoding='utf-8',xml_declaration=True)
    for model in models:
        if not model.get('name','').startswith('HX_SNOW_'):model.set('PixelSize','3')
    for camera in layout.findall('./Viewpoints/*'):
        for key,val in dict(angleX='18',angleY='0',distance='-360',panx='0',pany='-20',panz='-50').items():camera.set(key,val)
    ET.indent(layout);layout.write(output/'xlights_rgbeffects.xml',encoding='utf-8',xml_declaration=True)
    xsq=ET.parse(scenery/'performance.xsq');root=xsq.getroot();root.find('head/sequenceTiming').text='25 ms'
    root.find('head/mediaFile').text='audio.wav'
    removed=old|removed_groups
    for tag in ['ElementEffects','DisplayElements']:
        parent=root.find(tag)
        for element in list(parent):
            if element.get('name') in removed:parent.remove(element)
    stage=ET.parse(band/'Performance.xsq').getroot();doff=len(root.find('EffectDB'));poff=len(root.find('ColorPalettes'))
    maxid=max((int(e.get('id','0')) for e in root.findall('.//Effect') if e.get('id','0').isdigit()),default=0)
    for tag in ['EffectDB','ColorPalettes']:
        for item in stage.find(tag):root.find(tag).append(copy.deepcopy(item))
    for tag in ['ElementEffects','DisplayElements']:
        for item in stage.find(tag):
            if not item.get('name','').startswith('HX_SNOW_'):continue
            item=copy.deepcopy(item)
            for event in item.findall('.//Effect'):
                if event.get('ref') is not None:event.set('ref',str(int(event.get('ref'))+doff))
                if event.get('palette') is not None:event.set('palette',str(int(event.get('palette'))+poff))
                if event.get('id') is not None:event.set('id',str(int(event.get('id'))+maxid))
            root.find(tag).append(item)
    ET.indent(xsq);xsq.write(output/'Performance.xsq',encoding='utf-8',xml_declaration=True)
    (output/'performance.xsq').unlink(missing_ok=True)
    provenance=dict(scenery=str(scenery),band=str(band),audio_sha256=digest(scenery/'audio.wav'),band_channel_offset=offset,
                    band_scale=scale,removed_legacy_performers=sorted(old),performers=7,frame_ms=25,source_events_retimed=False,
                    original_scenery_effects_retained=True,scenery_groups_exclude_new_band=True,native_render_pending=True)
    (output/'combined_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');print(output.name,offset,len(models),flush=True)
    return provenance

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('scenery',type=Path);p.add_argument('band',type=Path);p.add_argument('output',type=Path);a=p.parse_args();combine(a.scenery,a.band,a.output)
