from xml.etree import ElementTree as ET

from core.band_vocal_face_export import VocalPhonemeTiming
from core.xsq_emitter import emit_xsq_sequence


def test_independent_face_styles_in_xsq():
    import inspect
    sig = inspect.signature(VocalPhonemeTiming)
    # Keep this contract test resilient to optional timing metadata additions.
    def event(performer, phoneme, start):
        args = dict(performer=performer, phoneme=phoneme, start=start, duration=0.2, intensity=0.8)
        return VocalPhonemeTiming(**{k: v for k, v in args.items() if k in sig.parameters})
    seq = emit_xsq_sequence(
        timings=[event("lead", "AH", 1.0), event("harmony", "EE", 1.2)],
        sequence_name="face_styles",
        model_name="TestFace",
        performer_styles={"lead": "snowman_lead", "harmony": "snowman_harmony"},
    )
    root = ET.fromstring(seq.xml_text)
    phonemes = root.findall("./timingtrack/phoneme")
    assert len(phonemes) == 2
    assert phonemes[0].get("mouthShape") == "HX_SNOWMAN_SINGER_MOUTH_AH"
    assert phonemes[1].get("mouthShape") == "HX_SNOWMAN_SINGER_FEMALE_MOUTH_EE"
    assert [p.get("start") for p in phonemes] == ["1.000000", "1.200000"]
