from __future__ import annotations


def map_drummer_parts(drum_events: dict[str, list[dict[str, object]]]) -> dict[str, str]:
    return {
        "kick_events": "kick",
        "snare_events": "snare",
        "tom_events": "tom",
        "hihat_events": "hi_hat",
        "cymbal_events": "cymbal",
    }
