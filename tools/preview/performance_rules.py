"""Rules translating instruments into performer actions."""


DEFAULT_RULES = {
    "kick": "drum_hit",
    "snare": "snare_hit",
    "bass": "bass_move",
    "melody": "play_pose",
    "beat": "pulse",
    "onset": "accent",
}



def action_for_instrument(instrument: str) -> str:
    return DEFAULT_RULES.get(instrument, "idle")
