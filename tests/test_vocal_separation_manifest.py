"""Two-stage vocal separation provenance checks; no network/API credentials needed."""
import hashlib
import json
import math
import struct
import wave

import pytest

from core.independent_vocals import analyze_independent_vocals
from core.vocal_separation_manifest import validate_vocal_separation_manifest
from tools.prepare_vocal_separation_manifest import prepare


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wav(path, hz):
    rate = 16000
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * hz * i / rate)))
                              for i in range(rate // 2)))


def fixture(tmp_path):
    original, lead, backing = (tmp_path / name for name in ("original.wav", "lead.wav", "backing.wav"))
    wav(original, 180)
    wav(lead, 220)
    wav(backing, 330)
    manifest = tmp_path / "stems.json"
    data = {
        "schema": "helix.vocal-separation.v1",
        "method": "vocals_first_then_lead_backing",
        "source_sha256": digest(original),
        "lead": {"path": lead.name, "sha256": digest(lead)},
        "backing": {"path": backing.name, "sha256": digest(backing)},
    }
    manifest.write_text(json.dumps(data))
    return original, lead, backing, manifest, data


def test_valid_two_stage_bundle_routes_distinct_singers(tmp_path):
    original, lead, backing, manifest, _ = fixture(tmp_path)
    paths = validate_vocal_separation_manifest(manifest, original)
    assert paths == (lead, backing)
    result = analyze_independent_vocals(*paths)
    assert result["status"] == "distinct_stem_inputs"
    assert result["independence"] == "duplicate_rejection_only_not_voice_identity_proof"


def test_source_identity_mismatch_rejected(tmp_path):
    original, _, _, manifest, _ = fixture(tmp_path)
    original.write_bytes(b"changed")
    with pytest.raises(ValueError, match="source audio SHA256 mismatch"):
        validate_vocal_separation_manifest(manifest, original)


def test_tampered_stem_rejected(tmp_path):
    original, lead, _, manifest, _ = fixture(tmp_path)
    lead.write_bytes(b"changed")
    with pytest.raises(ValueError, match="lead stem SHA256 mismatch"):
        validate_vocal_separation_manifest(manifest, original)


def test_path_escape_rejected(tmp_path):
    original, _, _, manifest, data = fixture(tmp_path)
    data["lead"]["path"] = "../escape.wav"
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Unsafe or missing"):
        validate_vocal_separation_manifest(manifest, original)


def test_unstaged_method_rejected(tmp_path):
    original, _, _, manifest, data = fixture(tmp_path)
    data["method"] = "unknown"
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="vocals-first"):
        validate_vocal_separation_manifest(manifest, original)


def test_cli_manifest_preparation_roundtrip(tmp_path):
    original, lead, backing, _, _ = fixture(tmp_path)
    output = tmp_path / "generated.json"
    assert prepare(original, lead, backing, output) == output
    assert validate_vocal_separation_manifest(output, original) == (lead, backing)


def test_cli_rejects_duplicate_stems_without_writing_manifest(tmp_path):
    original, lead, _, _, _ = fixture(tmp_path)
    output = tmp_path / "rejected.json"
    with pytest.raises(ValueError, match="Duplicate"):
        prepare(original, lead, lead, output)
    assert not output.exists()


def test_cli_rejects_stems_outside_manifest_directory(tmp_path):
    original, lead, backing, _, _ = fixture(tmp_path)
    output = tmp_path / "subdir" / "stems.json"
    with pytest.raises(ValueError, match="within"):
        prepare(original, lead, backing, output)
    assert not output.exists()


def test_cli_rejects_original_mix_as_lead(tmp_path):
    original, _, backing, _, _ = fixture(tmp_path)
    output = tmp_path / "unsafe.json"
    with pytest.raises(ValueError, match="matches original audio"):
        prepare(original, original, backing, output)
    assert not output.exists()


def test_cli_rejects_original_mix_as_backing(tmp_path):
    original, lead, _, _, _ = fixture(tmp_path)
    output = tmp_path / "unsafe.json"
    with pytest.raises(ValueError, match="matches original audio"):
        prepare(original, lead, original, output)
    assert not output.exists()


def test_handwritten_manifest_rejects_original_mix_as_lead(tmp_path):
    original, lead, _, manifest, data = fixture(tmp_path)
    lead.write_bytes(original.read_bytes())
    data["lead"]["sha256"] = digest(lead)
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="matches original source audio"):
        validate_vocal_separation_manifest(manifest, original)


def test_cli_never_overwrites_original_or_stems(tmp_path):
    original, lead, backing, _, _ = fixture(tmp_path)
    for protected in (original, lead, backing):
        before = protected.read_bytes()
        with pytest.raises(ValueError, match="cannot overwrite"):
            prepare(original, lead, backing, protected)
        assert protected.read_bytes() == before


def test_cli_preserves_existing_manifest_when_validation_fails(tmp_path):
    original, lead, _, _, _ = fixture(tmp_path)
    output = tmp_path / "existing.json"
    output.write_text("previous valid artifact")
    with pytest.raises(ValueError, match="Duplicate"):
        prepare(original, lead, lead, output)
    assert output.read_text() == "previous valid artifact"
    assert not list(tmp_path.glob(".helix-stems-*"))


def test_cli_writes_no_temporary_manifest_after_success(tmp_path):
    original, lead, backing, _, _ = fixture(tmp_path)
    output = tmp_path / "generated.json"
    prepare(original, lead, backing, output)
    assert output.exists()
    assert not list(tmp_path.glob(".helix-stems-*"))


def test_handwritten_manifest_rejects_duplicate_content_stems(tmp_path):
    original, lead, backing, manifest, data = fixture(tmp_path)
    backing.write_bytes(lead.read_bytes())
    data["backing"]["sha256"] = digest(backing)
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Duplicate vocal stems"):
        validate_vocal_separation_manifest(manifest, original)


def test_android_source_override_binds_the_selected_file(tmp_path, monkeypatch):
    original, _, _, _, _ = fixture(tmp_path)
    decoded = tmp_path / "audio.wav"
    decoded.write_bytes(b"reencoded")
    from core.vocal_separation_manifest import vocal_bundle_source
    assert vocal_bundle_source(decoded) == decoded
    monkeypatch.setenv("HELIX_VOCAL_SEPARATION_SOURCE", str(original))
    assert vocal_bundle_source(decoded) == original
    monkeypatch.setenv("HELIX_VOCAL_SEPARATION_SOURCE", str(tmp_path / "missing.wav"))
    with pytest.raises(ValueError, match="HELIX_VOCAL_SEPARATION_SOURCE is missing"):
        vocal_bundle_source(decoded)
