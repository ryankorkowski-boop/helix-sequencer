"""Opt-in, token-paired desktop jobs. No shell commands or client-chosen paths."""
from __future__ import annotations
import argparse
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
ROLES = {'audio':'original-audio', 'layout':'xlights_rgbeffects.xml', 'template':'template.xsq',
         'lor':'source.lms', 'networks':'xlights_networks.xml', 'routing':'routing.json'}
MAX_UPLOAD = 512*1024*1024


def settings(value):
    if not isinstance(value, dict): raise ValueError('Settings must be an object')
    allowed={'mode','variants','preview_seconds','preview','polish','palette','matrix','birdsong','spatial','ac_compatible'}
    if set(value)-allowed: raise ValueError('Unknown settings')
    result=dict(value)
    if result.get('mode','xlights') not in ('xlights','lor'): raise ValueError('Invalid mode')
    if result.get('palette','default') not in ('default','neon'): raise ValueError('Invalid palette')
    for key,default,high in [('variants',1,8),('preview_seconds',30,600)]:
        n=result.get(key,default)
        if type(n) is not int or not 1<=n<=high: raise ValueError('Invalid '+key)
        result[key]=n
    for key in allowed-{'mode','variants','preview_seconds','palette'}:
        if key in result and type(result[key]) is not bool: raise ValueError('Invalid '+key)
    return result


