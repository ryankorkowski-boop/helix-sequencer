import pytest

from helix_style.palette_chooser import (STRATEGIES, SectionPalette, SongFeatures, choose_palette,
                                         lyric_anchors, song_features_from_plan)


def features(**kw):
    base = dict(tempo_bpm=144.2, intensity=.62, key='A minor',
                sections=[dict(label='INTRO', energy=.2), dict(label='CHORUS', energy=.9)],
                lyrics='Tinsel tornado gold swans snowman on the mailbox drop the lights rainbow'.split())
    base.update(kw)
    return SongFeatures(**base)


def test_every_strategy_gives_distinct_palettes_with_rationale():
    seen = set()
    for strategy in STRATEGIES:
        d = choose_palette(features(), strategy)
        assert all(c.startswith('#') and len(c) == 7 for c in d.palette)
        assert d.rationale and d.inputs_used['tempo_bpm'] == 144.2
        seen.add(d.palette)
    assert len(seen) == len(STRATEGIES)


def test_lyrics_drive_lyric_semantic_hues():
    d = choose_palette(features(), 'lyric_semantic')
    assert {'gold', 'tinsel', 'snowman'} & set(d.inputs_used['lyric_anchors'])
    assert any('lyric' in r for r in d.rationale)
    other = choose_palette(features(lyrics=['fire', 'fire', 'red']), 'lyric_semantic')
    assert other.palette != d.palette


def test_tempo_and_intensity_change_tempo_energy_strategy():
    slow = choose_palette(features(tempo_bpm=70, intensity=.2), 'tempo_energy')
    fast = choose_palette(features(tempo_bpm=170, intensity=.9), 'tempo_energy')
    assert slow.palette != fast.palette


def test_key_and_mode_change_key_mood():
    assert choose_palette(features(key='A minor'), 'key_mood').palette != \
        choose_palette(features(key='A major'), 'key_mood').palette


def test_section_energy_changes_section_palettes():
    d = choose_palette(features(), 'lyric_semantic')
    assert d.for_section('INTRO') != d.for_section('CHORUS')
    assert d.for_section('UNKNOWN') == d.palette
    p = SectionPalette(d)
    assert tuple(p) == d.palette and p.for_section('CHORUS') == d.for_section('CHORUS')


def test_missing_inputs_are_reported_not_invented():
    d = choose_palette(SongFeatures(), 'tempo_energy')
    assert any('intensity unavailable' in r for r in d.rationale)
    assert any('no section data' in r for r in d.rationale)
    with pytest.raises(ValueError):
        choose_palette(SongFeatures(), 'nope')


def test_features_from_plan_aggregates_repeated_parts():
    plan = {'debug': {'tempo_bpm': 144.231}, 'global_timeline': {'song_parts': [
        dict(name='verse', start_time=0, end_time=10, energy_level=.4),
        dict(name='chorus', start_time=10, end_time=20, energy_level=.8),
        dict(name='verse', start_time=20, end_time=30, energy_level=.6)]}}
    f = song_features_from_plan(plan, words=['gold'])
    assert f.tempo_bpm == 144.231
    assert {s['label']: round(s['energy'], 2) for s in f.sections} == {'VERSE': .5, 'CHORUS': .8}
    assert 0.55 < f.intensity < 0.65
    assert lyric_anchors(['Gold,', 'gold', 'snow']) [0][0] == 'gold'
