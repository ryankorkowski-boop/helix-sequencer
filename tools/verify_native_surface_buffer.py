"""Native renderer compatibility gate, NOT a musical approval render.

Use a real recording as the media clock, controlled effect windows, one actual
advanced layout prop, and the production exporter. Only the native Bars layer
is retained to isolate renderer compatibility from the note overlays.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from core.output_provenance import sha256
from models.approval_layouts import build_layout
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_snowman_ensemble import NativeSequence
from tools.layout_bench.xlights_fseq import load_fseq, render_sequence_to_fseq
from tools.source_spatial_direction import export_model


def run(audio: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    g = build_layout(10)
    model = next(m for m in g.models if m.name == 'MOIRE_LINE_LATTICE_0')
    g.models = [model]
    model.start = 1
    model.attrs.pop('StartChannel', None)
    model.details['spatial_direction'] = 1
    sequence = NativeSequence(g, 4, audio.name, 'Native surface compatibility gate')
    cues = [dict(start_ms=a, end_ms=b, pitch_midi=60, velocity=.8, section=section)
            for a, b, section in [(0, 1000, 'verse'), (1000, 2000, 'pre_chorus'),
                                  (2000, 3000, 'chorus')]]
    export_model(sequence, model, {'cues': {'keyboardist': cues}}, {}, g.palette)
    for layer in sequence.root.findall('./ElementEffects/Element/SubModelEffectLayer'):
        for effect in list(layer):
            if effect.get('name') != 'Bars':
                layer.remove(effect)
    xsq = output / 'surface.xsq'
    sequence.write(xsq)
    write_layout(g, output, include_demo=False, export_all_custom=True)
    layout = output / 'xlights_rgbeffects.xml'
    surface = ET.parse(layout).find(".//subModel[@name='SPATIAL_SURFACE']")
    assert surface is not None and 'line1' in surface.attrib
    fseq = output / 'surface.fseq'
    version = render_sequence_to_fseq(layout_xml=layout, xsq_path=xsq, media_path=audio,
                                      fseq_path=fseq, show_dir=output / 'native')
    data = load_fseq(fseq)
    assert data.frames * data.step_ms == 4000, 'Incorrect native duration'
    start = model.start - 1 - data.sparse_start
    assert start >= 0 and start + model.channels <= data.channels
    blocks = np.stack([row[start:start + model.channels].copy() for row in data.rows()])
    assert len(blocks) == data.frames
    metrics = []
    for a, b, name in [(0, 1000, 'Left'), (1000, 2000, 'H-expand'),
                       (2000, 3000, 'Alternate Right')]:
        frames = blocks[a // data.step_ms:b // data.step_ms]
        metrics.append(dict(direction=name, lit_frames=int(np.any(frames, axis=1).sum()),
                            unique_frames=int(len(np.unique(frames, axis=0)))))
    rest = blocks[3100 // data.step_ms:]
    report = dict(classification='native compatibility test; controlled cues, not approval',
                  owner_approved=False, commit=os.environ.get('GITHUB_SHA'), native_version=version,
                  source_excerpt_sha256=sha256(audio), xsq_sha256=sha256(xsq),
                  layout_sha256=sha256(layout), fseq_sha256=sha256(fseq), metrics=metrics,
                  rest_nonzero=int(np.count_nonzero(rest)))
    (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    assert all(m['lit_frames'] > 0 and m['unique_frames'] > 1 for m in metrics), report
    assert report['rest_nonzero'] == 0, report
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.audio, args.output), indent=2))
