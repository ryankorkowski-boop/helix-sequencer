import numpy as np
from models.infinite_symphony_showcase import build_megagarden, mega_manifest


def test_full_layout_footprint_and_all_88_disjoint_physical_rungs():
    garden = build_megagarden(); manifest = mega_manifest(garden)
    assert 6 <= manifest['footprint_ratio_xz'] <= 10
    assert manifest['house_count'] >= 12
    assert all(n >= 3 for n in manifest['coverage'].values())
    hero = garden.models[-1]
    rungs = [set(hero.submodels[f'KEY_MIDI_{n:03d}']) for n in range(21, 109)]
    assert all(rungs) and sum(map(len, rungs)) == len(set.union(*rungs))
    heights = [np.mean(hero.points[[node-1 for node in ids], 1]) for ids in rungs]
    assert all(a < b for a, b in zip(heights, heights[1:]))
    assert all(a.start+a.channels == b.start for a, b in zip(garden.models,garden.models[1:]))
    assert len(manifest['band_stages']) == 2
    assert all(stage['performers'] == 6 and stage['unified_pitched_performer'] for stage in manifest['band_stages'])
    band = [m for m in garden.models if m.details.get('final_band_role')]
    assert len(band) == 12
    for prefix in ('HX_BETA_STAGE_A', 'HX_BETA_STAGE_B'):
        members = [m for m in band if m.details['stage'] == prefix]
        assert {m.details['final_band_role'] for m in members} == {'drummer','bass','guitar','lead','harmony','piano'}
        keyboard = next(m for m in members if m.details['final_band_role'] == 'piano')
        assert all(keyboard.submodels[f'NOTE_MIDI_{p}'] for p in range(48,85))
        assert keyboard.submodels.get('ARM_LEFT_IDLE') and keyboard.submodels.get('ARM_RIGHT_IDLE')
        notes=set().union(*(set(v) for k,v in keyboard.submodels.items() if k.startswith('NOTE_MIDI_')))
        assert notes and not notes & set(keyboard.submodels['BODY'])
        for singer in [m for m in members if m.details['final_band_role'] in ('lead','harmony')]:
            mouths = set().union(*(set(v) for k,v in singer.submodels.items() if k.startswith('MOUTH_')))
            assert not mouths & set(singer.submodels['BODY'])
