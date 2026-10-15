"""Package completed, independently verified review movies; refuse partial sets."""
from __future__ import annotations
import argparse,hashlib,html,json,shutil,struct,subprocess,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont
from core.output_provenance import stamp_mp4
from tools.verify_showcase_review import CATEGORIES


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def media_prefix(path):
    """Hash bytes preceding the terminal Helix-owned free box."""
    data=Path(path).read_bytes();position=0;end=len(data)
    while position<len(data):
        length,kind=struct.unpack_from('>I4s',data,position);head=8
        if length==1:length=struct.unpack_from('>Q',data,position+8)[0];head=16
        if not length or position+length>len(data):raise ValueError('Invalid MP4 atoms')
        if kind==b'free' and position+length==len(data) and data[position+head:].startswith(b'HELIX_PROVENANCE_V1\0'):end=position
        position+=length
    return hashlib.sha256(data[:end]).hexdigest(),end


def refresh_notice(movie,render,validation):
    before,size=media_prefix(movie);stamp_mp4(movie,refresh=True);after,newsize=media_prefix(movie)
    if (before,size)!=(after,newsize):raise ValueError('Notice refresh changed encoded media bytes')
    digest=sha(movie)
    for proof in (render,validation):proof.update(sha256=digest,bytes=movie.stat().st_size,metadata_refresh_media_bytes_unchanged=True,media_prefix_sha256=before)
    # Re-read final container timing; full decode evidence remains valid for the
    # exact preserved media prefix, independent of the replaced terminal notice.
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,duration','-of','json',str(movie)]))['streams'][0]
    assert int(probe['nb_frames'])==720 and abs(float(probe['duration'])-36)<.001


def virtual_export(movie,folder,source_audio):
    """Native Video matrix references the delivered movie and original excerpt."""
    from tools.export_refined_band_matrix import export
    folder.mkdir(parents=True,exist_ok=True)
    sequence=export(movie,folder)
    tree=ET.parse(sequence);r=tree.getroot();r.find('head/mediaFile').text='../audio.wav'
    rel=Path('../../../')/movie.parent.name/movie.name
    effect=r.find('EffectDB/Effect');effect.text=effect.text.replace('media/performance.mp4',rel.as_posix())
    r.find('head/comment').text='Native Video matrix of the exact review movie. Uses the original excerpt WAV; continuous meshes are not physical AC actuator channels.'
    tree.write(sequence,encoding='utf-8',xml_declaration=True)
    scope=json.loads((folder/'EXPORT_SCOPE.json').read_text());scope.update(movie_relative_path=rel.as_posix(),original_excerpt='../audio.wav',
        required_files=['xlights_rgbeffects.xml','xlights_networks.xml',sequence.name,rel.as_posix(),'../audio.wav'],
        source_movie_sha256=sha(movie),source_audio_sha256=sha(source_audio))
    (folder/'EXPORT_SCOPE.json').write_text(json.dumps(scope,indent=2)+'\n')


