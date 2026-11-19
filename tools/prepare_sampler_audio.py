"""Extract a source-bound PCM WAV and provenance manifest from an uploaded MP4."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command(args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def prepare(video, output_dir, *, overwrite=False):
    video, output_dir = Path(video).resolve(), Path(output_dir)
    if not video.is_file():
        raise FileNotFoundError(video)
    output_dir.mkdir(parents=True, exist_ok=True)
    wav = output_dir / (video.stem + "_audio.wav")
    manifest = output_dir / (video.stem + "_source.json")
    if not overwrite and (wav.exists() or manifest.exists()):
        raise FileExistsError("Output exists; specify --overwrite to replace")
    probe = json.loads(command(["ffprobe", "-v", "error", "-show_streams",
                                "-show_format", "-of", "json", str(video)]))
    audio = [s for s in probe["streams"] if s["codec_type"] == "audio"]
    if not audio:
        raise ValueError("Input contains no audio stream")
    partial = wav.with_suffix(".partial.wav")
    try:
        command(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(video),
                 "-map", "0:a:0", "-vn", "-ac", "2", "-ar", "44100",
                 "-c:a", "pcm_s16le", str(partial)])
        duration = float(probe["format"]["duration"])
        decoded = float(json.loads(command(["ffprobe", "-v", "error",
                        "-show_format", "-of", "json", str(partial)]))["format"]["duration"])
        # AAC encoder delay/padding can make decoded PCM slightly longer.
        if abs(decoded - duration) > 0.25:
            raise ValueError("Audio duration differs by more than 250 ms")
        data = dict(source_video_name=video.name, source_video_sha256=sha256(video),
                    source_video_duration_seconds=duration,
                    source_audio_codec=audio[0]["codec_name"],
                    extracted_audio_name=wav.name, extracted_audio_sha256=sha256(partial),
                    extracted_audio_duration_seconds=decoded,
                    audio_sample_rate=44100, audio_channels=2,
                    status="audio_extracted_only",
                    original_sampler_identity_verified=False,
                    instrument_analysis_verified=False)
        partial.replace(wav)
        manifest.write_text(json.dumps(data, indent=2) + "\n")
        return data
    finally:
        partial.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    print(json.dumps(prepare(args.video, args.output_dir, overwrite=args.overwrite), indent=2))


if __name__ == "__main__":
    main()
