"""
Audio Analysis Pipeline (Essentia + madmom)
Drop-in module for helix-sequencer
"""

from core.lazy_imports import optional_import
from core.feature_state import build_feature_state_sequence, serialize_feature_state_sequence


class AudioPipeline:
    def __init__(self, fps=40):
        self.fps = fps

    # ----------------------
    # MADMOM (TIMING)
    # ----------------------
    def extract_timing(self, audio_file):
        beats_module = optional_import("madmom.features.beats")
        downbeats_module = optional_import("madmom.features.downbeats")
        if beats_module is not None and downbeats_module is not None:
            beat_proc = beats_module.RNNBeatProcessor()
            beat_act = beat_proc(audio_file)

            beat_tracker = beats_module.DBNBeatTrackingProcessor(fps=100)
            beats = beat_tracker(beat_act)

            downbeat_proc = downbeats_module.RNNDownBeatProcessor()
            downbeat_act = downbeat_proc(audio_file)

            downbeat_tracker = downbeats_module.DBNDownBeatTrackingProcessor(beats_per_bar=[3, 4], fps=100)
            downbeats = downbeat_tracker(downbeat_act)

            return {
                "beats": [float(item) for item in list(beats)],
                "downbeats": [[float(row[0]), int(row[1])] for row in list(downbeats)],
                "backend": "madmom",
            }

        librosa = optional_import("librosa")
        numpy = optional_import("numpy")
        if librosa is None or numpy is None:
            raise RuntimeError("Audio timing requires either madmom or librosa")

        audio, sr = librosa.load(str(audio_file), sr=None, mono=True)
        tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr, hop_length=512, units="frames")
        beat_times = librosa.frames_to_time(numpy.asarray(beat_frames), sr=sr, hop_length=512)
        beats = [float(item) for item in list(beat_times)]
        downbeats = [[float(time), 1] for idx, time in enumerate(beats) if idx % 4 == 0]

        return {
            "beats": beats,
            "downbeats": downbeats,
            "backend": "librosa",
            "tempo": float(numpy.asarray(tempo).reshape(-1)[0]) if numpy.asarray(tempo).size else 0.0,
        }

    # ----------------------
    # ESSENTIA (FEATURES)
    # ----------------------
    def extract_features(self, audio_file):
        essentia = optional_import("essentia.standard")
        if essentia is not None:
            loader = essentia.MonoLoader(filename=str(audio_file))
            audio = loader()

            frame_size = 1024
            hop_size = 512

            window = essentia.Windowing(type="hann")
            spectrum = essentia.Spectrum()

            energy = []
            centroid = []

            for frame in essentia.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
                spec = spectrum(window(frame))
                energy.append(float(essentia.Energy()(frame)))
                centroid.append(float(essentia.Centroid()(spec)))

            tempo, _, _, _, _ = essentia.RhythmExtractor2013()(audio)

            return {
                "energy": energy,
                "centroid": centroid,
                "tempo": float(tempo),
                "backend": "essentia",
            }

        librosa = optional_import("librosa")
        numpy = optional_import("numpy")
        if librosa is None or numpy is None:
            raise RuntimeError("Audio features require either essentia or librosa")

        audio, sr = librosa.load(str(audio_file), sr=None, mono=True)
        hop_size = 512
        rms = librosa.feature.rms(y=audio, hop_length=hop_size)[0]
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr, hop_length=hop_size)[0]
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sr, hop_length=hop_size, units="frames")

        return {
            "energy": [float(item) for item in list(rms)],
            "centroid": [float(item) for item in list(centroid)],
            "tempo": float(numpy.asarray(tempo).reshape(-1)[0]) if numpy.asarray(tempo).size else 0.0,
            "backend": "librosa",
        }

    # ----------------------
    # FEATURE STATE ENGINE
    # ----------------------
    def build_feature_state(self, features, history_size=128, ema_alpha=0.2):
        features = self._normalized_features(features)
        frames = build_feature_state_sequence(
            features,
            fps=float(self.fps),
            history_size=history_size,
            ema_alpha=ema_alpha,
        )
        return serialize_feature_state_sequence(frames)

    def _normalized_features(self, features):
        out = dict(features)
        energy = [float(item) for item in list(out.get("energy", []))]
        peak = max(energy) if energy else 0.0
        if peak > 0.0:
            out["energy"] = [item / peak for item in energy]
        return out

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
                "brightness": None,
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
        feature_state = self.build_feature_state(features)
        timeline = self.build_timeline(timing, features)

        return {
            "timing": timing,
            "features": features,
            "feature_state": feature_state,
            "timeline": timeline,
        }
