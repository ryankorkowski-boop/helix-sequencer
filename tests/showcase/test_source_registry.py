import pytest

from tools.showcase.source_registry import (
    SourceRegistryError,
    parse_source_registry_entry,
    summarize_source_permissions,
    validate_source_registry,
)


def _entry(**overrides):
    data = {
        "source_id": "synthetic_trace_001",
        "title": "Synthetic trace fixture",
        "source_type": "synthetic_fixture",
        "url": None,
        "copyright_status": "project_generated",
        "permission_basis": "created_for_tests",
        "storage_allowed": True,
        "raw_asset_storage_allowed": True,
        "derived_metrics_allowed": True,
        "training_allowed": True,
        "creator_specific_reproduction_allowed": False,
        "reviewed_by": "project_owner",
        "review_date": "2026-05-07",
        "notes": "Safe synthetic fixture.",
    }
    data.update(overrides)
    return data


def test_parse_safe_synthetic_fixture():
    entry = parse_source_registry_entry(_entry())

    assert entry.source_id == "synthetic_trace_001"
    assert entry.can_store_raw_assets is True
    assert entry.can_store_derived_metrics is True


def test_public_video_reference_cannot_allow_raw_storage_training_or_reproduction():
    with pytest.raises(SourceRegistryError, match="public_video_reference_only"):
        parse_source_registry_entry(
            _entry(
                source_id="public_video_001",
                source_type="public_video_reference_only",
                permission_basis="human_reference_only",
                storage_allowed=True,
                raw_asset_storage_allowed=True,
                derived_metrics_allowed=False,
                training_allowed=False,
                creator_specific_reproduction_allowed=False,
            )
        )

    with pytest.raises(SourceRegistryError, match="public_video_reference_only"):
        parse_source_registry_entry(
            _entry(
                source_id="public_video_002",
                source_type="public_video_reference_only",
                permission_basis="human_reference_only",
                storage_allowed=True,
                raw_asset_storage_allowed=False,
                derived_metrics_allowed=False,
                training_allowed=True,
                creator_specific_reproduction_allowed=False,
            )
        )


def test_unknown_sources_cannot_allow_any_use():
    with pytest.raises(SourceRegistryError, match="unknown_or_unreviewed"):
        parse_source_registry_entry(
            _entry(
                source_id="unknown_001",
                source_type="unknown_or_unreviewed",
                storage_allowed=True,
                raw_asset_storage_allowed=False,
                derived_metrics_allowed=False,
                training_allowed=False,
                creator_specific_reproduction_allowed=False,
            )
        )


def test_raw_storage_requires_storage_allowed():
    with pytest.raises(SourceRegistryError, match="raw_asset_storage_allowed requires storage_allowed"):
        parse_source_registry_entry(
            _entry(storage_allowed=False, raw_asset_storage_allowed=True)
        )


def test_missing_required_fields_raise_error():
    data = _entry()
    del data["permission_basis"]

    with pytest.raises(SourceRegistryError, match="missing required"):
        parse_source_registry_entry(data)


def test_duplicate_source_ids_raise_error():
    with pytest.raises(SourceRegistryError, match="duplicate source_id"):
        validate_source_registry([_entry(), _entry()])


def test_summarize_source_permissions():
    entries = [
        _entry(),
        _entry(
            source_id="public_doc_001",
            source_type="public_documentation",
            raw_asset_storage_allowed=False,
            training_allowed=False,
            creator_specific_reproduction_allowed=False,
        ),
    ]

    summary = summarize_source_permissions(entries)

    assert summary["total"] == 2
    assert summary["raw_asset_storage_allowed"] == 1
    assert summary["derived_metrics_allowed"] == 2
    assert summary["training_allowed"] == 1
