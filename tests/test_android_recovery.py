import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'android/app/src/main/python'))
import helix_mobile as mobile


class Callback:
    def __init__(self): self.checkpoints=[];self.logs=[]
    def log(self,line): self.logs.append(line)
    def checkpoint(self,raw): self.checkpoints.append(json.loads(raw))
    def stage(self,*args): pass


@pytest.fixture
def completed_job(tmp_path,monkeypatch):
    # The bridge intentionally sets JIT off in its dedicated Android process.
    # Restore that environment change after each in-process host recovery fixture.
    monkeypatch.setenv('NUMBA_DISABLE_JIT', '0')
    from core import sequence_builder
    from tools import preview_renderer
    import helix_numba
    monkeypatch.setattr(helix_numba,'install',lambda:None)
    engine=tmp_path/'engine';engine.mkdir()
    for name in ['template.xsq','xlights_rgbeffects.xml']:(engine/name).write_text('<fixture/>')
    job=tmp_path/'job';(job/'input').mkdir(parents=True);(job/'input/audio.wav').write_bytes(b'PCM fixture')
    def sequence(profile,args):
        output=job/'outputs';output.mkdir();(output/'song.xsq').write_text('<sequence/>')
        (output/'xlights_rgbeffects.xml').write_text('<layout/>')
        (output/'audio.wav').write_bytes((job/'input/audio.wav').read_bytes())
    monkeypatch.setattr(sequence_builder,'run_profile',sequence)
    monkeypatch.setattr(preview_renderer,'parse_sequence',lambda x:SimpleNamespace(model_effects={'Roof':[object()]}))
    return engine,job


def test_failed_preview_keeps_sequence_and_zip(completed_job,monkeypatch):
    engine,job=completed_job;callback=Callback()
    def fail(*args):
        assert callback.checkpoints and Path(callback.checkpoints[0]['bundle']).is_file()
        raise ValueError('codec failure')
    monkeypatch.setattr(mobile,'render_preview',fail)
    result=json.loads(mobile.run(str(engine),str(job),'{}',callback))
    assert Path(result['sequence']).is_file() and result['preview']==''
    assert result['stages']['sequencing']['status']=='success'
    assert result['stages']['preview']=={'status':'failed','error':'codec failure'}
    with zipfile.ZipFile(result['bundle']) as archive:
        assert archive.testzip() is None and 'audio.wav' in archive.namelist()
        report=json.loads(archive.read('android-run.json'))
        assert report['stages']['preview']['status']=='failed'
        assert not any(name.endswith('.mp4') for name in archive.namelist())


def test_disabled_preview_is_skipped(completed_job,monkeypatch):
    engine,job=completed_job
    monkeypatch.setattr(mobile,'render_preview',lambda *a:pytest.fail('preview disabled'))
    result=json.loads(mobile.run(str(engine),str(job),'{"preview":false}',Callback()))
    assert result['stages']['preview']['status']=='skipped'


def test_zip_failure_keeps_direct_sequence_export(completed_job,monkeypatch):
    engine,job=completed_job
    monkeypatch.setattr(mobile,'package_show',lambda *a:(_ for _ in ()).throw(OSError('disk full')))
    result=json.loads(mobile.run(str(engine),str(job),'{"preview":false}',Callback()))
    assert Path(result['sequence']).is_file() and result['bundle']==''
    assert result['stages']['packaging']['status']=='failed'


def test_interrupted_preview_keeps_checkpoint(completed_job,monkeypatch):
    engine,job=completed_job;callback=Callback()
    monkeypatch.setattr(mobile,'render_preview',lambda *a:(_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):mobile.run(str(engine),str(job),'{}',callback)
    checkpoint=callback.checkpoints[0]
    assert Path(checkpoint['sequence']).is_file() and Path(checkpoint['bundle']).is_file()


def test_empty_engine_output_is_still_failure(completed_job,monkeypatch):
    engine,job=completed_job
    from tools import preview_renderer
    monkeypatch.setattr(preview_renderer,'parse_sequence',lambda p:SimpleNamespace(model_effects={}))
    with pytest.raises(RuntimeError,match='nonempty'):
        mobile.run(str(engine),str(job),'{"preview":false}',Callback())


@pytest.mark.parametrize('seconds',[121,240,600])
def test_long_preview_request_reaches_renderer(completed_job,monkeypatch,seconds):
    engine,job=completed_job;received=[]
    def render(xsq,layout,wav,length,callback):
        received.append(length)
        movie=xsq.with_suffix('.mp4');movie.write_bytes(b'fixture');return movie
    monkeypatch.setattr(mobile,'render_preview',render)
    result=json.loads(mobile.run(str(engine),str(job),json.dumps({'preview_seconds':seconds}),Callback()))
    assert received==[seconds] and result['stages']['preview']['status']=='success'


@pytest.mark.parametrize('seconds',[0,601])
def test_preview_outside_desktop_parity_limit_is_rejected(tmp_path,seconds):
    with pytest.raises(ValueError,match='1–600'):
        mobile.run(str(tmp_path),str(tmp_path),json.dumps({'preview_seconds':seconds}),Callback())
