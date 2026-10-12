"""Assemble verified review files without modifying source assets."""
from pathlib import Path
import hashlib,json,shutil,zipfile
from tools.render_refined_helix_band import OUT,ROOT

def main():
    native=json.loads((OUT/'native_verification.json').read_text())
    output=json.loads((OUT/'output_verification.json').read_text())
    audio=json.loads((OUT/'montage_audio_verification.json').read_text())
    assert len(native)==10 and len(output['movies'])==10 and len(audio)==8
    assert all(r['full_decode_passed'] for r in output['movies'])
    assert all(r['waveform_correlation']>.995 and abs(r['offset_error_ms'])<2 for r in audio)
    assert sum(r['frames'] for r in output['movies'])==7747
    assert sum(r['native_frames'] for r in native)==6981
    output['visual_review_by_model_pending']=True
    (OUT/'output_verification.json').write_text(json.dumps(output,indent=2)+'\n')
    for source,name in [('docs/BAND_REFINEMENT_REPORT.md','Helix_Band_Refinement_Report.md'),('docs/BAND_REFINEMENT_HANDOFF.md','HANDOFF.md'),('docs/BAND_REFINEMENT_CHECKLIST.md','BAND_REFINEMENT_CHECKLIST.md')]:
        shutil.copyfile(ROOT/source,OUT/name)
    proof=OUT/'evidence';proof.mkdir(exist_ok=True)
    for path in (ROOT/'evidence/band_refinement').glob('*'):
        if path.is_file() and path.suffix in ('.json','.log'):shutil.copyfile(path,proof/path.name)
    (OUT/'README.md').write_text('Helix Band review. Source and primary branches preserved.\nEach xlights/<name> folder is an independent 384x216 native Video-on-matrix show. Keep XML/XSQ/media together. Separate physical prop articulation is not implemented; mallet identity remains unverified. See the report.\n')
    files=[]
    for path in OUT.rglob('*'):
        if not path.is_file() or path.suffix in ('.fseq','.zip'):continue
        if 'pilot' in path.as_posix() or path.name.endswith('.silent.mp4'):continue
        if path.suffix not in ('.xsq','.xml','.mp4','.wav','.json','.jpg','.png','.md','.log'):continue
        if path.parent==OUT and path.suffix=='.mp4':continue
        files.append(path)
    manifest=[dict(file=p.relative_to(OUT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
    meta=OUT/'delivery_manifest.json';meta.write_text(json.dumps(dict(files=manifest,source_implementation='37ffbedde20a9f41f6723223d7fd6a65ceba2fb9',primary_merged=False),indent=2)+'\n')
    files.append(meta)
    archive=OUT/'Helix_Band_Review_Matrix_XSQ_Bundle.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4) as z:
        for p in files:z.write(p,p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for item in manifest:assert hashlib.sha256(z.read(item['file'])).hexdigest()==item['sha256']
    result=dict(file=archive.name,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),entries=len(files),crc_passed=True,all_hashes_verified=True)
    (OUT/'archive_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)

if __name__=='__main__':main()
