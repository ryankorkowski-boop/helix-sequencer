import pytest
from models.progressive_showcase import build_progressive, RED, WHITE, GREEN


@pytest.mark.parametrize('level,count', [(0, 64), (1, 128)])
def test_ac_layout_uses_real_single_color_circuits(level, count):
    g = build_progressive(level)
    assert sum(m.channels for m in g.models) == count
    assert {m.colors[0] for m in g.models} == {RED, WHITE, GREEN}
    for m in g.models:
        assert m.kind == 'ac' and m.channels <= 16
        circuits = {int(e.split(',')[0]) for e in m.attrs['CustomModelCompressed'].split(';')}
        assert circuits == set(range(1, m.channels + 1))
        assert all(len(nodes) == 1 for nodes in m.submodels.values())


def test_layout_complexity_increases_in_models_and_addressable_channels():
    shows = [build_progressive(i) for i in range(6)]
    metrics = [(len(g.models), sum(m.channels for m in g.models)) for g in shows]
    assert all(a[0] < b[0] and a[1] < b[1] for a, b in zip(metrics, metrics[1:]))
    assert any(m.details.get('moire') for m in shows[4].models)
    assert any(m.details.get('forced_perspective') for m in shows[5].models)
    assert not any(m.details.get('review_role') == 'xylophone' for g in shows for m in g.models)
