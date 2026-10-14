"""Assemble native diagnostic payload, hash and decode all included media."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, wave, zipfile
import numpy as np
from scipy.signal import correlate, correlation_lags

SOURCE='b7576e28008b938b0f4d832ae3f2688bde996444'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):return subprocess.check_output(args)

def main():
    ap=argparse.ArgumentParser()
    for name in ('source','native','notes','output'):ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();out=a.output;folder=out/'Helix_Beta_v1.0_Layouts_and_Diagnostics'
    shutil.copytree(a.native,folder,dirs_exist_ok=True)
    native=json.loads((folder/'VALIDATION.json').read_text());assert native['source_commit']==SOURCE
    for name,v in native['files'].items():
        p=folder/name;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],name
    for name in ('LICENSE','NOTICE','COMMERCIAL_LICENSING.md','WELCOME_TO_HELIX.md','INSTALL_AND_TROUBLESHOOT.md'):
        shutil.copy2(a.source/name,folder/name)
    shutil.copytree(a.source/'LICENSES',folder/'LICENSES',dirs_exist_ok=True)
    shutil.copy2(a.notes,folder/'BETA_RELEASE_NOTES.md')
    for p in folder.rglob('README.md'):
        if p.parent!=folder:p.unlink()
    (folder/'README.md').write_text("""# Helix Beta Release v1.0 — layouts and native diagnostics

This package is a verified layout and wiring diagnostic, not the full-song showcase.

Infinite_Symphony_Layout contains the native xLights show directory, 1,081 models,
18 houses, 919,839 channels, 88 independently mapped keyboard rungs, layout scaling
metadata and the matching 2.4-second XSQ/FSEQ rung probe. Open this directory as
the xLights show folder, then open Native_Keyboard_Rung_Diagnostic.xsq.
Its cleared showcase XSQ is retained as a source template, not a finished sequence.
Native import/render was tested with pinned xLights 2026.18 on Linux.

Physical_Drummer_Diagnostic contains a 12-channel Single Color White layout, matching
3-second XSQ/FSEQ, synthetic authored calibration WAV and a synchronized diagnostic
MP4. The video displays actual rendered FSEQ values as circuit cards. It does not
depict mechanical movement or complete performers. Eight 60-ms-spaced authored
kick contacts, independent drum circuits, dim body and exclusive snare poses are
verified. The cards include all circuits; controller/output addresses are unassigned.
Tom-stick poses require additional fixed circuits or pixels. Preserve the supplied
channel_map.json and inspect your hardware configuration before connecting outputs.

Layouts and sequences must stay together in their supplied directories.
No original song audio or song movies are included because individual redistribution
clearances have not been established. See MUSIC_OMISSIONS.json and release notes.
Two complete bands, phrase choreography, six-layout comparison and original-song
rapid-kick detection remain unfinished. No physical controller/native LOR validation
is claimed. SHA256SUMS.txt and MANIFEST.json document every payload.
Community and support: https://Facebook.com/helixsequencer.
""")
    tracks=[
      'Helix Audiolights','Wire Tree','Tinsel','Frostbitten','Holly','Bell',
      "Who Knew (Grinch's Redemption) (Remastered)",'49 (Remastered)',
      'Candy Cane Chaos','Phoneme Test Hook','Festivus (Remastered)']
    (folder/'MUSIC_OMISSIONS.json').write_text(json.dumps({
      'verified_unique_recordings':11,'redistribution_clearances_verified':0,
      'tracks':[{'track':n,'distributed':False,'reason':'Creation account/date and applicable subscription rights not independently verified'} for n in tracks],
      'archived_inputs_blob':'5fa07a94fe9816a1e3613e968f16424226f1d5b3',
      'archived_inputs_sha256':'8032377efd136fa0b20d87d936a6fefed8131f088049bd2f0f36f2eb7754ab89',
      'missing_full_song':'LightsOutTheme.mp3','synthetic_diagnostic_audio_included':True,
      'different_accounts_must_remain_separate':True},indent=2)+'\n')
    media=[]
    for p in folder.rglob('*.mp4'):
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(p),'-f','null','-'],check=True)
        probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
        v=next(s for s in probe['streams'] if s['codec_type']=='video')
        au=next(s for s in probe['streams'] if s['codec_type']=='audio')
        assert int(v['nb_read_frames'])==300 and abs(float(v['duration'])-3)<.02
        assert abs(float(au['duration'])-3)<.03
        decoded=np.frombuffer(run(['ffmpeg','-v','error','-i',str(p),'-vn','-ac','1','-ar','22050','-f','f32le','-']),dtype='<f4')
        with wave.open(str(p.parent/'Diagnostic_Only.wav')) as w:
            assert w.getframerate()==22050;original=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
        cross=correlate(decoded,original,mode='full',method='fft')
        lag=int(correlation_lags(len(decoded),len(original))[np.argmax(cross)])
        start=max(0,lag);offset=max(0,-lag);n=min(len(original)-offset,len(decoded)-start)
        corr=float(np.corrcoef(original[offset:offset+n],decoded[start:start+n])[0,1])
        assert abs(lag)<=220 and corr>.98,(lag,corr)
        raw=run(['ffmpeg','-v','error','-i',str(p),'-vf','scale=160:90','-pix_fmt','rgb24','-f','rawvideo','-'])
        frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,90,160,3)
        black=int(np.sum(frames.mean(axis=(1,2,3))<2));assert black==0
        samples=folder/'Verification_Frames';samples.mkdir(exist_ok=True)
        for when in (.2,.44,1.0,2.2):
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(when),'-i',str(p),'-frames:v','1',str(samples/f'frame_{when:.2f}.png')],check=True)
        media.append({'file':str(p.relative_to(folder)),'bytes':p.stat().st_size,'sha256':sha(p),
          'frames':len(frames),'video_seconds':float(v['duration']),'audio_seconds':float(au['duration']),
          'decoded_aac_seconds':len(decoded)/22050,'audio_offset_ms':lag/22050*1000,
          'source_audio_correlation':corr,'black_frames':black,'full_decode':True,
          'claim':'Synthetic circuit timing, not original song or complete animated band'})
    (folder/'MEDIA_VERIFICATION.json').write_text(json.dumps(media,indent=2)+'\n')
    files={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(folder.rglob('*')) if p.is_file()}
    manifest={'source_commit':SOURCE,'integration_commit':'cb6cff6bcf0227386a244b4bf2ea369ee9bab228',
      'native_version':'xLights 2026.18','showcase_complete':False,'files':files}
    (folder/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (folder/'SHA256SUMS.txt').write_text(''.join(f"{v['sha256']}  {name}\n" for name,v in files.items()))
    archive=out/'Helix_Beta_v1.0_Layouts_and_Diagnostics.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(folder).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,v in files.items():assert hashlib.sha256(z.read(name)).hexdigest()==v['sha256'],name
        extracted=out/'extraction-check';z.extractall(extracted)
        for name,v in files.items():assert sha(extracted/name)==v['sha256'],name
        shutil.rmtree(extracted)
    sums=out/'SHA256SUMS.txt'
    with sums.open('a') as f:f.write(f'{sha(archive)}  {archive.name}\n')
    print(json.dumps({'archive':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'media':media},indent=2))
if __name__=='__main__':main()
