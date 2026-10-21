"""Regression for direct LMS -> Helix virtual layout -> mapped LMS workflow."""
from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from tools.lor_lms_import import prepare_lms_workspace
from tools.lor_lms_export_from_source import export_lms_from_xsq
from tools.lor_compatibility import ac_layout_targets


def source(path: Path):
    path.write_text(
        '<?xml version="1.0"?><sequence saveFileVersion="14" musicFilename="original.wav">'
        '<channels>'
        '<channel name="Roof red" deviceType="LOR" unit="1" circuit="1" '
        'color="255" savedIndex="12" centiseconds="900">'
        '<effect type="intensity" startCentisecond="100" endCentisecond="160" intensity="100"/>'
        '</channel>'
        '<channel name="Roof green" deviceType="LOR" unit="1" circuit="2" '
        'color="65280" savedIndex="14" centiseconds="900"/>'
        '<channel name="Snowflake white" deviceType="LOR" unit="2" circuit="1" '
        'color="16777215" savedIndex="19" centiseconds="900"/>'
        '</channels>'
        '<timingGrids><timingGrid saveID="0" name="Old song grid" type="fixed" spacing="10"/></timingGrids>'
        '<tracks><track totalCentiseconds="900" timingGrid="0">'
        '<channels><channel savedIndex="12"/><channel savedIndex="14"/><channel savedIndex="19"/>'
        '</channels><loopLevels/></track></tracks>'
        '</sequence>', encoding="utf-8",
    )


def test_import_lms_keeps_real_addresses_and_generates_all_models(tmp_path: Path):
    original = tmp_path / "source.lms"
    source(original)
    untouched = original.read_bytes()
    workspace = tmp_path / "workspace"
    result = prepare_lms_workspace(original, workspace)
    assert original.read_bytes() == untouched
    assert len(result["channels"]) == 3
    assert [(x["unit"], x["circuit"], x["savedIndex"]) for x in result["channels"]] == [
        (1, 1, "12"), (1, 2, "14"), (2, 1, "19")
    ]
    safe, other, groups = ac_layout_targets(result["layout"])
    assert len(safe) == 3 and not other
    assert "01_ALL" in groups
    root = ET.parse(result["template"]).getroot()
    assert len(root.findall("./ElementEffects/Element[@type='model']")) == 3
    assert all(row.get("name") in safe for row in root.findall("./DisplayElements/Element"))
    layout = ET.parse(result["layout"]).getroot()
    assert all(model.get("ModelBrightness") == "0" for model in layout.findall("models/model"))


def test_direct_lms_export_reuses_real_controller_wiring(tmp_path: Path):
    original = tmp_path / "source.lms"
    source(original)
    imp = prepare_lms_workspace(original, tmp_path / "workspace")
    sequence = ET.parse(imp["template"])
    root = sequence.getroot()
    ET.SubElement(root.find("ColorPalettes"), "ColorPalette").text = (
        "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
    )
    root.find("./head/sequenceDuration").text = "3.5"
    root.find("./head/mediaFile").text = "mysong.wav"
    names = {c["name"]: c["model"] for c in imp["channels"]}
    row1 = next(e for e in root.findall("./ElementEffects/Element") if e.get("name") == names["Roof red"])
    layer1 = row1.find("EffectLayer")
    ET.SubElement(layer1, "Effect", {"name": "On", "startTime": "100",
                  "endTime": "430", "ref": "0", "palette": "0"})
    ET.SubElement(layer1, "Effect", {"name": "Shimmer", "startTime": "500",
                  "endTime": "900", "ref": "0", "palette": "0"})
    row2 = next(e for e in root.findall("./ElementEffects/Element") if e.get("name") == names["Roof green"])
    ET.SubElement(row2.find("EffectLayer"), "Effect", {"name": "Twinkle",
                  "startTime": "700", "endTime": "980", "ref": "0", "palette": "0"})
    song = tmp_path / "song.xsq"
    sequence.write(song, encoding="utf-8")
    destination = tmp_path / "new-song.lms"
    report = export_lms_from_xsq(song, original, destination, Path(imp["manifest"]))
    assert report["output_effects"] == 3
    output_root = ET.parse(destination).getroot()
    assert output_root.get("musicFilename") == "mysong.wav"
    channels = output_root.findall("./channels/channel")
    assert [(c.get("unit"), c.get("circuit"), c.get("savedIndex")) for c in channels] == [
        ("1", "1", "12"), ("1", "2", "14"), ("2", "1", "19")
    ]
    assert [(e.get("type"), e.get("startCentisecond"), e.get("endCentisecond"))
            for e in channels[0].findall("effect")] == [
        ("intensity", "10", "43"), ("shimmer", "50", "90")
    ]
    assert channels[1].find("effect").get("type") == "twinkle"
    assert channels[2].findall("effect") == []
    assert original.read_text().find("original.wav") >= 0
    assert report["verified_lor_import"] is False


