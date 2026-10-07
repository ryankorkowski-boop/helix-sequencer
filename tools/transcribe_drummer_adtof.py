"""Run external pretrained ADTOF; export source-bound polyphonic drum evidence.

No training, count tuning, beat-generated notes or legacy family classifier.
Requires the external ADTOF-pytorch package, deliberately not vendored here.
A five-family model cannot name a physical tom: unresolved toms remain in the
report with an explicit rejection reason. Optional isolated resonance evidence
and a recording calibration can resolve identity; human review remains pending.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from audio.drum_transcription import SCHEMA


def resolve_tom_pitch(samples, sr, references):
    """Resolve pitch only against an explicitly supplied recording calibration.

    References are HIGH, MID, FLOOR measured resonances, strictly decreasing.
    No kit calibration means abstention. Noise or pitches beyond the calibrated
    kit range abstain; source separation can still leak other instruments.
    """
    n = 16384
    spectrum = np.abs(np.fft.rfft(samples*np.hanning(len(samples)),n))
    freqs = np.fft.rfftfreq(n,1/sr)
    mask = (freqs>=60)&(freqs<=400)
    band, hz = spectrum[mask], freqs[mask]
    if not len(band) or band.sum()<=1e-9:
        return None, dict(reason="no_tom_resonance")
    i = int(np.argmax(band));pitch=float(hz[i])
    # A changing mixture of bass, kick and tom can move the largest bin. Demand
    # the same resonance in two overlapping body windows before naming a tom.
    window_peaks=[]
    for segment in (samples[:round(.075*sr)],samples[round(.020*sr):]):
        part=np.abs(np.fft.rfft(segment*np.hanning(len(segment)),n))[mask]
        window_peaks.append(float(hz[int(np.argmax(part))]))
    stable=bool(min(window_peaks)>0 and max(window_peaks)/min(window_peaks)<1.08)
    prominence=float(band[i]/max(float(band.mean()),1e-9))
    share=float(band.sum()/max(float(spectrum.sum()),1e-9))
    evidence=dict(tom_peak_hz=pitch,tom_peak_prominence=prominence,tom_body_spectral_share=share,
                  tom_window_peaks_hz=window_peaks,tom_resonance_stable=stable)
    if references is None or not stable or prominence<6 or share<.50:
        return None, evidence
    distances=np.abs(np.log(pitch/np.asarray(references)))
    order=np.argsort(distances)
    if distances[order[0]]>np.log(1.20) or distances[order[1]]-distances[order[0]]<np.log(1.04):
        return None,evidence
    return ("high","mid","floor")[int(order[0])],evidence


def transcribe(audio_path, analysis_audio, output, activation_output=None, family_stems=None, tom_references=None):
    import torch
    from adtof_pytorch import (calculate_n_bins, create_frame_rnn_model,
                               get_default_weights_path, load_audio_for_model,
                               PeakPicker, FRAME_RNN_THRESHOLDS, LABELS_5)
    weights = Path(get_default_weights_path())
    if not weights.is_file():
        raise FileNotFoundError("Pretrained ADTOF weights missing; refusing random inference")
    torch.set_num_threads(2)
    model = create_frame_rnn_model(calculate_n_bins()).eval()
    state = torch.load(weights, map_location="cpu", weights_only=True)
    model.load_state_dict(state.get("model_weights", state), strict=True)
    with torch.inference_mode():
        activations = model(load_audio_for_model(str(analysis_audio))).cpu().numpy()
    if activation_output:
        np.save(activation_output, activations)
    peaks = PeakPicker(thresholds=FRAME_RNN_THRESHOLDS, fps=100).pick(activations)[0]
    y, sr = sf.read(analysis_audio, dtype="float32", always_2d=True)
    y = y.mean(axis=1)
    names = dict(zip(LABELS_5, ("kick", "snare", "tom", "hihat", "cymbal")))
    rows = []
    stem_signals = {}
    if family_stems:
        for name,file in (("kick","kick"),("snare","snare"),("tom","toms"),("hihat","hihat"),("cymbal","cymbals")):
            v, stem_sr=sf.read(Path(family_stems)/f"{file}.wav",dtype="float32",always_2d=True)
            if abs(len(v)/stem_sr-len(y)/sr)>1/min(sr,stem_sr):
                raise ValueError("Family stems must have the same timeline duration as analysis audio")
            stem_signals[name]=(v.mean(axis=1),stem_sr)
    if tom_references is not None and not (len(tom_references)==3 and tom_references[0]>tom_references[1]>tom_references[2]>0):
        raise ValueError("Tom references must be positive HIGH,MID,FLOOR resonances")
    for col, label in enumerate(LABELS_5):
        for timestamp in peaks[label]:
            frame = round(timestamp*100)
            lo, hi = max(0,round((timestamp-.01)*sr)), min(len(y),round((timestamp+.05)*sr))
            signal,signal_sr=stem_signals.get(names[label],(y,sr))
            lo,hi=max(0,round((timestamp-.01)*signal_sr)),min(len(signal),round((timestamp+.05)*signal_sr))
            rms = float(np.sqrt(np.mean(signal[lo:hi]**2)))
            rows.append(dict(timestamp=timestamp, drum_family=names[label], tom_class=None,
                             confidence=float(activations[0,frame,col]), velocity=rms,
                             source_onset_index=frame*5+col,
                             rejection_reason="unresolved_tom_identity" if label == 47 else None,
                             evidence=dict(activation_frame=frame, class_index=col,
                                           source_midi_family=label, attack_rms=rms,
                                           timing_source="100fps_learned_family_activation_peak",
                                           timing_refinement_ms=0, input=str(analysis_audio))))
    for row in rows:
        if row["drum_family"] != "tom" or "tom" not in stem_signals:
            continue
        # Use the isolated post-attack body; do not estimate pitch from the full mix.
        t=row["timestamp"];signal,body_sr=stem_signals["tom"]
        lo=max(0,round((t+.012)*body_sr));hi=min(len(signal),lo+round(.10*body_sr))
        body=signal[lo:hi]
        identity,evidence=resolve_tom_pitch(body,body_sr,tom_references)
        row["tom_class"]=identity
        row["evidence"].update(evidence,tom_identity_method="isolated_tom_resonance_against_recording_calibration")
        if identity:
            row["rejection_reason"]=None
            row["tom_class_confidence"]=row["confidence"]
    # Loudness is estimated, not a claimed MIDI velocity label. Normalize each
    # family's measured attacks, so simultaneous body hits don't dim metal lanes.
    for family in names.values():
        group = [row for row in rows if row["drum_family"] == family]
        scale = max(float(np.percentile([r["velocity"] for r in group],95)),1e-8) if group else 1
        for row in group:
            row["velocity"] = round(float(np.clip(np.sqrt(row["velocity"]/scale),.12,1)),4)
    rows.sort(key=lambda row:(row["timestamp"],row["drum_family"]))
    payload = dict(schema=SCHEMA, audio=str(audio_path),
                   audio_sha256=hashlib.sha256(Path(audio_path).read_bytes()).hexdigest(),
                   analysis_audio_sha256=hashlib.sha256(Path(analysis_audio).read_bytes()).hexdigest(),
                   review_status="model_inferred_pending_human_listening",
                   provenance=dict(engine="adtof_frame_rnn_polyphonic",
                                   code_url="https://github.com/xavriley/ADTOF-pytorch",
                                   code_revision="85c192e78f716ea0b111cc8a5ee4a8f6a3a4f8a9",
                                   weights_sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
                                   weights_license="CC-BY-NC-SA-4.0 (original ADTOF)",
                                   analysis_audio=str(analysis_audio),
                                   family_thresholds=FRAME_RNN_THRESHOLDS, activation_fps=100,
                                   velocity_method="per_family_95th_percentile_attack_rms_sqrt",
                                   tom_identity="isolated_resonance_calibration" if tom_references else "not_provided_by_five_family_model",
                                   tom_reference_hz=tom_references, family_stems=str(family_stems) if family_stems else None), events=rows)
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(payload,indent=2)+"\n")
    return payload


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio",type=Path);p.add_argument("--analysis-audio",type=Path)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--activations",type=Path)
    p.add_argument("--family-stems",type=Path)
    p.add_argument("--tom-reference-hz",help="Measured recording resonances: HIGH,MID,FLOOR; absent means abstain")
    a=p.parse_args();references=[float(v) for v in a.tom_reference_hz.split(",")] if a.tom_reference_hz else None
    result=transcribe(a.audio,a.analysis_audio or a.audio,a.output,a.activations,a.family_stems,references)
    from collections import Counter
    print(json.dumps(dict(raw_counts=Counter(r["drum_family"] for r in result["events"]),
                          output=str(a.output),review_status=result["review_status"]),indent=2))
