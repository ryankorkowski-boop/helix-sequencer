"""Render real-source generated light cues without shipping the soundtrack."""
from pathlib import Path
import gzip,hashlib,json
import numpy as np
from models.showcase_flavors import build_flavor
from tools.build_helpers.ultimate_showcase import write_layout


def probe(out,executable,render):
    inputs=Path(__file__).parent/'sampler_native_inputs'
    manifest=json.loads((inputs/'manifest.json').read_text());reports=[]
    for row in manifest['runs']:
        garden=build_flavor(row['flavor']);folder=out/'Six_Real_Sampler_Layouts'/row['folder']
        write_layout(garden,folder);data=gzip.decompress((inputs/row['input']).read_bytes())
        assert hashlib.sha256(data).hexdigest()==row['native_render_copy_sha256']
        sequence=folder/'Real_Sampler_Light_Cues.xsq';sequence.write_bytes(data)
        frames,step=render(executable,folder,sequence)
        assert step==50 and len(frames)==3603,(row['folder'],frames.shape,step)
        active={};controls=[]
        for m in garden.models:
            count=int(np.any(frames[:,m.start-1:m.start-1+m.channels],axis=1).sum())
            if m.kind=='pixel':active[m.name]=count
            elif count:controls.append(m.name)
        assert not controls and all(active.values()),(row['folder'],controls,[k for k,v in active.items() if not v])
        report=dict(row,native_frames=len(frames),channels=frames.shape[1],frame_ms=step,
            native_import_and_render_verified=True,active_rgb_model_frames=active,control_activity=controls,
            fseq_sha256=hashlib.sha256(sequence.with_suffix('.fseq').read_bytes()).hexdigest(),
            audio_included=False,music_rights_cleared=False)
        (folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
    assert len(reports)==6
    (out/'six_layout_native_verification.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports
