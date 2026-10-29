import copy
import shutil
import subprocess
import wave

import numpy as np
import pytest

from tools.assemble_beta_review import assemble, assembly_key, package
from tools.phoneme_source import digest


def test_native_presentation_reuses_only_matching_decoded_bytes(tmp_path):
    if not shutil.which('ffmpeg'):pytest.skip('ffmpeg required')
    audio=tmp_path/'source.wav';video=tmp_path/'native.mp4'
    with wave.open(str(audio),'wb') as w:
        w.setparams((1,2,16000,0,'NONE','not compressed'))
        t=np.arange(9600)/16000
        w.writeframes((np.sin(2*np.pi*440*t)*10000).astype('<i2').tobytes())
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=s=160x90:r=20',
                    '-t','0.6','-c:v','libx264',str(video)],check=True)
    item=dict(filename='review.mp4',title='Native review',audio=str(audio),audio_sha256=digest(audio),
              duration=.6,kind='single',sources=[dict(video=str(video),video_sha256=digest(video),gamma=1)])
    config=dict(source_commit='fixture',limitations=['Test fixture only'],movies=[item])
    output=tmp_path/'movies'
    first=assemble(config,output)[0]
    before=(output/'review.mp4').stat().st_mtime_ns
    second=assemble(config,output)[0]
    assert not first['cache_hit'] and first['decode_verified']
    assert second['cache_hit'] and (output/'review.mp4').stat().st_mtime_ns==before
    # Restored identical sources at a different path retain their identity.
    moved=tmp_path/'restored.mp4';shutil.copyfile(video,moved)
    item['sources'][0]['video']=str(moved)
    assert assemble(config,output)[0]['cache_hit']
    # A corrupt output is rebuilt, never silently reused by filename.
    (output/'review.mp4').write_bytes(b'truncated')
    assert not assemble(config,output)[0]['cache_hit']
    item['title']='Changed title'
    assert not assemble(config,output)[0]['cache_hit']
    item['kind']='residential_pair'
    item['sources']=[dict(item['sources'][0],title='Traditional AC'),dict(item['sources'][0],title='RGB')]
    assert assemble(config,output)[0]['decode_verified']
    with pytest.raises(ValueError,match='Exactly two'):
        item['sources'].pop()
        assemble(config,output)
    item['kind']='montage';item['sources'][0]['title']='Source view'
    item['segments']=[dict(start=0,end=.3,source=0),dict(start=.3,end=.6,source=0)]
    assert assemble(config,output)[0]['decode_verified']
    clips=list((tmp_path/'montage-cache').glob('*.mp4'));assert len(clips)==2
    clip_times={p.name:p.stat().st_mtime_ns for p in clips}
    (output/'review.mp4').unlink()
    assert not assemble(config,output)[0]['cache_hit']
    assert {p.name:p.stat().st_mtime_ns for p in clips}==clip_times
    moved.write_bytes(b'different source')
    with pytest.raises(ValueError,match='Native video hash'):assemble(config,output)


def test_encoder_and_visual_settings_invalidate_presentation_key():
    item=dict(audio='a',audio_sha256='hash',sources=[dict(video='v',video_sha256='native',gamma=1)])
    original=assembly_key(item,'ffmpeg v1')
    assert assembly_key(item,'ffmpeg v2')!=original
    changed=copy.deepcopy(item);changed['sources'][0]['gamma']=2
    assert assembly_key(changed,'ffmpeg v1')!=original


def test_package_count_is_explicit_and_failed_write_preserves_previous(tmp_path):
    for i in range(9):(tmp_path/f'{i}.mp4').write_bytes(bytes([i]))
    names=[f'{i}.mp4' for i in range(9)];target=tmp_path/'review.zip'
    assert package(tmp_path,target,names,expected_count=9)['crc_and_hashes_verified']
    before=digest(target)
    with pytest.raises(ValueError):package(tmp_path,target,names)
    (tmp_path/'8.mp4').unlink()
    with pytest.raises(FileNotFoundError):package(tmp_path,target,names,expected_count=9)
    assert digest(target)==before
