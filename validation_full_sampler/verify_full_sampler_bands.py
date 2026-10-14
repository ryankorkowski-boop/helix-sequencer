"""Stream the complete real-source two-band FSEQ without distributing audio."""
from pathlib import Path
import gzip,hashlib,json,subprocess,xml.etree.ElementTree as ET
import numpy as np
from models.infinite_symphony_showcase import build_megagarden
from tools.build_helpers.ultimate_showcase import write_layout
from tools.fseq_pixel_preview import FseqReader

def main():
    folder=Path('full-native-sampler');folder.mkdir(exist_ok=True)
    garden=build_megagarden();write_layout(garden,folder)
    data=gzip.decompress(Path('proof/Real_Sampler_Final_Two_Bands.xsq.gz').read_bytes())
    path=folder/'Real_Sampler_Final_Two_Bands.xsq';path.write_bytes(data)
    root=ET.fromstring(data);bands=[m for m in garden.models if m.details.get('final_band_role')]
    assert len(bands)==12
    xylo=[m for m in bands if m.details['final_band_role']=='xylophone']
    notes={};active={m.name:0 for m in bands};kick_curves={}
    for m in xylo:
        expected=np.zeros((3603,49),bool)
        parent=root.find(f"ElementEffects/Element[@name='{m.name}']")
        for p in range(48,97):
            for e in parent.findall(f"SubModelEffectLayer[@name='NOTE_MIDI_{p}']/Effect"):
                expected[int(e.get('startTime'))//50:int(e.get('endTime'))//50,p-48]=True
        ids={p:np.asarray(m.submodels['NOTE_MIDI_'+str(p)])-1 for p in range(48,97)}
        notes[m.name]=(expected,ids)
    executable=Path('native-xlights/squashfs-root/AppRun').resolve()
    with (folder/'native_render.log').open('w') as log:
        subprocess.run([str(executable),'--headless','-q','-s',str(folder.resolve()),'-od',str(folder.resolve()),str(path.resolve())],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
    reader=FseqReader(path.with_suffix('.fseq'));assert reader.info.frames==3603 and reader.info.step_ms==50
    checked=0
    for i,packed in enumerate(reader.iter_frames()):
        values=np.frombuffer(packed,np.uint8);frame=np.zeros(1182750,np.uint8);offset=0
        for start,length in reader.info.ranges:
            frame[start:start+length]=values[offset:offset+length];offset+=length
        assert offset==len(values)
        for m in bands:
            rgb=frame[m.start-1:m.start-1+m.channels].reshape(-1,3)
            active[m.name]+=int(rgb.any())
            if m.name in notes:
                expected,ids=notes[m.name]
                for p in range(48,97):
                    assert bool(rgb[ids[p]].any())==bool(expected[i,p-48]),(m.name,i,p)
                    checked+=1
            if m.details['final_band_role']=='drummer' and i<55:
                ids=np.asarray(m.submodels['HX_SNOWMAN_DRUMMER_V3_KICK'])-1
                kick_curves.setdefault(m.name,[]).append(int(rgb[ids].max()))
    assert all(v==3603 for v in active.values()),active
    kicks={}
    for name,curve in kick_curves.items():
        on=np.asarray(curve)>curve[0]+1;starts=np.flatnonzero(on&~np.r_[False,on[:-1]])*.05
        assert len(starts)==16,(name,curve,starts)
        kicks[name]=starts.tolist()
    result={'source_commit':'f38f489d1efed08e2e5007835a07213d00633c7a',
        'source_audio_sha256':'0fc2ab5dfee87d4af3e2ab326f76c7ee9cb3a5a893644487d2e7350a48cefafb',
        'frames':3603,'fps':20,'seconds':180.15,'active_performer_frames':active,
        'exact_bar_state_checks':checked,'opening_kicks':kicks,'audio_included':False,
        'independent_voices_verified':False,'musical_classification_listening_verified':False,
        'source_xsq_sha256':hashlib.sha256(data).hexdigest(),'fseq_sha256':hashlib.sha256(path.with_suffix('.fseq').read_bytes()).hexdigest()}
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
