import json
import xml.etree.ElementTree as ET

import numpy as np
import pytest

from core.ac_cymbal_shimmer import cymbal_shimmer
from core.ctb16pc_drummer_chorus import ctb16pc_drummer_chorus_patch
from core.ctb16pc_sequence import compile_ctb16pc_sequence
from tools.export_ctb16pc_sequence import export_ctb16pc_sequence
from tools.lor_lms_import import _source_channels


def cues():
    return dict(duration=3, hits=[dict(time=.2 + i * .105, target="kick") for i in range(8)] + [
        dict(time=1.1, target="snare", side="left"),
        dict(time=1.3, target="snare", side="right"),
        dict(time=1.5, target="cymbal_left", tail_amplitudes=[1, .7, .4, .1, 0], tail_fps=20),
        dict(time=2.1, target="tom_high"), dict(time=2.3, target="tom_mid"),
        dict(time=2.5, target="tom_floor"), dict(time=2.7, target="hi_hat")], vocals=[
        dict(start=.3, end=.5, phoneme="AH", vocal_layers=1),
        dict(start=1, end=1.2, phoneme="EE", chorus=True),
        dict(start=1.2, end=1.4, phoneme="L", vocal_layers=3)])


def source_lms(path, unit=10):
    root = ET.Element("sequence", saveFileVersion="14")
    channels = ET.SubElement(root, "channels")
    for i in range(1, 17):
        row = ET.SubElement(channels, "channel", name=f"Physical output {i}", unit=str(unit),
                            circuit=str(i), savedIndex=str(i - 1), deviceType="LOR", color="16777215")
        ET.SubElement(row, "effect", type="intensity", startCentisecond="0", endCentisecond="10", intensity="50")
    tracks = ET.SubElement(root, "tracks")
    track = ET.SubElement(tracks, "track", totalCentiseconds="100")
    listed = ET.SubElement(track, "channels")
    for i in range(16):
        ET.SubElement(listed, "channel", savedIndex=str(i))
    ET.ElementTree(root).write(path)
    return path


def test_cues_drive_eight_distinct_kicks_hands_and_exclusive_chorus():
    data = cues()
    values = compile_ctb16pc_sequence(data["hits"], duration=3, vocals=data["vocals"])
    assert values.shape == (300, 16)
    assert np.all(values[:, 0] == 18)
    kick = values[:, 6] > 0
    rises = np.flatnonzero(kick & ~np.r_[False, kick[:-1]])
    assert len(rises) == 8
    assert np.max(np.abs(rises / 100 - [.2 + i * .105 for i in range(8)])) <= .0051
    assert values[110, 4] == 100 and values[110, 5] == 0
    assert values[130, 5] == 100 and values[130, 4] == 0
    assert not values[30:50, 10:].any()
    assert np.all(values[100:120, 11] == 100)
    assert np.all(values[120:140, 15] == 100)
    assert np.all((values[:, 10:] > 0).sum(axis=1) <= 1)
    assert values[150, 1] == 100 and values[165, 1] < values[155, 1]
    assert not values[170:, 1].any()


@pytest.mark.parametrize('review_cases', [False, True])
def test_real_lms_roundtrip_preserves_addresses_timing_and_native_settings(tmp_path, review_cases):
    source = source_lms(tmp_path / "source.lms")
    original = source.read_bytes()
    data = cues()
    if review_cases:
        data['hits'] += [dict(time=1.62, target='cymbal_left', tail_amplitudes=[1, .6, .2, 0], tail_fps=20),
                         dict(time=2.85, target='kick', velocity=.001)]
    folder = tmp_path / "export"
    report = export_ctb16pc_sequence(data, source, folder, unit_id="0A")
    assert source.read_bytes() == original
    root, channels = _source_channels(folder / "CTB16PC_Drummer_Chorus.lms")
    assert {(c["unit"], c["circuit"]) for c in channels} == {(10, i) for i in range(1, 17)}
    expected = compile_ctb16pc_sequence(data["hits"], duration=3, vocals=data["vocals"])
    decoded = np.zeros_like(expected)
    for channel in root.findall("channels/channel"):
        circuit = int(channel.get("circuit")) - 1
        for effect in channel.findall("effect"):
            a, b = (int(effect.get(k)) for k in ("startCentisecond", "endCentisecond"))
            decoded[a:b, circuit] = int(effect.get("intensity"))
    np.testing.assert_array_equal(decoded, expected)
    if review_cases:
        assert decoded[161, 1] == 0 and decoded[162, 1] > 0
        assert decoded[285, 6] == 1
    xsq = ET.parse(folder / "CTB16PC_Drummer_Chorus.xsq").getroot()
    db = xsq.findall("EffectDB/Effect")
    for effect in xsq.findall(".//EffectLayer/Effect"):
        assert db[int(effect.get("ref"))].text == effect.get("settings")
    assert report["timing_ms"] == 10 and report["physical_controller_verified"] is False
    geometry = json.loads((folder / "front_projection_contract.json").read_text())
    assert geometry["2d"]["channels"] == geometry["3d"]["channels"]
    assert geometry["2d"]["unit_id"] == "0A"
    layout = ET.parse(folder / "xlights_rgbeffects.xml").getroot()
    assert all(m.get("ModelBrightness") == "0" for m in layout.findall("models/model"))
    with pytest.raises(FileExistsError):
        export_ctb16pc_sequence(data, source, folder, unit_id="0A")


