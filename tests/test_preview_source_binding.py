"""Batch previews must bind each new sequence to its own actual soundtrack."""
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest

from core.sequence_builder import _preview_audio_for_sequence, _render_new_previews


def sequence(path, media=None):
    root = ET.Element('xsequence')
    head = ET.SubElement(root, 'head')
    if media is not None:
        ET.SubElement(head, 'mediaFile').text = media
    ET.ElementTree(root).write(path)
    return path


def test_batch_mux_and_provenance_use_each_sequence_media(tmp_path, monkeypatch):
    from core import sequence_builder
    from tools import preview_renderer
    import json

    songs = [tmp_path/'a.wav', tmp_path/'b.wav']
    for song in songs:
        song.write_bytes(b'soundtrack identity fixture')
    outputs = [sequence(tmp_path/f'{song.stem}.xsq', song.name) for song in songs]
    monkeypatch.setattr(sequence_builder, '_generated_sequence_paths', lambda *args: outputs)
    monkeypatch.setattr(preview_renderer, 'parse_models', lambda *args: object())
    seen = []

    def render(**kwargs):
        seen.append(kwargs['audio_path'])
        return kwargs['sequence_path'].with_suffix('.mp4')

    monkeypatch.setattr(preview_renderer, 'render_sequence_to_mp4', render)
    context = SimpleNamespace(record_artifact=lambda *args: None)
    _render_new_previews([], {}, ['--audio', *(str(p) for p in songs), '--single'],
                         tmp_path/'layout.xml', context)
    assert seen == songs
    for output, song in zip(outputs, songs):
        receipt = json.loads(output.with_suffix('.preview_provenance.json').read_text())
        assert Path(receipt['audio']) == song


def test_moved_show_uses_matching_original_input_or_packaged_relative_media(tmp_path):
    inputs = tmp_path/'inputs'
    inputs.mkdir()
    song = inputs/'song.wav'
    song.write_bytes(b'original fixture')
    xsq = sequence(tmp_path/'song.xsq', r'C:\old-show\song.wav')
    assert _preview_audio_for_sequence(xsq, [song]) == song
    media = tmp_path/'media'
    media.mkdir()
    packaged = media/'song.wav'
    packaged.write_bytes(song.read_bytes())
    sequence(xsq, 'media/song.wav')
    assert _preview_audio_for_sequence(xsq, [song]) == packaged


def test_ambiguous_or_mismatched_batch_never_uses_first_song(tmp_path):
    songs = [tmp_path/'a.wav', tmp_path/'b.wav']
    for song in songs:
        song.touch()
    xsq = sequence(tmp_path/'unknown.xsq')
    with pytest.raises(RuntimeError, match='per-sequence media identity'):
        _preview_audio_for_sequence(xsq, songs)
    sequence(xsq, 'missing.wav')
    with pytest.raises(RuntimeError, match='soundtrack could not be resolved'):
        _preview_audio_for_sequence(xsq, songs)
