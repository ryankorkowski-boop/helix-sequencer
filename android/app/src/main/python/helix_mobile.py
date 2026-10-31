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
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

# Set before librosa/joblib or a numerical backend is imported. Android has no
# POSIX sem_open; serial joblib executes the same HPSS/analysis kernels.
os.environ['JOBLIB_MULTIPROCESSING'] = '0'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'


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
    from core.gui_options import palette_key, resolve_layout
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
    if request.get('quick_clip', False):
        args.append('--helix-quick-clip')
    if mode == 'xlights' and not (job/'input/xlights_rgbeffects.xml').is_file() and request.get('sample_layout', 'custom') != 'custom':
        args[args.index('--layout-file') + 1] = str(resolve_layout(engine, request['sample_layout']))
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
            if not request.get('pitched_props',True):
                args += ['--helix-no-pitched-props']
            selected_palette = palette_key(request.get('palette', 'default'))
            if selected_palette != 'default':
                args += ['--palette-mode', selected_palette]
            args += ['--matrix-intelligence' if request.get('matrix', True) else '--no-matrix-intelligence']
            args += ['--birdsong' if request.get('birdsong', True) else '--no-birdsong']
            if request.get('birdsong', True):
                args += ['--birdsong-auto', '--birdsong-profile', 'canopy', '--birdsong-intensity', '1.20', '--birdsong-min-confidence', '0.45']
            if request.get('spatial', True):
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


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as src:
        for block in iter(lambda: src.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def notify(callback, method, *args):
    # Older host fixtures may implement only the media callbacks.
    target = getattr(callback, method, None)
    if target is not None:
        target(*args)


def write_report(job, manifest):
    output = job/'outputs'
    output.mkdir(exist_ok=True)
    temporary = output/'android-run.json.tmp'
    temporary.write_text(json.dumps(manifest, indent=2))
    temporary.replace(output/'android-run.json')
    lines = ['Helix Android run', 'Mode: ' + manifest['mode']]
    for name, state in manifest['stages'].items():
        lines.append(name + ': ' + state['status'] + (' — ' + state['error'] if state.get('error') else ''))
    lines += ['Sequences: ' + ', '.join(manifest.get('sequences', [])),
              'LMS: ' + ', '.join(manifest.get('lms', []))]
    (output/'Android-run-report.txt').write_text('\n'.join(lines) + '\n')


def package_show(job):
    bundle, temporary = job/'Helix-show.zip', job/'Helix-show.zip.tmp'
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted((job/'outputs').rglob('*')):
                if (path.is_file() and '.helix_lor_workspace' not in path.parts
                        and not path.name.endswith(('.tmp', '.pending.mp4', '.alignment.wav',
                                                    '.video.mp4', '.audio.m4a'))):
                    archive.write(path, path.relative_to(job/'outputs'))
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise RuntimeError('Show ZIP integrity check failed')
        temporary.replace(bundle)
        return bundle
    finally:
        temporary.unlink(missing_ok=True)


def render_preview(xsq, layout, wav, seconds, callback):
    from tools import preview_renderer as p
    seq = preview_sequence(p.parse_sequence(xsq), seconds)
    geom = p.parse_models(layout)
    # Crop the frame timeline BEFORE allocating RGB/intensity matrices on a phone.
    fps, width, height = 15, 640, 360
    leaves, intensities = p.build_leaf_intensity_matrix(geom, seq, fps)
    colors = p.build_leaf_color_matrix(geom, seq, fps, leaves, intensities.shape[1])
    renderer = p.HouseRenderer(geom, width=width, height=height)
    final_output = xsq.with_suffix('.mp4')
    output = xsq.with_suffix('.pending.mp4')
    callback.beginPreview(str(output), str(wav), width, height, fps)
    try:
        for i in range(intensities.shape[1]):
            image = renderer.render_frame(leaf_names=leaves, frame_values=intensities[:, i],
                title=xsq.name, t_ms=round(i*1000/fps), duration_ms=seq.duration_ms,
                overlays={}, frame_colors=colors[:, i, :])
            from core.output_provenance import brand_frame
            image = brand_frame(image)
            buffer = io.BytesIO()
            image.convert('RGB').save(buffer, format='PNG')
            callback.previewFrame(buffer.getvalue(), i*1_000_000//fps)
            if i % fps == 0:
                notify(callback, 'previewProgress', i, intensities.shape[1])
                notify(callback, 'stage', 'preview',
                       'Rendering preview: %d/%d seconds' % (i//fps, round(intensities.shape[1]/fps)))
        callback.endPreview()
    except BaseException:
        callback.abortPreview()
        output.unlink(missing_ok=True)
        raise
    from helix_mp4 import synchronize
    decoded = output.with_suffix('.alignment.wav')
    try:
        callback.decodePreviewAudio(str(output), str(decoded))
        alignment = synchronize(output, wav, decoded, intensities.shape[1]/fps)
        from core.output_provenance import stamp_mp4
        stamp_mp4(output)
        output.replace(final_output)
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    finally:
        decoded.unlink(missing_ok=True)
    final_output.with_suffix('.preview_provenance.json').write_text(json.dumps({
        'schema': 'helix.preview_provenance.v1', 'native_xlights': False,
        'source': 'Helix simulated effect-level model preview; Android MediaCodec H.264/AAC',
        'duration_seconds': intensities.shape[1]/fps, 'fps': fps, 'audio_alignment': alignment,
        'generator': 'Helix', 'credit': 'Made with Helix | Audio in. Lights out.',
        'visible_watermark': True,
    }, indent=2))
    return final_output


def run(engine_path, job_path, request_json, callback):
    engine, job = Path(engine_path), Path(job_path)
    request = json.loads(request_json)
    seconds = int(request.get('preview_seconds', 30))
    if request.get('quick_clip', False):
        seconds = 10
    if not 1 <= seconds <= 600:
        raise ValueError('Android preview length must be 1–600 seconds')
    if str(engine) not in sys.path:
        sys.path.insert(0, str(engine))
    os.environ['NUMBA_DISABLE_JIT'] = '1'
    import helix_numba
    helix_numba.install()
    stream = LogStream(callback)
    old_cwd = Path.cwd()
    stages = {'sequencing': {'status': 'running'}, 'packaging': {'status': 'pending'},
              'preview': {'status': 'pending' if request.get('preview', True) else 'skipped'}}
    manifest = {'schema': 'helix.android.run.v2', 'processing': 'on-device',
        'mode': request.get('mode', 'xlights'), 'stages': stages,
        'band_enabled': bool(request.get('band_enabled', True)),
        'sequences': [], 'lms': [], 'previews': [],
        'limitations': ['No neural stem separation/Whisper', 'Simulated preview, not native xLights playback',
                        'Serial joblib and Python Numba kernels; large songs may run slowly'],
        'input_hashes': {x.name: file_hash(x) for x in (job/'input').iterdir() if x.is_file()}}
    result = {'bundle': '', 'preview': '', 'sequence': '', 'report': str(job/'outputs/Android-run-report.txt'),
              'manifest': str(job/'outputs/android-run.json'), 'sequence_count': 0, 'mode': manifest['mode'],
              'stages': stages}
    try:
        if manifest['mode'] == 'xlights':
            for name in ('template.xsq', 'xlights_rgbeffects.xml'):
                dest = job/'input'/name
                if not dest.exists():
                    if name == 'xlights_rgbeffects.xml' and request.get('sample_layout', 'custom') != 'custom':
                        from core.gui_options import resolve_layout
                        shutil.copy2(resolve_layout(engine, request['sample_layout']), dest)
                    else:
                        shutil.copy2(engine/name, dest)
                manifest['input_hashes'][name] = file_hash(dest)
            from core.band_visibility import apply as apply_band_visibility
            manifest['band_visibility'] = apply_band_visibility(
                job/'input/xlights_rgbeffects.xml', job/'input/template.xsq',
                enabled=request.get('band_enabled', True))
            manifest['effective_input_hashes'] = {
                name: file_hash(job/'input'/name) for name in ('template.xsq', 'xlights_rgbeffects.xml')}
        os.chdir(job)
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            from core import sequence_builder
            callback.log('Running the existing Helix master sequencer entirely on this device.')
            callback.log('Serial analysis avoids Android sem_open. HPSS remains active; neural stems and Whisper require desktop.')
            notify(callback, 'stage', 'sequencing', 'Analyzing music and generating sequence…')
            args = build_args(request, job, engine)
            sequence_builder.run_profile('master', args)
            xsqs = sorted((job/'outputs').rglob('*.xsq'))
            from tools.preview_renderer import parse_sequence
            valid = [x for x in xsqs if any(parse_sequence(x).model_effects.values())
                     and '.helix_lor_workspace' not in x.parts]
            if not valid:
                raise RuntimeError('Helix produced no nonempty sequence; inspect the run log')
            lms_files = [x for x in (job/'outputs').rglob('*.lms')
                         if x.name != 'helix_lor_source_layout.lms' and '.helix_lor_workspace' not in x.parts]
            if manifest['mode'] == 'lor' and not lms_files:
                raise RuntimeError('LOR export did not produce an LMS')
            selected = next((x for x in valid if '.runtime_' not in x.name), valid[0])
            result['sequence'] = str(selected.with_suffix('.lms') if manifest['mode'] == 'lor' else selected)
            if not Path(result['sequence']).is_file():
                raise RuntimeError('Selected sequence export is missing')
            result['sequence_count'] = len(valid)
            stages['sequencing'] = {'status': 'success'}
            manifest['sequences'] = [str(x.relative_to(job)) for x in valid]
            manifest['lms'] = [str(x.relative_to(job)) for x in lms_files]
            from core.output_provenance import stamp_xml,write_manifest,notice
            for sequence_file in valid+lms_files:stamp_xml(sequence_file)
            manifest['provenance']=notice()
            write_manifest(job/'outputs',valid+lms_files)
            # Checkpoint completed sequence and portable ZIP BEFORE optional rendering.
            def package():
                notify(callback, 'stage', 'packaging', 'Packaging completed sequence, layout and soundtrack…')
                stages['packaging'] = {'status': 'success'}
                write_report(job, manifest)
                try:
                    result['bundle'] = str(package_show(job))
                except Exception as exc:
                    stages['packaging'] = {'status': 'failed', 'error': str(exc)}
                    callback.log('Show ZIP failed; sequence can still be saved: ' + str(exc))
                    write_report(job, manifest)
                notify(callback, 'checkpoint', json.dumps(result))
            package()
            if request.get('preview', True):
                notify(callback, 'stage', 'preview', 'Encoding preview with the actual soundtrack…')
                stages['preview'] = {'status': 'running'}
                write_report(job, manifest)
                layout = selected.parent/'xlights_rgbeffects.xml'
                if not layout.is_file():
                    layout = next((job/'outputs').rglob('xlights_rgbeffects.xml'), None)
                try:
                    if layout is None:
                        raise RuntimeError('Generated sequence is missing its packaged preview layout')
                    preview = render_preview(selected, layout, job/'input/audio.wav', seconds, callback)
                    result['preview'] = str(preview)
                    manifest['previews'] = [str(preview.relative_to(job))]
                    stages['preview'] = {'status': 'success'}
                except Exception as exc:
                    stages['preview'] = {'status': 'failed', 'error': str(exc)}
                    callback.log('Sequence succeeded. Optional MP4 preview failed: ' + str(exc))
                    # Keep the original stack in the local log; never advertise a failed movie.
                    callback.log(traceback.format_exc())
                package()
            write_report(job, manifest)
            return json.dumps(result)
    except BaseException as exc:
        if stages['sequencing']['status'] != 'success':
            stages['sequencing'] = {'status': 'failed', 'error': str(exc)}
        write_report(job, manifest)
        raise
    finally:
        stream.flush()
        os.chdir(old_cwd)

