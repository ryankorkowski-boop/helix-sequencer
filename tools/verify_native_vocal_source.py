"""Reject unqualified full-band sources before an expensive native build."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from models.band_sampler_logic import SHAPE_NAMES


def verify(audio: Path, analysis: Path) -> dict:
    report = json.loads((analysis / "voice_roles.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    if report.get("source_sha256") != digest:
        raise ValueError("Vocal analysis does not belong to this source audio")
    if report.get("mixed_bus_only") or not report.get("voice_identity_resolved") or report.get("independent_tracks", 0) < 2:
        raise ValueError("Full-band source lacks independently resolved lead and backing vocal tracks; supply source-bound vocal analysis instead of repeating the silent-harmony render")
    tracks = report.get("input_tracks", {})
    lanes = report.get("model_lanes", [])
    if len(lanes) != 2 or {item.get("model_lane") for item in lanes} != {0, 1}:
        raise ValueError("Lead and backing require distinct model lanes")
    fingerprints = []
    for item in lanes:
        expected = {"lead"} if item["model_lane"] == 0 else {"second", "background"}
        track = tracks.get(item.get("name"), {})
        if item.get("role") not in expected or track.get("evidence") not in {"individual", "ensemble"} or track.get("duplicate_of"):
            raise ValueError("Vocal model lanes lack independent source ownership")
        if track.get("origin") == "model_estimate":
            raise ValueError("Model-estimated vocal candidates are not verified independent singer sources")
        fingerprints.append(track.get("sha256"))
    if any(not isinstance(value, str) or len(value) != 64 for value in fingerprints) or len(set(fingerprints)) != 2:
        raise ValueError("Duplicate or missing vocal source fingerprints")
    frames = round(sf.info(audio).duration * 20)
    with np.load(analysis / "voice_roles.npz", allow_pickle=False) as data:
        energy, shapes = data["energy"], data["shapes"]
        if (energy.shape != (frames, 2) or shapes.shape != energy.shape
                or not np.isfinite(energy).all() or not np.isfinite(shapes).all()
                or np.any(energy < 0) or np.any(energy > 1)
                or np.any(shapes != np.floor(shapes)) or np.any(shapes < 0)
                or np.any(shapes >= len(SHAPE_NAMES))):
            raise ValueError("Invalid source-bound vocal frame arrays")
        # A mouth must be REST whenever its source lane is silent. Otherwise
        # stale phoneme shapes can animate a singer during instrumental gaps.
        rest = SHAPE_NAMES.index("REST")
        if np.any((energy == 0) & (shapes != rest)):
            raise ValueError("Silent vocal frames contain non-REST mouth shapes")
        if np.any((energy > 0) & (shapes == rest)):
            raise ValueError("Active vocal frames contain REST mouth shapes")
        active = np.sum((energy > 0) & (shapes != SHAPE_NAMES.index("REST")), axis=0)
    if not np.all(active > 0):
        raise ValueError("Full-band source has an empty lead/backing non-rest vocal lane; no render can repair absent source events")
    # Distinct source fingerprints alone do not prove independent mouth clocks.
    # A copied vocal lane can have a different file hash after re-encoding.
    # Re-encoding, gain changes or tiny noise can make copies byte-distinct.
    # Reject a proportional copy only when *all* active/rest decisions and
    # mouth shapes match, with negligible normalized envelope residual.
    lead, backing = energy[:, 0], energy[:, 1]
    if np.array_equal(shapes[:, 0], shapes[:, 1]) and np.array_equal(lead > 0, backing > 0):
        active_mask = lead > 0
        if np.any(active_mask):
            x, y = lead[active_mask].astype("float64"), backing[active_mask].astype("float64")
            gain = float(np.dot(x, y) / max(np.dot(x, x), 1e-12))
            residual = float(np.linalg.norm(y - gain * x) / max(np.linalg.norm(y), 1e-12))
            if gain > 0 and residual < 1e-4:
                raise ValueError("Lead and backing mouth clocks are identical or gain-scaled copies; independent vocal activity not demonstrated")
    return {"passed": True, "audio_sha256": digest, "frames": frames,
            "non_rest_frames": {"lead": int(active[0]), "harmony": int(active[1])},
            "limit": "Source qualification only; native output and artistic acceptance remain separate"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.audio, args.analysis)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {"passed": False, "error": str(exc)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
