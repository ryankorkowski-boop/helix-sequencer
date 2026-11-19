"""Recheck genuine local native files; retain every failed gate separately."""
from pathlib import Path
import hashlib
import json

import numpy as np
from scipy.signal import correlate

from tools.phoneme_source import digest, EXPECTED_SHA256
from tools.quality.native import read_frames
from tools.render_approval_collection import verify, pcm


BASE = Path('/workspace/helix-output')
EVIDENCE = Path(__file__).resolve().parent


def check(old_name, new_name, label):
    old, new = BASE/old_name, BASE/new_name
    old_manifest = json.loads((old/'run_manifest.json').read_text())
    manifest = json.loads((new/'run_manifest.json').read_text())
    before, native = old_manifest['native_preview'], manifest['native_preview']
    assert native['status'] == 'success' and native['audio_stream_verified']
    movie, source = Path(native['mp4']), new/'media/Phoneme_Test_Hook.mp3'
    assert digest(source) == native['audio_sha256'] == EXPECTED_SHA256
    assert digest(movie) == native['mp4_sha256']
    # Metadata in a native FSEQ may change when the layout changes. Compare
    # every actual channel sample, not just headers or the container checksum.
    old_fseq = next(Path(before['evidence_dir']).glob('*.fseq'))
    fseq = next(Path(native['evidence_dir']).glob('*.fseq'))
    previous = read_frames(old_fseq)
    current = read_frames(fseq)
    same = previous == current
    assert same, 'A preview alpha correction must not alter channel frames'
    assert native['xsq_sha256'] == before['xsq_sha256']
    raw, channels, frames, step = current
    samples = np.frombuffer(raw, 'u1').reshape(frames, channels)
    lit = (samples > 0).sum(axis=1)
    report = verify(movie, source, native=True)
    report['source_audio'] = dict(filename=source.name, sha256=digest(source), kind='retained_owner_upload')
    report['source_commit'] = manifest.get('export_source_commit', manifest['source_commit'])
    report['analysis_source_commit'] = 'a9beaa7c9be89fffc21a856e033bf75a3136c29b'
    report['analysis_identity'] = 'cached_analysis_identity.json'
    report['native'] = dict(version=native['xlights_version'], movie=str(movie),
                            xsq_sha256=native['xsq_sha256'], fseq=str(fseq),
                            fseq_sha256=digest(fseq), layout_sha256=native['layout_sha256'],
                            workflow_url=None, execution='local native xLights2026.18',
                            log='/workspace/transparent-native.log')
    x, y = pcm(source), pcm(movie)
    windows = []
    for t in (0, 10, 20, 30):
        a, b = t*16000, min(len(x), len(y), (t+3)*16000)
        correlation = correlate(y[a:b], x[a:b], method='fft')
        center = b-a-1
        lag = int(np.argmax(correlation[center-320:center+321])-320)
        windows.append(dict(start_seconds=t, lag_ms=lag/16))
    report['soundtrack_windows'] = windows
    report['channel_evidence'] = dict(channels=channels, frames=frames, step_ms=step,
        raw_frame_sha256=hashlib.sha256(raw).hexdigest(), identical_to_opaque_preview=same,
        unique_channel_timelines=len({samples[:,i].tobytes() for i in range(channels)}),
        peak_lit_channels=int(lit.max()), all_channels_on_frames=int((lit==channels).sum()))
    report['status'] = ('PASS' if report['readability']['passed'] and
                        report['dimensions'] == [1920,1080] and
                        all(w['lag_ms'] == 0 for w in windows) else 'FAIL')
    report['musical_and_owner_acceptance'] = 'UNVERIFIED'
    report['owner_approved'] = False
    report['qualified_for_final_nine'] = False
    report['limitations'] = ['20fps native source clock;30fps not exercised',
        'Cached mixed-source instrument estimates are not acoustic ground truth',
        '34.88s verse/prechorus hook does not prove complete-song structure',
        'Virtual geometry is not a surveyed installation',
        'RGB singer acoustic ownership and exact lexical/phoneme timing remain unqualified']
    (EVIDENCE/(label+'_transparent_candidate.json')).write_text(json.dumps(report, indent=2)+'\n')
    print(label, report['status'], report['readability']['measurements'],
          'identical channel frames:', same, flush=True)
    return report


if __name__ == '__main__':
    check('ac256', 'ac256-transparent', 'ac256')
    check('rgb/06_Modern_Pixel_House', 'rgb-transparent/06_Modern_Pixel_House', 'rgb')
