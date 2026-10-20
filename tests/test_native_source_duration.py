"""Actual WAV duration flows into the retained-score adapter, without a 36s cap."""
import hashlib
import json
from types import SimpleNamespace
import wave

from tools import render_approval_revision as renderer


def test_source_setup_uses_actual_audio_duration_and_hash(tmp_path, monkeypatch):
    folder=tmp_path/'sources'/'FULL';folder.mkdir(parents=True)
    (folder.parent/'selected_excerpts.json').write_text(json.dumps([
        {'excerpt_id':'FULL','filename':'original.wav'}]))
    audio=folder/'audio.wav'
    with wave.open(str(audio),'wb') as stream:
        stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(8000)
        stream.writeframes(bytes(8000*2*42))
    captured={}
    def performance(source, scene, analysis):
        captured.update(source)
        return SimpleNamespace(n=round(source['duration']*20))
    monkeypatch.setattr(renderer,'ReviewBandPerformance',performance)
    _,selected,_,score=renderer.setup(tmp_path,'FULL',scene_factory=lambda _:object())
    assert selected==audio
    assert captured['duration']==42
    assert score.n==840
    assert captured['sha256']==hashlib.sha256(audio.read_bytes()).hexdigest()
