import os,sys,socket,subprocess,time,json,hashlib
from pathlib import Path

root=Path(__file__).resolve().parent
deps=root/'native-deps';app=root/'runtime/squashfs-root'
os.environ.update(LD_LIBRARY_PATH=str(root/'runtime/compat')+':'+str(deps/'usr/lib/x86_64-linux-gnu'),
    PATH=str(deps/'usr/bin')+':'+os.environ['PATH'],
    XDG_DATA_DIRS=str(deps/'usr/share')+':'+str(app/'usr/share')+':/usr/local/share:/usr/share',
    LIBGL_ALWAYS_SOFTWARE='1',XL_NO_GPU_COMPUTE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
    HELIX_NATIVE_PREVIEW_WIDTH='1920',HELIX_NATIVE_PREVIEW_HEIGHT='1080',
    DISPLAY='127.0.0.1:241',XDG_CONFIG_HOME=str(root/'xconfig241'))
if not Path('/usr/bin/xkbcomp').exists():Path('/usr/bin/xkbcomp').symlink_to(deps/'usr/bin/xkbcomp')
xlog=(root/'xvfb241.log').open('w');wlog=(root/'openbox241.log').open('w')
xvfb=subprocess.Popen([str(deps/'usr/bin/Xvfb'),':241','-screen','0','1920x1080x24','-ac','-listen','tcp','-nolisten','local'],stdout=xlog,stderr=xlog)
wm=None
try:
    for i in range(40):
        try:
            with socket.create_connection(('127.0.0.1',6241),timeout=.2):break
        except OSError:time.sleep(.25)
    else:raise RuntimeError((root/'xvfb241.log').read_text())
    wm=subprocess.Popen([str(deps/'usr/bin/openbox'),'--sm-disable'],stdout=wlog,stderr=wlog)
    from tools.native_preview import preview_run
    for raw in sys.argv[1:]:
        show=Path(raw).resolve();manifest=json.loads((show/'run_manifest.json').read_text())
        sequence=manifest.get('sequence_file') or manifest.get('xsq') or next(show.glob('*.xsq')).name
        started=time.perf_counter();print('RENDERING',show,flush=True)
        report=preview_run(show,xsq=show/sequence,audio=next((show/'media').glob('*.wav')),xlights=str(app/'usr/bin/xLights'))
        elapsed=time.perf_counter()-started
        receipt=dict(show=str(show),elapsed_seconds=elapsed,report=report,renderer=json.loads((root/'runtime/phoneme-work/runtime/renderer.json').read_text()))
        (show/'optimization_native_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        if report.get('status')!='success':raise RuntimeError(report.get('warnings'))
        print('RENDERED',show.name,elapsed,flush=True)
finally:
    if wm:wm.terminate();wm.wait()
    xvfb.terminate();xvfb.wait()
