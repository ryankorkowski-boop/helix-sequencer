"""Real HTTP -> canonical desktop engine -> XSQ/LMS/audio MP4 proof, synthetic only."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import threading
import time
import urllib.request
import numpy as np
import soundfile as sf
from tools.desktop_remote import RemoteJobs,RemoteServer


def run(output):
    output.mkdir(parents=True,exist_ok=True);rate=22050;t=np.arange(rate*8)/rate
    y=.15*np.sin(2*np.pi*220*t)+.07*np.sin(2*np.pi*440*t)
    for at in np.arange(.2,8,.5):
        i=int(at*rate);n=min(800,len(y)-i);y[i:i+n]+=.55*np.exp(-np.arange(n)/95)
    song=output/'synthetic.wav';sf.write(song,y,rate,subtype='PCM_16')
    jobs=RemoteJobs(output/'jobs');server=RemoteServer(('127.0.0.1',0),jobs);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
    def request(method,path,data=None,raw=False):
        body=data if raw else json.dumps(data).encode() if data is not None else None
        req=urllib.request.Request(base+path,data=body,method=method,headers={'Authorization':'Bearer '+jobs.token})
        with urllib.request.urlopen(req,timeout=30) as r:return r.read() if raw and method=='GET' else json.load(r)
    reports=[]
    try:
        for mode in ('xlights','lor'):
            identity=request('POST','/v1/jobs',{'mode':mode,'variants':1,'preview':True,'preview_seconds':3,'palette':'neon'})['id'];prefix='/v1/jobs/'+identity
            request('PUT',prefix+'/files/audio',song.read_bytes(),raw=True)
            if mode=='lor':
                lms=b'<sequence musicFilename="old.wav"><channels><channel name="Roof red" deviceType="LOR" unit="1" circuit="1" color="255" savedIndex="0" centiseconds="800"/><channel name="Roof green" deviceType="LOR" unit="1" circuit="2" color="65280" savedIndex="1" centiseconds="800"/></channels><tracks><track totalCentiseconds="800"><channels><channel savedIndex="0"/><channel savedIndex="1"/></channels></track></tracks></sequence>'
                request('PUT',prefix+'/files/lor',lms,raw=True)
            request('POST',prefix+'/start',{})
            deadline=time.monotonic()+300
            while time.monotonic()<deadline:
                state=request('GET',prefix)
                if state['phase']!='running':break
                time.sleep(.5)
            if state['phase']!='complete':raise RuntimeError(mode+': '+state['message']+'\n'+state.get('log','')[-5000:])
            bundle=output/(mode+'-show.zip');bundle.write_bytes(request('GET',prefix+'/bundle',raw=True))
            movie=output/(mode+'-preview.mp4');movie.write_bytes(request('GET',prefix+'/preview',raw=True))
            subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True)
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
            reports.append({'mode':mode,'phase':state['phase'],'uploaded':state['uploaded'],'full_movie_decode':True,'codecs':[s['codec_name'] for s in probe['streams']], 'duration':probe['format']['duration'],'bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'movie_sha256':hashlib.sha256(movie.read_bytes()).hexdigest()})
            print(json.dumps(reports[-1]),flush=True)
    finally:server.close();thread.join(timeout=3)
    (output/'verification.json').write_text(json.dumps(reports,indent=2)+'\n');return reports

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.output)
