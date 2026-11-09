"""Compare every native-rendered channel against the source-clock cue contract."""
from pathlib import Path
import json,hashlib
import numpy as np
from models.review_spatial_worlds import build_world
from models.native_review_band import add_band,ac_variant,allocate,ac_midi_helix
from models.ultimate_showcase import Garden
from tools.build_helpers.ultimate_showcase_preview import read_fseq,_rgb


def geometry(name):
    if name=='AC_MIDI_Helix':return ac_midi_helix(next(m for m in build_world(0).models if m.details.get('midi_rungs')))
    if name.startswith('World_'):return build_world(int(name[-1])-1)
    g=Garden();add_band(g)
    if name.startswith('AC16'):g.models=[ac_variant(m) for m in g.models];allocate(g)
    return g


def verify(root):
    reports=[]
    for path in sorted((root/'shows').glob('E*/*/Performance.fseq')):
        folder=path.parent;g=geometry(folder.name);actual,step=read_fseq(path)
        assert actual.shape[0]==720 and step==50
        expected=np.zeros(actual.shape,'u1')
        with np.load(folder/'expected_cues.npz') as cues:
            for m in g.models:
                for key in cues.files:
                    model,part=key.split('::')
                    if model==m.name and part=='SCORE_ALL':m.submodels[part]=list(range(1,len(m.points)+1))
                    if model!=m.name or part not in m.submodels or not m.submodels[part]:continue
                    ids=np.array(m.submodels[part])-1;values=cues[key]
                    if m.kind=='ac':
                        # xLights rounds On brightness to integer channel values.
                        v=np.rint(values*2.55).astype('u1')
                        expected[:,m.start-1+ids]=np.maximum(expected[:,m.start-1+ids],v[:,None])
                    else:
                        color=_rgb([m.colors[ids[0]]])[0]
                        rgb=np.floor(values[:,None]*color/100).astype('u1')
                        for k in range(3):
                            offsets=m.start-1+ids*3+k
                            expected[:,offsets]=np.maximum(expected[:,offsets],rgb[:,k,None])
        difference=np.abs(actual.astype('i2')-expected.astype('i2'))
        worst=int(difference.max());bad=int((difference>2).sum())
        report=dict(show=str(folder.relative_to(root)),frames=720,frame_ms=step,channels=actual.shape[1],
            channel_samples=int(actual.size),max_absolute_error=worst,samples_over_tolerance=bad,
            native_xlights_version='2026.18',native_xlights_rendered=True,
            fseq_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            ac_model_circuits={m.name:m.channels for m in g.models if m.kind=='ac'})
        reports.append(report);print(report,flush=True)
        if bad:
            row,col=np.argwhere(difference>2)[0];print('first mismatch',row,col,int(actual[row,col]),int(expected[row,col]),flush=True)
            raise AssertionError('Native source/sequence channel mismatch')
    out=root/'validation';out.mkdir(exist_ok=True)
    (out/'NATIVE_CHANNEL_PARITY.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports

if __name__=='__main__':
    import sys
    verify(Path(sys.argv[1]))
