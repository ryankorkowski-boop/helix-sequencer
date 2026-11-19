from pathlib import Path
import pytest
from tools import render_approval_collection as collection


def test_incomplete_caption_export_does_not_replace_existing_review_video(tmp_path, monkeypatch):
    source = tmp_path/'source.mp4'
    source.write_bytes(b'input')
    target = tmp_path/'review.mp4'
    target.write_bytes(b'previous complete review')
    def interrupted_export(args):
        Path(args[-1]).write_bytes(b'\0\0\0 ftypisom\0\0\0\0mdat')
    monkeypatch.setattr(collection, 'command', interrupted_export)
    with pytest.raises(RuntimeError):
        collection.label(source, target, 'Review')
    assert target.read_bytes() == b'previous complete review'
    assert not list(tmp_path.glob('.label-*.mp4'))
