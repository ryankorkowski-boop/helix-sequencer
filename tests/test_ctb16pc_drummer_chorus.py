from core.ctb16pc_drummer_chorus import (
    ctb16pc_drummer_chorus_patch, active_mouth_circuit,
)


def test_exactly_sixteen_outputs():
    rows = ctb16pc_drummer_chorus_patch()
    assert len(rows) == 16
    assert [r["circuit"] for r in rows] == list(range(1, 17))
    assert [r["function"] for r in rows[10:]] == [
        "MOUTH_AH", "MOUTH_EE", "MOUTH_OH",
        "MOUTH_MBP", "MOUTH_FV", "MOUTH_L",
    ]


def test_chorus_mouth_only_with_backing_vocals():
    assert active_mouth_circuit(chorus=False, vocal_layers=1, detected_phoneme="AH") is None
    assert active_mouth_circuit(chorus=False, vocal_layers=3, detected_phoneme="AH") == 11
    assert active_mouth_circuit(chorus=True, vocal_layers=2, detected_phoneme="L") == 16
    assert active_mouth_circuit(chorus=True, vocal_layers=3, detected_phoneme="REST") is None
    assert active_mouth_circuit(chorus=True, vocal_layers=3, detected_phoneme="UNKNOWN") is None
