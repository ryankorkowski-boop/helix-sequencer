"""Apply the original faint Helix H and internal credit to existing review media."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
from core.output_provenance import stamp_mp4, sha256


def mark(path):
    path=Path(path)
    proof=path.with_suffix('.verification.json')
    data=json.loads(proof.read_text()) if proof.exists() else {}
    if data.get('visible_helix_watermark') and b'HELIX_PROVENANCE_V1\0' in path.read_bytes()[-4096:]:
        return path
    logo=Path(__file__).resolve().parents[1]/'helix_h_logo.png'
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(path)]))
    width=next(s['width'] for s in probe['streams'] if s['codec_type']=='video')
    temporary=path.with_name(path.stem+'.branding.mp4')
    subprocess.run(['ffmpeg','-y','-v','error','-threads','2','-i',str(path),'-i',str(logo),
        '-filter_complex_threads','1','-filter_complex',
        f'[1:v]scale={round(width*.027)}:-1,format=rgba,colorchannelmixer=aa=0.055[logo];[0:v][logo]overlay=W-w-8:H-h-8[v]',
        '-map','[v]','-map','0:a:0','-c:v','libx264','-preset','fast','-crf','18','-threads','2','-c:a','copy',
        '-metadata','comment=Made with Helix | Audio in. Lights out.','-movflags','+faststart',str(temporary)],check=True)
    stamp_mp4(temporary);temporary.replace(path)
    data.update(visible_helix_watermark=True,watermark_opacity=.055,internal_helix_credit=True,movie_sha256=sha256(path))
    proof.write_text(json.dumps(data,indent=2)+'\n')
    return path


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('movies',type=Path,nargs='+')
    for movie in p.parse_args().movies:print(mark(movie),flush=True)
