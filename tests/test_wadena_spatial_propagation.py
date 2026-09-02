from core.wadena_spatial_graph import wadena_spatial_graph
from core.wadena_spatial_propagation import (
    PropagationProfile,
    compile_direction_propagation,
    compile_propagation,
    sample_weight_at,
)


def test_route_propagates_in_graph_order_with_monotonic_arrival_times():
    samples = compile_propagation(
        "LEFT_TREE",
        "RIGHT_LINDEN",
        profile=PropagationProfile(launch_s=1.0, travel_s=0.25),
    )

    assert tuple(sample.landmark for sample in samples) == (
        "LEFT_TREE",
        "BLVD_LEFT",
        "BLVD_CENTER",
        "BLVD_RIGHT",
        "RIGHT_LINDEN",
    )
    assert [sample.arrival_s for sample in samples] == [1.0, 1.25, 1.5, 1.75, 2.0]
    assert all(
        left.arrival_s <= right.arrival_s
        for left, right in zip(samples, samples[1:])
    )


def test_propagation_is_deterministic():
    profile = PropagationProfile(
        launch_s=0.37,
        travel_s=0.13,
        attack_s=0.04,
        decay_s=0.28,
        hop_decay=0.91,
    )
    first = compile_propagation("WREATH", "ROOF_SNOWFLAKE", 0.8, profile)
    second = compile_propagation("WREATH", "ROOF_SNOWFLAKE", 0.8, profile)
    assert first == second


def test_strength_is_clamped_and_hop_decay_is_applied():
    samples = compile_propagation(
        "WREATH",
        "ROOF_SNOWFLAKE",
        strength=4.0,
        profile=PropagationProfile(hop_decay=0.5),
    )
    assert [sample.weight for sample in samples] == [1.0, 0.5, 0.25]


def test_invalid_route_fails_safe():
    assert compile_propagation("NO_SUCH_LANDMARK", "WREATH") == ()
    assert compile_propagation("WREATH", "NO_SUCH_LANDMARK") == ()
    assert compile_propagation("WREATH", "ROOF_SNOWFLAKE", strength=-1.0) == ()


def test_zero_travel_is_allowed_without_negative_or_nonmonotonic_time():
    samples = compile_propagation(
        "WREATH",
        "ROOF_SNOWFLAKE",
        profile=PropagationProfile(travel_s=0.0),
    )
    assert [sample.arrival_s for sample in samples] == [0.0, 0.0, 0.0]
    assert all(sample.release_s >= sample.arrival_s for sample in samples)


def test_directional_propagation_uses_graph_order():
    graph = wadena_spatial_graph()
    samples = compile_direction_propagation("right_to_left", graph=graph)
    assert tuple(sample.landmark for sample in samples) == graph.order("right_to_left")
    assert [sample.order for sample in samples] == list(range(len(samples)))


def test_directional_unknown_direction_uses_deterministic_default_order():
    samples = compile_direction_propagation("not_a_real_direction")
    assert samples
    assert samples[0].landmark == "BLVD_LEFT"


def test_envelope_is_zero_before_arrival_and_peaks_then_decays():
    profile = PropagationProfile(attack_s=0.1, decay_s=0.4)
    sample = compile_propagation("WREATH", "ROOF_SNOWFLAKE", profile=profile)[0]

    assert sample_weight_at(sample, -0.01, profile) == 0.0
    assert sample_weight_at(sample, sample.arrival_s, profile) == 0.0
    assert sample_weight_at(sample, sample.arrival_s + 0.05, profile) == 0.5
    assert sample_weight_at(sample, sample.arrival_s + 0.1, profile) == 1.0
    assert sample_weight_at(sample, sample.arrival_s + 0.5, profile) < 1.0


def test_zero_duration_envelope_is_finite_and_safe():
    profile = PropagationProfile(attack_s=0.0, decay_s=0.0)
    sample = compile_propagation("WREATH", "ROOF_SNOWFLAKE", profile=profile)[0]
    assert sample_weight_at(sample, sample.arrival_s, profile) == 1.0
    assert sample_weight_at(sample, sample.arrival_s + 0.001, profile) == 0.0
