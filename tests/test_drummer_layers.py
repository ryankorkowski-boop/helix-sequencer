from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "generate_drummer_layers.py"
VALIDATOR = ROOT / "tools" / "validate_drummer_layers.py"
MANIFEST = ROOT / "assets" / "drummers" / "snowman_locked" / "drummer_layers.yaml"


def test_drummer_generator_creates_dim_base_and_transparent_overlays(tmp_path: Path) -> None:
    source = tmp_path / "source_drummer.png"
    source_img = Image.new("RGBA", (128, 128), (200, 200, 200, 255))
    source_img.save(source)

    out_dir = tmp_path / "snowman_locked"
    result = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--source",
            str(source),
            "--manifest",
            str(MANIFEST),
            "--out-dir",
            str(out_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr + result.stdout

    base = out_dir / "drummer_base_locked_dim.png"
    right_tom = out_dir / "drummer_hit_right_tom.png"
    crash_right = out_dir / "drummer_hit_crash_right.png"

    assert base.exists()
    assert right_tom.exists()
    assert crash_right.exists()

    with Image.open(base) as img:
        assert img.size == (2048, 2048)
        assert img.mode == "RGBA"

    with Image.open(right_tom) as img:
        assert img.size == (2048, 2048)
        assert img.mode == "RGBA"
        assert img.getbbox() is None  # fully transparent placeholder


def test_drummer_validator_accepts_generated_stack(tmp_path: Path) -> None:
    source = tmp_path / "source_drummer.png"
    Image.new("RGBA", (64, 64), (255, 255, 255, 255)).save(source)
    out_dir = tmp_path / "snowman_locked"

    subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--source",
            str(source),
            "--manifest",
            str(MANIFEST),
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--manifest",
            str(MANIFEST),
            "--asset-dir",
            str(out_dir),
            "--strict-missing",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr + result.stdout