def archive(path,root,files):
    temporary=path.with_suffix('.building.zip');checks={}
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4) as z:
        for file in sorted(set(files)):
            name=(Path('Helix_Showcase_Review')/file.relative_to(root)).as_posix();checks[name]=sha(file)
            z.write(file,name,compress_type=zipfile.ZIP_STORED if file.suffix.lower() in ('.mp4','.jpg','.png','.npz','.fseq') else zipfile.ZIP_DEFLATED)
        z.writestr('Helix_Showcase_Review/ARCHIVE_CHECKSUMS_'+path.stem+'.json',json.dumps(checks,indent=2)+'\n')
    with zipfile.ZipFile(temporary) as z:
        if z.testzip() is not None:raise ValueError('ZIP CRC check failed')
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate ZIP entries')
    temporary.replace(path)
    return dict(file=path.name,bytes=path.stat().st_size,sha256=sha(path),entries=len(checks)+1,CRC_verified=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    rows={r['excerpt_id']:r for r in json.loads((root/'05_Source_Excerpt_Manifests/selected_excerpts.json').read_text())}
    expected=[12,8,10,10];movies=[];proofs=[]
    for category,count in zip(CATEGORIES,expected):
        local=[]
        for p in sorted((root/category).glob('*.render.json')):
            render=json.loads(p.read_text());movie=root/render['file'];validation_path=root/'06_Validation_Reports'/(movie.stem+'.json')
            validation=json.loads(validation_path.read_text())
            if validation['sha256']!=sha(movie) or not validation['complete_video_decode']:raise ValueError('Missing current decode proof: '+movie.name)
            if validation['source_sha256']!=rows[render['excerpt_id']]['sha256']:raise ValueError('Wrong source provenance')
            refresh_notice(movie,render,validation)
            p.write_text(json.dumps(render,indent=2)+'\n');validation_path.write_text(json.dumps(validation,indent=2)+'\n')
            movies.append((movie,render,validation));local.append(movie);proofs.append(validation)
        if len(local)!=count:raise ValueError(f'{category}: {len(local)} completed, {count} required')
    if len({v['sha256'] for _,_,v in movies})!=40:raise ValueError('Videos are not distinct')
    # Preserve all source-bound estimates, including rejected text for review.
    shutil.copytree(root/'analysis',root/'05_Source_Excerpt_Manifests/Analysis',dirs_exist_ok=True,
        ignore=lambda directory,names:[n for n in names if n.startswith('whisper_words')])
    for eid in rows:
        source=root/'07_Layouts_and_Sequences'/eid/'drummer.xsq'
        shutil.copyfile(source,root/'05_Source_Excerpt_Manifests/Analysis'/eid/'drummer_cues_renderer_input.xsq')
    for movie,render,validation in movies:
        if render['category'] in ('01_Standalone_Bands','04_Lyric_Band_Videos'):
            eid=render['excerpt_id'];virtual_export(movie,root/'07_Layouts_and_Sequences'/eid/'Virtual_Band_View',root/'07_Layouts_and_Sequences'/eid/'audio.wav')
    guide='''# Helix showcase review collection

40 new movies, each 36 seconds at a supported native 20 FPS. Standalone and vocal bands are 1280×720; embedded layouts and six-panel comparisons are 1920×1080. Every movie uses H.264 video and AAC stereo, with the original source tempo and pitch.

Unzip the six bundles into the same parent folder so they share `Helix_Showcase_Review`. Open MASTER_VIDEO_INDEX.html or the Markdown index. The first four ZIPs contain movies; the two technical ZIPs contain layouts, sequences, original excerpt WAVs, manifests and diagnostics. Native Video matrix exports refer to the movies in their category folders, so keep this structure intact.

Start with a standalone band, the matching embedded stage, then its six-layout comparison. Use the movie ID and source timestamp when reporting a correction. Each band has six visible performers and one unified keyboard/mallet player. Snow and solid rock styles alternate. Embedded movies contain two native band stages plus a live stage-detail inset; at least eight comparisons include a band-bearing panel.

## Review checklist

- Drums: count rapid kicks, inspect alternating snare hands, cymbal attack/decay and stick contact/recovery. Note missing or incorrect toms.
- Guitar/bass: compare riff, solo and bass movement with what you hear. Bass notes should differ from kick timing and guitar notes.
- Pitched performer: check active bars, alternating hands and contacts during piano, synth, bell and mallet passages.
- Vocals: inspect phrase entrances, rests, mouth shapes and any lyric timing. A second singer remains quiet without independent source evidence.
- Layouts: compare independent prop reactions, chases, phrase changes, palettes and stage placement. All six panels use the same excerpt and soundtrack clock.
- Playback: listen for drift or missing audio and report movie ID plus the visible source time.

## Evidence and limits

All 91 Drive entries were inspected and ranked; exact decoded hashes resolve 82 distinct recordings. Names alone never deduplicate audio. Source selection uses repeatable activity metrics and title-family diversity; spectral bands are proxies rather than confirmed instruments. Full per-recording rankings, original hashes, exact excerpt times and selection reasons are included.

Fresh htdemucs_6s stems, pinned ADTOF drum inference and Helix harmonic/playable-note logic drive the band. These are estimates, not independently labelled musical ground truth. Confidence values describe screening strength and are not calibrated instrument probabilities. Source separation can leak instruments. Unresolved tom identities abstain instead of fabricating a three-tom pattern. The five-family detector cannot establish all actual tom pitches. Mallet chords requiring more than two hands and unreachable poses are recorded as motion omissions; all notes still have explicit lighting lanes. Drum motion rejects impossible same-hand travel without inventing new instruments.

Lyric captions appear only where isolated-vocal recognition is corroborated against actual embedded lyrics. Other vocal songs retain acoustic mouth animation without invented words. Word/phone boundaries remain estimates. One mixed vocal bus does not establish separate lead and backing voices; no fabricated duet is claimed.

Surrounding shows are real Helix sequences rendered by native xLights 2026.18. MP4s show actual FSEQ values; stock geometry projection is approximate. Open `performance.xsq` with its matching layout and `audio.wav` in each native-show folder. Native band props use stationary addressable pixel poses; the cinematic inset and standalone movies show continuous meshes. Virtual matrix exports reproduce the movies and are explicitly separate from physical AC actuator parity. Tagged drummer XSQs under Analysis are renderer cue inputs, not separate portable shows. Original CTB16PC/LOR contracts remain intact. No controllers, Samsung/ARM64 or other physical hardware were tested in this phase.

Every completed MP4 was fully decoded, checked for 720 frames, stereo audio, source correspondence, zero-offset alignment, unexpected black frames and prolonged complete-scene freezes. Decoded diagnostic frames and numerical mallet-contact errors are included. These technical checks do not replace listening/artistic review.

## Approval hold

No final/default branch merge or public EXE/APK rebuild was performed. Review the movies and request corrections. Final release integration requires your explicit approval; successful tests and silence do not constitute approval.

Music: HelixHelps / hardKor / Helix music mix. Use is authorized by the user's collection permission. Community: https://facebook.com/helixsequencer
'''
    (root/'README_REVIEW_GUIDE.md').write_text(guide)
    index=['# Helix master video index','',f'{len(movies)} verified new MP4s · 36 seconds each · final release integration on hold.','']
    cards=[]
    for movie,render,validation in movies:
        row=rows[render['excerpt_id']];rel=movie.relative_to(root).as_posix();id=dict(zip(CATEGORIES,['B','L','C','V']))[render['category']]+movie.stem.split('_',2)[0]+'-'+render['excerpt_id']
        description=('Six independent native layouts, same soundtrack' if render['category'].startswith('03') else 'Native lighting neighborhood with two band stages and live stage closeup' if render['category'].startswith('02') else 'Vocal band; checked captions where available' if render['category'].startswith('04') else 'Instrumental band with stage and instrument closeups')
        index += [f'- [{id} — {row["filename"]}]({rel}) — {description}; source {row["start_seconds"]:.2f}–{row["end_seconds"]:.2f}s.']
        cards.append(f'<article><h3>{html.escape(id+" · "+row["filename"])}</h3><p>{html.escape(description)} · {row["start_seconds"]:.2f}–{row["end_seconds"]:.2f}s source</p><video controls preload="none" src="{html.escape(rel,quote=True)}"></video><a href="{html.escape(rel,quote=True)}" download>Download MP4</a></article>')
    (root/'MASTER_VIDEO_INDEX.md').write_text('\n'.join(index)+'\n')
    (root/'MASTER_VIDEO_INDEX.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Helix showcase review</title><style>body{background:#08111d;color:#dfeffa;font:16px system-ui;margin:24px auto;max-width:1200px;padding:0 16px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}article{background:#102237;padding:16px;border-radius:12px}video{width:100%;background:black}a{color:#8cdef2}p{color:#b5cbdc}h3{font-size:18px}</style><h1>Helix showcase review</h1><p>40 new 36-second movies. Final EXE/APK integration awaits your explicit video approval. Unzip all bundles into the same parent folder to play these local files.</p><p><a href="README_REVIEW_GUIDE.md">Review guide and limitations</a></p><main>'+''.join(cards)+'</main>')
    summary=dict(verified_videos=40,categories=dict(zip(CATEGORIES,expected)),total_seconds=1440,
        minimum_soundtrack_correlation=min(p['minimum_soundtrack_correlation'] for p in proofs),reports=proofs,
        release_approval_received=False,public_exe_apk_rebuilt=False)
    (root/'06_Validation_Reports/MASTER_VALIDATION.json').write_text(json.dumps(summary,indent=2)+'\n')
    records={str(p.relative_to(root)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p,_,_ in movies}
    (root/'VIDEO_MANIFEST.json').write_text(json.dumps(records,indent=2)+'\n')
    common=[root/n for n in ['README_REVIEW_GUIDE.md','MASTER_VIDEO_INDEX.md','MASTER_VIDEO_INDEX.html','VIDEO_MANIFEST.json']]
    archives=[]
    for i,category in enumerate(CATEGORIES,1):
        files=common+[p for p in (root/category).glob('*') if p.is_file() and (p.suffix=='.mp4' or p.name.endswith('.render.json')) and '.rendering.' not in p.name and '.detail.' not in p.name]
        files += [root/'06_Validation_Reports'/(m.stem+'.json') for m,r,v in movies if r['category']==category]
        files += [p for m,r,v in movies if r['category']==category for p in (root/'06_Validation_Reports/Diagnostic_Frames'/m.stem).glob('*.jpg')]
        archives.append(archive(out/f'Helix_Review_{i:02}_{category[3:]}.zip',root,files));print('PACKAGED',archives[-1]['file'],flush=True)
    metadata=common+[p for d in ['05_Source_Excerpt_Manifests','06_Validation_Reports'] for p in (root/d).rglob('*') if p.is_file()]
    for part,eids in enumerate([list(rows)[:12],list(rows)[12:]],1):
        files=metadata[:]
        for eid in eids:
            files += [p for p in (root/'07_Layouts_and_Sequences'/eid).rglob('*') if p.is_file()
                and p.suffix.lower() not in ('.log','.html') and not ('Virtual_Band_View/media' in p.as_posix())
                and not p.name.startswith(('engine_raw','drum_seed','drum_injected','Helix_'))
                and p.name not in ('drummer.xsq','canonical_drums.xsq','README.txt')]
        archives.append(archive(out/f'Helix_Review_Technical_Part_{part}.zip',root,files));print('PACKAGED',archives[-1]['file'],flush=True)
    (out/'PACKAGE_VERIFICATION.json').write_text(json.dumps(dict(archives=archives,video_count=40,all_archive_CRCs_verified=True),indent=2)+'\n')


if __name__=='__main__':main()
