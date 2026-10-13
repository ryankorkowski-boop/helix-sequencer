"""ISO box regressions plus independently decoded AAC presentation edits."""
import struct
import subprocess
import sys
from pathlib import Path
import numpy as np
import pytest
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'android/app/src/main/python'))
import helix_mp4 as mp4


def extended(kind, data):
    return struct.pack('>I4sQ', 1, kind, len(data)+16)+data


def movie(*, version=0, extended_containers=False):
    wrap = extended if extended_containers else mp4.box
    time = (struct.pack('>IQQIQ', 1<<24, 0, 0, 1000, 5000) if version else
            struct.pack('>IIIIII', 0, 0, 0, 1000, 5000, 0))
    track = (struct.pack('>IQQIIQ', 1<<24, 0, 0, 1, 0, 5000) if version else
             struct.pack('>IIIIIII', 0, 0, 0, 1, 0, 5000, 0))
    handler = mp4.box(b'hdlr', struct.pack('>II4s', 0, 0, b'soun'))
    chunks = mp4.box(b'stco', struct.pack('>III', 0, 1, 40))
    mdia = wrap(b'mdia', mp4.box(b'mdhd', time)+handler+chunks)
    return wrap(b'moov', mp4.box(b'mvhd', time)+wrap(b'trak', mp4.box(b'tkhd', track)+mdia))


@pytest.mark.parametrize('header', [
    b'x', struct.pack('>I4s', 7, b'mdat'),
    struct.pack('>I4s', 99, b'mdat'), struct.pack('>I4s', 1, b'mdat'),
    struct.pack('>I4sQ', 1, b'mdat', 15),
    struct.pack('>I4sQ', 1, b'mdat', 100),
    struct.pack('>I4s', 8, b'uuid'),
])
def test_malformed_boundaries_are_rejected(header):
    with pytest.raises(ValueError):
        list(mp4.boxes(header))


def test_extended_and_eof_boxes_parse():
    data=extended(b'mdat', b'abc')+struct.pack('>I4s', 0, b'free')+b'end'
    assert list(mp4.boxes(data)) == [(0,19,b'mdat'), (19,11,b'free')]
    with pytest.raises(ValueError):
        list(mp4.boxes(data, 0, len(data)+1))


@pytest.mark.parametrize('version', [0,1])
@pytest.mark.parametrize('containers', [False,True])
@pytest.mark.parametrize('terminal', ['extended-media','eof-media','eof-moov'])
def test_edits_preserve_media_positions_and_support_all_box_sizes(tmp_path, version, containers, terminal):
    metadata=movie(version=version, extended_containers=containers)
    if terminal=='eof-media':
        content=metadata+struct.pack('>I4s',0,b'mdat')+b'actual samples'
    elif terminal=='eof-moov':
        # A size=0 moov is a valid terminal movie container.
        ordinary=movie(version=version)
        content=extended(b'mdat',b'actual samples')+b'\0\0\0\0'+ordinary[4:]
    else:
        content=extended(b'mdat',b'actual samples')+metadata
    path=tmp_path/'native.mp4';path.write_bytes(content)
    original_sample_position=content.index(b'actual samples')
    mp4.add_audio_edit(path,2048,22050,3)
    result=path.read_bytes()
    assert result.index(b'actual samples')==original_sample_position
    top=list(mp4.boxes(result))
    assert top[-1][2]==b'moov' and sum(k==b'moov' for _,_,k in top)==1
    assert b'stco'+struct.pack('>III',0,1,40) in result
    assert b'elst' in result
    elst=result.index(b'elst')+4
    assert struct.unpack_from('>IIIi',result,elst)==(0,1,3000,93)


@pytest.mark.parametrize('suffix', [
    b'bad', struct.pack('>I4sQ',1,b'mdat',999), mp4.box(b'moof',b'')
])
def test_bad_trailing_boxes_leave_movie_unchanged(tmp_path,suffix):
    content=movie()+suffix;path=tmp_path/'bad.mp4';path.write_bytes(content)
    with pytest.raises(ValueError):
        mp4.add_audio_edit(path,0,22050,3)
    assert path.read_bytes()==content


def test_large_duration_upgrades_headers_and_edit_list(tmp_path):
    path=tmp_path/'long.mp4';path.write_bytes(movie())
    mp4.add_audio_edit(path,0,22050,5_000_000)
    data=path.read_bytes();root=list(mp4._boxes(data))[-1]
    revised=data[root[0]:root[0]+root[1]];r=next(mp4._boxes(revised))
    mvhd=mp4._child(revised,r[3],len(revised),b'mvhd')
    assert revised[mvhd[0]+mvhd[3]]==1
    elst=revised.index(b'elst')+4
    assert struct.unpack_from('>IIQq',revised,elst)==(1<<24,1,5_000_000_000,0)


@pytest.mark.parametrize('audio_format', ['wav','mp3'])
@pytest.mark.parametrize('seconds', [2,30])
def test_real_aac_edit_full_decode_and_soundtrack_alignment(tmp_path,audio_format,seconds):
    rate=22050;t=np.arange(rate*(seconds+1))/rate
    rng=np.random.default_rng(51)
    audio=(.12*np.sin(2*np.pi*220*t)+.04*rng.normal(size=len(t))).astype('float32')
    original=tmp_path/'source.wav';sf.write(original,audio,rate)
    source=tmp_path/'normalized.wav'
    if audio_format=='mp3':
        compressed=tmp_path/'source.mp3'
        subprocess.run(['ffmpeg','-v','error','-i',str(original),str(compressed)],check=True)
        subprocess.run(['ffmpeg','-v','error','-i',str(compressed),str(source)],check=True)
    else:
        source.write_bytes(original.read_bytes())
    path=tmp_path/'encoded.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=size=64x64:rate=15',
                    '-i',str(source),'-t',str(seconds+.2),'-c:v','libx264','-c:a','aac',
                    '-use_editlist','0',str(path)],check=True)
    # Mimic MediaMuxer's extended-size mdat without moving chunk addresses.
    data=path.read_bytes();top=list(mp4.boxes(data));free=next(x for x in top if x[2]==b'free');mdat=next(x for x in top if x[2]==b'mdat')
    assert free[1]==8 and free[0]+8==mdat[0]
    replacement=extended(b'mdat',data[mdat[0]+8:mdat[0]+mdat[1]])
    path.write_bytes(data[:free[0]]+replacement+data[mdat[0]+mdat[1]:])
    decoded=tmp_path/'before.wav'
    subprocess.run(['ffmpeg','-v','error','-i',str(path),str(decoded)],check=True)
    alignment=mp4.synchronize(path,source,decoded,seconds)
    assert alignment['alignment_correlation']>.85
    after=tmp_path/'after.wav'
    subprocess.run(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0',str(after)],check=True)
    subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],check=True)
    expected,sr=sf.read(source);actual,sr2=sf.read(after);n=min(len(expected),len(actual),seconds*sr)
    assert sr==sr2 and np.corrcoef(expected[:n],actual[:n])[0,1]>.85
    assert abs(len(actual)/sr-seconds)<.06