class RemoteJobs:
    def __init__(self, root, token=None, command=None):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.token=token or secrets.token_urlsafe(32)
        if len(self.token)<32: raise ValueError('Pairing key must contain at least32 characters')
        self.lock=threading.RLock();self.jobs={};self.command=command or self.worker_command
    @staticmethod
    def worker_command(folder):
        if getattr(sys,'frozen',False): return [str(ROOT/'HelixCLI.exe'),'--helix-remote-worker',str(folder)]
        return [sys.executable,'-m','tools.desktop_remote_worker',str(folder)]
    def create(self, request):
        request=settings(request)
        with self.lock:
            if len(self.jobs)>=100: raise ValueError('Session has100 jobs; restart the phone link to create more')
            identity=str(uuid.uuid4());folder=self.root/identity;(folder/'input').mkdir(parents=True)
            (folder/'request.json').write_text(json.dumps(request))
            self.jobs[identity]={'id':identity,'phase':'draft','message':'Choose files, then start','folder':folder,'uploading':False,'process':None,'uploads':set()}
            return self.state(identity)
    def find(self, identity):
        if not re.fullmatch(r'[0-9a-f-]{36}',identity) or identity not in self.jobs: raise KeyError('Unknown job')
        return self.jobs[identity]
    def state(self, identity):
        with self.lock:
            job=self.find(identity);folder=job['folder'];log=folder/'run.log'
            result={k:job[k] for k in ('id','phase','message')}
            if log.exists():
                with log.open('rb') as f:f.seek(max(0,log.stat().st_size-60000));result['log']=f.read().decode(errors='replace')
            result['uploaded']=[role for role,name in ROLES.items() if role in job['uploads']]
            result['bundle']=(folder/'Helix-show.zip').is_file() and job['phase']=='complete'
            result['preview']=(folder/'result.json').is_file() and job['phase']=='complete' and bool(json.loads((folder/'result.json').read_text()).get('preview'))
            return result
    def upload(self, identity, role, stream, length):
        if role not in ROLES: raise ValueError('Unsupported file role')
        if not 0<length<=MAX_UPLOAD: raise ValueError('File must contain1byte–512MiB')
        with self.lock:
            job=self.find(identity)
            if job['phase']!='draft' or job['uploading']: raise ValueError('Job is not accepting files')
            job['uploading']=True;target=job['folder']/'input'/ROLES[role];part=target.with_suffix(target.suffix+'.part')
        try:
            with part.open('wb') as out:
                remaining=length
                while remaining:
                    data=stream.read(min(65536,remaining))
                    if not data: raise ValueError('Interrupted file upload')
                    out.write(data);remaining-=len(data)
            with self.lock:
                if job['phase']!='draft': raise ValueError('Upload cancelled')
                part.replace(target);job['uploads'].add(role)
        finally:
            part.unlink(missing_ok=True)
            with self.lock:job['uploading']=False
    def start(self, identity):
        with self.lock:
            job=self.find(identity)
            if job['phase']!='draft' or job['uploading']: raise ValueError('Job is not ready to start')
            if any(j['phase']=='running' for j in self.jobs.values()): raise ValueError('Another phone job is running')
            request=json.loads((job['folder']/'request.json').read_text());required=['audio']+(['lor'] if request.get('mode')=='lor' else [])
            if any(not (job['folder']/'input'/ROLES[r]).is_file() for r in required): raise ValueError('Missing required song or LOR layout')
            job.update(phase='running',message='Running desktop Helix')
            threading.Thread(target=self._run,args=(job,),daemon=True).start()
        return self.state(identity)
    def _run(self, job):
        try:
            with (job['folder']/'run.log').open('wb') as log:
                with self.lock:
                    if job['phase']=='cancelled': return
                    options={'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
                    proc=subprocess.Popen(self.command(job['folder']),cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,**options);job['process']=proc
                code=proc.wait()
            with self.lock:
                if job['phase']=='cancelled': return
                if code or not (job['folder']/'Helix-show.zip').is_file(): raise RuntimeError('Desktop build failed; inspect its log')
                job.update(phase='complete',message='Desktop build complete')
        except Exception as error:
            with self.lock:
                if job['phase']!='cancelled':job.update(phase='failed',message=str(error))
    def cancel(self, identity):
        with self.lock:
            job=self.find(identity)
            if job['phase'] in ('complete','failed','cancelled'): return self.state(identity)
            job.update(phase='cancelled',message='Desktop build cancelled');proc=job['process']
        if proc is not None and proc.poll() is None:
            if os.name=='nt': subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,check=False)
            else:
                try:os.killpg(proc.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:os.killpg(proc.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
        return self.state(identity)
    def close(self):
        for identity in list(self.jobs):self.cancel(identity)


class RemoteServer(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,jobs):self.jobs=jobs;super().__init__(address,RemoteHandler)
    def close(self):self.jobs.close();self.shutdown();self.server_close()


class RemoteHandler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass  # Pairing credentials and filenames never enter access logs.
    def _reply(self,code,value):
        data=json.dumps(value).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def _serve(self):
        try:
            if not hmac.compare_digest(self.headers.get('Authorization',''), 'Bearer '+self.server.jobs.token):
                self._reply(401,{'error':'Pairing key required'});return
            parts=self.path.split('/')[1:];jobs=self.server.jobs
            if self.command=='GET' and parts==['v1','status']:
                with jobs.lock:states=[jobs.state(i) for i in list(jobs.jobs)[-20:]]
                self._reply(200,{'schema':'helix.remote.v1','jobs':states,'modes':['xlights','lor']});return
            if self.command=='POST' and parts==['v1','jobs']:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=65536:raise ValueError('Invalid request size')
                self._reply(201,jobs.create(json.loads(self.rfile.read(length))));return
            if len(parts)>=3 and parts[:2]==['v1','jobs']:
                identity=parts[2];jobs.find(identity)
                if self.command=='GET' and len(parts)==3:self._reply(200,jobs.state(identity));return
                if self.command=='PUT' and len(parts)==5 and parts[3]=='files':
                    jobs.upload(identity,parts[4],self.rfile,int(self.headers.get('Content-Length','0')));self._reply(200,jobs.state(identity));return
                if self.command=='POST' and len(parts)==4 and parts[3] in ('start','cancel'):
                    self._reply(200,getattr(jobs,parts[3])(identity));return
                if self.command=='GET' and len(parts)==4 and parts[3] in ('bundle','preview'):
                    job=jobs.find(identity)
                    if job['phase']!='complete':raise ValueError('Build is not complete')
                    result=json.loads((job['folder']/'result.json').read_text())
                    file=job['folder']/'Helix-show.zip' if parts[3]=='bundle' else Path(result['preview'])
                    if not file.is_file() or not file.resolve().is_relative_to(job['folder']):raise ValueError('Output unavailable')
                    self.send_response(200);self.send_header('Content-Length',str(file.stat().st_size));self.send_header('Content-Type','application/zip' if parts[3]=='bundle' else 'video/mp4');self.end_headers()
                    with file.open('rb') as source:
                        while data:=source.read(65536):self.wfile.write(data)
                    return
            self._reply(404,{'error':'Unknown endpoint'})
        except KeyError:self._reply(404,{'error':'Unknown job'})
        except (ValueError,TypeError,json.JSONDecodeError) as error:self._reply(400,{'error':str(error)})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception:self._reply(500,{'error':'Desktop remote operation failed'})
    def do_GET(self):self._serve()
    def do_POST(self):self._serve()
    def do_PUT(self):self._serve()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bind',default='127.0.0.1');parser.add_argument('--port',type=int,default=8765);parser.add_argument('--jobs',type=Path,default=ROOT/'outputs/phone-jobs');args=parser.parse_args()
    jobs=RemoteJobs(args.jobs);server=RemoteServer((args.bind,args.port),jobs)
    print('Helix phone link at http://%s:%d' % server.server_address,flush=True);print('Pairing key: '+jobs.token,flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:jobs.close();server.server_close()
    return 0

if __name__=='__main__':raise SystemExit(main())
