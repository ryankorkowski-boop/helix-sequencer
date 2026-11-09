from tools.engine_comparison_preflight import validate_comparison_manifest


def manifest():
    shared = {
        "audio_sha256": "a" * 64, "layout_sha256": "b" * 64,
        "camera_id": "front", "palette_sha256": "c" * 64,
        "channel_map_sha256": "d" * 64, "fps": 20,
        "source_commit": "e" * 40, "audio_kind": "real",
        "features_source": "source_audio", "engine_execution_verified": True,
        "native_render_verified": True, "synthetic_fallback_used": False,
    }
    return {"panels": [
        {**shared, "panel": i, "xsq_sha256": f"{i:064x}",
         "fseq_sha256": f"{i+100:064x}", "birdsong_enabled": False}
        for i in range(1, 17)
    ]}


def test_complete_unique_native_outputs_pass():
    assert validate_comparison_manifest(manifest()) == []


def test_frozen_audio_and_layout_rejected():
    data = manifest()
    data["panels"][2]["audio_sha256"] = "z" * 64
    data["panels"][3]["layout_sha256"] = "y" * 64
    errors = validate_comparison_manifest(data)
    assert any("audio_sha256" in e for e in errors)
    assert any("layout_sha256" in e for e in errors)


def test_synthetic_birdsong_and_identical_outputs_rejected():
    data = manifest()
    data["panels"][8].update({
        "birdsong_enabled": True, "birdsong_native_rows": 0,
        "birdsong_real_features_verified": False, "features_source": "synthetic",
    })
    data["panels"][15]["fseq_sha256"] = data["panels"][14]["fseq_sha256"]
    errors = validate_comparison_manifest(data)
    assert any("Birdsong" in e for e in errors)
    assert any("synthetic" in e for e in errors)
    assert any("identical FSEQ" in e for e in errors)


def test_missing_or_unverified_native_artifacts_rejected():
    data = manifest()
    data["panels"][0]["native_render_verified"] = False
    data["panels"][1]["xsq_sha256"] = None
    assert len(validate_comparison_manifest(data)) >= 2


def test_malformed_manifest_and_hashes_fail_closed():
    assert validate_comparison_manifest(None) == ["manifest must be an object"]
    data = manifest()
    data["panels"][0]["xsq_sha256"] = "not-a-sha"
    data["panels"][1]["fseq_sha256"] = 123
    errors = validate_comparison_manifest(data)
    assert any("invalid or missing xsq_sha256" in e for e in errors)
    assert any("invalid or missing fseq_sha256" in e for e in errors)


def test_invalid_birdsong_row_type_fails_without_exception():
    data = manifest()
    data["panels"][8].update({"birdsong_enabled": True,
        "birdsong_native_rows": "many", "birdsong_real_features_verified": True})
    assert any("Birdsong" in e for e in validate_comparison_manifest(data))


def test_baseline_uses_panel_one_even_when_unordered():
    data = manifest()
    data["panels"] = data["panels"][1:] + data["panels"][:1]
    assert validate_comparison_manifest(data) == []


def test_birdsong_native_hook_rejects_synthetic_data():
    # The native post-run adapter previously wrote plausible-looking fake
    # features without changing the actual XSQ/FSEQ. It must now fail closed.
    from core.sequence_builder import _run_birdsong_hook
    import pytest

    with pytest.raises(RuntimeError, match="Birdsong native export unavailable"):
        _run_birdsong_hook(None, ["--enable-birdsong"], None)
    assert _run_birdsong_hook(None, [], None) is None



def test_native_artifact_bytes_match_claimed_hashes(tmp_path):
    import hashlib
    from tools.engine_comparison_preflight import verify_local_artifacts

    data = manifest()
    for p in data["panels"]:
        for kind in ("xsq", "fseq"):
            payload = f"native-{p['panel']}-{kind}".encode()
            name = f"panel-{p['panel']}.{kind}"
            (tmp_path / name).write_bytes(payload)
            p[f"{kind}_path"] = name
            p[f"{kind}_sha256"] = hashlib.sha256(payload).hexdigest()
    assert verify_local_artifacts(data, tmp_path) == []
    (tmp_path / "panel-3.fseq").write_bytes(b"tampered")
    assert any("bytes differ" in error for error in verify_local_artifacts(data, tmp_path))


def test_native_artifact_traversal_is_rejected(tmp_path):
    from tools.engine_comparison_preflight import verify_local_artifacts
    data = manifest()
    for p in data["panels"]:
        p["xsq_path"] = "../outside.xsq"
        p["fseq_path"] = "/tmp/outside.fseq"
    errors = verify_local_artifacts(data, tmp_path)
    assert any("unsafe xsq_path" in error for error in errors)
    assert any("unsafe fseq_path" in error for error in errors)


def test_unordered_panel_cannot_bypass_frozen_field_validation():
    data = manifest()
    data["panels"] = data["panels"][1:] + data["panels"][:1]
    data["panels"][0]["camera_id"] = "changed-camera"
    errors = validate_comparison_manifest(data)
    assert any("differs in frozen field camera_id" in e for e in errors)
