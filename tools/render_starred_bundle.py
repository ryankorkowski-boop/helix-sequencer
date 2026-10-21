"""Render generated Starred shows through native xLights House Preview.

Requires a running display and the xLights executable. Existing FSEQ is
inspected and source hashes are recorded; absent FSEQ is rendered first.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from tools import native_preview as native
from tools.quality.native import inspect_fseq
from tools.native_x11_canvas import prepare_canvas


def render(root, binary, *, float_preview=False, prefix=None):
    root, binary = root.resolve(), binary.resolve()
    videos = root/'videos'
    videos.mkdir(exist_ok=True)
    for show in sorted((root/'shows').iterdir()):
        if prefix and not show.name.startswith(prefix):
            continue
        destination = videos/(show.name+'.mp4')
        if destination.exists():
            raise FileExistsError(destination)
        xsq, fseq = show/'Performance.xsq', show/'Performance.fseq'
        stamp = show/'native_render_stamp.json'
        identity = dict(xsq_sha256=native._sha256(xsq),
                        layout_sha256=native._sha256(show/'xlights_rgbeffects.xml'))
        cached = json.loads(stamp.read_text()) if stamp.exists() else {}
        if (not fseq.exists() or any(cached.get(k)!=v for k,v in identity.items())
                or cached.get('fseq_sha256')!=native._sha256(fseq)):
            with (show/'native_render.log').open('w') as log:
                subprocess.run([str(binary), '--headless', '--quiet', '--show', str(show),
                    '--outputdir', str(show), str(xsq)], check=True, stdout=log, stderr=log, timeout=900)
            stamp.write_text(json.dumps({**identity, 'fseq_sha256':native._sha256(fseq)},indent=2)+'\n')
        channels = inspect_fseq(fseq, streaming=True)
        # Keep growing movies outside synchronized source trees. Publish only
        # a closed, decoded complete MP4 and retain its small native receipts.
        stage = Path(tempfile.mkdtemp(prefix='helix-native-'+show.name+'-'))
        staged = stage/xsq.name
        shutil.copy2(xsq, staged)
        shutil.copy2(fseq, stage/fseq.name)
        report = native._native_export(str(binary), show, staged, 49914,
            prepare_preview=prepare_canvas if float_preview else None)
        video = Path(report['native_video'])
        stream = native._stream(native.probe_media(video, 'ffprobe'), 'video')
        if (stream['width'], stream['height']) != native._export_size():
            raise ValueError('Native video resolution does not match requested dimensions')
        import xml.etree.ElementTree as ET
        duration = float(ET.parse(xsq).findtext('head/sequenceDuration'))
        audio = show/'media/audio.wav'
        complete=stage/'complete.mp4'
        report['media'] = native.mux_original_audio(video, audio, complete,
            duration=duration, ffmpeg='ffmpeg', ffprobe='ffprobe')
        temporary=videos/(show.name+'.complete.mp4')
        shutil.copy2(complete,temporary)
        if native._sha256(temporary)!=native._sha256(complete):
            raise ValueError('Completed native movie changed during publication')
        temporary.replace(destination)
        report.update(backend='xlights_house_preview', status='rendered_pending_visual_review',
            mp4_sha256=native._sha256(destination), audio_sha256=native._sha256(audio),
            xsq_sha256=native._sha256(xsq), layout_sha256=native._sha256(show/'xlights_rgbeffects.xml'),
            native_channels=channels, source_audio_offset_seconds=0)
        evidence=show/'native-export-evidence'
        evidence.mkdir(exist_ok=True)
        for item in stage.iterdir():
            if item.suffix in {'.json','.log','.txt'}:
                shutil.copy2(item,evidence/item.name)
        (show/'native_movie_proof.json').write_text(json.dumps(report, indent=2)+'\n')
        print('FINISHED_VIDEO', show.name, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--xlights', type=Path, required=True)
    p.add_argument('--float-house-preview', action='store_true')
    p.add_argument('--prefix')
    args = p.parse_args()
    render(args.root, args.xlights, float_preview=args.float_house_preview, prefix=args.prefix)
