"""Source-bound before/after offline production, using the Android kernels."""
import os
os.environ['JOBLIB_MULTIPROCESSING']='0'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import sys,subprocess,json,time,threading,resource,hashlib,shutil,traceback
from pathlib import Path
repo=Path(__file__).resolve().parents[1]
if len(sys.argv) != 3 or sys.argv[2] not in ('baseline','candidate'):
    raise SystemExit('Usage: python -m tools.profile_android_full_song_memory WORK baseline|candidate')
base=Path(sys.argv[1]).resolve()
mode=sys.argv[2]
output=base/'offline-memory'/mode
if output.exists():raise FileExistsError(output)
output.mkdir(parents=True)
sys.path[:0]=[str(repo),str(repo/'android/app/src/main/python')]
if mode=='baseline':
    old=base/'baseline-modules'
    for package in ('core','audio'):
        (old/package).mkdir(parents=True,exist_ok=True)
        (old/package/'__init__.py').write_text('__path__.append('+repr(str(repo/package))+')\n')
    for path in ('core/audio_intelligence.py','core/effect_engine.py','audio/drummer_v3.py'):
        (old/path).write_bytes(subprocess.check_output(['git','show','45f17d69fac91d7683984cc22c54bb701eb2226e:'+path],cwd=repo))
    sys.path.insert(0,str(old))
import helix_numba
helix_numba.install()
import helix_mobile
from core import effect_engine as engine,audio_intelligence as ai
from audio import drummer_v3
from tools.profile_real_sequence import musical_signature
active=True;stage='setup';peaks={};timings=[]
def rss():
    return int(next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('VmRSS:')))*1024
def sample():
    while active:
        peaks[stage]=max(peaks.get(stage,0),rss())
        time.sleep(.02)
def wrap(module,name):
    fn=getattr(module,name)
    def measured(*a,**kw):
        global stage
        old=stage;stage=name;started=time.monotonic()
        try:return fn(*a,**kw)
        finally:
            timings.append(dict(function=name,elapsed_seconds=time.monotonic()-started))
            stage=old
    setattr(module,name,measured)
for m,n in [(engine,'analyze_harmonic'),(ai,'build_stem_analysis'),(ai,'_classify_background_vocals'),(ai,'_summarize_stem_file'),(drummer_v3,'analyze_drummer_samples'),(engine,'derive_multiband_analysis')]:wrap(m,n)
job=output/'job';inp=job/'input';inp.mkdir(parents=True)
source=base/'full-song.wav';shutil.copy2(source,inp/'audio.wav')
stems=job/'RenderCache/stems/audio';stems.mkdir(parents=True)
for role in ('bass','drums','vocals','other'):shutil.copy2(base/('memory-profile/stems/full-song.'+role+'.wav'),stems/('audio.'+role+'.wav'))
(stems/'helix-local-stems.json').write_text(json.dumps(dict(format='helix-local-hpss-v1',source_sha256=helix_mobile.file_hash(source))))
log=(output/'production.log').open('w',buffering=1)
class Callback:
    def log(self,s):log.write(s+'\n')
    def stage(self,*args):log.write('STAGE '+repr(args)+'\n')
    def checkpoint(self,*args):pass
thread=threading.Thread(target=sample,daemon=True);thread.start()
started=time.monotonic();result=None
try:
    result=json.loads(helix_mobile.run(str(repo),str(job),json.dumps(dict(mode='xlights',preview=False,variants=1)),Callback()))
except BaseException:
    log.write(traceback.format_exc());raise
finally:
    active=False;thread.join();log.close()
    report=dict(mode=mode,elapsed_seconds=time.monotonic()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,stage_peaks=peaks,stages=timings,result=result,audio_sha256=helix_mobile.file_hash(source),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),preview=False)
    if result and result.get('sequence'):report['musical_signature'],report['model_effect_count']=musical_signature(result['sequence'])
    (output/'metrics.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('stage_peaks','stages','result')},indent=2),flush=True)
