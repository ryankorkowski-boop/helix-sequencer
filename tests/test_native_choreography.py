import json
import struct
import numpy as np
import pytest

from tools.quality.native_choreography import ChoreographyObserver, inspect_choreography


def models(kind='pixel'):
    width = 3 if kind == 'pixel' else 1
    return [dict(name=f'M{i}', kind=kind, nodes=1, start_channel=i*width+1,
                 end_channel=(i+1)*width, bounds_ft=[[i, 0, i], [i, 0, i]])
            for i in range(8)]


def observe(data, kind='pixel'):
    obs = ChoreographyObserver(models(kind))
    obs.begin(np.arange(data.shape[1]), data.shape[1], len(data), 50)
    for frame in data:
        obs.frame(frame)
    return obs.result()


def test_broadcast_white_vs_travel():
    flash = np.zeros((40, 24), dtype=np.uint8)
    flash[::2] = 255
    report = observe(flash)
    assert report['peak_white_rgb_pixel_fraction'] == 1
    assert report['same_direction_model_transition_fraction'] == 1
    assert report['normalized_centroid_travel_xyz'] == [0, 0, 0]
    assert 'sustained_broad_rgb_white' in report['warnings']
    chase = np.zeros_like(flash)
    for i in range(len(chase)):
        chase[i, (i%8)*3] = 255
    report = observe(chase)
    assert report['peak_white_rgb_pixel_fraction'] == 0
    assert report['same_direction_model_transition_fraction'] == 0
    assert report['normalized_centroid_travel_xyz'][0] > 3
    assert report['normalized_centroid_travel_xyz'][2] > 3
    assert report['models_ever_active'] == 8


def test_ac_does_not_count_as_rgb_white():
    data = np.zeros((10, 8), dtype=np.uint8)
    data[::2] = 255
    report = observe(data, 'ac')
    assert report['peak_white_rgb_pixel_fraction'] is None
    assert report['ac_synchronized_transition_fraction'] == 1


def test_native_v2_raw_and_manifest_binding(tmp_path):
    data = np.zeros((10, 24), dtype=np.uint8)
    data[::2] = 255
    header = bytearray(32)
    header[:4] = b'PSEQ'
    struct.pack_into('<H', header, 4, 32)
    header[7] = 2
    struct.pack_into('<II', header, 10, 24, 10)
    header[18] = 50
    fseq = tmp_path/'show.fseq'
    fseq.write_bytes(header + data.tobytes())
    manifest = tmp_path/'showcase_manifest.json'
    manifest.write_text(json.dumps({'models': models()}))
    layout = tmp_path/'xlights_rgbeffects.xml'
    layout.write_text('<xrgb><models>' + ''.join(
        f'<model name="{m["name"]}" StartChannel="{m["start_channel"]}"/>'
        for m in models()) + '</models></xrgb>')
    report = inspect_choreography(fseq, manifest)
    assert report['frames'] == 10
    assert report['same_direction_model_transition_fraction'] == 1
    layout.write_text('<xrgb><models/></xrgb>')
    with pytest.raises(ValueError, match='channel map'):
        inspect_choreography(fseq, manifest)


def test_sparse_omission_measured_as_zero():
    obs = ChoreographyObserver(models())
    obs.begin(np.arange(3), 24, 2, 50)
    obs.frame(np.array([255, 0, 0], dtype=np.uint8))
    obs.frame(np.array([0, 0, 0], dtype=np.uint8))
    report = obs.result()
    assert report['sparse_omitted_channels'] == 21
    assert report['models_ever_active'] == 1
