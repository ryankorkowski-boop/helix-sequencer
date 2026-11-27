"""Exercise packaged CLI, legacy LOR mode and the eight-variant GUI review."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import xml.etree.ElementTree as ET


def verify_movies(movies, audio, ffmpeg):
    import numpy as np

    def pcm(path):
        return np.frombuffer(subprocess.check_output([
            ffmpeg, '-nostdin', '-v', 'error', '-i', str(path), '-map', '0:a:0',
            '-ac', '1', '-ar', '16000', '-f', 'f32le', '-',
        ]), dtype='<f4')

    original = pcm(audio)
    proof = []
    for movie in movies:
        subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-xerror', '-i', str(movie),
                        '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'], check=True)
        soundtrack = pcm(movie)
        count = min(len(soundtrack), len(original))
        correlation = float(np.corrcoef(original[:count], soundtrack[:count])[0, 1])
        if abs(len(original)-len(soundtrack)) > 2400 or not correlation >= .97:
            raise RuntimeError(f'{movie.name} soundtrack clock/identity failed: {correlation}')
        proof.append({'movie': movie.name, 'soundtrack_correlation': correlation,
                      'decoded_audio_seconds': len(soundtrack) / 16000})
    return proof


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); worker=a.worker.resolve(); out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    results=[]
    # The packaged smoke proves the EXE can sequence and export. It does not
    # download Demucs weights. A real desktop run still requires Demucs unless
    # HELIX_REQUIRE_NEURAL_STEMS=0 is set.
    smoke_env=os.environ.copy()
    smoke_env['HELIX_REQUIRE_NEURAL_STEMS']='0'
    def run(args,label):
        process=subprocess.run([str(worker),*map(str,args)],capture_output=True,text=True,timeout=600,env=smoke_env)
        (out/(label+'.log')).write_text(process.stdout+process.stderr,encoding='utf-8')
        if process.returncode:
            print((process.stdout+process.stderr)[-14000:],flush=True)
            raise RuntimeError(f'{label} failed: {process.returncode}; see {out}')
        results.append({'step':label,'returncode':0})
    # A tiny deterministic FSEQ checks the installed worker/codec, not musical quality.
    header=bytearray(28);header[:4]=b'PSEQ';struct.pack_into('<H',header,4,28);header[7]=1
    struct.pack_into('<II',header,10,6,4);header[18]=50
    (out/'probe.fseq').write_bytes(header+bytes([255,0,0,0,255,0])*4)
    (out/'pixels.csv').write_text('channel,x,y,kind\n1,0,0,rgb\n4,1,1,rgb\n')
    run(['--helix-fseq-preview',out/'probe.fseq','--pixel-map',out/'pixels.csv','--output',out/'native.mp4','--width','64','--height','64'],'native_fseq')
    assert json.loads((out/'native.pixel_preview.json').read_text())['frames']==4
    # Real repository audio runs the packaged sequencing engine in both modes.
    import imageio_ffmpeg
    candidates=sorted(root.glob('*.mp3'))
    assert candidates,'No real repository audio for portable smoke'
    source=next((f for f in candidates if 'Tinsel' in f.name),candidates[0])
    audio=out/'real_excerpt.wav'
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg,'-v','error','-y','-i',str(source),'-t','8',str(audio)],check=True)
    lms=out/'source.lms'
    lms.write_text('<sequence saveFileVersion="14"><channels>'
                   '<channel name="Roof red" deviceType="LOR" unit="1" circuit="1" color="255" savedIndex="0" centiseconds="800"/>'
                   '<channel name="Roof green" deviceType="LOR" unit="1" circuit="2" color="65280" savedIndex="1" centiseconds="800"/>'
                   '</channels><timingGrids/><tracks><track totalCentiseconds="800"><channels><channel savedIndex="0"/><channel savedIndex="1"/></channels></track></tracks></sequence>')
    digest=hashlib.sha256(lms.read_bytes()).hexdigest()
    common=['--helix-cli','--profile','master','--','--audio',audio,'--no-prompt',
            '--no-polish','--no-effects-orchestrator','--no-pixel-reactive','--no-matrix-intelligence']
    run([*common,'--variants','1','--helix-preview-mp4','--helix-preview-seconds','2',
         '--helix-lor-source-lms',lms,'--ac-lights-only','--output-dir',out/'lor'],'lor_engine')
    assert list((out/'lor').glob('*.lms')) and list((out/'lor').glob('*.mp4'))
    for file in (out/'lor').glob('*.lms'):
        if file.name=='helix_lor_source_layout.lms':continue
        channels=ET.parse(file).getroot().findall('./channels/channel')
        assert [(c.get('unit'),c.get('circuit')) for c in channels]==[('1','1'),('1','2')]
    assert hashlib.sha256(lms.read_bytes()).hexdigest()==digest
    show = out/'xlights'
    run([*common,'--variants','8','--helix-review-previews','--template',worker.parent/'template.xsq',
         '--layout-file',worker.parent/'xlights_rgbeffects.xml','--output-dir',show,
         '--palette-mode','neon'],'xlights_engine')
    movies = sorted(show.glob('*.mp4'))
    assert len(movies)==8 and all(p.with_suffix('.xsq').is_file() for p in movies)
    variants = verify_movies(movies, audio, ffmpeg)
    run(['--helix-gui-smoke', show], 'variant_gui_selection')
    (out/'verification.json').write_text(json.dumps({'steps':results,'real_audio_source':source.name,
        'source_lms_preserved':True,'legacy_lor_import_in_vendor_app_verified':False,
        'variant_movies':variants,'windows_external_player_verified':False,
        'stem_path':'diagnostic_hpss','demucs_executed':False},indent=2)+'\n')


if __name__=='__main__':main()
