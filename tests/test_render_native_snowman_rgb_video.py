"""Native seven-model RGB renderer rejects incomplete or fabricated input."""
import csv
import hashlib
import subprocess
import json
from pathlib import Path
import pytest
from tools.render_native_snowman_rgb_video import layout, render, ROLES


def fixture(tmp_path):
    models = []
    for role in ROLES:
        name = "HX_SNOW_" + role.upper()
        filename = name + "_positions.csv"
        with (tmp_path / filename).open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["node_or_circuit", "design_x", "design_y"])
            w.writeheader()
            w.writerow(dict(node_or_circuit=1, design_x=0, design_y=0))
        models.append(dict(name=name, role=role, mode="pixel",
                           geometry_positions=1, coordinate_csv=filename))
    (tmp_path / "audit.json").write_text(json.dumps(dict(models=models)))
    return tmp_path


def test_seven_native_models(tmp_path):
    assert len(layout(fixture(tmp_path))) == 7


def test_missing_role_rejected(tmp_path):
    folder = fixture(tmp_path)
    manifest = json.loads((folder / "audit.json").read_text())
    manifest["models"].pop()
    (folder / "audit.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="seven"):
        layout(folder)


def test_partial_native_rgb_frame_rejected(tmp_path):
    folder = fixture(tmp_path)
    frames = folder / "frames.rgb"
    frames.write_bytes(b"\x00" * 20)  # 7 nodes * 3 channels = 21 bytes per frame
    audio = folder / "audio.wav"
    audio.write_bytes(b"placeholder")
    with pytest.raises(ValueError, match="complete"):
        render(folder, frames, audio, folder / "out.mp4")


def test_duplicate_native_pixel_ids_rejected(tmp_path):
    folder = fixture(tmp_path)
    p = folder / "HX_SNOW_DRUMMER_positions.csv"
    with p.open("a") as f:
        f.write("1,1,1\n")
    manifest = json.loads((folder / "audit.json").read_text())
    manifest["models"][0]["geometry_positions"] = 2
    (folder / "audit.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="unique"):
        layout(folder)

def test_encodes_real_native_frame_video(tmp_path):
    folder = fixture(tmp_path)
    frames = folder / "frames.rgb"
    frames.write_bytes(bytes([255, 0, 0] * 7 * 20))
    audio = folder / "audio.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=1", "-y", str(audio)], check=True)
    output = folder / "native.mp4"
    report = render(folder, frames, audio, output, fps=20, width=640, height=360)
    assert output.stat().st_size > 100
    assert report["frames"] == 20
    assert report["video_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert report["musical_accuracy_independently_verified"] is False
    assert report["audio_synchronized"] is False

def test_audio_frame_duration_mismatch_rejected(tmp_path):
    folder = fixture(tmp_path)
    frames = folder / "frames.rgb"
    frames.write_bytes(bytes([255, 0, 0] * 7 * 10))  # 0.5 seconds at 20 fps
    audio = folder / "audio.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=1", "-y", str(audio)], check=True)
    with pytest.raises(ValueError, match="duration does not match"):
        render(folder, frames, audio, folder / "mismatched.mp4", fps=20, width=640, height=360)
