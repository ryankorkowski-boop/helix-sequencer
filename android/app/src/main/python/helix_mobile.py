"""In-process bridge to the canonical sequencer; all paths are app-private."""
from __future__ import annotations
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import traceback
import zipfile
from dataclasses import replace
from pathlib import Path


class LogStream(io.TextIOBase):
    def __init__(self, callback):
        self.callback = callback
        self.pending = ''
    def write(self, value):
        self.pending += value
        while '\n' in self.pending:
            line, self.pending = self.pending.split('\n', 1)
            self.callback.log(line)
        return len(value)
    def flush(self):
        if self.pending:
            self.callback.log(self.pending)
            self.pending = ''


def build_args(request, job, engine):
    mode = request.get('mode', 'xlights')
    if mode not in {'xlights', 'lor'}:
        raise ValueError('Choose xLights or Light-O-Rama')
    variants = int(request.get('variants', 1))
    if not 1 <= variants <= 8:
        raise ValueError('Use 1–8 variants')
    args = ['--template', str(job/'input/template.xsq' if (job/'input/template.xsq').exists() else engine/'template.xsq'),
            '--audio', str(job/'input/audio.wav'), '--layout-file',
            str(job/'input/xlights_rgbeffects.xml' if (job/'input/xlights_rgbeffects.xml').exists() else engine/'xlights_rgbeffects.xml'),
            '--output-dir', str(job/'outputs'), '--variants', str(variants), '--no-prompt',
            '--no-save-settings', '--no-effects-orchestrator', '--no-workspace-history',
            '--no-learning-memory', '--auto-shortlist']
    args.append('--polish' if request.get('polish', True) else '--no-polish')
    if mode == 'lor':
        source = job/'input/source.lms'
        if not source.is_file():
            raise ValueError('Select an LMS containing your real LOR Unit/Circuit addresses')
        args += ['--helix-lor-source-lms', str(source), '--ac-lights-only', '--no-pixel-reactive',
                 '--no-matrix-intelligence', '--no-birdsong', '--no-birdsong-auto']
    else:
        if request.get('ac_compatible', False):
            args += ['--ac-lights-only', '--no-pixel-reactive', '--no-matrix-intelligence', '--no-birdsong', '--no-birdsong-auto']
        else:
            if request.get('palette', 'default') == 'neon':
                args += ['--palette-mode', 'neon']
            args += ['--matrix-intelligence' if request.get('matrix', True) else '--no-matrix-intelligence']
            args += ['--birdsong' if request.get('birdsong', True) else '--no-birdsong']
            if request.get('birdsong', True):
                args += ['--birdsong-auto', '--birdsong-profile', 'canopy', '--birdsong-intensity', '1.20', '--birdsong-min-confidence', '0.45']
            if request.get('spatial', False):
                args += ['--helix-spatial-accent']
        if (job/'input/routing.json').is_file():
            args += ['--model-overrides-file', str(job/'input/routing.json')]
    return args


def preview_sequence(sequence, seconds):
    end = min(sequence.duration_ms, int(seconds*1000))
    # Retain original end times so a fade spanning the cutoff is not sped up.
    # Late effects must be excluded before the existing matrix builder allocates.
    return replace(sequence, duration_ms=end, model_effects={
        name: [e for e in effects if e.start_ms < end and e.end_ms > 0]
        for name, effects in sequence.model_effects.items()
    })


