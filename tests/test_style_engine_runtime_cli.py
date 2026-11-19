from core.effect_engine import parse_args, VARIANTS
from core.style_engine import get_style_profile, style_effect_contract


def test_style_flag_is_accepted():
    version = next(iter(VARIANTS))
    args = parse_args(VARIANTS[version], ["--music-style", "rock", "--no-prompt"])
    assert args.music_style == "rock"


def test_explicit_effect_override_remains_available():
    version = next(iter(VARIANTS))
    args = parse_args(VARIANTS[version], ["--music-style", "rock", "--base-effect", "On", "--no-prompt"])
    assert args.music_style == "rock"
    assert args.base_effect == "On"


def test_style_contract_supplies_native_effect_names():
    assert style_effect_contract(get_style_profile("orchestral"))["motion_effect"] == "Wave"
