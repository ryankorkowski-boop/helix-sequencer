"""Package only this reassessment's hash-bound movies, analyses and audit evidence."""
import hashlib,json,zipfile
from tools.rebuild_band_logic_review import ROOT,OUT
from tools.render_band_logic_reassessment import JOBS
from tools.render_intricate_band_samplers import sha


def main():
    reports=json.loads((ROOT/'evidence/band_logic_reassessment/render_batch.json').read_text())
    assert len(reports)==len(JOBS)
    quiet_checks={(r['id'],c['source_time']) for r in reports for c in r['encoded_quiet_drum_checks']}
    assert quiet_checks=={('00',190.15),('00',190.20),('02',191.95),('02',192.00),('03',4.95),('03',5.00)}
    files={}
    for p in sorted((OUT/'movies').glob('*.mp4')):
        proof=p.with_suffix('.verification.json');data=json.loads(proof.read_text())
        assert data['sha256']==sha(p) and data['bytes']==p.stat().st_size
        assert data['full_decode_passed'] and data['all_frames_pose_routing_checked']
        assert data['soundtrack']['zero_offset_correlation']>.995
        for name,expected in data['implementation_sha256'].items():assert sha(ROOT/name)==expected
        for name,expected in data['analysis_inputs'].items():assert sha(OUT/'analysis'/data['id']/name)==expected
        files['movies/'+p.name]=p;files['movies/'+proof.name]=proof
    assert sum(n.endswith('.mp4') for n in files)==len(JOBS)
    for p in (OUT/'analysis').rglob('*'):
        if p.is_file():files[p.relative_to(OUT).as_posix()]=p
    for name in ('recompiled_inputs.json','input_pose_audit.json','member_audit.json','render_batch.json','tests.txt'):
        files['evidence/'+name]=ROOT/'evidence/band_logic_reassessment'/name
    text='''Eight fresh source-bound band logic review movies with original audio.

Three 12-second instrument studies: 49 bass (100s), Who Knew guitar (108s),
Festivus keyboard/mallets (0s). Two 18-second intricate full-band excerpts:
Who Knew (27s) and Festivus (68s).
Three 3-second drummer studies verify all six previously hidden quiet hi-hat
hold frames in Wire Tree (189s), 49 (191s) and Candy Cane Chaos (4s).

Corrected active-note/release precedence, quiet retrigger velocity, real guitar
frets/contact, face/accessory/shoulder coherence, and depressed-key hand contact.
Original accepted notes, lyrics, duet casting and native drum schedules preserved.
Current outward/lower torso drummer shoulders retained. Pitch/mallet detections
remain estimates; singer casting is authored, not voice identity separation.
The guitar mitten represents the dominant supported contact, not every finger
of a full chord. These are 3D review movies, not new native/controller proof.

Analysis and verification JSONs are included. Reproduction instructions and
handoff: docs/BAND_LOGIC_REASSESSMENT_HANDOFF.md on the source branch
feature/band-logic-reassessment. Read MASTER_TODO.md before continuing.
'''
    readme=OUT/'README.txt';readme.write_text(text);files['README.txt']=readme
    inventory={name:{'bytes':p.stat().st_size,'sha256':sha(p)} for name,p in files.items()}
    archive=OUT/'Snowman_Band_Logic_Reassessment.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for name,p in sorted(files.items()):z.write(p,name)
        z.writestr('inventory.json',json.dumps(inventory,indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,record in inventory.items():
            h=hashlib.sha256();size=0
            with z.open(name) as f:
                while chunk:=f.read(1024*1024):h.update(chunk);size+=len(chunk)
            assert size==record['bytes'] and h.hexdigest()==record['sha256']
    receipt={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),
        'movie_count':len(JOBS),'crc_and_all_extracted_hashes_verified':True,'files':inventory}
    (ROOT/'evidence/band_logic_reassessment/archive_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(archive,receipt['bytes'],receipt['sha256'])


if __name__=='__main__':main()
