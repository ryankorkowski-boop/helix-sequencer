"""Verify this actual native candidate, without inventing acoustic acceptance."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import numpy as np
from tools.phoneme_source import digest, EXPECTED_SHA256
from tools.phoneme_vocal_export import FIXTURE, screened_lanes
from tools.quality.native_stream import inspect_stream
from tools.verify_recovery_media import verify
from tools.verify_showcase_luma import verify_mp4


def run(show, output):
    show, output = Path(show), Path(output)
    manifest = json.loads((show/'run_manifest.json').read_text())
    native = manifest['native_preview']
    if native['status'] != 'success':
        raise ValueError('No native MP4')
    movie = Path(native['mp4']); audio = show/'media/Phoneme_Test_Hook.mp3'
    layout = ET.parse(show/'xlights_rgbeffects.xml')
    models = layout.findall('./models/model')
    expected = {'HX_SNOW_'+x for x in ('DRUMMER','BASS','GUITAR','PIANO','LEAD','HARMONY')}
    if len(models) != 6 or {m.get('name') for m in models} != expected:
        raise ValueError('Wrong default cast')
    def nodes(submodel):
        values=set()
        for key, text in submodel.attrib.items():
            if not key.startswith('line'): continue
            for token in text.split(','):
                if not token: continue
                pair=[int(x) for x in token.split('-')]
                values.update(range(min(pair),max(pair)+1))
        return values
    selectors={}
    for role in ('LEAD','HARMONY'):
        model=next(m for m in models if m.get('name')=='HX_SNOW_'+role)
        parts={p.get('name'):nodes(p) for p in model.findall('subModel')}
        opened=set().union(*(v for k,v in parts.items() if k.startswith('MOUTH_') and k!='MOUTH_rest'))-parts['MOUTH_rest']
        base=int(model.get('StartChannel'))-1
        selectors[role]=np.array([base+(n-1)*3+c for n in sorted(opened) for c in range(3)])
    fseq=next(Path(native['evidence_dir']).glob('*.fseq'))
    frames=inspect_stream(fseq,selectors=selectors)
    clocks={}
    with np.load(FIXTURE/'acoustic_vocal_clocks.npz',allow_pickle=False) as data:
        lanes, screening=screened_lanes(data)
    lit={}
    for role,source in [('LEAD','estimated_lead'),('HARMONY','estimated_backing')]:
        active=lanes[source][0]>0
        times=np.arange(frames['frames'])*frames['frame_ms']/10
        ids=np.rint(times).astype(int)
        # Exclude +/- one native frame around acoustic boundaries. Pixel clock
        # quantization is not a measure of lexical alignment or singer identity.
        guarded=np.array([not active[max(0,i-5):min(len(active),i+6)].any() for i in ids])
        native_open=np.array(frames['selected_channel_max'][role])>0
        lit[role]=native_open
        clocks[role]=dict(native_open_frames=int(native_open.sum()),
            guarded_estimated_rest_frames=int(guarded.sum()),
            openings_on_guarded_estimated_rests=int((native_open & guarded).sum()))
    frames.pop('selected_channel_max')
    report=dict(media=verify(movie,audio,EXPECTED_SHA256),readability=verify_mp4(movie,static_cast=True),
        native_channel_evidence=frames,vocal_routes=clocks,
        native_lead_only_frames=int((lit['LEAD'] & ~lit['HARMONY']).sum()),
        native_harmony_only_frames=int((lit['HARMONY'] & ~lit['LEAD']).sum()),
        confidence_screening=screening,cast=sorted(expected),
        actual_engine_source_commit=manifest['source_commit'],
        published_equivalent_commit='2d4c505e442292f3cba9eb909aeabcc76acb33cf',
        exact_published_tree='a37c53cd90ba0168f696ed4466871f63d3e3c046',
        source_module_sha256=manifest['source_module_sha256'],
        native_xsq_sha256=digest(show/'Phoneme_Test_Hook_Helix.xsq'),
        native_fseq_sha256=digest(fseq),layout_sha256=digest(show/'xlights_rgbeffects.xml'),
        independent_acoustic_singer_identity_verified=False,lexical_phoneme_boundaries_verified=False,
        owner_approved=False,qualified_for_final_nine=False,
        limitations=['Retained source-art drummer is planar; solid-3D canonical acceptance remains open',
                     'Speech-VAD-screened source separation is estimated, not authenticated singer identity',
                     'Seven acoustic mouth families do not prove ten independently aligned lexical shapes'])
    report['native_vocal_rest_check_passed']=all(x['openings_on_guarded_estimated_rests']==0 for x in clocks.values())
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('vocal_routes','native_lead_only_frames','native_harmony_only_frames','native_vocal_rest_check_passed','readability')},indent=2))
    return report


if __name__=='__main__':
    import sys
    run(sys.argv[1],sys.argv[2])
