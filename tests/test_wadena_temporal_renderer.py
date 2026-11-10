from core.wadena_spatial_intent import SpatialGesture
from core.wadena_spatial_propagation import PropagationProfile, compile_direction_propagation
from core.wadena_temporal_renderer import (
    compile_ac_safe_events,
    render_gesture_at,
    render_samples_at,
    render_timeline,
)


def test_frame_is_dark_before_launch():
    profile = PropagationProfile(launch_s=1.0, travel_s=0.1, attack_s=0.1, decay_s=0.2)
    samples = compile_direction_propagation("left_to_right", profile=profile)
    assert render_samples_at(samples, 0.5, profile) == ()


def test_frame_follows_temporal_arrival_order():
    profile = PropagationProfile(travel_s=0.2, attack_s=0.0, decay_s=1.0)
    samples = compile_direction_propagation("left_to_right", profile=profile)
    first = render_samples_at(samples, 0.01, profile)
    later = render_samples_at(samples, 0.41, profile)
    assert len(first) >= 1
    assert len(later) >= len(first)
    assert [frame.order for frame in later] == sorted(frame.order for frame in later)


def test_render_gesture_compiles_and_samples():
    profile = PropagationProfile(travel_s=0.1, attack_s=0.0, decay_s=0.5)
    frame = render_gesture_at(SpatialGesture(direction="left_to_right"), 0.25, profile)
    assert frame
    assert all(0.0 <= item.intensity <= 1.0 for item in frame)


def test_ac_safe_event_compiler_rejects_unknown_effect():
    samples = compile_direction_propagation("left_to_right")
    events = compile_ac_safe_events(samples, effect="GalaxyPixelMorph")
    assert events
    assert {event.effect for event in events} == {"Level"}


def test_ac_safe_event_timing_matches_propagation():
    profile = PropagationProfile(launch_s=0.3, travel_s=0.2, attack_s=0.05, decay_s=0.25)
    samples = compile_direction_propagation("left_to_right", profile=profile)
    events = compile_ac_safe_events(samples, effect="Ramp")
    assert [event.start_s for event in events] == [sample.arrival_s for sample in samples]
    assert [event.end_s for event in events] == [sample.release_s for sample in samples]
    assert {event.effect for event in events} == {"Ramp"}


def test_timeline_is_deterministic_and_has_expected_frame_count():
    gesture = SpatialGesture(direction="left_to_right")
    a = render_timeline(gesture, 1.0, fps=20.0)
    b = render_timeline(gesture, 1.0, fps=20.0)
    assert a == b
    assert len(a) == 21


def test_negative_duration_fails_safe_to_single_zero_frame():
    timeline = render_timeline(SpatialGesture(), -5.0, fps=20.0)
    assert len(timeline) == 1
