"""Verify the explicitly requested movie batch and create its portable archive."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/Band_Instrument_Review'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(movie):
    q=json.loads(movie.with_suffix('.verification.json').read_text())
    assert movie.stat().st_size==q['bytes'] and sha(movie)==q['sha256']
    assert q['seconds']==42 and q['frames']==840 and q['width']==1920 and q['height']==1080
    assert q['all_frames_pose_routing_checked'] and q['full_decode_passed']
    assert q['soundtrack']['zero_offset_correlation']>.995
    assert all(c['muted_error']-c['active_error']>1 for c in q['encoded_instrument_checks'])
    focus={'bass':'bass','guitar':'guitar','keyboard':'piano'}.get(q['focus'])
    if focus:assert q['source_attacks'][focus]['visible_checks']>=1
    subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(movie),'-f','null','-'],check=True)
    p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(movie)]))
    video=next(s for s in p['streams'] if s['codec_type']=='video');audio=next(s for s in p['streams'] if s['codec_type']=='audio')
    assert int(video['nb_frames'])==840 and video['pix_fmt']=='yuv420p' and video['codec_name']=='h264' and audio['codec_name']=='aac'
    print('DELIVERY VERIFIED',movie.name,flush=True)
    return dict(file=movie.name,sha256=q['sha256'],bytes=q['bytes'],id=q['id'],title=q['title'],focus=q['focus'],layout=q['layout'],source_start_seconds=q['start'],encoded_checks=len(q['encoded_instrument_checks']),audio_correlation=q['soundtrack']['zero_offset_correlation'])


def expected_movies():
    jobs=json.loads((ROOT/'evidence/band_instrument_review/batch.json').read_text())
    return [OUT/'movies'/f'{j["id"]}_{j["layout"]}_{j["focus"]}{j.get("suffix","")}_42s.mp4' for j in jobs]


def main():
    p=argparse.ArgumentParser();p.add_argument('--media-commit');p.add_argument('--verify-only',action='store_true');args=p.parse_args()
    movies=expected_movies();assert len(movies)==21 and all(p.exists() for p in movies)
    with ThreadPoolExecutor(max_workers=2) as pool:manifest=list(pool.map(verify,movies))
    evidence=ROOT/'evidence/band_instrument_review';evidence.mkdir(exist_ok=True)
    (evidence/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if args.verify_only:return
    assert args.media_commit and len(args.media_commit)==40
    url='https://raw.githubusercontent.com/ryankorkowski-boop/helix-sequencer/'+args.media_commit+'/band_instrument_review/movies/'
    release='https://github.com/ryankorkowski-boop/helix-sequencer/releases/download/band-instrument-review-2026-10-10/Snowman_Band_Instrument_Review_42s.zip'
    text='# Snowman band: 21 new 42-second instrument studies\n\n'+f'[Download the entire ZIP]({release})\n\n'
    text+='Brighter independent string shimmer, source-timed picking, distinct playable guitar strings, pitch-directed bass hands, and piano/mallet keys. Latest outward torso shoulders retained. Each clip contains original audio.\n\n'
    text+='Full-stage and close-up views span Wire Tree, Who Knew, 49, Candy Cane Chaos and Festivus across six intricate stages. Who Knew includes its guitar outro; Festivus includes the mallet intro.\n\n'
    text+='All21 movies pass full decoding, original-audio checks and every-frame routing/pose checks. Encoded representative cues are tested against an instrument-muted version of the same scene. Pitches/stems are estimates; quiet instruments are not given fabricated notes. These are3D review movies, not new verified native xLights/controller exports.\n\n'
    for m in manifest:
        m['url']=url+m['file'];text+=f'- [{m["title"]} — {m["focus"]}, {m["layout"]}, {m["source_start_seconds"]:g}s start]({m["url"]})\n'
    (ROOT/'docs/BAND_INSTRUMENT_REVIEW_DOWNLOADS.md').write_text(text)
    archive=OUT/'Snowman_Band_Instrument_Review_42s.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
        for movie in movies:
            z.write(movie,'Movies/'+movie.name);z.write(movie.with_suffix('.verification.json'),'Verification/'+movie.with_suffix('.verification.json').name)
        z.writestr('README.md',text);z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
        z.write(ROOT/'docs/BAND_INSTRUMENT_REVIEW_HANDOFF.md','HANDOFF.md')
        z.write(evidence/'input_pose_audit.json','Verification/input_pose_audit.json')
        z.write(evidence/'focused_tests.json','Verification/focused_tests.json')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for m in manifest:assert hashlib.sha256(z.read('Movies/'+m['file'])).hexdigest()==m['sha256']
    report=dict(file=archive.name,bytes=archive.stat().st_size,sha256=sha(archive),movie_count=21,frames=21*840,
                encoded_checks=sum(m['encoded_checks'] for m in manifest),min_audio_correlation=min(m['audio_correlation'] for m in manifest),zip_crc_passed=True,all_extracted_movie_hashes_match=True,media_commit=args.media_commit,public_zip_url=release,movies=manifest)
    (evidence/'archive_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('ARCHIVE VERIFIED',archive.name,report['bytes'],report['sha256'],flush=True)


if __name__=='__main__':main()
