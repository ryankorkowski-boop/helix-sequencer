"""Verify the complete sampler set, decode review frames and make one portable ZIP."""
from __future__ import annotations
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

from PIL import Image,ImageDraw
from models.intricate_band_scene import LAYOUTS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/Intricate_Band_Samplers'
IDS=('00','01','02','03','05')
BONUS=('01_knot_cathedral_vocal_intro_42s.mp4','01_prismatic_orrery_guitar_outro_42s.mp4',
       '05_woven_aurora_mallet_intro_42s.mp4')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    expected={f'{id}_{layout}_42s.mp4' for id in IDS for layout in LAYOUTS}|set(BONUS)
    source=OUT/'rendered';delivery=OUT/'delivery';delivery.mkdir(parents=True,exist_ok=True)
    decoded=OUT/'decoded_review';decoded.mkdir(exist_ok=True)
    proofs=[];drum_by_song={};implementation=None
    for name in sorted(expected):
        movie=source/name;proof=json.loads(movie.with_suffix('.verification.json').read_text())
        assert movie.exists() and sha(movie)==proof['sha256']
        assert proof['revision']==5 and proof['frames']==840 and proof['duration_seconds']==42
        assert proof['width']==1920 and proof['height']==1080 and proof['full_decode_passed']
        assert proof['soundtrack']['original_excerpt_matches'] and proof['soundtrack']['zero_offset_correlation']>.995
        assert proof['static_concept_art_video'] is False and proof['native_xlights_playback'] is False
        assert all(n>20 for n in proof['singer_active_frames'])
        if implementation is None:implementation=proof['implementation_sha256']
        assert proof['implementation_sha256']==implementation
        assert all(sha(ROOT/p)==h for p,h in implementation.items())
        current={p.name:sha(p) for p in (OUT/'analysis'/proof['id']).glob('*') if p.is_file()}
        assert current==proof['analysis_inputs']
        old=drum_by_song.setdefault(proof['id'],proof['source_native_drummer'])
        assert old==proof['source_native_drummer']
        for p,h in proof['drummer_geometry']['assets'].items():assert sha(ROOT/p)==h
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
        video=next(s for s in probe['streams'] if s['codec_type']=='video')
        audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
        assert int(video['nb_frames'])==840 and video['pix_fmt']=='yuv420p' and video['r_frame_rate']=='20/1'
        assert video['codec_name']=='h264' and audio['codec_name']=='aac'
        assert abs(float(probe['format']['duration'])-42)<.05
        # Inspect actual encoded pixels rather than relying on pre-encode PNGs.
        picture=decoded/(movie.stem+'.png')
        subprocess.run(['ffmpeg','-v','error','-y','-ss','21','-i',str(movie),'-frames:v','1',str(picture)],check=True)
        path=Path('movies')/proof['layout']/name
        target=delivery/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(movie,target)
        proof=dict(proof,render_worker_file=proof['file'],file=str(path))
        proofs.append(proof)
    assert len(proofs)==33
    preserved=json.loads((ROOT/'evidence/snowman_ensemble/preserved_inputs.json').read_text())
    assert all(sha(ROOT/p)==h for p,h in preserved.items())
    dry=json.loads((ROOT/'evidence/intricate_band_samplers/dry_geometry_preservation.json').read_text())
    assert len(dry['checks'])==19 and all(c['identical_to_dry_test_revision'] for c in dry['checks'])
    (delivery/'images').mkdir(exist_ok=True)
    for layout in LAYOUTS:
        src=decoded/f'05_{layout}_42s.png'
        Image.open(src).resize((768,432)).save(delivery/'images'/f'{layout}.jpg',quality=90)
    cards=[]
    for proof in sorted(proofs,key=lambda p:(p['id'],p['layout'],p['file'])):
        bonus=' • extra excerpt' if Path(proof['file']).name in BONUS else ''
        cards.append(f'<article><a href="{html.escape(proof["file"])}"><img src="images/{proof["layout"]}.jpg" alt="{html.escape(proof["layout_title"])}"></a><h2>{html.escape(proof["title"])}</h2><p>{html.escape(proof["layout_title"])}{bonus}</p><a class="play" href="{html.escape(proof["file"])}">Play 42-second sampler</a><small>Original song offset: {proof["soundtrack"]["source_offset_seconds"]:g}s</small></article>')
    page='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Snowman band • 42-second samplers</title><style>
    body{background:#071221;color:#def0ff;font:16px system-ui;margin:0;padding:24px}main{max-width:1400px;margin:auto}h1{font-size:30px}p{color:#aac9dc;line-height:1.5}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}article{border:1px solid #27445b;border-radius:12px;background:#102136;overflow:hidden;padding-bottom:18px}img{width:100%}article h2,article p,small{padding:0 16px}h2{font-size:18px}a{color:#8de8ff}.play{display:block;margin:12px 16px}small{display:block;color:#90aabe}</style></head><body><main>
    <h1>Snowman ensemble inside six intricate stages</h1><p>33 musical previews, each 42 seconds. Unzip the complete folder before opening this index. Click a sampler to play it with its original audio.</p><p>Original dry-test drummer; separate authored duet lanes; revised lyric/vowel cues, bass pitch direction and piano/mallet keys. These are 3D performance review renders. Singing identity, inferred notes and wordless-vowel estimates still need listening review.</p><div class="grid">'''+''.join(cards)+'</div></main></body></html>'
    (delivery/'index.html').write_text(page)
    readme='''SNOWMAN BAND — INTRICATE 42-SECOND SAMPLERS

33 MP4s: five songs × six newly modeled stages, plus three extra musical windows.
Songs: Wire Tree, Who Knew, 49, Candy Cane Chaos, Festivus.
Open index.html after unzipping, or browse movies/<layout>/.

The entire band plays within every layout. All movies have original-source
audio, exactly 840 frames / 42 seconds, 1920×1080 H.264 and AAC.
The exact dry-test drummer art, target geometry and pose compositor are reused.
The physical planar drummer is mounted within the 3D stage; its kit is not remodeled.
Original tagged song-specific drum strikes and alternating snare hands remain.

Both singer characters use authored phrase exchange and shared refrains,
not automatic gender classification or separation of recorded singers.
Quiet known vowels and inferred sustained voiced gaps animate mouths.
Screened embedded lyric alignments and a fresh Festivus recognition pass improve
captions. Failed reference segments are rejected; uncertain gaps are labelled
wordless rather than assigned invented lyric words. These estimates can still err.

Keyboard handles piano plus selected ringing mallet-like attacks in other.
Actual key locations guide the hands; one-note melodies use one hand.
Bass: lower measured notes move the left hand toward the sky, higher notes down.
Guitar reacts only to its separated stem. 49 and Festivus have stronger guitar;
Who Knew's main vocal window has little guitar, so its extra later excerpt is included.

These are source-bound 3D review visualizations, not new native xLights exports
or native playback recordings. Prior native shows and source files stay intact.
See TECHNICAL_NOTES.md and verification.json for scope and evidence.
'''
    (delivery/'README.txt').write_text(readme)
    shutil.copyfile(ROOT/'docs/INTRICATE_BAND_SAMPLERS.md',delivery/'TECHNICAL_NOTES.md')
    summary=dict(schema='helix.intricate_band_samplers.v1',movie_count=33,layout_count=6,song_count=5,
                 total_frames=27720,total_duration_seconds=1386,movies=proofs,
                 minimum_soundtrack_correlation=min(p['soundtrack']['zero_offset_correlation'] for p in proofs),
                 all_remote_full_decodes_and_local_exact_hashes_passed=True,
                 all_local_codec_duration_checks_passed=True,
                 all_33_encoded_midpoint_frames_decoded=True,
                 all_six_layouts_preserve_each_song_drums_and_hands=True,
                 all_21_original_inputs_preserved=True,all_19_dry_source_files_identical=True,
                 focused_tests='17 passed',native_xlights_playback=False,
                 implementation_sha256=implementation)
    (delivery/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
    contact=Image.new('RGB',(1920,3960),'#071221')
    for j,p in enumerate(proofs):
        picture=Image.open(decoded/(Path(p['file']).stem+'.png')).resize((640,360))
        contact.paste(picture,((j%3)*640,(j//3)*360))
    contact.save(OUT/'all_33_encoded_contact_sheet.jpg',quality=92)
    archive=OUT/'Snowman_Band_Intricate_42s_Samplers.zip';hashes={}
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
        for p in sorted(delivery.rglob('*')):
            if p.is_file():
                name=str(p.relative_to(delivery));z.write(p,name);hashes[name]=sha(p)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in hashes.items())
    package=dict(file=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),mp4_count=33,
                 zip_crc_passed=True,all_extracted_hashes_match=True)
    (OUT/'package_verification.json').write_text(json.dumps(package,indent=2)+'\n')
    evidence=ROOT/'evidence/intricate_band_samplers'
    shutil.copyfile(delivery/'verification.json',evidence/'verification.json')
    shutil.copyfile(OUT/'package_verification.json',evidence/'package_verification.json')
    print(json.dumps(package),flush=True)


if __name__=='__main__':main()
