"""Source verification stays content-exact without whole-recording buffers."""
import hashlib
from pathlib import Path

import pytest

from core.audio_run_cache import AudioRunCache


@pytest.mark.parametrize("size", [0, 17, 3 * 1024 * 1024 + 17])
def test_source_hash_is_verified_with_bounded_reads(tmp_path, monkeypatch, size):
    data = (b"helix-audio\x00\xff" * (size // 13 + 1))[:size]
    source = tmp_path / "song.wav"
    source.write_bytes(data)
    cache = AudioRunCache(hashlib.sha256(data).hexdigest())
    original_open = Path.open
    reads = []

    class BoundedReader:
        def __init__(self, file):
            self.file = file

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.file.close()

        def read(self, count=-1):
            assert 0 < count <= 1024 * 1024
            reads.append(count)
            return self.file.read(count)

    def guarded_open(path, mode="r", *args, **kwargs):
        file = original_open(path, mode, *args, **kwargs)
        return BoundedReader(file) if path == source and mode == "rb" else file

    monkeypatch.setattr(Path, "open", guarded_open)
    cache.validate_source(source)
    assert reads
    # Same filename, length and configuration must not conceal changed bytes.
    source.write_bytes((b"x" + data[1:]) if data else b"x")
    with pytest.raises(ValueError, match="different source recording"):
        cache.validate_source(source)
