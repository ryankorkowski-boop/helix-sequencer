"""Owner-locked 3x3 pilot selection from existing native 16-layout inventory.

This is a non-rendering selection manifest. It deliberately does not claim that
the selected source panels already meet the new musical or visual acceptance gates.
"""
from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Panel:
    position: int
    name: str
    source_panel: int
    required_upgrade: str


PANELS = (
    Panel(1, "16-channel LOR AC", 1, "Preserve exactly sixteen AC channels"),
    Panel(2, "256-channel legacy AC", 3, "Add owner-approved arches and mega tree without changing AC channel addresses"),
    Panel(3, "RGB-heavy architectural house", 12, "Use dense realistic house and nested RGB routing"),
    Panel(4, "Coro singing-face house", 8, "Require qualified vocal activity and readable mouth shapes"),
    Panel(5, "Canonical six-member snowman band", 11, "Preserve V3 drummer and verify all six instrument roles"),
    Panel(6, "Pixel singing trees and matrices", 9, "Add dense matrices; qualify independent face sources"),
    Panel(7, "Birdsong spatial matrix", 15, "Build nested 3D matrix and verify Birdsong call/echo routing"),
    Panel(8, "Piano sequential instrument groups", 14, "Implement source-qualified note/chord/keyboard-driven sequential groups"),
    Panel(9, "Ultimate xLights megashow", 16, "Scale spiral trees and matrices with bounded native render memory"),
)


def manifest():
    assert len(PANELS) == 9
    assert [p.position for p in PANELS] == list(range(1, 10))
    assert len({p.source_panel for p in PANELS}) == 9
    return {
        "status": "layout_selection_only_not_rendered_or_approved",
        "rows": 3,
        "columns": 3,
        "resolution": [1920, 1080],
        "source_inventory": "docs/FULL_SONG_SHOWCASE_REBUILD.md",
        "panels": [asdict(p) for p in PANELS],
        "approval_required": True,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(manifest(), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
