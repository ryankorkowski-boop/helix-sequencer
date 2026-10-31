"""Reject changed native inputs and incompatible/incomplete phone videos."""
import hashlib
import subprocess

import pytest

from tools.render_portable_xlights_previews import assert_inputs, inspect_movie


def test_preview_rejects_changed_verified_fseq_and_soundtrack(tmp_path):
    folder = tmp_path / 'Show'
    folder.mkdir()
    files = {'xsq_sha256': 'Song.xsq', 'fseq_sha256': 'Song.fseq',
             'layout_sha256': 'xlights_rgbeffects.xml'}
    native = {'all_rgb_models_active': True, 'control_channels_dark': True}
    for key, name in files.items():
        (folder / name).write_bytes(name.encode())
        native[key] = hashlib.sha256(name.encode()).hexdigest()
    (folder / 'song.mp3').write_bytes(b'original recording')
    sequence = {'file': 'Song.xsq', 'media': 'song.mp3', 'native_verification': native,
                'audio_sha256': hashlib.sha256(b'original recording').hexdigest()}
    show = {'folder': 'Show'}
    assert assert_inputs(tmp_path, show, sequence)['fseq_sha256'] == native['fseq_sha256']
    (folder / 'Song.fseq').write_bytes(b'superseded rendering')
    with pytest.raises(ValueError, match='Verified native input changed'):
        assert_inputs(tmp_path, show, sequence)
    (folder / 'Song.fseq').write_bytes(b'Song.fseq')
    (folder / 'song.mp3').write_bytes(b'wrong song')
    with pytest.raises(ValueError, match='Soundtrack differs'):
        assert_inputs(tmp_path, show, sequence)


def make_movie(path, *, audio=True, faststart=True):
    command = ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=64x64:rate=20']
    if audio:
        command += ['-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-c:a', 'aac']
    command += ['-t', '1', '-c:v', 'libx264', '-threads', '1', '-pix_fmt', 'yuv420p']
    if faststart:
        command += ['-movflags', '+faststart']
    subprocess.run(command + [str(path)], check=True)


def test_phone_video_checks_actual_audio_duration_and_complete_decode(tmp_path):
    movie = tmp_path / 'phone.mp4'
    make_movie(movie)
    assert inspect_movie(movie, 1, True)['complete_decode_passed']
    with pytest.raises(ValueError, match='dropped frames or has incorrect duration'):
        inspect_movie(movie, 2, True)
    with pytest.raises(ValueError, match='soundtrack stream'):
        inspect_movie(movie, 1, False)


def test_phone_video_rejects_missing_audio_and_late_stream_index(tmp_path):
    movie = tmp_path / 'silent.mp4'
    make_movie(movie, audio=False)
    with pytest.raises(ValueError, match='soundtrack stream'):
        inspect_movie(movie, 1, True)
    assert inspect_movie(movie, 1, False)['faststart']
    late_index = tmp_path / 'late.mp4'
    make_movie(late_index, faststart=False)
    with pytest.raises(ValueError, match='optimized for streaming'):
        inspect_movie(late_index, 1, True)
