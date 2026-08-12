from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from helix.preview.drummer_v3 import DrummerV3RenderEvent, illumination_targets_for_pose
from helix.preview.pillow_renderer import PillowRenderer


def _assets(tmp_path: Path) -> Path:
    root = tmp_path / "assets"
    backdrop = root / "fixtures/band_geometry/source/drummerbg_preview_backdrop.png"
    backdrop.parent.mkdir(parents=True)
    Image.new("RGBA", (100, 100), (10, 10, 10, 255)).save(backdrop)
    manifest = root / "fixtures/band_geometry/drummer_v3_png_layer_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "layers": [
                    {
                        "id": "kick_hit",
                        "target_components": ["kick_drum"],
                        "commands": [
                            {
                                "shape": "ellipse",
                                "box": [0.4, 0.4, 0.6, 0.6],
                                "rgba": [255, 245, 120, 220],
                                "glow": 0,
                            }
                        ],
                    },
                    {
                        "id": "snare_hit",
                        "target_components": ["snare"],
                        "commands": [
                            {
                                "shape": "ellipse",
                                "box": [0.1, 0.1, 0.3, 0.3],
                                "rgba": [255, 245, 120, 220],
                                "glow": 0,
                            }
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    return root


def test_no_event_preserves_authored_base(tmp_path: Path) -> None:
    root = _assets(tmp_path)
    renderer = PillowRenderer(width=100, height=100)
    frame = renderer.render_drummer_v3(root, [], 0)
    assert frame.getpixel((50, 50)) == (10, 10, 10, 255)


def test_kick_illuminates_target_without_replacing_base(tmp_path: Path) -> None:
    root = _assets(tmp_path)
    renderer = PillowRenderer(width=100, height=100)
    event = DrummerV3RenderEvent(0, 100, "kick_hit", 1.0, ("HX_SNOWMAN_DRUMMER_V3_KICK",))
    frame = renderer.render_drummer_v3(root, [event], 50)
    assert frame.getpixel((50, 50)) != (10, 10, 10, 255)
    assert frame.getpixel((5, 5)) == (10, 10, 10, 255)
    assert frame.getpixel((50, 50))[0] > frame.getpixel((5, 5))[0]


def test_simultaneous_events_illuminate_multiple_targets(tmp_path: Path) -> None:
    root = _assets(tmp_path)
    renderer = PillowRenderer(width=100, height=100)
    events = [
        DrummerV3RenderEvent(0, 100, "kick_hit", 1.0, ("HX_SNOWMAN_DRUMMER_V3_KICK",)),
        DrummerV3RenderEvent(0, 100, "snare_hit", 1.0, ("HX_SNOWMAN_DRUMMER_V3_SNARE",)),
    ]
    frame = renderer.render_drummer_v3(root, events, 50)
    assert frame.getpixel((50, 50))[0] > 10
    assert frame.getpixel((20, 20))[0] > 10
    assert frame.getpixel((90, 90)) == (10, 10, 10, 255)


def test_pose_targets_are_named_physical_submodels(tmp_path: Path) -> None:
    root = _assets(tmp_path)
    assert illumination_targets_for_pose(root, "kick_hit") == ("HX_SNOWMAN_DRUMMER_V3_KICK",)
    assert illumination_targets_for_pose(root, "snare_hit") == ("HX_SNOWMAN_DRUMMER_V3_SNARE",)
