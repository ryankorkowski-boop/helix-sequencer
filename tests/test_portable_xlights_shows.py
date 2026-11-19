"""Portability, preservation and launch regressions for standalone shows."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET

import pytest

from tools import prepare_portable_xlights_shows as portable
from tools.launch_portable_xlights import launch_commands
from tools import launch_portable_xlights as launcher
from tools.verify_portable_xlights_native import audit


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    repository = tmp_path / "repo"
    (repository / "xlights").mkdir(parents=True)
    (repository / "xlights/effect_catalog.json").write_text(json.dumps({"effect_names": ["On"]}))
    (repository / "tools").mkdir()
    shutil.copy2(portable.ROOT / "tools/launch_portable_xlights.py", repository / "tools/launch_portable_xlights.py")
    names = ["Helix_Aurora", "Helix_Neon_Circuit", "Helix_Enchanted_Grove", "Helix_Celestial_Orrery",
             "Helix_Fire_and_Ice", "Helix_Crystal_Lagoon", "Helix_Midnight_Masquerade"]
    tracks = ["Wire_Tree", "Tinsel_Sawtooth", "Frostbitten_Fingerboard", "Holly_Steel_Run", "Bell_Circuit_Carol"]
    batch = tmp_path / "batch"
    rows = []
    for name in names:
        source = repository / "showcase" / ("" if name == "Helix_Aurora" else "flavors") / name
        source.mkdir(parents=True)
        (source / "assets").mkdir()
        (source / "assets/picture.png").write_bytes(b"picture")
        (source / "models").mkdir()
        (source / "xlights_rgbeffects.xml").write_text(
            '<xrgb><models><model name="PROP" Image="assets/picture.png"><subModel name="PART" /></model></models>'
            '<modelGroups><modelGroup name="GROUP" models="PROP/PART" /></modelGroups></xrgb>')
        (source / "xlights_networks.xml").write_text("<Networks />")
        sequence = ('<xsequence><head><sequenceType>Animation</sequenceType><sequenceDuration>1.250</sequenceDuration>'
                    '<mediaFile /></head><ColorPalettes><ColorPalette>red</ColorPalette></ColorPalettes>'
                    '<EffectDB><Effect>E_FILEPICKER_Pictures_Filename=assets/picture.png</Effect></EffectDB>'
                    '<ElementEffects><Element type="model" name="PROP"><SubModelEffectLayer name="PART">'
                    '<Effect name="On" startTime="1000" endTime="1250" ref="0" palette="0" />'
                    '</SubModelEffectLayer></Element></ElementEffects></xsequence>')
        (source / f"{name}_Showcase.xsq").write_text(sequence)
        if name == "Helix_Aurora":
            continue
        for track in tracks:
            folder = batch / "shows" / track / name
            folder.mkdir(parents=True)
            shutil.copy2(source / "xlights_rgbeffects.xml", folder / "xlights_rgbeffects.xml")
            audio = (track + ".mp3")
            (folder / audio).write_bytes(track.encode())
            xsq = track + "__" + name + ".xsq"
            root = ET.fromstring(sequence)
            root.find("head/sequenceType").text = "Media"
            root.find("head/mediaFile").text = audio
            ET.ElementTree(root).write(folder / xsq)
            rows.append({"folder": str(folder.relative_to(batch)), "xsq": xsq, "audio": audio,
                         "track": track, "title": track, "duration_seconds": 1.25,
                         "audio_sha256": hashlib.sha256(track.encode()).hexdigest()})
    (batch / "batch_manifest.json").write_text(json.dumps({"runs": rows}))
    monkeypatch.setattr(portable, "ROOT", repository)
    return repository, batch, tmp_path / "Delivery With Spaces"


def test_seven_shows_are_self_contained_after_relocation(inputs, tmp_path):
    repository, batch, output = inputs
    baseline = {str(p.relative_to(repository)): p.read_bytes() for p in repository.rglob("*") if p.is_file()}
    report = portable.prepare(batch, output)
    assert len(report["shows"]) == 7 and report["full_song_sequences"] == 30 and report["lighting_studies"] == 7
    relocated = tmp_path / "another drive" / "moved delivery"
    shutil.copytree(output, relocated)
    for show in report["shows"]:
        folder = relocated / show["folder"]
        for seq in show["sequences"]:
            kwargs = {"duration": seq["duration_seconds"], "audio_hash": seq["audio_sha256"]} if seq["kind"] == "full_song" else {}
            assert portable.validate_sequence(folder, folder / seq["file"], **kwargs)["references_resolve"]
        assert (folder / "media").is_dir()
    for name, content in baseline.items():
        assert (repository / name).read_bytes() == content
    portable.package(output, tmp_path / "delivery.zip")


def test_different_layout_for_one_song_is_rejected(inputs):
    _, batch, output = inputs
    path = batch / "shows/Wire_Tree/Helix_Fire_and_Ice/xlights_rgbeffects.xml"
    path.write_text(path.read_text().replace('name="PROP"', 'name="WRONG"'))
    with pytest.raises(ValueError, match="physical model nodes"):
        portable.prepare(batch, output)


def test_package_excludes_automatic_xlights_startup_backups(inputs, tmp_path):
    _, batch, output = inputs
    report = portable.prepare(batch, output)
    folder = output / report["default_show"]
    backup = folder / "Backup/OnStart"
    backup.mkdir(parents=True)
    shutil.copy2(folder / report["default_sequence"], backup / report["default_sequence"])
    archive = tmp_path / "delivery.zip"
    portable.package(output, archive)
    with zipfile.ZipFile(archive) as z:
        assert sum(n.endswith(".xsq") for n in z.namelist()) == 37
        assert not any("/Backup/" in n for n in z.namelist())


def test_missing_media_and_non_native_effects_are_rejected(inputs):
    _, batch, output = inputs
    report = portable.prepare(batch, output)
    show = next(s for s in report["shows"] if s["folder"] == "Helix_Fire_and_Ice")
    folder = output / show["folder"]
    seq = next(s for s in show["sequences"] if s["kind"] == "full_song")
    media = folder / seq["media"]
    media.unlink()
    with pytest.raises(ValueError, match="Missing or external"):
        portable.validate_sequence(folder, folder / seq["file"], duration=1.25, audio_hash=seq["audio_sha256"])
    demo = folder / "Helix_Fire_and_Ice_Showcase.xsq"
    tree = ET.parse(demo)
    tree.getroot().find("ElementEffects/Element/SubModelEffectLayer/Effect").set("name", "Ramp")
    tree.write(demo)
    with pytest.raises(ValueError, match="Non-native effect"):
        portable.validate_sequence(folder, demo)


def test_external_paths_and_overwrite_are_rejected(inputs):
    _, batch, output = inputs
    portable.prepare(batch, output)
    with pytest.raises(FileExistsError):
        portable.prepare(batch, output)
    for value in ("/etc/passwd", "C:\\outside.mp3", "../outside.mp3"):
        with pytest.raises(ValueError):
            portable.resolve_local(output, value)


def test_render_and_desktop_commands_preserve_spaced_paths_and_leave_gui_open(inputs):
    _, batch, output = inputs
    report = portable.prepare(batch, output)
    render, desktop = launch_commands(Path("/Application With Spaces/xLights"), output,
                                      report["default_show"], report["default_sequence"])
    assert "--headless" in render and "--headless" not in desktop and "-r" not in desktop
    assert desktop[-1] == str((output / report["default_show"] / report["default_sequence"]).resolve())
    assert all(flag not in desktop for flag in ("-o", "--on", "-w", "--wipe"))
    with pytest.raises(ValueError, match="inside"):
        launch_commands(Path("xLights"), output, report["default_show"], "../README.txt")


def test_launcher_rejects_stale_or_partial_native_output_before_opening(inputs, monkeypatch):
    _, batch, output = inputs
    report = portable.prepare(batch, output)
    folder = output / report["default_show"]
    fseq = (folder / report["default_sequence"]).with_suffix(".fseq")
    header = bytearray(32)
    header[:4] = b"PSEQ"
    header[18] = 50
    struct.pack_into("<I", header, 14, 25)
    fseq.write_bytes(header)
    monkeypatch.setenv("DISPLAY", ":99")
    monkeypatch.setattr(launcher, "find_xlights", lambda explicit: Path("/fake/xLights"))
    monkeypatch.setattr(sys, "argv", ["launch_xlights.py", "--root", str(output)])
    monkeypatch.setattr(launcher.subprocess, "run", lambda *args, **kwargs: None)
    def unexpected_desktop(*args, **kwargs):
        pytest.fail("Desktop must not open after an invalid native render")
    monkeypatch.setattr(launcher.subprocess, "Popen", unexpected_desktop)
    with pytest.raises(RuntimeError, match="did not update"):
        launcher.main()
    fseq.unlink()
    def partial_render(*args, **kwargs):
        struct.pack_into("<I", header, 14, 2)
        fseq.write_bytes(header)
    monkeypatch.setattr(launcher.subprocess, "run", partial_render)
    with pytest.raises(RuntimeError, match="complete sequence"):
        launcher.main()


def test_native_audit_allows_trimmed_dark_controls_but_requires_every_rgb_channel(tmp_path):
    folder = tmp_path / "Show"
    folder.mkdir()
    (folder / "song.xsq").write_text("<xsequence />")
    (folder / "xlights_rgbeffects.xml").write_text("<xrgb />")
    models = [{"name": "RGB", "kind": "pixel", "start_channel": 1, "end_channel": 3},
              {"name": "CONTROL", "kind": "control", "start_channel": 4, "end_channel": 5}]
    (folder / "showcase_manifest.json").write_text(json.dumps({"models": models}))
    header = bytearray(32)
    header[:4] = b"PSEQ"
    struct.pack_into("<H", header, 4, 32)
    header[7] = 2
    struct.pack_into("<H", header, 8, 32)
    struct.pack_into("<II", header, 10, 3, 2)
    header[18] = 50
    (folder / "song.fseq").write_bytes(header + bytes([1, 2, 3, 4, 5, 6]))
    proof = audit(folder, {"file": "song.xsq", "duration_seconds": .1})
    assert proof["control_channels_dark"] and proof["implicit_zero_trailing_controls"] == ["CONTROL"]
    models[0]["end_channel"] = 4
    (folder / "showcase_manifest.json").write_text(json.dumps({"models": models}))
    with pytest.raises(ValueError, match="declared model channels"):
        audit(folder, {"file": "song.xsq", "duration_seconds": .1})
