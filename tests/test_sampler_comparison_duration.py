from pathlib import Path
import json
import shutil
import subprocess

import numpy as np
import pytest
from tools import render_approval_collection as collection


def test_full_sampler_comparison_uses_256_seconds_one_audio_and_all_panels(tmp_path,monkeypatch):
    commands=[]
    def encode(command):commands.append(command);Path(command[-1]).write_bytes(b'test encode')
    monkeypatch.setattr(collection,'command',encode)
    monkeypatch.setattr(collection,'probe_media',lambda *args:{'streams':[]})
    collection.comparison([tmp_path/f'{i}.mp4' for i in range(3)],[],tmp_path/'comparison.mp4',tmp_path/'sampler.mp3',3,1,duration=256)
    command=commands[0]
    assert command[command.index('-t')+1]=='256'
    assert command.count('3:a:0')==1
    graph=command[command.index('-filter_complex')+1]
    assert all(f'[{i}:v]setpts=PTS-STARTPTS' in graph for i in range(3))


@pytest.mark.parametrize('cols,rows,labels',[(3,4,['layout']*12),(4,3,[]),(4,3,['layout']*11)])
def test_twelve_panel_grid_rejects_wrong_orientation_or_missing_labels(tmp_path,cols,rows,labels):
    with pytest.raises(ValueError):
        collection.comparison([tmp_path/f'{i}.mp4' for i in range(12)],labels,
            tmp_path/'out.mp4',tmp_path/'audio.wav',cols,rows)


def test_actual_twelve_panel_encode_has_correct_order_dimensions_clock_and_audio(tmp_path):
    """Test-only color fixtures expose transposed, missing and repeated cells.

    The soundtrack is the retained owner recording, never a synthesized tone.
    These subsecond fixtures are not native display or approval artifacts.
    """
    audio=Path(__file__).resolve().parents[1]/'fixtures/audio/Phoneme_Test_Hook.mp3'
    if not shutil.which('ffmpeg') or not audio.is_file():
        pytest.skip('ffmpeg and retained real-audio fixture required')
    colors=[(230,30,30),(30,230,30),(30,30,230),(230,230,30),
            (30,230,230),(230,30,230),(180,90,30),(90,180,30),
            (30,90,180),(180,30,90),(90,30,180),(30,180,90)]
    paths=[]
    for i,color in enumerate(colors):
        clip=tmp_path/f'{i}.mp4'
        rgb='0x'+''.join(f'{v:02x}' for v in color)
        subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',
            f'color=c={rgb}:s=48x36:r=30:d=0.4','-c:v','libx264',
            '-threads','1','-pix_fmt','yuv420p',str(clip)],check=True)
        paths.append(clip)
    output=tmp_path/'comparison.mp4'
    labels=[f'{i+1:02} - literal : apostrophe\' % label' for i in range(12)]
    collection.comparison(paths,labels,output,audio,4,3,duration=.4)
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(output)]))
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    soundtrack=next(s for s in info['streams'] if s['codec_type']=='audio')
    assert (video['width'],video['height'],video['avg_frame_rate'])==(1920,1080,'30/1')
    assert video['codec_name']=='h264' and soundtrack['codec_name']=='aac'
    assert int(video['nb_frames'])==12
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(output),'-f','null','-'],check=True)
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(output),'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-'])
    frame=np.frombuffer(raw,dtype=np.uint8).reshape(1080,1920,3)
    for i,color in enumerate(colors):
        pixel=frame[(i//4)*360+180,(i%4)*480+240].astype(int)
        assert np.max(np.abs(pixel-np.asarray(color)))<12,(i,pixel,color)
    samples=collection.pcm(output)
    assert np.isfinite(samples).all() and np.sqrt(np.mean(samples**2))>.001
