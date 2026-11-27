"""Android imports a desktop vocal bundle. It does not run the separator."""
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "android/app/src/main/python"))
from helix_mobile import bind_imported_vocals, install_vocal_bundle


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bundle(tmp_path, source_bytes=b"original-song"):
    folder = tmp_path / "desktop"
    folder.mkdir()
    original = folder / "song.wav"
    lead = folder / "lead.wav"
    backing = folder / "backing.wav"
    original.write_bytes(source_bytes)
    lead.write_bytes(b"lead-stem")
    backing.write_bytes(b"backing-stem")
    manifest = folder / "vocal_separation_manifest.json"
    manifest.write_text(json.dumps({
        "schema": "helix.vocal-separation.v1",
        "method": "vocals_first_then_lead_backing",
        "source_sha256": digest(original),
        "lead": {"path": "lead.wav", "sha256": digest(lead)},
        "backing": {"path": "backing.wav", "sha256": digest(backing)},
    }))
    archive = tmp_path / "vocals.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        for path in (manifest, lead, backing):
            zipped.write(path, path.name)
    return original, archive


def test_phone_binds_a_desktop_bundle_without_running_a_model(tmp_path, monkeypatch):
    monkeypatch.delenv("HELIX_VOCAL_SEPARATION_MANIFEST", raising=False)
    monkeypatch.delenv("HELIX_VOCAL_SEPARATION_SOURCE", raising=False)
    original, archive = bundle(tmp_path)
    job = tmp_path / "job"
    (job / "input").mkdir(parents=True)
    (job / "input/original-audio").write_bytes(original.read_bytes())
    (job / "input/vocal-separation.zip").write_bytes(archive.read_bytes())
    report = bind_imported_vocals(job)
    assert report == {
        "status": "imported_desktop_bundle", "on_device_model": False,
        "identity_verified": False, "method": "vocals_first_then_lead_backing",
        "lead": "lead.wav", "backing": "backing.wav"}
    assert os.environ["HELIX_VOCAL_SEPARATION_SOURCE"].endswith("original-audio")
    assert "HELIX_REQUIRE_NEURAL_STEMS" not in os.environ or os.environ["HELIX_REQUIRE_NEURAL_STEMS"] != "1"


def test_phone_rejects_a_bundle_for_a_different_song(tmp_path, monkeypatch):
    monkeypatch.delenv("HELIX_VOCAL_SEPARATION_MANIFEST", raising=False)
    original, archive = bundle(tmp_path)
    job = tmp_path / "job"
    (job / "input").mkdir(parents=True)
    (job / "input/original-audio").write_bytes(b"different-song")
    (job / "input/vocal-separation.zip").write_bytes(archive.read_bytes())
    with pytest.raises(ValueError, match="source audio SHA256 mismatch"):
        bind_imported_vocals(job)
    assert "HELIX_VOCAL_SEPARATION_MANIFEST" not in os.environ


def test_missing_bundle_leaves_hpss(tmp_path, monkeypatch):
    monkeypatch.setenv("HELIX_VOCAL_SEPARATION_MANIFEST", "stale")
    job = tmp_path / "job"
    (job / "input").mkdir(parents=True)
    report = bind_imported_vocals(job)
    assert report["status"] == "not_supplied"
    assert report["on_device_model"] is False
    assert "HELIX_VOCAL_SEPARATION_MANIFEST" not in os.environ


def test_vocal_zip_rejects_path_escape(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("../escape.wav", b"nope")
    with pytest.raises(ValueError, match="Unsafe vocal bundle path"):
        install_vocal_bundle(archive, tmp_path / "out")


def test_android_sources_keep_the_import_wiring():
    engine = (ROOT / "android/app/src/main/java/org/helixsequencer/android/EngineService.java").read_text()
    activity = (ROOT / "android/app/src/main/java/org/helixsequencer/android/MainActivity.java").read_text()
    assert "vocal-separation.zip" in engine
    assert "decodeWav" in engine
    assert 'select("vocals"' in activity
