"""Compliance-first source registry validation for Helix showcase work.

This module is intentionally small and dependency-free. It does not download,
scrape, train, or analyze external media. It validates metadata describing whether
a source may be used for storage, derived metrics, training, or direct third-party
reproduction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


SOURCE_TYPES = {
    "user_authored_rules",
    "user_owned_sequence",
    "permissioned_sequence",
    "public_tutorial",
    "public_documentation",
    "licensed_dataset",
    "public_video_reference_only",
    "synthetic_fixture",
    "internal_generated_output",
    "unknown_or_unreviewed",
}

REQUIRED_FIELDS = (
    "source_id",
    "title",
    "source_type",
    "copyright_status",
    "permission_basis",
    "storage_allowed",
    "raw_asset_storage_allowed",
    "derived_metrics_allowed",
    "training_allowed",
    "creator_specific_reproduction_allowed",
    "reviewed_by",
    "review_date",
    "notes",
)


class SourceRegistryError(ValueError):
    """Raised when source registry metadata is unsafe or malformed."""


@dataclass(frozen=True)
class SourceRegistryEntry:
    source_id: str
    title: str
    source_type: str
    url: str | None = None
    copyright_status: str = "unknown_or_unreviewed"
    permission_basis: str = "unknown"
    storage_allowed: bool = False
    raw_asset_storage_allowed: bool = False
    derived_metrics_allowed: bool = False
    training_allowed: bool = False
    creator_specific_reproduction_allowed: bool = False
    reviewed_by: str = ""
    review_date: str = ""
    notes: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.source_id:
            raise SourceRegistryError("source_id is required")
        if not self.title:
            raise SourceRegistryError("title is required")
        if self.source_type not in SOURCE_TYPES:
            raise SourceRegistryError(f"unsupported source_type: {self.source_type}")
        if not self.reviewed_by:
            raise SourceRegistryError("reviewed_by is required")
        if not self.review_date:
            raise SourceRegistryError("review_date is required")
        if self.source_type == "unknown_or_unreviewed" and (
            self.storage_allowed
            or self.raw_asset_storage_allowed
            or self.derived_metrics_allowed
            or self.training_allowed
            or self.creator_specific_reproduction_allowed
        ):
            raise SourceRegistryError("unknown_or_unreviewed sources cannot allow storage, metrics, training, or reproduction")
        if self.source_type == "public_video_reference_only":
            if self.raw_asset_storage_allowed or self.training_allowed or self.creator_specific_reproduction_allowed:
                raise SourceRegistryError(
                    "public_video_reference_only sources may not allow raw storage, training, or direct third-party reproduction"
                )
        if self.raw_asset_storage_allowed and not self.storage_allowed:
            raise SourceRegistryError("raw_asset_storage_allowed requires storage_allowed")
        if self.training_allowed and not (self.derived_metrics_allowed or self.raw_asset_storage_allowed):
            raise SourceRegistryError("training_allowed requires explicit data permission")

    @property
    def can_store_raw_assets(self) -> bool:
        return self.storage_allowed and self.raw_asset_storage_allowed

    @property
    def can_store_derived_metrics(self) -> bool:
        return self.storage_allowed and self.derived_metrics_allowed

    def as_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "source_type": self.source_type,
            "url": self.url,
            "copyright_status": self.copyright_status,
            "permission_basis": self.permission_basis,
            "storage_allowed": self.storage_allowed,
            "raw_asset_storage_allowed": self.raw_asset_storage_allowed,
            "derived_metrics_allowed": self.derived_metrics_allowed,
            "training_allowed": self.training_allowed,
            "creator_specific_reproduction_allowed": self.creator_specific_reproduction_allowed,
            "reviewed_by": self.reviewed_by,
            "review_date": self.review_date,
            "notes": self.notes,
            "tags": list(self.tags),
        }


def parse_source_registry_entry(raw: Mapping[str, object]) -> SourceRegistryEntry:
    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise SourceRegistryError(f"missing required source registry fields: {missing}")
    tags_raw = raw.get("tags", ())
    if isinstance(tags_raw, str):
        tags = (tags_raw,)
    elif isinstance(tags_raw, Iterable):
        tags = tuple(str(tag) for tag in tags_raw)
    else:
        tags = ()
    return SourceRegistryEntry(
        source_id=str(raw["source_id"]),
        title=str(raw["title"]),
        source_type=str(raw["source_type"]),
        url=str(raw["url"]) if raw.get("url") is not None else None,
        copyright_status=str(raw["copyright_status"]),
        permission_basis=str(raw["permission_basis"]),
        storage_allowed=bool(raw["storage_allowed"]),
        raw_asset_storage_allowed=bool(raw["raw_asset_storage_allowed"]),
        derived_metrics_allowed=bool(raw["derived_metrics_allowed"]),
        training_allowed=bool(raw["training_allowed"]),
        creator_specific_reproduction_allowed=bool(raw["creator_specific_reproduction_allowed"]),
        reviewed_by=str(raw["reviewed_by"]),
        review_date=str(raw["review_date"]),
        notes=str(raw["notes"]),
        tags=tags,
    )


def validate_source_registry(entries: Iterable[Mapping[str, object]]) -> list[SourceRegistryEntry]:
    parsed = [parse_source_registry_entry(entry) for entry in entries]
    ids = [entry.source_id for entry in parsed]
    duplicates = sorted({source_id for source_id in ids if ids.count(source_id) > 1})
    if duplicates:
        raise SourceRegistryError(f"duplicate source_id values: {duplicates}")
    return parsed


def summarize_source_permissions(entries: Iterable[Mapping[str, object] | SourceRegistryEntry]) -> dict[str, object]:
    parsed = [entry if isinstance(entry, SourceRegistryEntry) else parse_source_registry_entry(entry) for entry in entries]
    return {
        "total": len(parsed),
        "raw_asset_storage_allowed": sum(1 for entry in parsed if entry.can_store_raw_assets),
        "derived_metrics_allowed": sum(1 for entry in parsed if entry.can_store_derived_metrics),
        "training_allowed": sum(1 for entry in parsed if entry.training_allowed),
        "creator_specific_reproduction_allowed": sum(
            1 for entry in parsed if entry.creator_specific_reproduction_allowed
        ),
        "source_types": sorted({entry.source_type for entry in parsed}),
    }