def render_preview(xsq, layout, wav, seconds, callback):
    from tools import preview_renderer as p
    seq = preview_sequence(p.parse_sequence(xsq), seconds)
    geom = p.parse_models(layout)
    # Crop the frame timeline BEFORE allocating RGB/intensity matrices on a phone.
    fps, width, height = 15, 640, 360
    leaves, intensities = p.build_leaf_intensity_matrix(geom, seq, fps)
    colors = p.build_leaf_color_matrix(geom, seq, fps, leaves, intensities.shape[1])
    renderer = p.HouseRenderer(geom, width=width, height=height)
    output = xsq.with_suffix('.mp4')
    callback.beginPreview(str(output), str(wav), width, height, fps)
    try:
        for i in range(intensities.shape[1]):
            image = renderer.render_frame(leaf_names=leaves, frame_values=intensities[:, i],
                title=xsq.name, t_ms=round(i*1000/fps), duration_ms=seq.duration_ms,
                overlays={}, frame_colors=colors[:, i, :])
            buffer = io.BytesIO()
            image.convert('RGB').save(buffer, format='PNG')
            callback.previewFrame(buffer.getvalue(), i*1_000_000//fps)
        callback.endPreview()
    except BaseException:
        callback.abortPreview()
        raise
    from helix_mp4 import synchronize
    decoded = output.with_suffix('.alignment.wav')
    try:
        callback.decodePreviewAudio(str(output), str(decoded))
        alignment = synchronize(output, wav, decoded, intensities.shape[1]/fps)
    finally:
        decoded.unlink(missing_ok=True)
    output.with_suffix('.preview_provenance.json').write_text(json.dumps({
        'schema': 'helix.preview_provenance.v1', 'native_xlights': False,
        'source': 'Helix simulated effect-level model preview; Android MediaCodec H.264/AAC',
        'duration_seconds': intensities.shape[1]/fps, 'fps': fps, 'audio_alignment': alignment,
    }, indent=2))
    return output


def run(engine_path, job_path, request_json, callback):
    engine, job = Path(engine_path), Path(job_path)
    request = json.loads(request_json)
    seconds = int(request.get('preview_seconds', 30))
    if not 1 <= seconds <= 120:
        raise ValueError('Android preview length must be 1–120 seconds')
    if str(engine) not in sys.path:
        sys.path.insert(0, str(engine))
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['NUMBA_DISABLE_JIT'] = '1'
    import helix_numba
    helix_numba.install()
    stream = LogStream(callback)
    old_cwd = Path.cwd()
    try:
        if request.get('mode', 'xlights') == 'xlights':
            for name in ('template.xsq', 'xlights_rgbeffects.xml'):
                dest = job/'input'/name
                if not dest.exists():
                    shutil.copy2(engine/name, dest)
        os.chdir(job)
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            from core import sequence_builder
            callback.log('Running the existing Helix master sequencer entirely on this device.')
            callback.log('Desktop neural stem/Whisper tools are unavailable. Existing HPSS analysis remains active.')
            args = build_args(request, job, engine)
            sequence_builder.run_profile('master', args)
            xsqs = sorted((job/'outputs').rglob('*.xsq'))
            # Never declare success on a swallowed engine failure or empty output.
            from tools.preview_renderer import parse_sequence
            valid = [x for x in xsqs if any(parse_sequence(x).model_effects.values()) and '.helix_lor_workspace' not in x.parts]
            if not valid:
                raise RuntimeError('Helix produced no nonempty sequence; inspect the run log')
            lms_files = list((job/'outputs').rglob('*.lms'))
            if request.get('mode') == 'lor' and not lms_files:
                raise RuntimeError('LOR export did not produce an LMS')
            previews = []
            # Render the shortlisted canonical sequence only, retaining all variants.
            selected = next((x for x in valid if '.runtime_' not in x.name), valid[0])
            layout = selected.parent/'xlights_rgbeffects.xml'
            if not layout.is_file():
                layout = next((job/'outputs').rglob('xlights_rgbeffects.xml'), None)
            if request.get('preview', True):
                if layout is None:
                    raise RuntimeError('Generated sequence is missing its packaged layout')
                callback.log('Encoding simulated preview with the actual soundtrack on this phone…')
                previews.append(str(render_preview(selected, layout, job/'input/audio.wav', seconds, callback)))
            manifest = {'schema': 'helix.android.run.v1', 'processing': 'on-device',
                'mode': request.get('mode', 'xlights'), 'sequences': [str(x.relative_to(job)) for x in valid],
                'lms': [str(x.relative_to(job)) for x in lms_files], 'previews': previews,
                'limitations': ['No neural stem separation/Whisper', 'Simulated preview, not native xLights playback',
                                'Android Numba kernels use Python execution; large songs may run slowly'],
                'input_hashes': {x.name: hashlib.sha256(x.read_bytes()).hexdigest() for x in (job/'input').iterdir() if x.is_file()}}
            (job/'outputs/android-run.json').write_text(json.dumps(manifest, indent=2))
            bundle = job/'Helix-show.zip'
            with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as z:
                for path in sorted((job/'outputs').rglob('*')):
                    if path.is_file() and '.helix_lor_workspace' not in path.parts:
                        z.write(path, path.relative_to(job/'outputs'))
            return json.dumps({'bundle': str(bundle), 'preview': previews[0] if previews else '',
                               'sequence_count': len(valid), 'mode': manifest['mode']})
    finally:
        stream.flush()
        os.chdir(old_cwd)
