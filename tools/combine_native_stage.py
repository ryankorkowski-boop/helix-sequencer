"""Combine generated Helix scenery and a source-matched seven-performer stage.

Edits native XML inputs only; xLights must render fresh channel/video output.
"""
from pathlib import Path
import argparse,copy,json,shutil,math,re,tempfile
import xml.etree.ElementTree as ET
import numpy as np
from tools.audio_excerpt import digest
from tools.fseq_pixel_preview import FseqReader


def _input_file(folder, *names):
    candidates=[folder/name for name in names if (folder/name).is_file()]
    if not candidates:raise FileNotFoundError(f'{folder}: missing {names[0]}')
    if len({digest(p) for p in candidates})>1:
        raise ValueError(f'{folder}: conflicting input aliases for {names[0]}')
    return candidates[0]


def _start(model):
    raw=model.get('StartChannel','')
    if not raw.isdecimal() or int(raw)<1:
        raise ValueError(f'{model.get("name")}: explicit positive native StartChannel required')
    return int(raw)


def _custom_end(model):
    if model.get('DisplayAs')!='Custom':return None
    factor={'RGB Nodes':3,'Single Color White':1}.get(model.get('StringType'))
    compressed=model.get('CustomModelCompressed')
    if compressed:
        records=[row.split(',') for row in compressed.split(';') if row.strip()]
        if any(len(row)!=4 or any(not v.strip().isdecimal() for v in row) for row in records):
            raise ValueError(f'{model.get("name")}: invalid compressed native pixel mapping')
        # Compressed records are node,z,y,x. Coordinates are not addresses.
        tokens=[row[0].strip() for row in records]
    else:
        tokens=[v.strip() for v in re.split(r'[|;,]',model.get('CustomModel','')) if v.strip()]
    if factor is None or not tokens or any(not v.isdecimal() for v in tokens) or max(map(int,tokens))<1:
        raise ValueError(f'{model.get("name")}: invalid native Custom pixel mapping')
    return _start(model)+max(map(int,tokens))*factor-1


def _duration(root):
    value=float(root.findtext('head/sequenceDuration','nan'))
    if not math.isfinite(value) or value<=0:raise ValueError('Invalid source sequence duration')
    return value


SOURCE_METADATA=('expected_cues.npz','score_proof.json','showcase_manifest.json',
                 'preview_geometry.json','model_inventory.csv','pose_provenance.json')


