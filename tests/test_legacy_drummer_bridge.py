from legacy_ac.drummer_bridge import (
    DRUMMER_SUBMODEL_TO_CHANNEL,
    compile_drummer_v3_events_to_legacy,
    validate_legacy_drummer_reservation,
)


def test_drummer_bridge_uses_final_ten_legacy_channels():
    assert set(DRUMMER_SUBMODEL_TO_CHANNEL.values()) == set(range(247, 257))


def test_drummer_bridge_rejects_channel_collision():
    result = validate_legacy_drummer_reservation([1, 100, 247])
    assert not result["valid"]
    assert result["collisions"] == [247]


def test_drummer_v3_events_compile_to_legacy_channels():
    events = [
        {
            "timestamp_ms": 1000,
            "end_ms": 1150,
            "intensity": 0.8,
            "submodels": [
                "HX_SNOWMAN_DRUMMER_V3_HIT_KICK",
                "HX_SNOWMAN_DRUMMER_V3_HIT_HIHAT",
            ],
        }
    ]
    compiled = compile_drummer_v3_events_to_legacy(events)
    assert [event["channel_index"] for event in compiled] == [247, 249]
    assert all(event["source_kind"] == "drummer_v3_legacy_bridge" for event in compiled)
