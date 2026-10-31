import hashlib
from pathlib import Path
import wave
import numpy as np
import pytest
from tools.showcase_excerpt_rank import rank_one
from tools.showcase_vocal_alignment import corroborated
from models.ultimate_showcase import Garden
from tools.showcase_audio_preview import NativeSongView


def test_activity_selection_uses_late_busy_audio_and_retains_source_identity(tmp_path):
    rate=8000;t=np.arange(rate*80)/rate
    y=np.zeros(len(t));busy=t>=40
    y[busy]=.15*np.sin(2*np.pi*(220*t[busy]+10*np.sin(t[busy]*3)))
    for start in np.arange(40,79,.17):
        lo=round(start*rate);n=min(400,len(y)-lo)
        y[lo:lo+n]+=.25*np.exp(-np.arange(n)/80)*np.sin(np.arange(n)*.42)
    pcm=(np.column_stack((y,y*.8))*32767).astype('<i2')
    path=tmp_path/'source.wav'
    with wave.open(str(path),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm.tobytes())
    row=dict(id='source',mime_type='audio/wav',title='Not an instrument label.wav',folder='test')
    first=rank_one((row,tmp_path));second=rank_one((row,tmp_path))
    assert first==second
    assert first['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert first['candidates'][0]['start_seconds']>=38
    assert all(c['end_seconds']-c['start_seconds']==36 for c in first['candidates'])
    assert 'unverified' in first['classification']


def test_lyric_gate_rejects_uncorroborated_transcription():
    ref='Snow is falling. Lights are glowing. We are dancing through the night.'
    assert corroborated('Lights are glowing',ref)
    assert not corroborated('Thank you for watching and subscribe',ref)
    assert not corroborated('Duh',ref)
    assert not corroborated('The lights are broken in the night',ref)


def test_new_preview_camera_preserves_default_and_channel_addresses():
    g=Garden();g.custom('TEST',np.array([[-30,0,50],[30,0,50],[-30,40,-50],[30,40,-50]]),'TEST','camera test',['#CCAA55']*4,{})
    g.models[0].start=1
    old=NativeSongView(g,'test',320,180)
    explicit=NativeSongView(g,'test',320,180,yaw=7,pitch=18)
    front=NativeSongView(g,'test',320,180,yaw=7,pitch=-18)
    assert np.array_equal(np.asarray(old.base),np.asarray(explicit.base))
    assert np.array_equal(old.sorted_rgb_indices,explicit.sorted_rgb_indices)
    assert sorted(front.sorted_rgb_indices.ravel())==sorted(old.sorted_rgb_indices.ravel())
    assert not np.array_equal(front.unique,old.unique)
