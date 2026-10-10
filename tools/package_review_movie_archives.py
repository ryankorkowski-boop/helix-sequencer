"""Preserve recovered review movies once per byte payload, with provenance."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT.parent / 'runtime'
OUT = ROOT / 'outputs/Review_Movie_Archives'
CUTOFF = '2026-10-09T20:54:44Z'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(item):
    path = Path(item['sources'][0]['path'])
    cache = OUT / 'validation' / (item['sha256'] + '.json')
    if cache.exists():
        return json.loads(cache.read_text())
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries',
        'stream=codec_type,codec_name,width,height,nb_frames:format=duration',
        '-of', 'json', str(path)]))
    result = subprocess.run(['ffmpeg', '-v', 'error', '-threads', '1', '-i',
                             str(path), '-f', 'null', '-'], capture_output=True)
    if result.returncode or result.stderr:
        raise ValueError(f'Full decode failed: {path}: {result.stderr.decode()[:500]}')
    video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    proof = {'sha256': item['sha256'], 'bytes': path.stat().st_size,
             'duration_seconds': float(probe['format']['duration']),
             'video': video,
             'has_audio': any(s['codec_type'] == 'audio' for s in probe['streams']),
             'full_decode_passed': True}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(proof, indent=2) + '\n')
    return proof


def candidates(mode):
    remote = json.loads((RUNTIME / 'recovered_ci_mp4_inventory.json').read_text())
    if mode == 'earlier':
        return remote
    initial = json.loads((RUNTIME / 'mp4_inventory_initial_hashed.json').read_text())
    result = remote + initial
    for folder in ('Concept_Art_Comparisons', 'Snowman_Band_Upgrade/movies'):
        for p in sorted((ROOT / 'outputs' / folder).glob('*.mp4')):
            # A fresh render must have its completed verification before inclusion.
            if 'Snowman_Band_Upgrade' in str(p) and not p.with_suffix('.verification.json').exists():
                continue
            result.append({'path': str(p), 'bytes': p.stat().st_size,
                           'collection': folder, 'mtime': p.stat().st_mtime})
    return result


def earlier_source(source):
    # Include the explicitly requested favorite six-up family even though its
    # artifact upload is later than the short-silent batch's filesystem time.
    name = source.get('original_archive_path', '')
    return source.get('artifact_created_at', '9999') < CUTOFF or (
        'Six_Layouts' in name or 'Helix_Comparison_' in name)


def destination(item, mode):
    s = item['sources'][0]
    name = Path(s.get('original_archive_path', s['path']).split('::')[-1]).name
    if 'Helix_Comparison_' in name:
        group = '00_Start_Here'
    elif 'Six_Layouts' in name:
        group = '01_Six_Layout_Song_Clips'
    elif 'Refined_3D' in name:
        group = 'Fresh_Band_Upgrade'
    elif 'Concept_Art_Comparisons' in s['path']:
        group = 'Concept_Art_Comparisons'
    elif 'Concepts_62' in s['path'] or 'concepts-62' in s['path']:
        group = 'Silent_Concepts_1-62'
    elif 'drummer' in name.lower() or 'drummer' in s.get('artifact_name', '').lower():
        group = 'Historical_Drummer_Versions'
    elif 'Snowman' in s['path'] or 'snowman-band' in s['path']:
        group = 'Prior_Snowman_Band'
    elif 'Showcase' in name or 'Flavors' in name or 'Fingerboard__' in name:
        group = 'Earlier_Helix_Layouts'
    else:
        group = 'Other_Review_Previews'
    return f'{group}/{item["sha256"][:8]}_{name}'


def package(mode):
    OUT.mkdir(parents=True, exist_ok=True)
    grouped = {}
    for source in candidates(mode):
        p = Path(source['path'])
        if not p.exists():
            raise FileNotFoundError(p)
        h = digest(p)
        grouped.setdefault(h, {'sha256': h, 'bytes': p.stat().st_size,
                              'sources': []})['sources'].append(source)
    if mode == 'earlier':
        grouped = {h: i for h, i in grouped.items()
                   if any(earlier_source(s) for s in i['sources'])}
    items = sorted(grouped.values(), key=lambda i: destination(i, mode))
    with ThreadPoolExecutor(max_workers=3) as executor:
        for item, proof in zip(items, executor.map(verify, items)):
            item['verification'] = proof
            item['archive_path'] = destination(item, mode)
    if mode == 'earlier':
        title = 'Earlier_Layout_And_Drummer_MP4s'
        scope = ('Recovered earlier review movies, excluding all 62 short silent '
                 'concept movies and all later snowman/artwork/upgrade renders. '
                 'The explicitly requested favorite 90-second six-layout comparison '
                 'and its companion/individual clips are included, although their '
                 'CI upload dates follow the silent batch. No movie is regenerated.')
    else:
        title = 'All_Available_Recent_MP4s'
        scope = ('All unique MP4 payloads available locally at collection and '
                 'recovered from the 92 unexpired CI artifacts in the request '
                 'window, plus newly requested artwork comparisons and band upgrades.')
    missing = ('The older Android delivery documented 42 movies at '
               '/workspace/helix-laptop-prep/outputs/Helix_Android_Previews. '
               'That workspace and its 339126653-byte ZIP are absent here; no '
               'published copy was found. Those exact historical bytes are not '
               'claimed as recovered. This archive is the available recovered '
               'collection, not proof that every previously generated movie survives.')
    manifest = {'schema': 'helix.review_movie_archive.v1', 'title': title,
                'scope': scope, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'request_window_utc': ['2026-10-07T10:40:36Z', '2026-10-10T10:40:36Z'],
                'earlier_batch_boundary_utc': CUTOFF,
                'time_basis': 'Original CI artifact creation dates and initial local inventory; restored file mtimes are not original creation dates.',
                'unique_mp4_count': len(items), 'movie_bytes': sum(i['bytes'] for i in items),
                'known_unavailable_history': missing, 'movies': items}
    text = (f'{title}\n\n{scope}\n\n{len(items)} unique, fully decoded MP4s. '
            'Identical copies occur once; distinct revisions remain separate. '
            'SHA256 prefixes distinguish same-named revisions. See inventory.json '
            'for all recovered source paths and original artifact dates.\n\n'
            'Start with 00_Start_Here/*Comparison_A*90s.mp4 for the favorite '
            'six-layout reel, beginning with Wire Tree.\n\n' + missing + '\n')
    archive = OUT / (title + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
        z.writestr('README.txt', text)
        z.writestr('inventory.json', json.dumps(manifest, indent=2) + '\n')
        for item in items:
            z.write(item['sources'][0]['path'], item['archive_path'])
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for item in items:
            with z.open(item['archive_path']) as f:
                h = hashlib.sha256()
                for chunk in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(chunk)
                assert h.hexdigest() == item['sha256']
    proof = {'file': str(archive), 'bytes': archive.stat().st_size,
             'sha256': digest(archive), 'unique_mp4_count': len(items),
             'all_mp4s_fully_decoded': True, 'zip_crc_passed': True,
             'all_zipped_movie_sha256_match_sources': True,
             'known_unavailable_history': missing}
    (OUT / (title + '.inventory.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    (OUT / (title + '.verification.json')).write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['earlier', 'recent'], required=True)
    package(parser.parse_args().mode)
