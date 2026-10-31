"""Build standalone xmodel round-trip and ten-channel Faces validation shows."""
from pathlib import Path
import json,csv,copy,xml.etree.ElementTree as ET
import numpy as np
from models.native_review_band import add_band,ac_variant,allocate,instrument_models,VISEMES
from models.ultimate_showcase import Garden
from tools.build_helpers.ultimate_showcase import write_layout,model_xml,_write_xml
from tools.build_snowman_ensemble import NativeSequence


def build(root):
    base=Garden();add_band(base);instruments=instrument_models()
    # The drum kit is independently selectable from the original kit surfaces.
    drum=copy.deepcopy(base.models[0]);used=sorted(set().union(*(set(v) for k,v in drum.submodels.items() if k!='BASE_DIM')))
    old_to_new={n:i+1 for i,n in enumerate(used)}
    points=drum.points[np.array(used)-1];colors=[drum.colors[i-1] for i in used]
    instruments.custom('HX_INSTRUMENT_DRUMKIT',points,'INSTRUMENTS','Independent drum kit contact geometry',colors,
        {k:[old_to_new[n] for n in v if n in old_to_new] for k,v in drum.submodels.items() if k!='BASE_DIM'},
        details=dict(review_role='drummer',instrument_only=True))
    assets=root/'standalone_models';assets.mkdir(exist_ok=True)
    rows=[]
    for mode in ('pixel','ac16'):
        g=Garden();g.models=copy.deepcopy(base.models)+copy.deepcopy(instruments.models)
        if mode=='ac16':g.models=[ac_variant(m) for m in g.models]
        allocate(g)
        folder=assets/mode;folder.mkdir(exist_ok=True)
        for m in g.models:
            path=folder/(m.name+'.xmodel');_write_xml(model_xml(m,'custommodel'),path)
            rows.append(dict(model=m.name,role=m.details['review_role'],instrument_only=m.details.get('instrument_only',False),
                output_mode=mode,channels=m.channels,standalone_xmodel=str(path.relative_to(root)),
                circuits=m.details.get('ac_circuits',[]),hardware_tested=False))
        # Reload the written .xmodel XML, rather than reuse serializer objects.
        show=root/'native_probes'/mode;write_layout(g,show,include_demo=False)
        layout=ET.parse(show/'xlights_rgbeffects.xml');models=layout.getroot().find('models')
        for old in list(models):models.remove(old)
        for m in g.models:
            item=ET.parse(folder/(m.name+'.xmodel')).getroot();item.tag='model';models.append(item)
        _write_xml(layout.getroot(),show/'xlights_rgbeffects.xml')
        seq=NativeSequence(g,2,'','Native standalone and Faces circuit probe');seq.root.find('head/sequenceType').text='Animation'
        for m in g.models:
            if m.details['review_role'] not in ('lead','harmony'):
                for part in m.submodels:
                    if m.submodels[part]:seq.effect(m,part,0,2000,'#FFFFFF',50)
                continue
            palette=seq.palettes.setdefault('white',len(seq.palettes));ET.SubElement(seq.root.find('ColorPalettes'),'ColorPalette').text='C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1'
            for i,v in enumerate(VISEMES):
                setting='E_CHOICE_Faces_FaceDefinition=Helix independent phonemes,E_CHOICE_Faces_Phoneme='+v+',E_CHOICE_Faces_Eyes=Off,E_CHECKBOX_Faces_Outline=0,E_CHECKBOX_Faces_SuppressShimmer=1'
                if setting not in seq.settings:
                    seq.settings[setting]=len(seq.settings);ET.SubElement(seq.root.find('EffectDB'),'Effect').text=setting
                ref=seq.settings[setting]
                ET.SubElement(seq.elements[m.name].find('EffectLayer'),'Effect',dict(name='Faces',ref=str(ref),palette=str(palette),startTime=str(i*200),endTime=str((i+1)*200),id=str(seq.identifier)))
                seq.identifier+=1
        seq.write(show/'Probe.xsq')
    (assets/'MODEL_INDEX.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (assets/'AC_WIRING.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['model','local_circuit','function','reserved_capacity','address_status'])
        for row in rows:
            if row['output_mode']=='ac16':
                for i,name in enumerate(row['circuits'],1):w.writerow([row['model'],i,name,16,'logical circuit only; assign actual Unit ID in your show'])
    return rows


def verify(root):
    from tools.build_helpers.ultimate_showcase_preview import read_fseq
    reports=[]
    for mode in ('pixel','ac16'):
        folder=root/'native_probes'/mode;frames,step=read_fseq(folder/'Probe.fseq');layout=ET.parse(folder/'xlights_rgbeffects.xml')
        assert len(frames)==40 and step==50
        for m in layout.findall('./models/model'):
            if not m.get('name').endswith(('LEAD','HARMONY','LEAD_AC16','HARMONY_AC16')):continue
            start=int(m.get('StartChannel'))-1
            def expand(raw):
                values=[]
                for part in raw.split(','):
                    if '-' in part:
                        a,b=map(int,part.split('-'));values.extend(range(a,b+1))
                    elif part:values.append(int(part))
                return values
            sub={x.get('name'):expand(x.get('line0')) for x in m.findall('subModel') if x.get('name').startswith('MOUTH_')}
            for i,v in enumerate(VISEMES):
                ids=np.array(sub['MOUTH_'+v])-1
                expected=set((start+ids).tolist()) if mode=='ac16' else set((start+ids[:,None]*3+np.arange(3)).ravel().tolist())
                # Select only this singer's channel range.
                count=14 if mode=='ac16' else max(int(x.split(',')[0]) for x in m.get('CustomModelCompressed').split(';'))*3
                active=set((np.flatnonzero(frames[i*4+1,start:start+count])+start).tolist())
                assert active==expected,(mode,m.get('name'),v,len(active),len(expected))
            reports.append(dict(model=m.get('name'),mode=mode,visemes=10,exclusive_native_faces_channels=True,
                standalone_xmodel_roundtrip_loaded=True,xyz_preview_metadata_present=True))
    (root/'validation'/'NATIVE_FACES_PROBES.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports

if __name__=='__main__':
    import sys
    build(Path(sys.argv[1]))