def _cue_evidence(scenery,band,output,source_sequence,band_sequence,removed,expected):
    # Preserve input evidence under its original identity, never as a claim
    # about the replacement cast or the combined model/channel inventory.
    for label,folder in (('scenery',scenery),('band',band)):
        for name in SOURCE_METADATA:
            if (folder/name).is_file():
                archive=output/'source_metadata'/label;archive.mkdir(parents=True,exist_ok=True)
                shutil.copy2(folder/name,archive/name)
    report=dict(complete=False,frame_ms=25,reason='both source cue archives required')
    if not all((folder/'expected_cues.npz').is_file() for folder in (scenery,band)):
        return report
    result={};source_counts={};duration_ms=round(_duration(source_sequence)*1000)
    for label,folder,sequence in (('scenery',scenery,source_sequence),('band',band,band_sequence)):
        timing=sequence.findtext('head/sequenceTiming','')
        match=re.fullmatch(r'\s*(\d+)\s*ms\s*',timing)
        if not match:raise ValueError('Source cue evidence requires an explicit frame interval')
        step=int(match.group(1))
        pose=folder/'pose_provenance.json'
        if pose.is_file():step=json.loads(pose.read_text()).get('source_pose_frame_ms',step)
        if type(step) is not int or step<=0 or step%25 or duration_ms%step:
            raise ValueError('Source cue clock must align to the native 25 ms interval')
        count=0
        with np.load(folder/'expected_cues.npz',allow_pickle=False) as cues:
            for key in cues.files:
                model,separator,_=key.partition('::')
                if not separator:raise ValueError('Invalid source cue target')
                if label=='scenery' and model in removed:continue
                if label=='band' and model not in expected:raise ValueError('Unexpected band cue target')
                values=cues[key]
                if (values.ndim!=1 or len(values)!=duration_ms//step
                        or values.dtype.kind not in 'biuf' or not np.isfinite(values).all()
                        or np.any(values<0) or np.any(values>100)):
                    raise ValueError('Invalid source cue shape, clock or intensity')
                if key in result:raise ValueError('Duplicate combined cue target')
                result[key]=np.repeat(values,step//25);count+=1
        source_counts[label]=count
    np.savez_compressed(output/'expected_cues.npz',**result)
    return dict(complete=True,frame_ms=25,frames=duration_ms//25,
                source_curves=source_counts,curves=len(result),
                source_events_retimed=False)


def _combine_to(scenery:Path,band:Path,output:Path,scale=2.8):
    scenery,band,output=scenery.resolve(),band.resolve(),output.resolve()
    if output.exists():raise FileExistsError(output)
    if not math.isfinite(scale) or scale<=0:raise ValueError('Stage scale must be positive and finite')
    band_layout=ET.parse(band/'xlights_rgbeffects.xml').getroot()
    expected={'HX_SNOW_'+r for r in ['DRUMMER','BASS','GUITAR','PIANO','XYLOPHONE','LEAD','HARMONY']}
    band_models=band_layout.findall('./models/model')
    if len(band_models)!=7 or {m.get('name') for m in band_models}!=expected:raise ValueError('Expected the seven-performer native RGB band')
    source_audio=_input_file(scenery,'audio.wav','media/audio.wav')
    band_audio=_input_file(band,'media/audio.wav','audio.wav')
    if digest(source_audio)!=digest(band_audio):raise ValueError('Scenery and band must use identical original excerpts')
    source_sequence=_input_file(scenery,'Performance.xsq','performance.xsq')
    band_sequence=_input_file(band,'Performance.xsq','performance.xsq')
    xsq=ET.parse(source_sequence);stage=ET.parse(band_sequence).getroot()
    if abs(_duration(xsq.getroot())-_duration(stage))>1e-6:
        raise ValueError('Scenery and band must use the same sequence duration')
    spans=sorted((_start(m),_custom_end(m)) for m in band_models)
    if any(end is None for _,end in spans) or any(end>=following for (_,end),(following,_) in zip(spans,spans[1:])):
        raise ValueError('Band requires disjoint native RGB channel spans')
    if any(m.get('StringType')!='RGB Nodes' for m in band_models):
        raise ValueError('Source-pose stage requires RGB Nodes, not AC circuits')
    layout=ET.parse(scenery/'xlights_rgbeffects.xml');models=layout.getroot().find('models');source_models=list(models)
    names=[m.get('name') for m in source_models]
    present=set(names)&expected
    if len(set(names))!=len(names) or (present and present!=expected):
        raise ValueError('Scenery has duplicate or incomplete conflicting band model names')
    # Current native review worlds already contain the complete HX_SNOW cast;
    # replace that known stage just as the historical REVIEW_* stage is replaced.
    old={m.get('name') for m in source_models if m.get('name','').startswith(('REVIEW_SNOW','REVIEW_ROCK'))}|present
    if old:offset=min(int(m.get('StartChannel'))-1 for m in source_models if m.get('name') in old)
    else:
        reader=FseqReader(_input_file(scenery,'Performance.fseq','performance.fseq'))
        # Sparse headers hold packed width; destinations define physical extent.
        offset=max((start+count for start,count in reader.info.ranges),default=reader.info.channels)
        if reader.info.frames*reader.info.step_ms!=round(_duration(xsq.getroot())*1000):
            raise ValueError('Scenery FSEQ duration differs from its sequence')
        if sum(1 for _ in reader.iter_frames())!=reader.info.frames:
            raise ValueError('Incomplete scenery FSEQ')
    for m in list(models):
        if m.get('name') in old:models.remove(m)
    if any(_start(m)>offset or (_custom_end(m) or _start(m))>offset for m in models):
        raise ValueError('Retained scenery extends into the proposed band channels')
    # Publish a completed directory only; input validation above is read-only.
    shutil.copytree(scenery,output,ignore=shutil.ignore_patterns('*.fseq','*.mp4','*.log','native.json','engine_raw.xsq','Performance.xsq','performance.xsq',*SOURCE_METADATA))
    shutil.copy2(source_audio,output/'audio.wav')
    removed_groups=set()
    groups=layout.getroot().find('modelGroups')
    if groups is None:groups=ET.SubElement(layout.getroot(),'modelGroups')
    while True:
        removed=False
        for group in list(groups):
            members=[x for x in group.get('models','').split(',') if x and x.split('/')[0] not in old|removed_groups]
            if members:group.set('models',','.join(members))
            else:
                removed_groups.add(group.get('name'));groups.remove(group);removed=True
        if not removed:break
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
    root=xsq.getroot();root.find('head/sequenceTiming').text='25 ms'
    root.find('head/mediaFile').text='audio.wav'
    removed=old|removed_groups
    for tag in ['ElementEffects','DisplayElements']:
        parent=root.find(tag)
        for element in list(parent):
            if element.get('name') in removed:parent.remove(element)
    doff=len(root.find('EffectDB'));poff=len(root.find('ColorPalettes'))
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
    nextid=root.find('nextid')
    if nextid is None:nextid=ET.SubElement(root,'nextid')
    nextid.text=str(max((int(e.get('id','0')) for e in root.findall('.//Effect') if e.get('id','0').isdigit()),default=0)+1)
    ET.indent(xsq);xsq.write(output/'Performance.xsq',encoding='utf-8',xml_declaration=True)
    cue_evidence=_cue_evidence(scenery,band,output,ET.parse(source_sequence).getroot(),stage,removed,expected)
    provenance=dict(scenery=str(scenery),band=str(band),audio_sha256=digest(source_audio),band_channel_offset=offset,
                    band_scale=scale,removed_legacy_performers=sorted(old),performers=7,frame_ms=25,source_events_retimed=False,
                    original_scenery_effects_retained=True,scenery_groups_exclude_new_band=True,native_render_pending=True,
                    expected_cues=cue_evidence,source_metadata_is_archival=True)
    (output/'combined_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');print(output.name,offset,len(models),flush=True)
    return provenance


def combine(scenery:Path,band:Path,output:Path,scale=2.8):
    scenery,band,output=map(lambda p:Path(p).resolve(),(scenery,band,output))
    if output.exists():raise FileExistsError(output)
    if not math.isfinite(scale) or scale<=0:raise ValueError('Stage scale must be positive and finite')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.'+output.name+'-',dir=output.parent) as temporary:
        staged=Path(temporary)/output.name
        result=_combine_to(scenery,band,staged,scale)
        if output.exists():raise FileExistsError(output)
        staged.rename(output)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('scenery',type=Path);p.add_argument('band',type=Path);p.add_argument('output',type=Path);a=p.parse_args();combine(a.scenery,a.band,a.output)
