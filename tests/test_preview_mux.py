from __future__ import annotations

import subprocess
import pytest
from tools import preview_hq as phq


class DummyProc:
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode=returncode;self.stdout=stdout;self.stderr=stderr


def inputs(tmp_path, monkeypatch):
    silent=tmp_path/'in.silent.mp4';audio=tmp_path/'a.mp3';out=tmp_path/'out.mp4'
    silent.write_bytes(b'silent');audio.write_bytes(b'audio')
    monkeypatch.setattr(phq.pr.imageio_ffmpeg,'get_ffmpeg_exe',lambda:'/usr/bin/ffmpeg')
    return silent,audio,out


def test_mux_success_first_attempt(tmp_path, monkeypatch):
    silent,audio,out=inputs(tmp_path,monkeypatch);calls=[]
    def run(cmd,**kwargs):
        calls.append(cmd)
        if '-shortest' in cmd:out.write_bytes(b'encoded')
        return DummyProc()
    monkeypatch.setattr(subprocess,'run',run)
    phq._mux_audio_video(silent,audio,out,faststart=False)
    assert out.exists() and not silent.exists()
    assert len([c for c in calls if '-shortest' in c])==1
    assert any('0:v:0' in c and '0:a:0' in c and 'null' in c for c in calls)


def test_mux_fallback_then_success(tmp_path, monkeypatch):
    silent,audio,out=inputs(tmp_path,monkeypatch);calls=[]
    def run(cmd,**kwargs):
        calls.append(cmd)
        if '-shortest' in cmd:
            if '-fflags' not in cmd:return DummyProc(1,stderr='timestamp failure')
            out.write_bytes(b'fallback')
        return DummyProc()
    monkeypatch.setattr(subprocess,'run',run)
    phq._mux_audio_video(silent,audio,out,faststart=True)
    assert out.exists() and not silent.exists()
    assert len([c for c in calls if '-shortest' in c])==2
    assert any('-avoid_negative_ts' in c and 'make_zero' in c for c in calls)
    assert any('0:a:0' in c and 'null' in c for c in calls)


def test_mux_both_fail_preserve_silent(tmp_path, monkeypatch):
    silent,audio,out=inputs(tmp_path,monkeypatch);calls=[]
    def run(cmd,**kwargs):
        calls.append(cmd);return DummyProc(1,stderr='encoder failed')
    monkeypatch.setattr(subprocess,'run',run)
    with pytest.raises(RuntimeError):phq._mux_audio_video(silent,audio,out,faststart=False)
    assert silent.read_bytes()==b'silent' and not out.exists()
    assert len(calls)==2


def test_failed_audio_decode_cannot_delete_original_silent_render(tmp_path, monkeypatch):
    silent,audio,out=inputs(tmp_path,monkeypatch)
    def run(cmd,**kwargs):
        if '-shortest' in cmd:
            out.write_bytes(b'no-audio');return DummyProc()
        return DummyProc(1,stderr='missing audio stream')
    monkeypatch.setattr(subprocess,'run',run)
    with pytest.raises(RuntimeError,match='validation failed'):
        phq._mux_audio_video(silent,audio,out,faststart=False)
    assert silent.read_bytes()==b'silent' and not out.exists()