def test_changed_lms_is_rejected(tmp_path: Path):
    original = tmp_path / "source.lms"
    source(original)
    imp = prepare_lms_workspace(original, tmp_path / "work")
    original.write_text(original.read_text().replace('unit="1"', 'unit="9"'))
    with pytest.raises(ValueError, match="has changed"):
        export_lms_from_xsq(Path(imp["template"]), original, tmp_path / "new.lms", Path(imp["manifest"]))


def test_duplicate_controller_address_is_rejected(tmp_path: Path):
    original = tmp_path / "bad.lms"
    source(original)
    original.write_text(original.read_text().replace('unit="1" circuit="2"', 'unit="1" circuit="1"'))
    with pytest.raises(ValueError, match="Duplicate LOR"):
        prepare_lms_workspace(original, tmp_path / "work")


def test_loredit_requires_explicit_unavailable_legacy_import(tmp_path: Path):
    wrong = tmp_path / "modern.loredit"
    wrong.write_bytes(b"not an LMS")
    with pytest.raises(ValueError, match="Modern .loredit"):
        prepare_lms_workspace(wrong, tmp_path / "work")


def test_inline_fade_settings_are_exported_as_start_end_intensity(tmp_path: Path):
    original = tmp_path / "source.lms"
    source(original)
    imp = prepare_lms_workspace(original, tmp_path / "work")
    tree = ET.parse(imp["template"])
    root = tree.getroot()
    root.find("./head/sequenceDuration").text = "1.5"
    row = root.find("./ElementEffects/Element[@type='model']")
    ET.SubElement(row.find("EffectLayer"), "Effect", {
        "name": "On", "startTime": "0", "endTime": "1000",
        "settings": "E_TEXTCTRL_Eff_On_Start=20,E_TEXTCTRL_Eff_On_End=80",
        "palette": "0",
    })
    xsq = tmp_path / "fade.xsq"
    tree.write(xsq)
    destination = tmp_path / "fade.lms"
    export_lms_from_xsq(xsq, original, destination, Path(imp["manifest"]))
    exported = ET.parse(destination).getroot().find("./channels/channel/effect")
    assert exported is not None
    assert exported.get("startIntensity") == "20"
    assert exported.get("endIntensity") == "80"


@pytest.mark.parametrize("start,end", [(2000, 2500), (500, 1500), (-10, 50), (200, 200)])
def test_export_rejects_stale_header_or_invalid_interval_without_truncating(tmp_path, start, end):
    original = tmp_path / "source.lms"
    source(original)
    imported = prepare_lms_workspace(original, tmp_path / "work")
    tree = ET.parse(imported["template"])
    # Imported templates start at one second; late cues must not be shifted
    # into their final centisecond or silently dropped by the LMS exporter.
    row = tree.find("./ElementEffects/Element[@type='model']/EffectLayer")
    ET.SubElement(row, "Effect", {"name": "On", "startTime": str(start),
                                 "endTime": str(end), "ref": "0", "palette": "0"})
    xsq, destination = tmp_path / "bad.xsq", tmp_path / "keep.lms"
    tree.write(xsq)
    destination.write_bytes(b"preserve previous output")
    with pytest.raises(ValueError, match="declared sequence duration"):
        export_lms_from_xsq(xsq, original, destination, Path(imported["manifest"]))
    assert destination.read_bytes() == b"preserve previous output"


def test_sequence_builder_direct_lor_path_without_xlights(monkeypatch, tmp_path: Path):
    import types
    from core import sequence_builder as sequence

    original = tmp_path / "source.lms"
    source(original)
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not actually read by the mocked sequencing engine")
    output = tmp_path / "exports"
    output.mkdir()
    snapshots = []

    class Context:
        manifest_path = tmp_path / "manifest.json"
        def record_artifact(self, *args):
            snapshots.append(args)
        def finalize(self, **kwargs):
            snapshots.append(("finished", kwargs))

    class FakeManager:
        def __init__(self, _config):
            pass
        def start(self, **kwargs):
            return Context()

    class FakeEngine:
        @staticmethod
        def main_for(_version, args):
            def arg(name):
                return Path(args[args.index(name) + 1])
            assert arg("--template").exists()
            assert arg("--layout-file").exists()
            assert "--ac-lights-only" in args
            tree = ET.parse(arg("--template"))
            root = tree.getroot()
            root.find("./head/sequenceDuration").text = "2.5"
            row = root.find("./ElementEffects/Element[@type='model']")
            ET.SubElement(row.find("EffectLayer"), "Effect", {
                "name": "On", "startTime": "100", "endTime": "600",
                "settings": "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100",
                "palette": "0",
            })
            tree.write(output / "my-song.xsq", encoding="utf-8")

    monkeypatch.setattr(sequence, "_effect_engine", lambda: FakeEngine)
    monkeypatch.setattr(sequence, "RunManager", FakeManager)
    monkeypatch.setattr(sequence.RunConfig, "from_engine_args",
                        staticmethod(lambda *_args: types.SimpleNamespace(output_root=output)))
    monkeypatch.setattr(sequence, "_apply_prime_beat_grid_defaults",
                        lambda _id, args: list(args))
    monkeypatch.setattr(sequence, "_run_birdsong_hook", lambda *args: None)

    sequence.run_profile("master", [
        "--helix-lor-source-lms", str(original),
        "--audio", str(audio),
        "--output-dir", str(output),
        "--no-prompt", "--no-effects-orchestrator"
    ])
    result = output / "my-song.lms"
    assert result.is_file()
    assert (output / "helix_lor_source_layout.lms").is_file()
    assert (output / "my-song.xsq").is_file()
    channels = ET.parse(result).getroot().findall("./channels/channel")
    assert [(ch.get("unit"), ch.get("circuit")) for ch in channels] == [
        ("1", "1"), ("1", "2"), ("2", "1")
    ]
    assert any(kind == "lor_sequence" for kind, *_rest in snapshots if isinstance(kind, str))
    assert original.read_text().find("original.wav") >= 0


