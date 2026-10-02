from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_drummer_v3_png_layers.py"
MANIFEST = ROOT / "fixtures" / "band_geometry" / "drummer_v3_png_layer_manifest.json"

REQUIRED_FRAMES = {
    "idle_ready",
    "kick_hit",
    "snare_hit",
    "hi_hat_pulse",
    "left_tom_hit",
    "right_tom_hit",
    "floor_tom_hit",
    "left_crash",
    "right_crash",
    "downbeat_impact",
}


def _run_builder(source: Path, layers_dir: Path, preview_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--source",
            str(source),
            "--manifest",
            str(MANIFEST),
            "--layers-dir",
            str(layers_dir),
            "--preview-dir",
            str(preview_dir),
            "--overwrite",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_drummer_v3_manifest_declares_png_input_and_frames() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["source_image"] == "fixtures/band_geometry/source/drummerbg.png"
    assert manifest["contact_sheet"] == "HX_SNOWMAN_DRUMMER_V3_pose_sheet.png"
    assert set(manifest["required_frames"]) == REQUIRED_FRAMES
    assert len(manifest["layers"]) == 9

    layer_ids = {layer["id"] for layer in manifest["layers"]}
    assert REQUIRED_FRAMES - {"idle_ready"} <= layer_ids
    layers = {layer["id"]: layer for layer in manifest["layers"]}
    assert layers["hi_hat_pulse"]["contact_components"] == ["foot", "pedal"]
    assert all("stick" not in item for item in layers["hi_hat_pulse"]["contact_components"])
    assert "floor_tom_hit" in layers

    for layer in manifest["layers"]:
        assert layer["file"].endswith(".png")
        assert layer["target_components"]
        assert layer["contact_components"]
        assert layer["commands"]


def test_drummer_v3_builder_reports_absent_png_input(tmp_path: Path) -> None:
    source = tmp_path / "no_drummerbg.png"
    result = _run_builder(source, tmp_path / "layers", tmp_path / "previews")

    assert result.returncode == 1
    assert "no_drummerbg.png" in result.stderr


def test_drummer_v3_builder_creates_transparent_layers_and_contact_sheet(tmp_path: Path) -> None:
    source = tmp_path / "drummerbg.png"
    Image.new("RGBA", (320, 240), (40, 40, 50, 255)).save(source)

    layers_dir = tmp_path / "layers"
    preview_dir = tmp_path / "previews"
    result = _run_builder(source, layers_dir, preview_dir)

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["layer_count"] == 9
    assert payload["frame_count"] == 10

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for layer in manifest["layers"]:
        layer_path = layers_dir / layer["file"]
        assert layer_path.exists(), layer_path
        with Image.open(layer_path) as img:
            assert img.size == (320, 240)
            assert img.mode == "RGBA"
            alpha_min, alpha_max = img.getchannel("A").getextrema()
            assert alpha_min == 0
            assert alpha_max > 0
            assert img.getbbox() is not None

    contact_sheet = preview_dir / manifest["contact_sheet"]
    assert contact_sheet.exists()
    with Image.open(contact_sheet) as img:
        assert img.width > 0
        assert img.height > 0
        assert img.getbbox() is not None


def test_drummer_v3_builder_rejects_tiny_input_png(tmp_path: Path) -> None:
    source = tmp_path / "drummerbg.png"
    Image.new("RGBA", (32, 32), (255, 255, 255, 255)).save(source)

    result = _run_builder(source, tmp_path / "layers", tmp_path / "previews")

    assert result.returncode == 1
    assert "too small" in result.stderr
