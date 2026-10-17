"""Fail-closed provenance gate for real seven-member Snowman Band review videos.

A model-coordinate still or authored diagnostic cannot satisfy this contract.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROLES = ("drummer", "bass", "guitar", "piano", "xylophone", "lead", "harmony")


def verify(report: dict, video: Path) -> None:
    if not video.is_file() or video.stat().st_size <= 0:
        raise ValueError("Missing nonempty performance MP4")
    if video.suffix.lower() != ".mp4":
        raise ValueError("Expected an MP4")
    if report.get("fixture") or report.get("diagnostic") or report.get("authored_fixture"):
        raise ValueError("Authored diagnostic cannot pass real-song showcase gate")
    if report.get("layout_source") != "native_HX_SNOW":
        raise ValueError("Video must render the native seven-member HX_SNOW layout")
    if sorted(report.get("roles", [])) != sorted(ROLES):
        raise ValueError("All seven distinct performers must be present")
    if len(set(report.get("model_names", []))) != 7 or set(report["model_names"]) != {
        "HX_SNOW_" + role.upper() for role in ROLES
    }:
        raise ValueError("All seven native model names must match")
    if not report.get("source_audio_sha256") or len(report["source_audio_sha256"]) != 64:
        raise ValueError("Source audio SHA-256 is required")
    if not report.get("source_analysis_provenance"):
        raise ValueError("Source analysis provenance is required")
    if report.get("musical_accuracy_independently_verified") is not True:
        raise ValueError("Musical accuracy requires independent verification")
    if report.get("full_decode_passed") is not True:
        raise ValueError("Full video decode has not been verified")
    if report.get("audio_synchronized") is not True:
        raise ValueError("Audio synchronization has not been verified")
    if report.get("full_song_showcase_complete") is not True:
        raise ValueError("Full-song completion has not been verified")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("report", type=Path)
    p.add_argument("video", type=Path)
    a = p.parse_args()
    verify(json.loads(a.report.read_text(encoding="utf-8")), a.video)
    print("Seven-member native musical showcase provenance gate passed")


if __name__ == "__main__":
    main()
