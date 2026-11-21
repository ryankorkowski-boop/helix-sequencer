from core.face_style_adapter import FACE_STYLES, render_phoneme_events, resolve_face_mapping
import pytest

def test_every_style_covers_all_phonemes():
    for style in FACE_STYLES:
        assert len(resolve_face_mapping(style)) == 7

def test_singer_timing_preserved_and_styles_differ():
    events = [{"singer_id": "lead", "start": 1.2, "end": 1.4, "phoneme": "AH"},
              {"singer_id": "harmony", "start": 1.3, "end": 1.5, "phoneme": "EE"}]
    lead = render_phoneme_events(events, style="snowman_lead")
    tree = render_phoneme_events(events, style="singing_tree")
    assert lead[0]["mouth_shape"] != tree[0]["mouth_shape"]
    for source, target in zip(events, lead):
        assert all(target[k] == v for k, v in source.items())
    assert "mouth_shape" not in events[0]

def test_incomplete_custom_mapping_fails_closed():
    with pytest.raises(ValueError):
        resolve_face_mapping("custom", {"AH": "open"})

def test_unknown_phoneme_fails_closed():
    with pytest.raises(ValueError):
        render_phoneme_events([{"phoneme": "UNKNOWN"}], style="coro")
