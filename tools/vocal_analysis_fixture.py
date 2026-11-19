"""Adapt qualified 20 fps singer lanes to the native 10 ms export clock."""
import json
from pathlib import Path
import shutil
import numpy as np
import soundfile as sf
from tools.phoneme_source import digest
from tools.verify_native_vocal_source import verify


def build(audio, analysis, output):
    audio, analysis, output = map(Path, (audio, analysis, output))
    result = verify(audio, analysis)  # Fail before expensive native preparation.
    report = json.loads((analysis/'voice_roles.json').read_text())
    output.mkdir(parents=True, exist_ok=False)
    for name in ('voice_roles.json', 'voice_roles.npz'):
        shutil.copyfile(analysis/name, output/name)
    count = round(sf.info(audio).duration*100)
    indices = np.floor(np.arange(count)/5).astype(int)
    with np.load(analysis/'voice_roles.npz', allow_pickle=False) as data:
        # round(duration*20) may omit <25ms at the tail. Those frames are REST,
        # never an extension of the final syllable.
        valid = indices < len(data['energy'])
        energy = np.zeros((count, 2), 'f4'); shapes = np.zeros((count, 2), 'i1')
        energy[valid] = data['energy'][indices[valid]]
        shapes[valid] = data['shapes'][indices[valid]]
    arrays = {}
    tracks = {}
    for lane in report['model_lanes']:
        i = lane['model_lane']; key = ('estimated_lead', 'estimated_backing')[i]
        arrays[key+'_energy'] = energy[:, i]
        arrays[key+'_shapes'] = shapes[:, i]
        tracks[key] = dict(sha256=report['input_tracks'][lane['name']]['sha256'])
    np.savez_compressed(output/'acoustic_vocal_clocks.npz', **arrays)
    receipt = dict(audio_sha256=digest(audio), clock_sha256=digest(output/'acoustic_vocal_clocks.npz'),
                   clock_hop_seconds=.01, tracks=tracks, verification_state='VERIFIED',
                   source_verification=result, voice_roles_sha256=digest(output/'voice_roles.json'),
                   voice_arrays_sha256=digest(output/'voice_roles.npz'),
                   independent_backing_verified=True, exact_phoneme_boundaries_verified=False,
                   limitation='Independent source qualification; lexical phonemes and visual acceptance remain separate.')
    (output/'diagnostic.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return output


def verify_fixture(audio, fixture, receipt):
    """Recheck source and original lane bytes before trusting the adapter."""
    for name, key in [('voice_roles.json', 'voice_roles_sha256'), ('voice_roles.npz', 'voice_arrays_sha256')]:
        if digest(fixture/name) != receipt.get(key):
            raise ValueError('Qualified vocal analysis bytes changed')
    result = verify(Path(audio), fixture)
    count = round(sf.info(audio).duration*100)
    indices = np.floor(np.arange(count)/5).astype(int)
    with np.load(fixture/'voice_roles.npz', allow_pickle=False) as original, np.load(
            fixture/'acoustic_vocal_clocks.npz', allow_pickle=False) as native:
        valid = indices < len(original['energy'])
        for i, lane in enumerate(('estimated_lead', 'estimated_backing')):
            for key in ('energy', 'shapes'):
                expected = np.zeros(count, dtype=original[key].dtype)
                expected[valid] = original[key][indices[valid], i]
                if not np.array_equal(expected, native[lane+'_'+key]):
                    raise ValueError('Native singer clock differs from qualified vocal analysis')
    return result
