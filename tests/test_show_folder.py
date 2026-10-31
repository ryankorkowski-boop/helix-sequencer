import xml.etree.ElementTree as ET
import pytest
from core.show_folder import prepare_show_folder


def test_prepare_show_folder_copies_without_modifying_sources(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    layout = source / "xlights_rgbeffects.xml"
    layout.write_text("<xrgb><models/></xrgb>", encoding="utf-8")
    audio = source / "song.mp3"
    audio.write_bytes(b"sample audio")
    result = prepare_show_folder(str(layout), str(audio), str(tmp_path / "show"))
    assert (tmp_path / "show" / "xlights_rgbeffects.xml").read_bytes() == layout.read_bytes()
    assert (tmp_path / "show" / "song.mp3").read_bytes() == audio.read_bytes()
    assert result["audio_file"].endswith("song.mp3")


def test_refuse_overwrite(tmp_path):
    layout = tmp_path / "layout.xml"
    layout.write_text("<xrgb/>")
    audio = tmp_path / "song.mp3"
    audio.write_bytes(b"a")
    show = tmp_path / "show"
    show.mkdir()
    (show / "song.mp3").write_bytes(b"other")
    with pytest.raises(FileExistsError):
        prepare_show_folder(str(layout), str(audio), str(show))


def test_invalid_backup_rejected(tmp_path):
    layout = tmp_path / "backup.xbkp"
    layout.write_bytes(b"not XML")
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"wav")
    with pytest.raises(ValueError, match="restore"):
        prepare_show_folder(str(layout), str(audio), str(tmp_path / "show"))
