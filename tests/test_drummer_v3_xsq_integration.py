from __future__ import annotations

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import DRUMMER_COMPONENTS, map_events_to_drummer_components, map_events_to_drummer_v3_poses


LEGACY_STICK_OR_ARM_TOKENS = ("LEFT_STICK", "RIGHT_STICK", "LEFT_ARM", "RIGHT_ARM")


def test_canonical_drummer_has_approved_eight_hit_composites() -> None:
    assert len(DRUMMER_COMPONENTS) == 8
    assert len(set(DRUMMER_COMPONENTS)) == 8
    assert "HX_SNOWMAN_DRUMMER_HIT_TOM_FLOOR" in DRUMMER_COMPONENTS
    assert not any("TOM_4" in name for name in DRUMMER_COMPONENTS)


def test_component_mapper_never_emits_independent_sticks_or_arms() -> None:
    events = [
        DrumEvent(0.1, 0.8, 0.7, {}, 1, "kick"),
        DrumEvent(0.2, 0.9, 0.8, {}, 2, "snare"),
        DrumEvent(0.3, 0.6, 0.7, {}, 3, "hihat"),
        DrumEvent(0.4, 0.7, 0.7, {}, 4, "tom"),
        DrumEvent(0.5, 0.7, 0.7, {}, 5, "tom"),
        DrumEvent(0.6, 0.7, 0.7, {}, 6, "tom"),
        DrumEvent(0.7, 1.0, 0.8, {}, 7, "cymbal"),
        DrumEvent(0.8, 0.8, 0.8, {}, 8, "cymbal"),
    ]
    mapped = map_events_to_drummer_components(events)
    components = [str(item["component"]) for item in mapped]
    assert set(components).issubset(set(DRUMMER_COMPONENTS))
    assert not any(any(token in component for token in LEGACY_STICK_OR_ARM_TOKENS) for component in components)
    assert components[0] == "HX_SNOWMAN_DRUMMER_HIT_KICK"
    assert components[1] == "HX_SNOWMAN_DRUMMER_HIT_SNARE"
    assert components[2] == "HX_SNOWMAN_DRUMMER_HIT_HI_HAT"
    assert components[3:6] == [
        "HX_SNOWMAN_DRUMMER_HIT_TOM_LEFT",
        "HX_SNOWMAN_DRUMMER_HIT_TOM_RIGHT",
        "HX_SNOWMAN_DRUMMER_HIT_TOM_FLOOR",
    ]
    assert components[6:8] == [
        "HX_SNOWMAN_DRUMMER_HIT_CYMBAL_LEFT",
        "HX_SNOWMAN_DRUMMER_HIT_CYMBAL_RIGHT",
    ]


def test_component_mapper_suppresses_ambiguous_bus_instead_of_faking_kick() -> None:
    mapped = map_events_to_drummer_components([
        DrumEvent(0.1, 0.8, 0.4, {}, 1, "drum_bus", source="test"),
    ])
    assert mapped == []


def test_v3_pose_adapter_uses_only_canonical_component_targets() -> None:
    events = [
        DrumEvent(0.1, 0.8, 0.7, {}, 1, "kick"),
        DrumEvent(0.2, 0.9, 0.8, {}, 2, "snare"),
        DrumEvent(0.3, 0.6, 0.7, {}, 3, "hihat"),
        DrumEvent(0.4, 0.7, 0.7, {}, 4, "tom"),
        DrumEvent(0.5, 1.0, 0.8, {}, 5, "cymbal"),
    ]
    mapped = map_events_to_drummer_v3_poses(events)
    for item in mapped:
        assert str(item["component"]) in DRUMMER_COMPONENTS
        assert all(token not in str(item["component"]) for token in LEGACY_STICK_OR_ARM_TOKENS)
        assert list(item["submodels"]) == [item["component"]]


def test_injection_helper_preserves_existing_xlights_effect_container() -> None:
    from tools.integrate_drummer_v3_into_xsq import _find_or_create_element_effects

    root = ET.fromstring("<xsequence><ElementEffects><Element type='model' name='Existing'/></ElementEffects></xsequence>")
    container = _find_or_create_element_effects(root)
    assert container is root.find("ElementEffects")
    assert [e.get("name") for e in container.findall("Element")] == ["Existing"]


def test_injector_uses_production_stem_analysis_path() -> None:
    from tools import integrate_drummer_v3_into_xsq as injector

    with tempfile.TemporaryDirectory() as tempdir:
        root = Path(tempdir)
        base = root / "base.xsq"
        output = root / "out.xsq"
        audio = root / "song.wav"
        cache = root / "stem-cache"
        base.write_text("<xsequence><ElementEffects/></xsequence>", encoding="utf-8")
        audio.write_bytes(b"fake-audio")

        streams = {
            "kick_events": [DrumEvent(0.1, 0.8, 0.9, {}, 1, "kick", source="demucs:drums")],
            "snare_events": [],
            "tom_events": [],
            "hihat_events": [],
            "cymbal_events": [],
            "drum_bus_events": [],
        }
        analysis = SimpleNamespace(
            source="demucs",
            stems={"drums": cache / "song" / "drums.wav"},
            drum_event_streams=streams,
        )
        with mock.patch.object(injector, "build_stem_analysis", return_value=analysis) as build:
            report = injector.inject_drummer_v3(
                base,
                output,
                audio,
                stem_cache_dir=cache,
            )

        build.assert_called_once()
        assert build.call_args.kwargs["audio_path"] == audio
        assert build.call_args.kwargs["cache_dir"] == cache
        assert report["stem_source"] == "demucs"
        assert report["detector_counts"]["kick_events"] == 1
        assert report["placement_count"] == 1
        tree = ET.parse(output)
        effects = tree.findall(".//Element[@name='HX_SNOWMAN_DRUMMER_HIT_KICK']/EffectLayer/Effect")
        assert len(effects) == 1
        assert effects[0].get("sourceDrumType") == "kick"


def test_injection_helper_creates_current_xlights_container_without_legacy_effects() -> None:
    from tools.integrate_drummer_v3_into_xsq import _find_or_create_element_effects

    root = ET.fromstring("<xsequence/>")
    container = _find_or_create_element_effects(root)
    assert container.tag == "ElementEffects"
    assert root.find("effects") is None
