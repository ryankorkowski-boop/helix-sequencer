"""
Audio Analysis Pipeline (Essentia + madmom)
Drop-in module for helix-sequencer
"""

from madmom.features.beats import RNNBeatProcessor, DBNBeatTrackingProcessor
from madmom.features.downbeats import RNNDownBeatProcessor, DBNDownBeatTrackingProcessor

import essentia.standard as es


class AudioPipeline:
    def __init__(self, fps=40):
        self.fps = fps

    # ----------------------
    # MADMOM (TIMING)
    # ----------------------
    def extract_timing(self, audio_file):
        beat_proc = RNNBeatProcessor()
        beat_act = beat_proc(audio_file)

        beat_tracker = DBNBeatTrackingProcessor(fps=100)
        beats = beat_tracker(beat_act)

        downbeat_proc = RNNDownBeatProcessor()
        downbeat_act = downbeat_proc(audio_file)

        downbeat_tracker = DBNDownBeatTrackingProcessor(beats_per_bar=[3, 4], fps=100)
        downbeats = downbeat_tracker(downbeat_act)

        return {
            "beats": beats,
            "downbeats": downbeats
        }

    # ----------------------
    # ESSENTIA (FEATURES)
    # ----------------------
    def extract_features(self, audio_file):
        loader = es.MonoLoader(filename=audio_file)
        audio = loader()

        frame_size = 1024
        hop_size = 512

        window = es.Windowing(type='hann')
        spectrum = es.Spectrum()

        energy = []
        centroid = []

        for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
            spec = spectrum(window(frame))
            energy.append(es.Energy()(frame))
            centroid.append(es.Centroid()(spec))

        tempo, _, _, _, _ = es.RhythmExtractor2013()(audio)

        return {
            "energy": energy,
            "centroid": centroid,
            "tempo": tempo
        }

    # ----------------------
    # TIMELINE BUILDER
    # ----------------------
    def build_timeline(self, timing, features):
        timeline = []

        for beat_time in timing["beats"]:
            entry = {
                "time": float(beat_time),
                "is_downbeat": False,
                "energy": None,
                "brightness": None
            }

            idx = int(beat_time * self.fps)

            if idx < len(features["energy"]):
                entry["energy"] = features["energy"][idx]
                entry["brightness"] = features["centroid"][idx]

            for db in timing["downbeats"]:
                if abs(db[0] - beat_time) < 0.05:
                    entry["is_downbeat"] = True
                    break

            timeline.append(entry)

        return timeline

    # ----------------------
    # FULL PIPELINE
    # ----------------------
    def process(self, audio_file):
        timing = self.extract_timing(audio_file)
        features = self.extract_features(audio_file)
        timeline = self.build_timeline(timing, features)

        return {
            "timing": timing,
            "features": features,
            "timeline": timeline
        }
