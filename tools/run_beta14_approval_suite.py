"""One invocation, one source analysis, three native approval render commands.

This shared Python entry point can be invoked by Windows Helix or an Android
backend. It is NOT an Android APK integration or a native renderer itself.
Each renderer must write a verified receipt at <output>/<role>/receipt.json.
Commands are supplied explicitly; no placeholders are silently accepted.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from tools.build_shared_approval_analysis import create, verify
from tools.verify_shared_approval_source import verify as verify_three

ROLES = ("16-panel", "12-layout", "six-snowman-band")


def run_suite(source, stems, output, commit, commands, *, runner=subprocess.run):
    source = Path(source).resolve(strict=True)
    stems = Path(stems).resolve(strict=True)
    output = Path(output).resolve()
    if set(commands) != set(ROLES):
        raise ValueError("Three real renderer commands required")
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "shared_analysis.json"
    create(source, stems, manifest_path, commit)
    shared = verify(source, stems, manifest_path)
    receipts = []
    for role in ROLES:
        verify(source, stems, manifest_path)
        command = commands[role]
        if not isinstance(command, list) or not command or not all(isinstance(s, str) and s for s in command):
            raise ValueError(f"Invalid {role} renderer command")
        role_dir = output / role
        role_dir.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, HELIX_APPROVAL_AUDIO=str(source),
                   HELIX_APPROVAL_ANALYSIS_MANIFEST=str(manifest_path),
                   HELIX_APPROVAL_STEMS=str(stems), HELIX_APPROVAL_OUTPUT=str(role_dir),
                   HELIX_APPROVAL_ROLE=role, HELIX_APPROVAL_SOURCE_SHA256=shared["source_audio_sha256"],
                   HELIX_APPROVAL_ANALYSIS_SHA256=shared["analysis_sha256"])
        runner(command, check=True, env=env)
        receipt_path = role_dir / "receipt.json"
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("role") != role:
            raise ValueError(f"Renderer did not supply the correct {role} receipt")
        for key, expected in (("source_audio_sha256", shared["source_audio_sha256"]),
                              ("analysis_sha256", shared["analysis_sha256"]),
                              ("source_commit", commit)):
            if receipt.get(key) != expected:
                raise ValueError(f"{role} did not consume shared {key}")
        media = receipt.get("mp4")
        if not isinstance(media, dict) or not media.get("path") or not media.get("sha256"):
            raise ValueError(f"{role} missing MP4 file evidence")
        movie = (role_dir / media["path"]).resolve()
        if not movie.is_relative_to(role_dir) or not movie.is_file() or movie.stat().st_size < 1024:
            raise ValueError(f"{role} MP4 missing, outside output, or too small")
        digest = hashlib.sha256()
        with movie.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != media["sha256"]:
            raise ValueError(f"{role} MP4 SHA256 mismatch")
        # A hash only proves byte identity; ffprobe proves this is a decodable
        # media container with the required video and original soundtrack.
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format",
             "-of", "json", str(movie)], capture_output=True, text=True, check=True)
        info = json.loads(probe.stdout)
        video = [stream for stream in info.get("streams", []) if stream.get("codec_type") == "video"]
        audio = [stream for stream in info.get("streams", []) if stream.get("codec_type") == "audio"]
        if len(video) != 1 or not audio:
            raise ValueError(f"{role} MP4 missing video or audio")
        v = video[0]
        if (v.get("codec_name") != "h264" or int(v.get("width", 0)) != 1920
                or int(v.get("height", 0)) != 1080 or v.get("avg_frame_rate") != "30/1"):
            raise ValueError(f"{role} MP4 must be H264 1920x1080 30fps")
        if not any(a.get("codec_name") == "aac" for a in audio):
            raise ValueError(f"{role} MP4 must contain AAC audio")
        if float(info.get("format", {}).get("duration", 0)) <= 0:
            raise ValueError(f"{role} MP4 duration invalid")
        receipts.append(receipt_path)
    verify(source, stems, manifest_path)
    result = verify_three(receipts)
    (output / "approval_suite_receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audio", required=True, type=Path)
    p.add_argument("--stems", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--source-commit", required=True)
    for role in ROLES:
        p.add_argument("--render-" + role, required=True, nargs="+", metavar="ARG",
                       help="Executable and arguments for this native renderer (terminate with next option)")
    args = p.parse_args()
    commands = {role: getattr(args, "render_" + role.replace("-", "_")) for role in ROLES}
    print(json.dumps(run_suite(args.audio, args.stems, args.output, args.source_commit, commands), indent=2))


if __name__ == "__main__":
    main()
