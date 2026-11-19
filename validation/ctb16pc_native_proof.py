"""Compare real xLights FSEQ to the new physical kit's intensity timeline."""
from __future__ import annotations

import json
import shutil
import xml.etree.ElementTree as ET

import numpy as np

from core.ctb16pc_sequence import compile_ctb16pc_sequence
from tools.export_ctb16pc_sequence import export_ctb16pc_sequence


def probe(out, executable, render):
    # Explicit synthetic controller fixture; never used as user wiring.
    source = out / "Synthetic_CTB16PC_Source.lms"
    root = ET.Element("sequence", saveFileVersion="14")
    channels = ET.SubElement(root, "channels")
    for circuit in range(1, 17):
        ET.SubElement(channels, "channel", name=f"Diagnostic circuit {circuit}",
                      deviceType="LOR", unit="10", circuit=str(circuit),
                      savedIndex=str(circuit - 1), color="16777215")
    ET.ElementTree(root).write(source)
    cues = dict(duration=3, audio_filename="Diagnostic_Only.wav", hits=[
        dict(time=.2 + i * .105, target="kick") for i in range(8)] + [
        dict(time=1.1, target="snare", side="left"),
        dict(time=1.3, target="snare", side="right"),
        dict(time=1.5, target="cymbal_left", tail_amplitudes=[1, .7, .4, .1, 0], tail_fps=20),
        dict(time=1.62, target="cymbal_left", tail_amplitudes=[1, .6, .2, 0], tail_fps=20),
        dict(time=1.8, target="cymbal_right"), dict(time=2, target="tom_high"),
        dict(time=2.2, target="tom_mid"), dict(time=2.4, target="tom_floor"),
        dict(time=2.6, target="hi_hat"), dict(time=2.85, target="kick", velocity=.001)], vocals=[
        dict(start=.1, end=.4, phoneme="AH", vocal_layers=1),
        dict(start=1, end=1.2, phoneme="EE", chorus=True),
        dict(start=1.2, end=1.4, phoneme="L", vocal_layers=3)])
    folder = out / "CTB16PC_Drummer_Chorus_Diagnostic"
    report = export_ctb16pc_sequence(cues, source, folder, unit_id="0A")
    shutil.copy2(out / "Physical_Drummer_Diagnostic/Diagnostic_Only.wav", folder / "Diagnostic_Only.wav")
    frames, step = render(executable, folder, folder / "CTB16PC_Drummer_Chorus.xsq")
    expected = compile_ctb16pc_sequence(cues["hits"], duration=3, vocals=cues["vocals"])
    assert frames.shape == expected.shape and step == 10, (frames.shape, step)
    delta = np.abs(frames.astype(float) - expected.astype(float) * 2.55)
    assert delta.max() <= 1.01, (float(delta.max()), np.argwhere(delta > 1.01)[:10].tolist())
    assert frames[161, 1] == 0 and frames[162, 1] > 0, 'Cymbal retrigger release gap missing'
    assert frames[285, 6] > 0, 'Accepted quiet kick vanished in native output'
    report.update(native_xlights_verified=True, synthetic_diagnostic=True,
                  native_value_checks=int(expected.size), max_intensity_error=float(delta.max()),
                  cymbal_retrigger_gap_verified=True, positive_velocity_native_output_verified=True,
                  musical_transcription_verified=False)
    (folder / "native_verification.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
