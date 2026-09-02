from core.wadena_spatial_intent import SpatialGesture, compile_temporal_gesture
from core.wadena_spatial_propagation import PropagationProfile


def test_explicit_temporal_gesture_uses_route():
    samples = compile_temporal_gesture(
        SpatialGesture(
            start="LEFT_TREE",
            end="RIGHT_LINDEN",
            strength=0.75,
        ),
        profile=PropagationProfile(travel_s=0.2),
    )
    assert tuple(sample.landmark for sample in samples) == (
        "LEFT_TREE",
        "BLVD_LEFT",
        "BLVD_CENTER",
        "BLVD_RIGHT",
        "RIGHT_LINDEN",
    )
    assert samples[-1].arrival_s == 0.8
    assert samples[0].weight == 0.75


def test_directional_temporal_gesture_uses_direction_order():
    samples = compile_temporal_gesture(
        SpatialGesture(direction="center_out", strength=0.6),
        profile=PropagationProfile(travel_s=0.1),
    )
    assert samples[0].landmark == "WREATH"
    assert samples[0].arrival_s == 0.0
    assert all(
        left.arrival_s <= right.arrival_s
        for left, right in zip(samples, samples[1:])
    )


def test_partial_explicit_route_fails_safe():
    assert compile_temporal_gesture(SpatialGesture(start="WREATH")) == ()
    assert compile_temporal_gesture(SpatialGesture(end="WREATH")) == ()
