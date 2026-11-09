"""Reuse source-bound analysis from the earlier real-audio review, without inventing stems."""
from pathlib import Path
import argparse,copy,json,shutil
import numpy as np
from music.note_events import NoteEvent
from music.review_score import pitched_roles
from tools.audio_excerpt import digest


def recover(archive_root,output,ids):
    archive_root=Path(archive_root);output=Path(output);man=archive_root/'05_Source_Excerpt_Manifests'
    rows=json.loads((man/'selected_excerpts.json').read_text());(output/'sources').mkdir(parents=True,exist_ok=True)
    (output/'sources/selected_excerpts.json').write_text(json.dumps(rows,indent=2)+'\n')
    for eid in ids:
        row=next(r for r in rows if r['excerpt_id']==eid);audio=archive_root/'07_Layouts_and_Sequences'/eid/'audio.wav';folder=output/'analysis'/eid
        if folder.exists():raise FileExistsError(folder)
        h=digest(audio);cached=man/'Analysis'/eid
        proof=json.loads((cached/'verification.json').read_text());vocal=json.loads((cached/'vocals.json').read_text())
        if proof['source_sha256']!=h or vocal['audio_sha256']!=h:raise ValueError('Recovered source analysis hash mismatch')
        shutil.copytree(man/'Analysis'/eid,folder);source=output/'sources'/eid;source.mkdir();shutil.copy2(audio,source/'audio.wav')
        shutil.copy2(folder/'drummer_cues_renderer_input.xsq',source/'drummer.xsq')
        shutil.copy2(folder/'note_events.json',folder/'baseline_note_events.json')
        events=json.loads((folder/'baseline_note_events.json').read_text())
        with np.load(folder/'performance_curves.npz') as z:curves={k:z[k].copy() for k in z.files}
        other=[NoteEvent(**e) for e in events.get('pitched_other',[])]
        keys,mallets,corrections=pitched_roles([NoteEvent(**e) for e in events.get('piano',[])],other,proof['mallet_attacks'],curves['keyboard_mallet_energy'],np.array([e.start for e in other]))
        events['piano']=[e.to_dict() for e in keys];(folder/'note_events.json').write_text(json.dumps(events,indent=2)+'\n')
        shapes=curves['mouth_lanes'];shapes=shapes.max(axis=1) if shapes.ndim==2 else shapes
        energy=curves['vocal_energy'].copy()
        if not row['vocals_expected']:shapes=np.zeros_like(shapes);energy[:]=0
        np.savez_compressed(folder/'vocal_clock.npz',energy=np.repeat(energy,5),shapes=np.repeat(shapes,5))
        roles=dict(source_sha256=h,keyboard=[e.to_dict() for e in keys],mallets=[e.to_dict() for e in mallets],onset_corrections=corrections,
                   provenance='retained source-bound stem analysis; corrections use retained note onset times',fresh_source_separation=False,independent_voice_sources=False,exact_phonemes_verified=False)
        (folder/'pitched_roles.json').write_text(json.dumps(roles,indent=2)+'\n')
        (folder/'recovery_provenance.json').write_text(json.dumps(dict(audio_sha256=h,record=row,retained_analysis=True,source_voice_clock_ms=50,fresh_source_separation=False,voice_identity_inferred=False),indent=2)+'\n')
        print('RECOVERED_SOURCE',eid,row['filename'],len(keys),len(mallets),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive_root',type=Path);p.add_argument('output',type=Path);p.add_argument('ids',nargs='+');a=p.parse_args();recover(a.archive_root,a.output,a.ids)
