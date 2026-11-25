import pytest

from models.nine_panel_showcase import NAMES, build


def test_nine_panel_order():
    assert len(NAMES) == 9
    assert NAMES[4] == 'Canonical snowman band'
    assert NAMES[5:] == ('Fire & Ice', 'Celestial Orrery', 'Quantum City', 'Infinite Kingdom')


@pytest.mark.parametrize('number,channels', [(1, 16), (2, 256)])
def test_legacy_ac_budget(number, channels):
    garden, band = build(number, {}, duration=30)
    assert band is None
    assert sum(model.channels for model in garden.models) == channels


@pytest.mark.parametrize('number', [3, 4, 6, 7, 8, 9])
def test_distinct_native_geometry(number):
    garden, band = build(number, {}, duration=30)
    assert band is None
    assert len(garden.models) > 0
    assert len({m.name for m in garden.models}) == len(garden.models)
    assert all(len(m.points) and m.channels > 0 for m in garden.models)
    assert all(m.start >= 1 for m in garden.models)
    if number == 4:
        assert any(m.details.get('generic_singer') for m in garden.models)
    if number == 9:
        assert len({m.zone for m in garden.models if 'DISTRICT' in m.zone}) >= 8