def _mapped_export_fixture(tmp_path):
    original = tmp_path / 'source.lms'
    source(original)
    imported = prepare_lms_workspace(original, tmp_path / 'workspace')
    tree = ET.parse(imported['template'])
    tree.find('./head/sequenceDuration').text = '2.005'
    layer = tree.find('./ElementEffects/Element/EffectLayer')
    effect = ET.SubElement(layer, 'Effect', name='On', startTime='105', endTime='2005',
                           ref='0', palette='0')
    xsq = tmp_path / 'song.xsq'
    return original, imported, tree, effect, xsq, tmp_path / 'song.lms'


@pytest.mark.parametrize('attribute,value', [
    ('startTime', '-1'), ('endTime', '2006'), ('startTime', '5.5'),
    ('startTime', 'nan'), ('endTime', ''), ('startTime', None),
    ('endTime', None), ('endTime', '105'), ('startTime', '2006'),
])
def test_source_wired_export_rejects_bad_intervals_before_writing(tmp_path, attribute, value):
    original, imported, tree, effect, xsq, output = _mapped_export_fixture(tmp_path)
    if value is None:
        effect.attrib.pop(attribute)
    else:
        effect.set(attribute, value)
    tree.write(xsq)
    retained = original.read_bytes()
    with pytest.raises(ValueError, match='interval|timestamp'):
        export_lms_from_xsq(xsq, original, output, Path(imported['manifest']))
    assert original.read_bytes() == retained
    assert not output.exists()
    assert not output.with_suffix('.lms_validation.json').exists()


@pytest.mark.parametrize('config', [
    'E_TEXTCTRL_Eff_On_Start=-1', 'E_TEXTCTRL_Eff_On_End=101',
    'E_TEXTCTRL_Eff_On_Start=nan', 'E_TEXTCTRL_Eff_On_End=inf',
    'E_TEXTCTRL_Eff_On_Start=broken',
    'E_TEXTCTRL_Eff_On_Start=50,E_TEXTCTRL_Eff_On_Start=100',
    'E_TEXTCTRL_Eff_On_Start=100,B_SLIDER_Brightness=25', 'malformed',
])
def test_source_wired_export_rejects_unrepresentable_intensity(tmp_path, config):
    original, imported, tree, effect, xsq, output = _mapped_export_fixture(tmp_path)
    effect.set('settings', config)
    # Invalid effects cannot disappear from validation under a later layer.
    ET.SubElement(tree.find('./ElementEffects/Element/EffectLayer'), 'Effect',
                  name='On', startTime='105', endTime='2005', ref='0', palette='0')
    tree.write(xsq)
    with pytest.raises(ValueError, match='intensity'):
        export_lms_from_xsq(xsq, original, output, Path(imported['manifest']))
    assert not output.exists()
    assert not output.with_suffix('.lms_validation.json').exists()


@pytest.mark.parametrize('duration', ['NaN', 'Infinity', '-Infinity', 'broken', '0', '-1'])
def test_source_wired_export_rejects_nonfinite_duration(tmp_path, duration):
    original, imported, tree, effect, xsq, output = _mapped_export_fixture(tmp_path)
    tree.find('./head/sequenceDuration').text = duration
    tree.write(xsq)
    with pytest.raises(ValueError, match='duration'):
        export_lms_from_xsq(xsq, original, output, Path(imported['manifest']))
    assert not output.exists()


def test_source_wired_export_keeps_last_subcentisecond_and_inline_fade(tmp_path):
    original, imported, tree, effect, xsq, output = _mapped_export_fixture(tmp_path)
    effect.set('startTime', '2000')
    effect.set('settings', ' E_TEXTCTRL_Eff_On_End=80 , E_TEXTCTRL_Eff_On_Start=20 ')
    tree.write(xsq)
    export_lms_from_xsq(xsq, original, output, Path(imported['manifest']))
    root = ET.parse(output).getroot()
    assert root.find('./tracks/track').get('totalCentiseconds') == '201'
    event = root.find('./channels/channel/effect')
    assert (event.get('startCentisecond'), event.get('endCentisecond')) == ('200', '201')
    assert (event.get('startIntensity'), event.get('endIntensity')) == ('20', '80')
