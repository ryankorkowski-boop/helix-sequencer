from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT/'android/app/src/main/python'
sys.path.insert(0, str(MOBILE))
from helix_mobile import build_args, preview_sequence


def test_lor_disables_rgb_and_requires_real_lms(tmp_path):
    job=tmp_path/'job'; (job/'input').mkdir(parents=True)
    with pytest.raises(ValueError, match='LMS'):
        build_args({'mode':'lor'}, job, ROOT)
    (job/'input/source.lms').write_text('<sequence/>')
    args=build_args({'mode':'lor','palette':'neon','spatial':True},job,ROOT)
    assert '--helix-lor-source-lms' in args and '--ac-lights-only' in args
    assert '--palette-mode' not in args and '--helix-spatial-accent' not in args
    assert '--no-matrix-intelligence' in args


def test_neon_and_routing_use_current_cli(tmp_path):
    (tmp_path/'input').mkdir();(tmp_path/'input/routing.json').write_text('{}')
    args=build_args({'mode':'xlights','palette':'neon','spatial':True},tmp_path,ROOT)
    assert args[args.index('--palette-mode')+1]=='neon'
    assert '--model-overrides-file' in args and '--helix-spatial-accent' in args
    assert '--helix-lor-source-lms' not in args


@pytest.mark.parametrize('settings',[{'variants':0},{'variants':9},{'mode':'anything'}])
def test_invalid_mobile_requests_are_rejected(settings,tmp_path):
    with pytest.raises(ValueError):build_args(settings,tmp_path,ROOT)


def test_engine_bundle_preserves_source_and_excludes_media(tmp_path):
    from tools.stage_android_engine import stage
    manifest=stage(tmp_path)
    with zipfile.ZipFile(tmp_path/'helix-engine.zip') as z:
        assert z.read('core/effect_engine.py')==(ROOT/'core/effect_engine.py').read_bytes()
        assert z.read('core/sequence_builder.py')==(ROOT/'core/sequence_builder.py').read_bytes()
        assert 'helix_intent/placement_pipeline.py' in z.namelist()
        assert all(not n.endswith(('.mp3','.mp4','.wav')) for n in z.namelist())
        assert z.read('LICENSE')==(ROOT/'LICENSE').read_bytes()
    assert manifest['archive_sha256']
    extracted=tmp_path/'engine'
    with zipfile.ZipFile(tmp_path/'helix-engine.zip') as z:z.extractall(extracted)
    code='import sys;sys.path[:0]=sys.argv[1:];import helix_numba;helix_numba.install();from core import sequence_builder;print(sequence_builder.available_versions())'
    subprocess.run([sys.executable,'-I','-c',code,str(MOBILE),str(extracted)],cwd=tmp_path,check=True,timeout=60)


PARITY = r'''
import os,sys
sys.path.insert(0,sys.argv[1])
if sys.argv[2]=='mobile':
    import helix_numba;helix_numba.install()
import numpy as np,librosa
sr=22050;t=np.arange(sr*4)/sr
y=(.2*np.sin(2*np.pi*220*t)+.1*np.sin(2*np.pi*440*t)).astype(np.float32)
for p in np.arange(.15,4,.5):
    i=int(p*sr);y[i:i+400]+=.7*np.exp(-np.arange(400)/60).astype(np.float32)
o=librosa.onset.onset_strength(y=y,sr=sr)
tempo,beats=librosa.beat.beat_track(y=y,sr=sr)
h,p=librosa.effects.hpss(y)
pitch,magnitude=librosa.piptrack(y=y,sr=sr)
cqt=np.abs(librosa.cqt(y=y,sr=sr))
rng=np.random.default_rng(313)
x=rng.normal(size=(3,70)).astype(np.float32)
np.savez(sys.argv[3],onsets=o,tempo=tempo,beats=beats,harmonic=h,percussive=p,pitch=pitch,
    magnitude=magnitude,cqt=cqt,localmax=librosa.util.localmax(x,axis=-1),
    localmin=librosa.util.localmin(x,axis=-1),zcr=librosa.feature.zero_crossing_rate(y),
    peaks=librosa.util.peak_pick(o,pre_max=3,post_max=3,pre_avg=3,post_avg=5,delta=.5,wait=3))
'''


def test_android_numeric_kernels_match_original_librosa(tmp_path):
    for mode in ['desktop','mobile']:
        subprocess.run([sys.executable,'-c',PARITY,str(MOBILE),mode,str(tmp_path/f'{mode}.npz')],check=True,timeout=180)
    with np.load(tmp_path/'desktop.npz') as a,np.load(tmp_path/'mobile.npz') as b:
        assert a.files==b.files
        for key in a.files:
            np.testing.assert_allclose(a[key],b[key],rtol=1e-5,atol=1e-6,err_msg=key)


def test_manifest_keeps_offline_service_private_and_remote_opt_in():
    import xml.etree.ElementTree as ET
    root=ET.parse(ROOT/'android/app/src/main/AndroidManifest.xml').getroot()
    n='{http://schemas.android.com/apk/res/android}'
    permissions={p.get(n+'name') for p in root.findall('uses-permission')}
    assert 'android.permission.INTERNET' in permissions
    main=(ROOT/'android/app/src/main/java/org/helixsequencer/android/MainActivity.java').read_text()
    assert 'new Intent(this, RemoteActivity.class)' in main
    assert 'startForegroundService(new Intent(this,EngineService.class)' in main
    assert 'android.permission.MANAGE_EXTERNAL_STORAGE' not in permissions
    service=root.find('./application/service')
    assert service.get(n+'exported')=='false' and service.get(n+'process')==':engine'


def test_short_preview_matches_full_timeline_and_keeps_fade_shape():
    from tools.preview_renderer import parse_models, SequenceData, EffectRecord, build_leaf_intensity_matrix
    layout=parse_models(ROOT/'tests/fixtures/beta_demo/minimal_layout.xml')
    name=next(iter(layout.leaf_models))
    sequence=SequenceData(8000,{name:[
        EffectRecord('Ramp',0,6000,'E_TEXTCTRL_Eff_On_Start=0,E_TEXTCTRL_Eff_On_End=100'),
        EffectRecord('Bars',5000,7800),
    ]},{})
    clipped=preview_sequence(sequence,3)
    leaves,full=build_leaf_intensity_matrix(layout,sequence,15)
    short_leaves,short=build_leaf_intensity_matrix(layout,clipped,15)
    assert leaves==short_leaves and short.shape[1]==45
    np.testing.assert_allclose(short,full[:,:45])
    assert sequence.duration_ms==8000 and sequence.model_effects[name][1].start_ms==5000


def test_native_aac_delay_is_measured_from_actual_pcm(tmp_path):
    import soundfile as sf
    from helix_mp4 import measure_delay
    rate=22050
    signal=np.random.default_rng(67).normal(0,.1,(rate*3,2)).astype('float32')
    source=tmp_path/'source.wav';decoded=tmp_path/'decoded.wav'
    sf.write(source,signal,rate,subtype='PCM_16')
    sf.write(decoded,np.vstack([np.zeros((2048,2)),signal,np.zeros((rate//2,2))]),rate,subtype='PCM_16')
    delay,sr,correlation=measure_delay(source,decoded,3)
    assert delay==2048 and sr==rate and correlation>.999
