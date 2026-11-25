import pytest
from tools.offline_karaoke_review import CONFIG, MODEL, local_descriptor, validate_files
from tools.phoneme_source import digest


def test_exact_local_model_pair(tmp_path):
    for name in (MODEL, CONFIG):
        (tmp_path/name).write_bytes(name.encode())
    expected = {name: digest(tmp_path/name) for name in (MODEL, CONFIG)}
    assert validate_files(tmp_path, expected) == tmp_path
    assert local_descriptor(tmp_path, MODEL)[1] == 'MDXC'
    with pytest.raises(ValueError, match='Unexpected'):
        local_descriptor(tmp_path, 'other.ckpt')
    with pytest.raises(ValueError, match='digests'):
        validate_files(tmp_path, {MODEL: expected[MODEL]})
    (tmp_path/CONFIG).write_text('changed')
    with pytest.raises(ValueError, match='checksum mismatch'):
        validate_files(tmp_path, expected)
