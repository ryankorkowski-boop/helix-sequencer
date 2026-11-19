"""Verify the original sampler's source-bound opening kicks in native output."""
from pathlib import Path
import gzip,hashlib,json
import numpy as np
from models.snowman_ensemble import build_ensemble
from tools.build_helpers.ultimate_showcase import write_layout


def probe(out,executable,render):
    inputs=Path(__file__).parent/'sampler_native_inputs'
    evidence=json.loads((inputs/'opening_kick_manifest.json').read_text())
    data=gzip.decompress((inputs/'Original_Opening_Kick_Cues.xsq.gz').read_bytes())
    assert hashlib.sha256(data).hexdigest()==evidence['xsq_sha256']
    folder=out/'Original_Sampler_Opening_Kicks';garden=build_ensemble();write_layout(garden,folder)
    sequence=folder/'Original_Opening_Kick_Cues.xsq';sequence.write_bytes(data)
    frames,step=render(executable,folder,sequence)
    assert step==50 and len(frames)==60
    model=garden.models[0];ids=np.array(model.submodels['HX_SNOWMAN_DRUMMER_V3_KICK_SURFACE'])-1
    rgb=frames[:,model.start-1:model.start-1+model.channels].reshape(len(frames),-1,3)
    active=np.any(rgb[:55,ids],axis=(1,2))
    onsets=(np.flatnonzero(active & ~np.r_[False,active[:-1]])*.05).tolist()
    assert len(onsets)==16 and np.allclose(onsets,evidence['observed_visual_onsets'],atol=1e-9),onsets
    fast=[t for t in onsets if 1.85<=t<2.72]
    assert len(fast)==8 and not active[39] and not active[41]
    report=dict(source_audio_sha256=evidence['source_audio_sha256'],native_kick_onsets=onsets,
        rapid_kicks_preserved=8,all_opening_kicks_preserved=16,frame_ms=50,
        original_source_bound_cues=True,audio_included=False,
        independent_listening_verified=False,claim='Measured source events survive XSQ and native render; acoustic similarity is not instrument-class ground truth')
    (folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