def test_wrong_unit_and_conflicting_mouths_fail_before_output(tmp_path):
    source = source_lms(tmp_path / "source.lms")
    destination = tmp_path / "new"
    with pytest.raises(ValueError, match="sixteen circuits"):
        export_ctb16pc_sequence(cues(), source, destination, unit_id="01")
    assert not destination.exists()
    with pytest.raises(ValueError, match="Conflicting"):
        compile_ctb16pc_sequence([], duration=1, vocals=[
            dict(start=.1, end=.4, chorus=True, phoneme="AH"),
            dict(start=.2, end=.5, chorus=True, phoneme="EE")])


@pytest.mark.parametrize("hit", [dict(time=.1, target="snare"), dict(time=float("nan"), target="kick"),
    dict(time=.1, target="kick", velocity=float("inf")), dict(time=.1, target="unknown")])
def test_invalid_source_hits_abstain(hit):
    with pytest.raises(ValueError):
        compile_ctb16pc_sequence([hit], duration=1)


@pytest.mark.parametrize("unit", ["00", "0G", "1", None])
def test_invalid_unit_ids_are_rejected(unit):
    with pytest.raises(ValueError):
        ctb16pc_drummer_chorus_patch(unit)


@pytest.mark.parametrize("rate", [float("nan"), float("inf"), -1, 21])
def test_shimmer_rejects_invalid_sampled_frequency(rate):
    with pytest.raises(ValueError):
        cymbal_shimmer([1, .5, 0], fps=40, shimmer_hz=rate)


@pytest.mark.parametrize('first_tail', [False, True])
@pytest.mark.parametrize('second_tail', [False, True])
def test_cymbal_retriggers_release_old_tail_before_each_attack(first_tail, second_tail):
    tail = dict(tail_amplitudes=[1, .8, .4, .2, 0], tail_fps=20)
    first = dict(time=.1, target='cymbal_left', **(tail if first_tail else {}))
    second = dict(time=.12, target='cymbal_left', **(tail if second_tail else {}))
    values = compile_ctb16pc_sequence([second, first], duration=1)
    assert values[10, 1] == 100 and values[11, 1] == 0 and values[12, 1] == 100
    if not second_tail:
        assert not values[16:, 1].any()  # The first measured tail must not reappear.


@pytest.mark.parametrize('target', ['kick', 'cymbal_left'])
@pytest.mark.parametrize('times', [(.1, .11), (.004, .016)])
def test_repeat_spacing_rejects_unrepresentable_or_sub_20ms_attacks(target, times):
    tail = dict(tail_amplitudes=[1, .5, 0], tail_fps=20) if target.startswith('cymbal') else {}
    with pytest.raises(ValueError, match='at least 20 ms'):
        compile_ctb16pc_sequence([dict(time=t, target=target, **tail) for t in times], duration=1)


@pytest.mark.parametrize('tail', [False, True])
@pytest.mark.parametrize('velocity', [1e-12, .001, .005])
def test_positive_velocity_survives_percent_quantization_without_lighting_rest(tail, velocity):
    hit = dict(time=.1, target='cymbal_left' if tail else 'kick', velocity=velocity)
    if tail:
        hit.update(tail_amplitudes=[1, .4, 0], tail_fps=20)
    values = compile_ctb16pc_sequence([hit], duration=1)
    channel = 1 if tail else 6
    assert values[10, channel] == 1
    assert not values[:10, channel].any() and not values[20:, channel].any()
    if tail:
        assert values[15, channel] == 1
