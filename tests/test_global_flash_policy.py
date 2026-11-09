import pytest

from core.global_flash_policy import allows_global_flash


@pytest.mark.parametrize('guard', [0, 0.35, 0.8, 0.999])
def test_guard_preserves_existing_caller_gates_below_one(guard):
    assert allows_global_flash(0, guard)


@pytest.mark.parametrize('guard', [1.0, 1.5])
def test_full_guard_disables_every_color_and_drop(guard):
    assert not allows_global_flash(10000, guard, 100)


@pytest.mark.parametrize('cap', [0, -1])
def test_nonpositive_cap_disables_flashes(cap):
    assert not allows_global_flash(0, 0.8, cap)


def test_one_cooldown_across_all_colors():
    accepted = []
    results = []
    for color, time in [('red', 0), ('green', 100), ('white', 200), ('green', 500), ('white', 600)]:
        allowed = allows_global_flash(time, 0.8, 2, accepted)
        results.append((color, allowed))
        if allowed:
            accepted.append(time)
    assert results == [('red', True), ('green', False), ('white', False), ('green', True), ('white', False)]
    assert accepted == [0, 500]


def test_spacing_checks_both_sides_of_out_of_order_request_without_mutation():
    history = [2000, 0, 1000]
    assert not allows_global_flash(1499, 0.8, 2, history)
    assert not allows_global_flash(1501, 0.8, 2, history)
    assert allows_global_flash(1500, 0.8, 2, history)
    assert not allows_global_flash(1000, 0.8, 2, history)
    assert history == [2000, 0, 1000]


@pytest.mark.parametrize('cap,spacing', [(1, 1000), (4, 250), (0.5, 2000), (3, 1000 / 3)])
def test_configurable_spacing_including_fractional_caps(cap, spacing):
    assert not allows_global_flash(spacing - 0.001, 0.8, cap, [0])
    assert allows_global_flash(spacing, 0.8, cap, [0])


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_nonfinite_inputs_are_rejected(value):
    assert not allows_global_flash(value, 0.8)
    assert not allows_global_flash(0, value)
    assert not allows_global_flash(0, 0.8, value)
