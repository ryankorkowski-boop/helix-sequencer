import pytest
from tools.build_sampler_technical_pilot import build


def test_wrong_sampler_is_rejected_before_any_output_or_analysis_read(tmp_path):
    audio=tmp_path/'sampler.mp3';audio.write_bytes(b'another montage')
    output=tmp_path/'shows'
    with pytest.raises(ValueError,match='substitution refused'):
        build(audio,tmp_path/'missing-analysis',tmp_path/'missing-provenance',output)
    assert not output.exists()
