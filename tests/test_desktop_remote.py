"""Real HTTP/process lifecycle tests, isolated from musical decisions."""
import io
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
import pytest
from tools.desktop_remote import RemoteJobs, RemoteServer, settings
from tools.desktop_remote_worker import build_args

TOKEN='synthetic-pairing-key-for-test-only-12345678'

@pytest.fixture
def remote(tmp_path):
    jobs=RemoteJobs(tmp_path,token=TOKEN)
    server=RemoteServer(('127.0.0.1',0),jobs);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield jobs,'http://127.0.0.1:'+str(server.server_port)
    server.close();thread.join(timeout=3)


def call(base,path,method='GET',data=None,token=TOKEN):
    body=json.dumps(data).encode() if data is not None else None
    request=urllib.request.Request(base+path,data=body,method=method,headers={'Authorization':'Bearer '+token})
    with urllib.request.urlopen(request,timeout=3) as response:return json.load(response)


def test_auth_and_fixed_routes(remote):
    jobs,base=remote
    with pytest.raises(urllib.error.HTTPError) as error:call(base,'/v1/status',token='incorrect')
    assert error.value.code==401 and jobs.jobs=={}
    state=call(base,'/v1/status');assert state['modes']==['xlights','lor']
    for path in ('/v1/jobs/../../etc/passwd','/v1/jobs/%2e%2e/bundle'):
        with pytest.raises(urllib.error.HTTPError):call(base,path)


def test_upload_start_real_child_and_download(remote):
    jobs,base=remote
    script="import sys,json,zipfile;from pathlib import Path;p=Path(sys.argv[1]);(p/'result.json').write_text(json.dumps({'preview':''}));z=zipfile.ZipFile(p/'Helix-show.zip','w');z.writestr('synthetic-controller-test.txt','test');z.close()"
    jobs.command=lambda folder:[sys.executable,'-c',script,str(folder)]
    identity=call(base,'/v1/jobs','POST',{'mode':'xlights','preview':False})['id']
    request=urllib.request.Request(base+'/v1/jobs/'+identity+'/files/audio',data=b'synthetic-controller-test-only',method='PUT',headers={'Authorization':'Bearer '+TOKEN})
    with urllib.request.urlopen(request) as r:assert json.load(r)['uploaded']==['audio']
    assert call(base,'/v1/jobs/'+identity+'/start','POST',{})['phase'] in ('running','complete')
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        state=call(base,'/v1/jobs/'+identity)
        if state['phase']!='running':break
        time.sleep(.02)
    assert state['phase']=='complete' and state['bundle']
    request=urllib.request.Request(base+'/v1/jobs/'+identity+'/bundle',headers={'Authorization':'Bearer '+TOKEN})
    with urllib.request.urlopen(request) as r:assert r.read().startswith(b'PK')


def test_cancel_only_owned_process_and_reject_parallel_job(remote):
    jobs,base=remote;jobs.command=lambda folder:[sys.executable,'-c','import time;time.sleep(60)']
    first=jobs.create({'preview':False})['id'];jobs.upload(first,'audio',io.BytesIO(b'song'),4);jobs.start(first)
    second=jobs.create({})['id'];jobs.upload(second,'audio',io.BytesIO(b'song'),4)
    with pytest.raises(ValueError,match='Another'):jobs.start(second)
    state=call(base,'/v1/jobs/'+first+'/cancel','POST',{})
    assert state['phase']=='cancelled'
    proc=jobs.find(first)['process'];assert proc is None or proc.poll() is not None
    assert jobs.state(second)['phase']=='draft'


def test_upload_failure_does_not_promote_partial_file(remote):
    jobs,_=remote;identity=jobs.create({'mode':'lor'})['id']
    with pytest.raises(ValueError,match='Interrupted'):jobs.upload(identity,'audio',io.BytesIO(b'a'),3)
    assert jobs.state(identity)['uploaded']==[]
    with pytest.raises(ValueError,match='Unsupported'):jobs.upload(identity,'../escape',io.BytesIO(b'a'),1)
    with pytest.raises(ValueError,match='Missing'):jobs.start(identity)


@pytest.mark.parametrize('value',[{'variants':True},{'variants':9},{'preview_seconds':0},{'shell':'rm'},{'preview':'false'},{'mode':'other'}])
def test_untrusted_settings_cannot_supply_commands(value):
    with pytest.raises(ValueError):settings(value)


def test_remote_uses_canonical_modes_and_keeps_desktop_orchestrator(tmp_path):
    (tmp_path/'input').mkdir()
    args=build_args({'mode':'xlights','palette':'neon','spatial':True},tmp_path)
    assert '--palette-mode' in args and '--helix-spatial-accent' in args
    assert '--no-effects-orchestrator' not in args
    assert '--helix-preview-mp4' in args
    args=build_args({'mode':'lor','palette':'neon','spatial':True},tmp_path)
    assert '--helix-lor-source-lms' in args and '--ac-lights-only' in args
    assert '--palette-mode' not in args and '--helix-spatial-accent' not in args
