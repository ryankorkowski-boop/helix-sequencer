"""Stage verified movies and reconstructable archive parts in an artifact checkout."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/Intricate_Band_Samplers'
REPO='ryankorkowski-boop/helix-sequencer'
TAG='intricate-band-samplers-2026-10-10'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('media_checkout',type=Path);args=parser.parse_args()
    media=args.media_checkout.resolve()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=media,text=True).strip()
    assert branch.startswith('artifacts/intricate-band-samplers-')
    proof=json.loads((OUT/'delivery/verification.json').read_text())
    package=json.loads((OUT/'package_verification.json').read_text());archive=Path(package['file'])
    assert sha(archive)==package['sha256'] and proof['movie_count']==package['mp4_count']==33
    (media/'samplers').mkdir(exist_ok=True);(media/'sampler_thumbnails').mkdir(exist_ok=True)
    for row in proof['movies']:
        source=OUT/'delivery'/row['file'];assert sha(source)==row['sha256']
        shutil.copyfile(source,media/'samplers'/source.name)
    for p in (OUT/'delivery/images').glob('*.jpg'):shutil.copyfile(p,media/'sampler_thumbnails'/p.name)
    shutil.copyfile(OUT/'delivery/verification.json',media/'sampler_verification.json')
    shutil.copyfile(OUT/'package_verification.json',media/'sampler_package_verification.json')
    parts=[];folder=media/'archive_parts/Intricate_42s_Samplers';folder.mkdir(parents=True,exist_ok=True)
    with archive.open('rb') as f:
        number=0
        while data:=f.read(47*1024*1024):
            number+=1;part=folder/f'part-{number:04}.bin';part.write_bytes(data)
            parts.append(dict(file=str(part.relative_to(media)),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    transport={'archives':[dict(file=archive.name,bytes=package['bytes'],sha256=package['sha256'],parts=parts)]}
    (media/'archive_transport.json').write_text(json.dumps(transport,indent=2)+'\n')
    base='https://raw.githubusercontent.com/'+REPO+'/{MEDIA_COMMIT}'
    zip_url=f'https://github.com/{REPO}/releases/download/{TAG}/{archive.name}'
    lines=['# Snowman band inside intricate stages',
           '',f'[Download all 33 × 42-second MP4s in one ZIP]({zip_url})',
           '', 'Five songs across six new geometric stages, plus three focused vocal/instrument excerpts. '
               'The complete band appears inside every layout. Full-HD H.264/AAC with original-source audio.',
           '', 'The exact dry-test drummer is preserved. Both singer characters perform through authored duet casting. '
               'Revised lyric/vowel cues, mallet-aware keys and absolute-pitch bass hand placement are included. '
               'These are 3D review renders; singer identity and inferred notes remain estimates.',
           '', '| Stage | Who Knew | Festivus | Other songs |','| --- | --- | --- | --- |']
    from models.intricate_band_scene import LAYOUTS
    for layout,title in LAYOUTS.items():
        link=lambda id,label:f'[{label}]({base}/samplers/{id}_{layout}_42s.mp4)'
        lines.append('| '+title+' | '+link('01','Play')+' | '+link('05','Play')+' | '+
                     ' · '.join([link('00','Wire Tree'),link('02','49'),link('03','Candy Cane Chaos')])+' |')
    lines+=['','Extra excerpts:','']
    for name,label in [('01_knot_cathedral_vocal_intro_42s.mp4','Who Knew opening vocals'),
                       ('01_prismatic_orrery_guitar_outro_42s.mp4','Who Knew later guitar part'),
                       ('05_woven_aurora_mallet_intro_42s.mp4','Festivus early mallet part')]:
        lines.append(f'- [{label}]({base}/samplers/{name})')
    lines+=['','All 33 clips have 840 frames / 42 seconds. Every final movie fully decoded on the render worker; '
            'its exact downloaded hash, codec/duration and encoded review frame were checked again. '
            '17 focused tests pass. All 21 original inputs and 19 canonical dry-test source files match.',
            '',f'ZIP bytes: {package["bytes"]:,}. SHA256: `{package["sha256"]}`.',
            f'Minimum original/encoded excerpt correlation: {proof["minimum_soundtrack_correlation"]:.10f}.',
            '', 'The ZIP includes an offline browsing index, technical notes and verification. '
            'It contains fresh final samplers only. Earlier/silent/draft previews are excluded.',
            '', 'These movies are geometric performance visualizations, not new native xLights exports or native playback recordings.']
    (media/'RELEASE.template.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'staged_movies':33,'archive_parts':len(parts),'zip_bytes':package['bytes']}),flush=True)


if __name__=='__main__':main()
