from pathlib import Path
import os,sys,subprocess,json,hashlib,time,shutil,zipfile,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[4]
candidate=root/'helix-sequencer'; control=root/'recovery-control'
audio=root/'source-recovery/long-song/full-song.wav'
out=root/'long-song-verification';out.mkdir(exist_ok=True)
def sha(p): return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
with zipfile.ZipFile(root/'source-recovery/HELIX_INTERNAL_ANDROID_MEMORY_CHECKPOINT_20261029.zip') as z:
 manifest=json.loads(z.read('memory_checkpoint_manifest.json'))
 for item in manifest['files']:
  if item['path']=='full-song.wav' or item['path'].startswith('memory-profile/stems/'):
   actual=root/'source-recovery/long-song'/item['path']
   assert sha(actual)==item['sha256'],item['path']
for repo in [candidate,control]:
 dest=repo/'RenderCache/stems/full-song';dest.mkdir(parents=True,exist_ok=True)
 for role in ['vocals','drums','bass','other']:
  shutil.copy2(root/f'source-recovery/long-song/memory-profile/stems/full-song.{role}.wav',dest/f'full-song.{role}.wav')
 (dest/'helix-local-stems.json').write_text(json.dumps({'format':'helix-local-hpss-v1','source_sha256':sha(audio)}))
report={'schema':'helix.pr205.long_song_verification.v1','audio_sha256':sha(audio),'audio_checkpoint':'libfile_fcf68c0edd7481918e7892adbd8def38',
 'controls':{'template_sha256':sha(candidate/'template.xsq'),'layout_sha256':sha(candidate/'xlights_rgbeffects.xml'),'source_verified_stems_equal':True,'fresh_processes':True,'numerical_threads':2},
 'limits':['Recovered 237.44s PCM checkpoint is a different byte input from the old MP3 benchmark; do not compare its count/timing to 42305-effect receipt.','Concurrent full-suite execution makes these correctness runs unsuitable for an isolated speedup claim.','Native render and physical acceptance are separate.'], 'runs':[]}
for label,repo,cache in [('control',control,None),('candidate_off',candidate,None),('candidate_miss',candidate,out/'feature-cache'),('candidate_hit',candidate,out/'feature-cache')]:
 folder=out/label;folder.mkdir(exist_ok=False)
 env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',NUMBA_NUM_THREADS='2',PYTHONHASHSEED='0',NUMBA_CACHE_DIR=str(root/'numba-long-song'),HELIX_PROFILE_OUTPUT=str(folder/'stages.json'))
 env.pop('HELIX_AUDIO_CACHE_DIR',None)
 if cache:env['HELIX_AUDIO_CACHE_DIR']=str(cache)
 command=[str(root/'helix-venv/bin/python'),str(repo/'main.py'),'--profile','master','--','--audio',str(audio),'--template',str(candidate/'template.xsq'),'--layout-file',str(candidate/'xlights_rgbeffects.xml'),'--output-dir',str(folder/'sequences'),'--settings',str(folder/'absent-settings.json'),'--no-prompt','--no-save-settings','--no-workspace-history','--no-learning-memory']
 started=time.perf_counter()
 with (folder/'cli.log').open('w') as log:
  result=subprocess.run(command,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 entry={'label':label,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'source_tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=repo,text=True).strip(),'returncode':result.returncode,'cli_wall_seconds':time.perf_counter()-started}
 report['runs'].append(entry)
 if result.returncode==0:
  xsq=folder/'sequences/full-song,v27.3.xsq';band=xsq.with_suffix('.snowman_band.json')
  entry.update(xsq_sha256=sha(xsq),band_sha256=sha(band),effects=len(ET.parse(xsq).getroot().findall('./ElementEffects/Element[@type="model"]/EffectLayer/Effect')))
  if (folder/'stages.json').exists():entry['metrics']=json.loads((folder/'stages.json').read_text())
 (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(entry),flush=True)
 if result.returncode:raise RuntimeError(f'{label} failed; see {folder}/cli.log')
assert len({x['xsq_sha256'] for x in report['runs']})==1,'XSQ drift'
assert len({x['band_sha256'] for x in report['runs']})==1,'Band export drift'
report['exact_xsq_and_band_parity']=True
(out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
