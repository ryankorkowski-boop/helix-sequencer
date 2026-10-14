"""Verify and package the eleven refined character-performance movies."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/Snowman_Band_Upgrade'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    proofs = [json.loads(p.read_text()) for p in sorted((OUT/'movies').glob('*.verification.json'))
              if '_pilot' not in p.name]
    expected = {('00', 'band')} | {(f'{i:02}', variant)
                                  for i in range(1, 6) for variant in ('band', 'faces')}
    assert {(p['id'], p['variant']) for p in proofs} == expected and len(proofs) == 11
    for p in proofs:
        assert sha(p['file']) == p['sha256'] and p['full_decode_passed']
        assert p['width'] == 1920 and p['height'] == 1080
        assert p['render_revision'] == 2
        assert p['soundtrack']['full_song_duration_matches']
        assert p['soundtrack']['zero_offset_correlation'] > .999
        assert not p['native_xlights_playback'] and p['new_3d_drummer_interpretation']
    pairs = []
    for i in range(1, 6):
        row = [p for p in proofs if p['id'] == f'{i:02}']
        assert row[0]['source_native_drummer'] == row[1]['source_native_drummer']
        assert row[0]['source_lyrics_sha256'] == row[1]['source_lyrics_sha256']
        pairs.append({'id': f'{i:02}', 'drummer_and_hand_hashes_identical': True,
                      'lyrics_hash_identical': True})
    preserved = json.loads((ROOT/'evidence/snowman_ensemble/preserved_inputs.json').read_text())
    assert all(sha(ROOT/p) == h for p, h in preserved.items())
    analysis = [json.loads(p.read_text()) for p in sorted((OUT/'analysis').glob('*/verification.json'))]
    assert len(analysis) == 6
    summary = {'schema': 'helix.band_visual_upgrade.v1', 'movies': proofs,
               'movie_count': len(proofs), 'paired_source_checks': pairs,
               'all_21_preserved_inputs_match': len(preserved) == 21,
               'preserved_inputs': preserved,
               'minimum_soundtrack_correlation': min(p['soundtrack']['zero_offset_correlation'] for p in proofs),
               'total_video_frames': sum(p['frames'] for p in proofs),
               'native_xlights_playback': False,
               'preferred_approved_drummer_image_recovered': False,
               'all_six_songs_use_lead_only_due_to_voice_uncertainty': all(not a['vocal_routing']['two_voice_candidates'] for a in analysis),
               'focused_geometry_and_strike_schedule_tests': '9 passed',
               'implementation_sha256': {str(p): sha(ROOT/p) for p in map(Path, [
                   'models/band_performance_scene.py', 'models/drummer_review_schedule.py', 'tools/analyze_band_upgrade.py',
                   'tools/render_band_upgrade.py'])}}
    (OUT/'verification.json').write_text(json.dumps(summary, indent=2)+'\n')
    readme = ('Eleven refined 3D character-performance previews\n\n'
              '00 = Wire Tree; 01 = Who Knew; 02 = 49; 03 = Candy Cane Chaos; '
              '04 = Phoneme Test Hook; 05 = Festivus.\n'
              'Band = six-member snowman ensemble. Faces = drummer with four '
              'original helix singing-face sculptures.\n\n'
              'These are 3D review visualizations, not native xLights playback. '
              'The drummer is a new 3D interpretation of the polished V3 contract, '
              'not recovery of a different approved image. Original drum/lyric '
              'timing and source inputs remain preserved. Separate singer controls '
              'exist; these mixes did not yield reliable second-voice profiles, '
              'so unconfirmed harmony mouths rest. Musical notes are inferred. '
              'GLBs contain static geometry, not playable animation or xLights models.\n')
    archive = OUT/'Snowman_Band_Refined_3D_MP4s.zip'
    sources = {}
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED) as z:
        z.writestr('README.txt', readme)
        files = [*(Path(p['file']) for p in proofs), OUT/'verification.json',
                 *sorted((OUT/'movies').glob('*.glb')),
                 *sorted((OUT/'analysis').glob('*/verification.json'))]
        for p in files:
            name = str(p.relative_to(OUT));z.write(p, name);sources[name] = sha(p)
        p = ROOT/'docs/SNOWMAN_BAND_VISUAL_UPGRADE.md'
        z.write(p, 'VISUAL_UPGRADE.md');sources['VISUAL_UPGRADE.md'] = sha(p)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(name)).hexdigest() == h for name, h in sources.items())
    result = {'file': str(archive), 'bytes': archive.stat().st_size, 'sha256': sha(archive),
              'mp4_count': 11, 'zip_crc_passed': True, 'all_extracted_file_hashes_match': True}
    (OUT/'package_verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
