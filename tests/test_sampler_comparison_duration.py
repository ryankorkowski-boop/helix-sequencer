from pathlib import Path
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
