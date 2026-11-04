"""Build the argv the GUI sends to main.py.

Kept separate from gui_launcher so tests can check flags without Tk.
"""

from __future__ import annotations

from pathlib import Path


def build_operator_command(
    *,
    python: str,
    main_py: str,
    profile: str,
    template: str,
    audio: str,
    layout: str,
    output_dir: str,
    variants: int,
    vendor_bar: bool,
    matrix: bool,
    polish: bool,
    shortlist: bool,
    workspace_history: bool,
    birdsong: bool,
    birdsong_profile: str,
    birdsong_intensity: float,
    birdsong_min_confidence: float,
    birdsong_auto: bool,
) -> list[str]:
    """Return the main.py command for one GUI run.

    Vendor bar forces polish, auto-shortlist, and workspace history inside
    effect_engine. Those flags are sent explicitly so the command matches
    the engine. Matrix and birdsong follow the checkboxes.
    """

    cmd = [
        python,
        main_py,
        "--profile",
        profile.strip() or "master",
        "--",
        "--template",
        template,
        "--audio",
        audio,
        "--layout-file",
        layout,
        "--output-dir",
        output_dir,
        "--variants",
        str(max(1, int(variants))),
        "--no-prompt",
    ]
    if vendor_bar:
        cmd.append("--vendor-bar")
    cmd.append("--matrix-intelligence" if matrix else "--no-matrix-intelligence")
    if vendor_bar or polish:
        cmd.append("--polish")
    else:
        cmd.append("--no-polish")
    if vendor_bar or shortlist:
        cmd.append("--auto-shortlist")
    if vendor_bar or workspace_history:
        cmd.append("--workspace-history")
    else:
        cmd.append("--no-workspace-history")
    if birdsong:
        cmd.extend(
            [
                "--birdsong",
                "--birdsong-profile",
                (birdsong_profile or "wild").strip() or "wild",
                "--birdsong-intensity",
                f"{float(birdsong_intensity):.2f}",
                "--birdsong-min-confidence",
                f"{float(birdsong_min_confidence):.2f}",
            ]
        )
        if birdsong_auto:
            cmd.append("--birdsong-auto")
    return cmd


def newest_canonical_xsq(output_dir: Path, audio: Path, version: str) -> Path | None:
    """Pick the newest effect_engine XSQ for this audio, skipping orchestrator sidecars."""

    prefix = f"{audio.stem},{version}"
    candidates = [
        path
        for path in output_dir.glob(f"{prefix}*.xsq")
        if path.is_file() and ".orchestrated." not in path.name
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def operator_run_notes(*, audio: str, vendor_bar: bool) -> list[str]:
    stem = Path(audio).stem or "audio"
    notes = [
        f"Import the effect_engine XSQ (name starts with {stem}, and a profile version), not {stem}.orchestrated.xsq.",
        f"{stem}.orchestrated.xsq is a sidecar from a fixed planning graph. It is not the audio sequence.",
        "Beat-grid snapping does not move effect rows unless you pass --snap-grid yourself.",
    ]
    if vendor_bar:
        notes.append("Vendor bar forces polish, auto-shortlist, and Helix workspace history.")
    return notes
