#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from build_allmodels_pack import build_allmodels_pack


ROOT = Path(__file__).resolve().parent
MANUAL_DIR = ROOT / "allmodels"


def resolve_generation_pack() -> dict[str, Path]:
    manual_layout = MANUAL_DIR / "xlights_rgbeffects.xml"
    manual_audio_candidates = [
        ROOT / "2.wav",
        MANUAL_DIR / "2.wav",
        MANUAL_DIR / "13.wav",
    ]
    manual_audio = next((path for path in manual_audio_candidates if path.exists()), None)
    manual_template_candidates = [
        MANUAL_DIR / "pixelstest.xsq",
        MANUAL_DIR / "13.xsq",
        MANUAL_DIR / "template2.xsq",
    ]
    manual_template = next((path for path in manual_template_candidates if path.exists()), None)
    if manual_layout.exists() and manual_audio is not None and manual_template is not None:
        print(
            "Using existing manual allmodels source: "
            f"template={manual_template.name}, layout={manual_layout.name}, audio={manual_audio.name}"
        )
        return {
            "template": manual_template,
            "layout": manual_layout,
            "audio": manual_audio,
        }
    return build_allmodels_pack()

RUNS = [
    ("v20.1.py", ROOT / "allmodels" / "final" / "v20.1", []),
    ("v20.2.py", ROOT / "allmodels" / "final" / "v20.2", []),
    ("v20.3.py", ROOT / "allmodels" / "final" / "v20.3", []),
    ("v21.1.py", ROOT / "allmodels" / "final" / "v21.1", []),
    ("v21.2.py", ROOT / "allmodels" / "final" / "v21.2", ["--spatial-awareness", "0.42", "--chase-style", "wave", "--keyboard-mix", "0.12"]),
    ("v21.3.py", ROOT / "allmodels" / "final" / "v21.3", []),
    ("v21.4.py", ROOT / "allmodels" / "final" / "v21.4", []),
    ("v21.5.py", ROOT / "allmodels" / "final" / "v21.5", []),
    ("v21.6.py", ROOT / "allmodels" / "final" / "v21.6", []),
    ("v22.1.py", ROOT / "allmodels" / "final" / "v22.1", ["--spatial-awareness", "0.58", "--chase-style", "left_to_right", "--keyboard-mix", "0.22"]),
    ("v22.2.py", ROOT / "allmodels" / "final" / "v22.2", ["--spatial-awareness", "0.42", "--chase-style", "group_to_group", "--keyboard-mix", "0.12"]),
    ("v22.3.py", ROOT / "allmodels" / "final" / "v22.3", ["--spatial-awareness", "0.62", "--chase-style", "wave", "--keyboard-mix", "0.18"]),
    ("v23.1.py", ROOT / "allmodels" / "final" / "v23.1", ["--spatial-awareness", "0.34", "--chase-style", "group_to_group", "--keyboard-mix", "0.12"]),
    ("v23.2.py", ROOT / "allmodels" / "final" / "v23.2", ["--spatial-awareness", "0.26", "--chase-style", "group_to_group", "--keyboard-mix", "0.08"]),
    ("v23.3.py", ROOT / "allmodels" / "final" / "v23.3", ["--spatial-awareness", "0.38", "--chase-style", "wave", "--keyboard-mix", "0.10"]),
    ("v23.4.py", ROOT / "allmodels" / "final" / "v23.4", ["--spatial-awareness", "0.34", "--chase-style", "group_to_group", "--keyboard-mix", "0.08"]),
    ("v23.5.py", ROOT / "allmodels" / "final" / "v23.5", ["--spatial-awareness", "0.42", "--chase-style", "wave", "--keyboard-mix", "0.10"]),
    ("v23.6.py", ROOT / "allmodels" / "final" / "v23.6", ["--spatial-awareness", "0.52", "--chase-style", "wave", "--keyboard-mix", "0.12"]),
]


def run() -> int:
    pack = resolve_generation_pack()
    for script_name, output_dir, tuning_args in RUNS:
        cmd = [
            sys.executable,
            str(ROOT / script_name),
            "--template", str(pack["template"]),
            "--audio", str(pack["audio"]),
            "--layout-file", str(pack["layout"]),
            "--output-dir", str(output_dir),
            "--no-prompt",
            "--no-save-settings",
            "--no-workspace-history",
            "--layering-mode", "smart_layer",
            "--strict-xlights-effects",
        ] + tuning_args
        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True, cwd=ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
