#!/usr/bin/env python3
"""Render selected GMD MIDI files to WAV using a local FluidSynth soundfont."""
from __future__ import annotations
import argparse, shutil, subprocess
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--midi-root',type=Path,required=True); ap.add_argument('--soundfont',type=Path,required=True); ap.add_argument('--output',type=Path,default=Path('helix-drum-test-data/audio/gmd')); args=ap.parse_args()
    if shutil.which('fluidsynth') is None: raise SystemExit('fluidsynth executable not found; install FluidSynth or use another local MIDI renderer')
    args.output.mkdir(parents=True,exist_ok=True)
    files=sorted(list(args.midi_root.glob('*.mid'))+list(args.midi_root.glob('*.midi')))
    if not files: raise SystemExit('No selected GMD MIDI files found')
    for midi in files:
        out=args.output/f'{midi.stem}.wav'
        subprocess.run(['fluidsynth','-ni','-F',str(out),'-r','44100',str(args.soundfont),str(midi)],check=True)
        print(out)
if __name__=='__main__': main()
