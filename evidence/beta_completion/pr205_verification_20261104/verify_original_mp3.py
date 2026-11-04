from pathlib import Path
import os,subprocess,json,hashlib,time,shutil
root=Path(__file__).resolve().parents[4];candidate=root/'helix-sequencer';control=root/'recovery-control'
audio=candidate/'Helix Audiolights.mp3';out=root/'original-mp3-verification';out.mkdir(exist_ok=False)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(audio)=='8ced92ba179c931a2c7f29f834df1c8fd6a399d78074de0de030bc952bb5f0ec'
report={'schema':'helix.pr205.original_mp3_parity.v1','audio_sha256':sha(audio),'template_sha256':sha(candidate/'template.xsq'),'layout_sha256':sha(candidate/'xlights_rgbeffects.xml'),'baseline_commit':'05c1de55d2e4d747652452ade0d9752d370b55d9','candidate_implementation_commit':'37fb716cc9581cb1024760a23b53d65589496f02','runs':[],'limits':['Original byte-identical MP3, same fresh-process CLI/configuration. Latest recovery control contains intentional fixes added after the historical Oct31 baseline.','First control includes initial local stem computation; subsequent runs reuse those exact source-verified stems. Do not compare cold control speed with cache-hit speed.','Correctness proof; no controlled overall speedup or native acceptance claim.']}
for label,repo,cache in [('control',control,None),('candidate_off',candidate,None),('candidate_miss',candidate,out/'features'),('candidate_hit',candidate,out/'features')]:
 if label=='candidate_off':
  src=control/'RenderCache/stems'/audio.stem;dest=candidate/'RenderCache/stems'/audio.stem
  assert json.loads((src/'helix-local-stems.json').read_text())['source_sha256']==sha(audio)
  shutil.copytree(src,dest,dirs_exist_ok=True)
 folder=out/label;folder.mkdir()
 env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',NUMBA_NUM_THREADS='2',NUMBA_CACHE_DIR=str(root/'numba-verify'),PYTHONHASHSEED='0',HELIX_PROFILE_OUTPUT=str(folder/'stages.json'))
 env.pop('HELIX_AUDIO_CACHE_DIR',None)
 if cache:env['HELIX_AUDIO_CACHE_DIR']=str(cache)
 args=[str(root/'helix-venv/bin/python'),str(repo/'main.py'),'--profile','master','--','--audio',str(audio),'--template',str(candidate/'template.xsq'),'--layout-file',str(candidate/'xlights_rgbeffects.xml'),'--output-dir',str(folder/'sequences'),'--settings',str(folder/'absent-settings.json'),'--no-prompt','--no-save-settings','--no-workspace-history','--no-learning-memory']
 start=time.perf_counter()
 with (folder/'cli.log').open('w') as log:r=subprocess.run(args,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 row={'mode':label,'returncode':r.returncode,'cli_wall_seconds':time.perf_counter()-start,'command':args}
 if r.returncode==0:
  xsq=folder/'sequences/Helix Audiolights,v27.3.xsq'
  row.update(xsq_sha256=sha(xsq),band_sha256=sha(xsq.with_suffix('.snowman_band.json')))
  if (folder/'stages.json').exists():row['metrics']=json.loads((folder/'stages.json').read_text())
 report['runs'].append(row);(out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in row.items() if k not in ['metrics','command']}),flush=True)
 assert r.returncode==0,label
assert len({r['xsq_sha256'] for r in report['runs']})==1,'XSQ drift'
assert len({r['band_sha256'] for r in report['runs']})==1,'Band drift'
report['exact_xsq_and_band_parity']=True
(out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
