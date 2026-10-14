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
