import json
from pathlib import Path
import shutil

import numpy as np
import pytest
import soundfile as sf

from tools.build_starred_sampler import build, digest, select_window


def test_activity_window_retains_loud_interior_and_is_repeatable():
    pcm = np.zeros((12000, 2), 'f4')
    pcm[5000:8000] = .6
    start, end = select_window(pcm, 1000, 2)
    assert 5000 <= start and end <= 8000
    assert (start, end) == select_window(pcm, 1000, 2)


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='ffmpeg required')
def test_every_drive_identity_survives_same_titles_and_audio_ranges(tmp_path):
    rows = []
    for i, frequency in enumerate((220, 510)):
        p = tmp_path / f'{i}.wav'
        x = np.sin(np.arange(44100 * 2) * 2 * np.pi * frequency / 44100) * .2
        sf.write(p, np.c_[x, x], 44100, subtype='PCM_24')
        rows.append(dict(id=str(i), title='Same name', name=p.name, sha256=digest(p)))
    inv = tmp_path / 'sources.json'
    inv.write_text(json.dumps(rows))
    out = tmp_path / 'sampler'
    report = build(inv, out, .5)
    pcm, rate = sf.read(out / report['audio'])
    assert report['songs'] == 2 and report['duration_seconds'] == 1
    assert [c['drive_file_id'] for c in report['clips']] == ['0', '1']
    for clip, row in zip(report['clips'], rows):
        original, _ = sf.read(tmp_path / row['name'])
        a, b = clip['source_start_sample'], clip['source_end_sample']
        sa, sb = clip['sampler_start_sample'], clip['sampler_end_sample']
        # Boundary fades are documented; untouched interiors match decoded PCM.
        np.testing.assert_allclose(pcm[sa + 1000:sb - 1000], original[a + 1000:b - 1000], atol=2e-7)
    assert rate == 44100 and digest(out / report['audio']) == report['audio_sha256']


def test_mismatched_source_hash_rejected_before_sampler_publication(tmp_path):
    p = tmp_path / 'song.wav'
    sf.write(p, np.ones(1000), 1000)
    inv = tmp_path / 'sources.json'
    inv.write_text(json.dumps([dict(id='a', name=p.name, sha256='0' * 64)]))
    with pytest.raises(ValueError, match='hash mismatch'):
        build(inv, tmp_path / 'out', .5)
    assert not (tmp_path / 'out/Helix_Starred_All_Songs.wav').exists()


def test_late_mallet_event_keeps_full_song_clock():
    from music.review_score import pitched_roles
    candidates = [dict(start_ms=120000, midi=72, concentration=.8,
                       decay_ratio=2, vocal_similarity=0)]
    _, events, _ = pitched_roles([], [], candidates, np.ones(5120), [], duration=256)
    assert len(events) == 1
    assert events[0].start == 120 and events[0].end == 120.12


def test_review_setup_uses_decoded_audio_duration(tmp_path, monkeypatch):
    from tools import render_approval_revision as review
    source = tmp_path/'sources/sampler'
    source.mkdir(parents=True)
    sf.write(source/'audio.wav', np.zeros(1000), 1000)
    (tmp_path/'sources/selected_excerpts.json').write_text(json.dumps([
        dict(excerpt_id='sampler', filename='Sampler')]))
    captured = {}
    def performer(row, scene, analysis):
        captured.update(row)
        return object()
    monkeypatch.setattr(review, 'ReviewBandPerformance', performer)
    review.setup(tmp_path, 'sampler', scene_factory=lambda layout: object())
    assert captured['duration'] == 1
