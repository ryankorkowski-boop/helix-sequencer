import pytest

from models import nine_panel_showcase as catalog


def test_nine_panel_order_and_source_features():
    assert catalog.NAMES == (
        '16-channel LOR AC', 'Original 256-channel AC', 'RGB-heavy house',
        'House with coro singing faces', 'Canonical six-snowman band',
        'Fire & Ice singing trees and matrices', 'Advanced 3D spatial matrix',
        'Sequential keyboard-driven groups', 'Ultimate xLights showcase',
    )
    gardens = {number: catalog.build(number, {}, duration=30)[0]
               for number in (3, 4, 6, 7, 8, 9)}
    assert any(model.name.endswith('GARAGE_MATRIX') for model in gardens[3].models)
    assert sum(model.details.get('generic_singer') is not None for model in gardens[4].models) == 2
    assert sum(model.zone == 'SINGING_TREES' for model in gardens[6].models) == 2
    assert sum(model.zone == 'MATRICES' for model in gardens[6].models) >= 2
    planes = [model for model in gardens[7].models if model.zone == 'THREE_D_GRID']
    assert len(planes) == 9
    assert len({round(float(model.points[:, 2].mean())) for model in planes}) >= 3
    ruler = next(model for model in gardens[8].models if model.details.get('keyboard_pitch_rungs'))
    assert all(f'KEY_MIDI_{note:03d}' in ruler.submodels for note in range(21, 109))
    assert all(model.details.get('musical_role') == 'keyboardist'
               for model in gardens[8].models if model.zone == 'MATRICES')
    assert len({model.zone for model in gardens[9].models if 'DISTRICT' in model.zone}) >= 8


@pytest.mark.parametrize(('number', 'channels'), [(1, 16), (2, 252)])
def test_locked_legacy_channel_budgets(number, channels):
    garden, band = catalog.build(number, {}, duration=30)
    assert band is None
    assert sum(model.channels for model in garden.models) == channels
    starts = sorted(model.start for model in garden.models)
    if number == 1:
        assert starts == list(range(1, channels + 1))
    else:
        from tools.build_source_ac_review import ACTIVE_AC_CHANNELS
        assert starts == sorted(ACTIVE_AC_CHANNELS)


def test_middle_cell_uses_canonical_six_snowmen(monkeypatch):
    calls = []
    plan = {'cues': {}}
    band = object()

    def canonical(garden, source, **options):
        calls.append((garden.title, source, options))
        return band

    monkeypatch.setattr(catalog, 'canonical_owner_band', canonical)
    assert catalog.build(5, plan, duration=30)[1] is band
    assert calls == [('Canonical six-snowman band', plan, {'duration': 30, 'native_extended_mouths': False})]
