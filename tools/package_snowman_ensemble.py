"""Collect only complete verified performances into durable review packages."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

import numpy as np
from PIL import Image,ImageDraw
from tools.analyze_snowman_ensemble import sha
from tools.build_helpers.ultimate_showcase_preview import read_fseq,_font

SHORT={'00':'Wire_Tree','01':'Who_Knew','02':'49','03':'Candy_Cane_Chaos','04':'Phoneme_Test_Hook','05':'Festivus'}


def archive(path,entries):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for source,name in entries:z.write(source,name)
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:raise ValueError('Delivery ZIP CRC failure')


def package(root,destination):
    destination.mkdir(parents=True,exist_ok=True)
    sources=json.loads((root/'sources.json').read_text());proof=[];entries=[];movies=[]
    for row in sources:
        for variant in ['band'] if row['previous'] else ['band','faces']:
            folder=root/'shows'/(row['id']+'_'+variant)
            report=json.loads((folder/'verification.json').read_text())
            if report['source_sha256']!=row['sha256']:raise ValueError('Incorrect song provenance')
            if not report['native_mouth_nodes_match'] or not report['native_arm_pose_holds_match']:raise ValueError('Missing native animation proof')
            if sha(folder/'media/song.mp3')!=row['sha256']:raise ValueError('Portable soundtrack changed')
            for name,digest in report['hashes'].items():
                if sha(folder/name)!=digest:raise ValueError('Deliverable changed after verification: '+name)
            movie=folder/(row['id']+'_'+variant+'.mp4')
            filename=row['id']+'_'+SHORT[row['id']]+'_'+('Band' if variant=='band' else 'Helix_Faces')+'.mp4'
            shutil.copy2(movie,destination/filename);movies.append((destination/filename,filename))
            for path in folder.rglob('*'):
                if path.is_file() and path.suffix not in ('.mp4','.log') and not path.name.startswith(('preview_','decoded_')):
                    entries.append((path,'Snowman_Ensemble/'+folder.name+'/'+str(path.relative_to(folder))))
            report.update(download_file=filename,portable_media_original_sha256=row['sha256'])
            proof.append(report)
    if len(proof)!=11:raise ValueError('The requested eleven performances are incomplete')
    comparisons=[]
    for row in sources:
        if row['previous']:continue
        a,_=read_fseq(root/'shows'/(row['id']+'_band')/'Snowman_Band.fseq')
        b,_=read_fseq(root/'shows'/(row['id']+'_faces')/'Helix_Singing_Faces.fseq')
        if not np.array_equal(a[:,:20736],b[:,:20736]):raise ValueError('Same-song native drummer differs between variants')
        comparisons.append(dict(id=row['id'],native_drummer_channels_identical_all_frames=True,channels=20736,frames=len(a)))
    native=destination/'Snowman_Ensemble_XLights.zip';archive(native,entries)
    movie_zip=destination/'Snowman_Ensemble_All_MP4s.zip';archive(movie_zip,movies)
    if max(native.stat().st_size,movie_zip.stat().st_size)>=95*1024**2:
        if movie_zip.stat().st_size>=95*1024**2:
            movie_zip.unlink()
            for variant,label in [('Band','Band'),('Helix_Faces','Helix_Faces')]:
                chosen=[item for item in movies if item[1].endswith('_'+variant+'.mp4')]
                archive(destination/('Snowman_Ensemble_'+label+'_MP4s.zip'),chosen)
        if native.stat().st_size>=95*1024**2:raise ValueError('Split native package before Git hosting')
    # Contact sheet images are decoded from the finished MP4s, not the renderer.
    sheet=Image.new('RGB',(1200,math_rows(len(proof))*255),'#07111D');draw=ImageDraw.Draw(sheet)
    for i,row in enumerate(proof):
        image_path=destination/f'decoded_{row["id"]}_{row["variant"]}.png'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(min(row['duration_s']*.35,60)),
                        '-i',row['movie'],'-frames:v','1',str(image_path)],check=True)
        picture=Image.open(image_path).convert('RGB').resize((400,225))
        x,y=(i%3)*400,(i//3)*255;sheet.paste(picture,(x,y+30))
        draw.text((x+8,y+5),f'{row["id"]} / {row["title"][:30]} / {row["variant"]}',font=_font(12),fill='#DAEAF5')
    sheet.save(destination/'Snowman_Ensemble_Contact_Sheet.jpg',quality=94)
    result=dict(schema='helix.snowman_ensemble_delivery.v1',performances=proof,identical_native_drummer=comparisons,
                native_zip_crc='pass',movie_zip_crc='pass',native_show_count=11,full_song_movie_count=11,
                musical_review_status='inferred_first_performances_pending_user_listening')
    (destination/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    rows=[]
    for row in proof:
        rows.append(f'<tr><td>{html.escape(row["title"])}</td><td>{row["variant"]}</td><td><a href="{row["download_file"]}">Play/download MP4</a></td></tr>')
    (destination/'index.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Snowman ensemble previews</title><style>body{background:#0b1624;color:#edf4ff;font:16px system-ui;max-width:1100px;margin:30px auto;padding:15px}a{color:#83e4ff}td,th{padding:14px;text-align:left;border-bottom:1px solid #34455b}img{width:100%}</style>'
        '<h1>Snowman ensemble — full-song previews</h1><p>Six-member band, plus original helix singing-face/drummer alternatives. Original audio; native xLights lighting on matching3D geometry.</p>'
        '<p>Lip sync uses detected words and allocated pronunciation shapes; inferred lyrics/timing need listening review. Male/female roles share the vocal line. Instrument notes are separated-stem pitch proxies.</p>'
        '<p><a href="Snowman_Ensemble_XLights.zip">Native xLights shows/models/sequences/media</a></p>'
        '<table><tr><th>Song</th><th>Layout</th><th>Preview</th></tr>'+''.join(rows)+'</table><p><img src="Snowman_Ensemble_Contact_Sheet.jpg" alt="Decoded movie contact sheet"></p>')
    (destination/'README.md').write_text('# Snowman ensemble —11 complete song performances\n\n'
        'The band contains the unchanged canonical drummer, upright bass, guitar, male/female singers and keyboardist. '
        'The alternative uses the same drummer with original helix tree, bulb, pumpkin and snowman singing props.\n\n'
        'Native ZIP:11 independent xLights2026.18+ shows with3D Custom geometry, model exports, XSQ, actual rendered FSEQ, original relative media and static orbit review HTML. '
        'Select one extracted show folder, open its XSQ and Render All. No physical controllers.\n\n'
        'All11 MP4s are full-song1280×72020fps H.264/yuv420p with the original-source AAC soundtrack. '
        'They project real native channel values onto identical exported XYZ; they are not GUI recordings.\n\n'
        'Drums reuse source-bound ADTOF and the unchanged V3 mapper. Bass/guitar/keys use separated-stem onset/dominant-pitch proxies. '
        'Whisper word timing plus dictionary/sung-syllable pronunciations drives seven mouths. Within-word phone durations are estimated. '
        'Both singers/faces share recognized vocals. Unknown tom identities abstain. Inferred lyrics/musical timing require listening review.\n\n'
        'See verification.json, contact sheet and the individual movie links in the release index. External inference model code and weights are not included.\n')
    return result


def math_rows(n):return (n+2)//3


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('destination',type=Path)
    a=p.parse_args();r=package(a.root.resolve(),a.destination.resolve());print('PACKAGED',len(r['performances']),flush=True)
