from __future__ import annotations

from core.band_vocal_face_export import VocalPhonemeTiming
from core.xsq_emitter import emit_xsq_sequence



def _timing(start: float, phoneme: str = "AH") -> VocalPhonemeTiming:
    return VocalPhonemeTiming(
        performer="singer",
        phoneme=phoneme,
        start=start,
        duration=0.5,
        intensity=0.8,
    )



def test_emits_valid_structure():
    xsq = emit_xsq_sequence(
        timings=[_timing(0.0)],
        sequence_name="TestSeq",
        model_name="SingerFace",
    )

    assert "<xsequence" in xsq.xml_text
    assert "<timingtrack" in xsq.xml_text
    assert "<phoneme" in xsq.xml_text
    assert "<effects" in xsq.xml_text



def test_preserves_timing_values():
    xsq = emit_xsq_sequence(
        timings=[_timing(1.25)],
        sequence_name="TestSeq",
        model_name="SingerFace",
    )

    assert 'start="1.250000"' in xsq.xml_text
    assert 'duration="0.500000"' in xsq.xml_text



def test_deterministic_output():
    timings = [_timing(0.5), _timing(0.0)]

    first = emit_xsq_sequence(
        timings=timings,
        sequence_name="Seq",
        model_name="Face",
    )

    second = emit_xsq_sequence(
        timings=timings,
        sequence_name="Seq",
        model_name="Face",
    )

    assert first.xml_text == second.xml_text



def test_stable_ordering():
    timings = [_timing(1.0, "B"), _timing(0.0, "A")]

    xsq = emit_xsq_sequence(
        timings=timings,
        sequence_name="Seq",
        model_name="Face",
    )

    a_index = xsq.xml_text.find('phoneme="A"')
    b_index = xsq.xml_text.find('phoneme="B"')

    assert a_index < b_index
