from core.style_engine import STYLE_PROFILES, style_effect_contract


def test_all_style_profiles_have_effect_contracts():
    for profile in STYLE_PROFILES.values():
        contract = style_effect_contract(profile, energy=0.8)
        assert contract["style"] == profile.name
        assert contract["base_effect"]
        assert contract["motion_effect"]
        assert contract["accent_effect"]
        assert contract["palette"]
        assert 0 <= contract["density"] <= 1


def test_style_effect_contract_is_deterministic_and_energy_sensitive():
    profile = STYLE_PROFILES["rock"]
    assert style_effect_contract(profile, energy=0.5) == style_effect_contract(profile, energy=0.5)
    assert style_effect_contract(profile, energy=0.9)["density"] > style_effect_contract(profile, energy=0.1)["density"]
