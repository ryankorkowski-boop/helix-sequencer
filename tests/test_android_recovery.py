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
    preview_stage=result['stages']['preview']
    assert preview_stage['status']=='failed' and 'codec failure' not in result['preview']
    assert preview_stage['failed_variants']==['song.xsq'] and preview_stage['rendered']==0
    assert result['preview_paths']==[''] and [Path(x).name for x in result['sequence_paths']]==['song.xsq']
    assert any('codec failure' in line for line in callback.logs)
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



def test_variant_previews_continue_after_one_codec_failure(completed_job, monkeypatch):
    engine, job = completed_job
    from core import sequence_builder
    original = sequence_builder.run_profile

    def sequence(profile, args):
        original(profile, args)
        for name in ('variant-b.xsq', 'variant-c.xsq'):
            (job/'outputs'/name).write_text('<sequence/>')

    def render(xsq, layout, wav, seconds, callback):
        if xsq.name == 'variant-b.xsq':
            raise ValueError('codec failure')
        movie = xsq.with_suffix('.mp4')
        movie.write_bytes(xsq.name.encode())
        return movie

    monkeypatch.setattr(sequence_builder, 'run_profile', sequence)
    monkeypatch.setattr(mobile, 'render_preview', render)
    callback = Callback()
    result = json.loads(mobile.run(str(engine), str(job), '{"variants":3}', callback))
    # preview_paths stays index-aligned with sequence_paths so the phone picker can
    # play every rendered variant and show the failed one as unavailable.
    by_sequence = {Path(sequence).name: Path(preview).name if preview else ''
                   for sequence, preview in zip(result['sequence_paths'], result['preview_paths'])}
    assert by_sequence == {'song.xsq': 'song.mp4', 'variant-b.xsq': '', 'variant-c.xsq': 'variant-c.mp4'}
    assert Path(result['preview']).name == 'song.mp4'
    preview_stage = result['stages']['preview']
    assert preview_stage['status'] == 'partial'
    assert preview_stage['failed_variants'] == ['variant-b.xsq'] and preview_stage['rendered'] == 2
    assert any('codec failure' in line for line in callback.logs)
    with zipfile.ZipFile(result['bundle']) as archive:
        assert {name for name in archive.namelist() if name.endswith('.mp4')} == {
            'song.mp4', 'variant-c.mp4',
        }
