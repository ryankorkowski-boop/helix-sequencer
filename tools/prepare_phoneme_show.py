"""Build an editable native show with the retained six-snowman geometry.

This exercises the current production sequencer. It is a diagnostic candidate,
not a declaration that the artwork, instrument motion or vocal identities have
passed owner acceptance. No external prepared show ZIP is required.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from tools.phoneme_source import digest, EXPECTED_SHA256

ROOT = Path(__file__).resolve().parents[1]


def prepare(audio: Path, output: Path, *, expected_sha256=EXPECTED_SHA256,
            vocal_fixture=None, title='Phoneme Test Hook', include_xylophonist=False, full_keyboard=False,
            drum_events=None) -> Path:
    import soundfile as sf
    from models.canonical_native_band import add_band, visual_identity
    from models.ultimate_showcase import Garden
    from tools.native_source_pose_band import stage_native_cast
    from tools.build_snowman_ensemble import NativeSequence
    from tools.build_helpers.ultimate_showcase import write_layout

    audio, output = audio.resolve(), output.resolve()
    if digest(audio) != expected_sha256:
        raise ValueError('Original owner source hash mismatch')
    from tools.phoneme_vocal_export import FIXTURE
    vocal_fixture = Path(vocal_fixture) if vocal_fixture is not None else FIXTURE
    receipt = json.loads((vocal_fixture/'diagnostic.json').read_text())
    if receipt.get('audio_sha256') != expected_sha256:
        raise ValueError('Vocal cache belongs to another recording')
    if output.exists():
        raise FileExistsError('Use a fresh show directory: ' + str(output))
    duration = sf.info(audio).duration
    garden = Garden(title='Helix '+title+' diagnostic candidate', slug=audio.stem)
    add_band(garden,include_xylophonist=include_xylophonist,full_keyboard=full_keyboard)
    stage_native_cast(garden.models,legacy_xylophone=include_xylophonist)
    for model in garden.models:
        if model.details['review_role'] in {'lead', 'harmony'}:
            model.attrs['HelixPhonemeOwnership'] = 'exclusive'
    from tools.phoneme_vocal_export import static_materials
    static_materials(garden)
    write_layout(garden, output, include_demo=False)
    layout = output / 'xlights_rgbeffects.xml'
    tree = ET.parse(layout)
    for camera in tree.findall('./Viewpoints/*'):
        for key, value in dict(angleX='8', angleY='0', distance='-65', pany='-18', panz='-75').items():
            camera.set(key, value)
    tree.write(layout, encoding='utf-8', xml_declaration=True)
    media = output / 'media'
    media.mkdir()
    retained = media / audio.name
    shutil.copyfile(audio, retained)
    seed = output / 'input.xsq'
    NativeSequence(garden, duration, 'media/'+audio.name, title).write(seed)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    manifest = dict(schema='helix.run_manifest.v1', status='in_progress', warnings=[],
                    source_commit=commit, audio_sha256=expected_sha256,
                    sequence_file=audio.stem+'_Helix.xsq',
                    source_duration_seconds=duration, visual_review_status='not_reviewed',
                    geometry_source='models.final_band_scene.FinalBandScene / canonical_native_band',
                    owner_approved_geometry=False, independent_backing_verified=False)
    # The retained native-review cast is not the owner's approved solid 3D
    # snowman scene. Record this explicitly so a passing native video or
    # successful harmony mouth test cannot be mistaken for visual approval.
    manifest['visual_identity'] = visual_identity(include_xylophonist=include_xylophonist)
    (output / 'VISUAL_ACCEPTANCE.json').write_text(
        json.dumps(manifest['visual_identity'], indent=2) + '\n')
    manifest['source_worktree_dirty'] = bool(subprocess.check_output(
        ['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    manifest['source_module_sha256'] = {name: digest(ROOT / name) for name in (
        'core/effect_engine.py', 'core/snowman_band.py', 'core/native_face_instructions.py',
        'xlights/xsq_writer.py', 'models/canonical_native_band.py', 'models/final_band_scene.py', 'models/final_band_native.py',
        'tools/prepare_phoneme_show.py', 'tools/native_preview.py', 'tools/phoneme_vocal_export.py',
        'tools/vocal_diagnostic.py',
        'tools/native_source_pose_band.py', 'xlights/xml_io.py')}
    manifest['vocal_cache_sha256'] = digest(vocal_fixture/'acoustic_vocal_clocks.npz')
    manifest['vocal_receipt_sha256'] = digest(vocal_fixture/'diagnostic.json')
    (output / 'run_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    command = [sys.executable, str(ROOT / 'main.py'), '--profile', 'master', '--',
               '--template', str(seed), '--audio', str(retained), '--layout-file', str(layout),
               '--output-dir', str(output / 'sequence'), '--single', '--variants', '1',
               '--no-prompt', '--no-save-settings', '--no-workspace-history', '--no-learning-memory',
               '--palette-mode', 'warm', '--sync-lyrics-heads']
    (output / 'sequencer_command.json').write_text(json.dumps(command, indent=2) + '\n')
    started = time.monotonic()
    with (output / 'sequencer.log').open('w') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=False)
    manifest['sequencer_seconds'] = time.monotonic() - started
    manifest['sequencer_exit_code'] = result.returncode
    manifest['status'] = 'sequence_failed' if result.returncode else 'sequence_generated'
    (output / 'run_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    if result.returncode:
        raise RuntimeError('Sequencer failed; inspect ' + str(output / 'sequencer.log'))
    sequences = [p for p in (output / 'sequence').glob('*.xsq') if '.uncolored.' not in p.name]
    if len(sequences) != 1:
        raise ValueError('Expected exactly one production sequence, found ' + str(len(sequences)))
    final = output / (audio.stem+'_Helix.xsq')
    shutil.copyfile(sequences[0], final)
    # Relative media must be valid when the complete show is unpacked elsewhere.
    tree = ET.parse(final)
    tree.find('head/mediaFile').text = 'media/'+audio.name
    from tools.canonical_band_cues import export_instruments, export_drums
    plans = list((output / 'sequence').glob('*.snowman_band.json'))
    if len(plans) != 1:
        raise ValueError('Expected one retained production band plan')
    plan=json.loads(plans[0].read_text())
    if drum_events is not None:
        from tools.source_drum_plan import bind
        plans[0].with_suffix('.original-production.json').write_text(json.dumps(plan,indent=2)+'\n')
        plan,drum_receipt=bind(plan,drum_events,retained)
        plans[0].write_text(json.dumps(plan,indent=2)+'\n')
        (output/'source_percussion.json').write_text(json.dumps(drum_receipt,indent=2)+'\n')
    instrument_report = export_instruments(tree.getroot(), garden, plan)
    instrument_report['drummer'] = export_drums(tree.getroot(),garden,plan)
    from tools.canonical_band_cues import refresh_models
    refresh_models(garden, layout)
    (output / 'instrument_export.json').write_text(json.dumps(instrument_report, indent=2) + '\n')
    from tools.phoneme_vocal_export import export as export_vocal_estimates
    separated = export_vocal_estimates(tree.getroot(), layout, garden,
        fixture=vocal_fixture, expected_sha256=expected_sha256)
    (output / 'source_separated_vocal_export.json').write_text(json.dumps(separated, indent=2) + '\n')
    from xlights.xml_io import materialize_native_effect_tables
    native_tables = materialize_native_effect_tables(tree.getroot())
    (output / 'native_effect_tables.json').write_text(json.dumps(native_tables, indent=2) + '\n')
    tree.write(final, encoding='utf-8', xml_declaration=True)
    if abs(float(tree.findtext('head/sequenceDuration')) - duration) > .001:
        raise ValueError('Generated sequence does not cover original full recording')
    report = dict(audio_sha256=expected_sha256, source_duration_seconds=duration,
                  independent_backing_verified=False, exact_phoneme_boundaries_verified=False,
                  source_kind='mixed stereo owner upload', models={},
                  limitation='Production mixed-bus cues are estimates. Separate non-rest faces do not prove independent vocal parts. Obtain isolated backing/lead sources or validated source separation before release acceptance.')
    for role in ('LEAD', 'HARMONY'):
        name = 'HX_SNOW_' + role
        elements = tree.findall(f'./ElementEffects/Element[@name="{name}"]')
        effects = [e for el in elements for e in el.iter('Effect')]
        report['models'][name] = dict(effect_count=len(effects), faces_effect_count=sum(e.get('name') == 'Faces' for e in effects),
                                     **{k:v for k,v in separated['models'][name].items() if k != 'faces_effect_count'})
    report['source_separation'] = separated['source']
    report['limitation'] = 'Two-stage source separation produces distinct lead/residual-backing estimates with measured clocks; leakage and voice identity require review. Acoustic vowel colors are not verified lexical phonemes. No independent backing ground truth or artistic approval is claimed.'
    (output / 'vocal_lane_diagnostic.json').write_text(json.dumps(report, indent=2) + '\n')
    from tools.vocal_diagnostic import export as export_timeline
    export_timeline(audio, vocal_fixture, output/'vocal_diagnostic')
    return final


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-sha256', default=EXPECTED_SHA256)
    parser.add_argument('--vocal-fixture', type=Path)
    parser.add_argument('--title', default='Phoneme Test Hook')
    parser.add_argument('--include-xylophonist',action='store_true')
    parser.add_argument('--full-keyboard',action='store_true')
    parser.add_argument('--drum-events',type=Path,help='Original-source-hash-bound polyphonic percussion transcription')
    args = parser.parse_args()
    print(prepare(args.audio, args.output, expected_sha256=args.expected_sha256,
                  vocal_fixture=args.vocal_fixture, title=args.title,
                  include_xylophonist=args.include_xylophonist,full_keyboard=args.full_keyboard,drum_events=args.drum_events))
