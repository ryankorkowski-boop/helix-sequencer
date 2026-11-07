"""Run an isolated remote job through the unchanged desktop master profile."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from tools.desktop_remote import ROOT, settings
from core.gui_options import resolve_layout


def build_args(request, job):
    request=settings(request);inputs=job/'input';output=job/'outputs'
    args=['--template',str(inputs/'template.xsq'),'--layout-file',str(inputs/'xlights_rgbeffects.xml'),
          '--audio',str(inputs/'audio.wav'),'--output-dir',str(output),'--variants',str(request['variants']),
          '--no-prompt','--no-save-settings','--no-workspace-history','--no-learning-memory','--auto-shortlist']
    args.append('--polish' if request.get('polish',True) else '--no-polish')
    if request.get('quick_clip',False):args+=['--helix-quick-clip']
    lor=request.get('mode')=='lor';ac=lor or request.get('ac_compatible',False)
    if lor:args+=['--helix-lor-source-lms',str(inputs/'source.lms')]
    if ac:args+=['--ac-lights-only','--no-pixel-reactive','--no-matrix-intelligence','--no-effects-orchestrator','--no-birdsong','--no-birdsong-auto']
    else:
        if request.get('palette','default')!='default':args+=['--palette-mode',request['palette']]
        args+=['--matrix-intelligence' if request.get('matrix',True) else '--no-matrix-intelligence', '--birdsong' if request.get('birdsong',True) else '--no-birdsong']
        if request.get('birdsong',True):args+=['--birdsong-auto','--birdsong-profile','canopy','--birdsong-intensity','1.2','--birdsong-min-confidence','.45']
        if request.get('spatial',False):args+=['--helix-spatial-accent']
    if not lor and (inputs/'routing.json').is_file():args+=['--model-overrides-file',str(inputs/'routing.json')]
    if request.get('preview',True):args+=['--helix-preview-mp4','--helix-preview-seconds',str(request['preview_seconds'])]
    return args


def run(job):
    request=settings(json.loads((job/'request.json').read_text()));inputs=job/'input';output=job/'outputs';output.mkdir(exist_ok=True)
    for name in ('template.xsq','xlights_rgbeffects.xml'):
        if not (inputs/name).is_file():
            source = resolve_layout(ROOT, request['sample_layout']) if name == 'xlights_rgbeffects.xml' and request.get('sample_layout','custom') != 'custom' else ROOT/name
            shutil.copy2(source,inputs/name)
    import imageio_ffmpeg
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-nostdin','-y','-i',str(inputs/'original-audio'),'-vn','-c:a','pcm_s16le',str(inputs/'audio.wav')],check=True)
    # The canonical packager finds controller XML beside the supplied layout.
    from core.sequence_builder import run_profile
    run_profile('master',build_args(request,job))
    from tools.preview_renderer import parse_sequence
    sequences=[p for p in output.rglob('*.xsq') if '.helix_lor_workspace' not in p.parts and any(parse_sequence(p).model_effects.values())]
    if not sequences:raise RuntimeError('Desktop Helix produced no nonempty sequence')
    if request.get('mode')=='lor' and not any(output.rglob('*.lms')):raise RuntimeError('Missing LOR export')
    movies=sorted(output.rglob('*.mp4'))
    if request.get('preview',True) and not movies:raise RuntimeError('Requested desktop preview was not produced')
    result={'schema':'helix.remote.job.v1','processing':'desktop','mode':request.get('mode','xlights'),
            'sequence_count':len(sequences),'preview':str(movies[0]) if movies else ''}
    (output/'remote-run.json').write_text(json.dumps(result,indent=2));(job/'result.json').write_text(json.dumps(result))
    with zipfile.ZipFile(job/'Helix-show.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(output.rglob('*')):
            if path.is_file() and '.helix_lor_workspace' not in path.parts:z.write(path,path.relative_to(output))
    print('Remote desktop show packaged successfully',flush=True)
    return result


def main():
    if len(sys.argv)!=2:raise ValueError('Specify a private desktop job directory')
    run(Path(sys.argv[1]).resolve());return 0

if __name__=='__main__':raise SystemExit(main())
