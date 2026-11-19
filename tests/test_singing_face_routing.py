from core.singing_face_discovery import SingingFace
from core.singing_face_routing import route_singing_faces


def test_routes_existing_mouth_attributes():
    face = SingingFace("Tree", "Default", "NodeRange",
                       {"Mouth-AI": "1-3", "Mouth-MBP": "4-5", "Mouth-O": "6"}, "layout.xml")
    targets = route_singing_faces([face])
    assert len(targets) == 1
    assert targets[0].phoneme_keys["A"] == "Mouth-AI"
    assert targets[0].phoneme_keys["I"] == "Mouth-AI"
    assert targets[0].phoneme_keys["MBP"] == "Mouth-MBP"
    assert "FV" in targets[0].unresolved


def test_no_mouth_mapping_does_not_claim_singer():
    face = SingingFace("Tree", "Eyes", "NodeRange", {"Eyes-Open": "1-2"}, "layout.xml")
    assert route_singing_faces([face]) == []
