from __future__ import annotations

import json
import subprocess
import sys
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools/build_drummer_v3_png_layers.py"
MANIFEST = ROOT / "fixtures/band_geometry/drummer_v3_png_layer_manifest.json"
XMODEL = ROOT / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"
SOURCE = ROOT / "fixtures/band_geometry/source/drummerbg.png"

REQUIRED_FRAMES = {
    "idle_ready", "kick_hit", "snare_hit", "hi_hat_pulse",
    "tom_high_hit", "tom_mid_hit", "tom_floor_hit",
    "left_crash", "right_crash", "both_crash", "downbeat_impact",
}


def _run_builder(source: Path, layers_dir: Path, preview_dir: Path):
    return subprocess.run(
        [sys.executable, str(BUILDER), "--source", str(source), "--manifest", str(MANIFEST),
         "--xmodel", str(XMODEL), "--layers-dir", str(layers_dir),
         "--preview-dir", str(preview_dir), "--overwrite"],
        check=False, capture_output=True, text=True,
    )


def test_manifest_selects_canonical_targets_without_duplicate_geometry_commands() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["xmodel_path"].endswith("HX_SNOWMAN_DRUMMER_V3.xmodel")
    assert set(manifest["required_frames"]) == REQUIRED_FRAMES
    assert len(manifest["layers"]) == 10
    for layer in manifest["layers"]:
        assert layer["file"].endswith(".png")
        assert layer["targets"]
        assert "commands" not in layer


def test_builder_reports_absent_png_input(tmp_path: Path) -> None:
    result = _run_builder(tmp_path / "missing.png", tmp_path / "layers", tmp_path / "previews")
    assert result.returncode == 1
    assert "missing.png" in result.stderr


def test_builder_creates_exact_source_pixel_layers_and_contact_sheet(tmp_path: Path) -> None:
    source = tmp_path / "drummerbg.png"
    shutil.copyfile(SOURCE, source)
    layers_dir, preview_dir = tmp_path / "layers", tmp_path / "previews"
    result = _run_builder(source, layers_dir, preview_dir)
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["layer_count"] == 10 and payload["frame_count"] == 11
    assert "exact drummerbg source pixels" in payload["geometry_source"]

    with Image.open(SOURCE) as canonical:
        expected_size = canonical.size
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for layer in manifest["layers"]:
        path = layers_dir / layer["file"]
        assert path.exists()
        with Image.open(path) as image:
            assert image.size == expected_size and image.mode == "RGBA"
            assert image.getchannel("A").getextrema() == (0, 255)
    assert (preview_dir / manifest["contact_sheet"]).exists()


def test_builder_rejects_tiny_input_png(tmp_path: Path) -> None:
    source = tmp_path / "drummerbg.png"
    Image.new("RGBA", (32, 32), (255, 255, 255, 255)).save(source)
    result = _run_builder(source, tmp_path / "layers", tmp_path / "previews")
    assert result.returncode == 1
    assert "too small" in result.stderr
