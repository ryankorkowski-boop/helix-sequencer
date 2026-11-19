from pathlib import Path
import pytest


def test_direct_main_for_raises_original_cause_after_song_failure(tmp_path,monkeypatch):
    from core import effect_engine as engine
    audio=tmp_path/'song.wav';audio.write_bytes(b'fixture; never analyzed')
    marker=ValueError('injected source analysis failure')
    def fail(*args,**kwargs):raise marker
    monkeypatch.setattr(engine,'run_variant',fail)
    root=Path(__file__).resolve().parents[1]
    with pytest.raises(RuntimeError,match='song.wav') as caught:
        engine.main_for(engine.ACTIVE_STYLE_VERSION,['--template',str(root/'template.xsq'),
            '--audio',str(audio),'--output-dir',str(tmp_path/'output'),'--variants','1',
            '--no-prompt','--no-save-settings','--quiet'])
    assert caught.value.__cause__ is marker
