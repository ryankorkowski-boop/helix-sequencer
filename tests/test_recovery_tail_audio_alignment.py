from pathlib import Path
import numpy as np
import pytest
from tools import verify_recovery_media as media


def test_long_comparison_rejects_delay_only_in_final_two_seconds(tmp_path,monkeypatch):
    source=tmp_path/'source.mp3';source.write_bytes(b'authenticated source')
    video=tmp_path/'movie.mp4';video.write_bytes(b'unit fixture')
    pcm=np.random.default_rng(9).normal(0,.1,256*16000).astype('float32')
    delayed=pcm.copy();delayed[-32000:]=np.roll(pcm[-32000:],1600)
    assert np.corrcoef(pcm,delayed)[0,1]>.97
    monkeypatch.setattr(media,'pcm',lambda p:pcm if Path(p)==source else delayed)
    monkeypatch.setattr(media,'probe_media',lambda *a:{'streams':[
        dict(codec_type='video',codec_name='h264',width=1280,height=720,duration='256',avg_frame_rate='20/1'),
        dict(codec_type='audio',codec_name='aac',duration='256')]})
    monkeypatch.setattr(media.subprocess,'run',lambda *a,**k:None)
    with pytest.raises(ValueError,match='Soundtrack alignment'):
        media.verify(video,source,media.digest(source))
