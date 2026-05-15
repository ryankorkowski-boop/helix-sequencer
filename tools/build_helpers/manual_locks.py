"""Manual-lock contract helpers for Helix sequence planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

LOCK_VERSION = "0.1"
LOCK_MODES = {"protect", "trim", "avoid", "override"}
LOCK_STRENGTHS = {"hard", "soft"}
LOCK_SCOPES = {"cue", "section", "group", "time_range"}
ANCHOR_TYPES = {"cue_ref", "section_ref", "time_range"}
FREEZE_FIELDS = {"occupancy", "timing", "targeting", "payload"}


class ManualLockError(ValueError):
    """Raised when a manual-lock contract cannot be normalized safely."""


@dataclass(frozen=True)
class LockPolicy:
    mode: str = "protect"
    strength: str = "hard"
    padding_before_ms: int = 0
    padding_after_ms: int = 0
    min_remaining_ms: int = 0
    require_user_consent: bool = False

    def __post_init__(self) -> None:
        if self.mode not in LOCK_MODES:
            raise ManualLockError(f"Unsupported lock mode: {self.mode}")
        if self.strength not in LOCK_STRENGTHS:
            raise ManualLockError(f"Unsupported lock strength: {self.strength}")
        if self.padding_before_ms < 0 or self.padding_after_ms < 0:
            raise ManualLockError("Lock padding must be non-negative")
        if self.min_remaining_ms < 0:
            raise ManualLockError("min_remaining_ms must be non-negative")
        if self.mode == "override" and not self.require_user_consent:
            raise ManualLockError("override locks must require user consent")

    def as_dict(self) -> dict[str, object]:
        return {"mode": self.mode, "strength": self.strength, "padding_before_ms": self.padding_before_ms, "padding_after_ms": self.padding_after_ms, "min_remaining_ms": self.min_remaining_ms, "require_user_consent": self.require_user_consent}


@dataclass(frozen=True)
class LockAnchor:
    type: str
    cue_id: str | None = None
    section_id: str | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    fallback_start_ms: int | None = None
    fallback_end_ms: int | None = None

    def __post_init__(self) -> None:
        if self.type not in ANCHOR_TYPES:
            raise ManualLockError(f"Unsupported anchor type: {self.type}")
        if self.type == "cue_ref" and not self.cue_id:
            raise ManualLockError("cue_ref anchors require cue_id")
        if self.type == "section_ref" and not self.section_id:
            raise ManualLockError("section_ref anchors require section_id")
        if self.type == "time_range":
            _validate_interval(self.start_ms, self.end_ms, "time_range anchor")
        if (self.fallback_start_ms is None) != (self.fallback_end_ms is None):
            raise ManualLockError("fallback interval must include both start_ms and end_ms")
        if self.fallback_start_ms is not None:
            _validate_interval(self.fallback_start_ms, self.fallback_end_ms, "fallback interval")

    def interval_or_fallback(self) -> tuple[int, int] | None:
        if self.start_ms is not None and self.end_ms is not None:
            return (self.start_ms, self.end_ms)
        if self.fallback_start_ms is not None and self.fallback_end_ms is not None:
            return (self.fallback_start_ms, self.fallback_end_ms)
        return None

    def as_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"type": self.type}
        for key in ("cue_id", "section_id", "start_ms", "end_ms"):
            value = getattr(self, key)
            if value is not None and value != "":
                data[key] = value
        if self.fallback_start_ms is not None and self.fallback_end_ms is not None:
            data["fallback_interval"] = {"start_ms": self.fallback_start_ms, "end_ms": self.fallback_end_ms}
        return data


@dataclass(frozen=True)
class LockSelector:
    all_groups: bool = False
    groups: tuple[str, ...] = field(default_factory=tuple)
    models: tuple[str, ...] = field(default_factory=tuple)
    layers: tuple[str, ...] = field(default_factory=tuple)
    effect_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.all_groups and not (self.groups or self.models or self.effect_ids):
            raise ManualLockError("lock selector must target all_groups, groups, models, or effect_ids")

    @property
    def selector_keys(self) -> tuple[str, ...]:
        keys: list[str] = []
        if self.all_groups:
            keys.append("all_groups:*")
        keys.extend(f"group:{group}" for group in self.groups)
        keys.extend(f"model:{model}" for model in self.models)
        keys.extend(f"effect:{effect_id}" for effect_id in self.effect_ids)
        if self.layers:
            keys = [key + "|layers:" + ",".join(self.layers) for key in keys]
        return tuple(keys)

    def as_dict(self) -> dict[str, object]:
        return {"all_groups": self.all_groups, "groups": list(self.groups), "models": list(self.models), "layers": list(self.layers), "effect_ids": list(self.effect_ids)}


@dataclass(frozen=True)
class ManualLock:
    id: str
    label: str
    enabled: bool
    scope: str
    anchor: LockAnchor
    selector: LockSelector
    policy: LockPolicy
    origin: str = "manual"
    freeze: tuple[str, ...] = ("occupancy",)
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ManualLockError("lock id is required")
        if not self.label:
            raise ManualLockError("lock label is required")
        if self.scope not in LOCK_SCOPES:
            raise ManualLockError(f"Unsupported lock scope: {self.scope}")
        unsupported_freeze = set(self.freeze) - FREEZE_FIELDS
        if unsupported_freeze:
            raise ManualLockError(f"Unsupported freeze fields: {sorted(unsupported_freeze)}")

    @property
    def resolved_shadow_window(self) -> tuple[int, int] | None:
        interval = self.anchor.interval_or_fallback()
        if interval is None:
            return None
        start_ms, end_ms = interval
        return (max(0, start_ms - self.policy.padding_before_ms), end_ms + self.policy.padding_after_ms)

    @property
    def raw_interval(self) -> tuple[int, int] | None:
        return self.anchor.interval_or_fallback()

    def as_dict(self) -> dict[str, object]:
        return {"id": self.id, "label": self.label, "enabled": self.enabled, "origin": self.origin, "scope": self.scope, "anchor": self.anchor.as_dict(), "selector": self.selector.as_dict(), "freeze": list(self.freeze), "policy": self.policy.as_dict(), "notes": self.notes}


@dataclass(frozen=True)
class ManualLockFile:
    version: str
    sequence_id: str
    fps: int
    timebase: str
    locks: tuple[ManualLock, ...]
    sequence_plan_ref: str = ""
    source_audio_ref: str = ""

    def __post_init__(self) -> None:
        if self.version != LOCK_VERSION:
            raise ManualLockError(f"Unsupported manual lock version: {self.version}")
        if not self.sequence_id:
            raise ManualLockError("sequence_id is required")
        if self.fps <= 0:
            raise ManualLockError("fps must be positive")
        if self.timebase != "ms":
            raise ManualLockError("Slice 7 v0.1 only supports millisecond timebase")
        ids = [lock.id for lock in self.locks]
        duplicates = sorted({lock_id for lock_id in ids if ids.count(lock_id) > 1})
        if duplicates:
            raise ManualLockError(f"Duplicate lock ids: {duplicates}")

    @property
    def enabled_locks(self) -> tuple[ManualLock, ...]:
        return tuple(lock for lock in self.locks if lock.enabled)

    def summary(self) -> dict[str, object]:
        enabled = self.enabled_locks
        return {"total": len(self.locks), "enabled": len(enabled), "hard": sum(1 for lock in enabled if lock.policy.strength == "hard"), "soft": sum(1 for lock in enabled if lock.policy.strength == "soft"), "protect": sum(1 for lock in enabled if lock.policy.mode == "protect"), "trim": sum(1 for lock in enabled if lock.policy.mode == "trim"), "avoid": sum(1 for lock in enabled if lock.policy.mode == "avoid"), "override": sum(1 for lock in enabled if lock.policy.mode == "override")}

    def as_dict(self) -> dict[str, object]:
        return {"version": self.version, "sequence_id": self.sequence_id, "sequence_plan_ref": self.sequence_plan_ref, "source_audio_ref": self.source_audio_ref, "fps": self.fps, "timebase": self.timebase, "locks": [lock.as_dict() for lock in self.locks]}


def _validate_interval(start_ms: int | None, end_ms: int | None, label: str) -> None:
    if start_ms is None or end_ms is None:
        raise ManualLockError(f"{label} requires start_ms and end_ms")
    if start_ms < 0 or end_ms < 0:
        raise ManualLockError(f"{label} times must be non-negative")
    if end_ms <= start_ms:
        raise ManualLockError(f"{label} must be half-open with end_ms > start_ms")


def _normalize_token(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", "_").split())


def _as_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (_normalize_token(value),)
    if isinstance(value, Iterable):
        return tuple(_normalize_token(str(item)) for item in value if str(item).strip())
    return ()


def parse_policy(raw: Mapping[str, object] | None, defaults: Mapping[str, object] | None = None) -> LockPolicy:
    merged: dict[str, object] = dict(defaults or {})
    merged.update(raw or {})
    return LockPolicy(mode=str(merged.get("mode", "protect")), strength=str(merged.get("strength", "hard")), padding_before_ms=int(merged.get("padding_before_ms", 0)), padding_after_ms=int(merged.get("padding_after_ms", 0)), min_remaining_ms=int(merged.get("min_remaining_ms", 0)), require_user_consent=bool(merged.get("require_user_consent", False)))


def parse_anchor(raw: Mapping[str, object]) -> LockAnchor:
    fallback = raw.get("fallback_interval")
    fallback_start_ms = fallback_end_ms = None
    if isinstance(fallback, Mapping):
        fallback_start_ms = int(fallback["start_ms"])
        fallback_end_ms = int(fallback["end_ms"])
    return LockAnchor(type=str(raw.get("type", "time_range")), cue_id=str(raw["cue_id"]) if raw.get("cue_id") is not None else None, section_id=str(raw["section_id"]) if raw.get("section_id") is not None else None, start_ms=int(raw["start_ms"]) if raw.get("start_ms") is not None else None, end_ms=int(raw["end_ms"]) if raw.get("end_ms") is not None else None, fallback_start_ms=fallback_start_ms, fallback_end_ms=fallback_end_ms)


def parse_selector(raw: Mapping[str, object]) -> LockSelector:
    return LockSelector(all_groups=bool(raw.get("all_groups", False)), groups=_as_string_tuple(raw.get("groups")), models=_as_string_tuple(raw.get("models")), layers=_as_string_tuple(raw.get("layers")), effect_ids=_as_string_tuple(raw.get("effect_ids")))


def parse_manual_lock(raw: Mapping[str, object], defaults: Mapping[str, object] | None = None) -> ManualLock:
    return ManualLock(id=str(raw.get("id", "")), label=str(raw.get("label", raw.get("id", ""))), enabled=bool(raw.get("enabled", True)), origin=str(raw.get("origin", "manual")), scope=str(raw.get("scope", "time_range")), anchor=parse_anchor(_require_mapping(raw.get("anchor"), "anchor")), selector=parse_selector(_require_mapping(raw.get("selector"), "selector")), freeze=_as_string_tuple(raw.get("freeze", ("occupancy",))), policy=parse_policy(_optional_mapping(raw.get("policy"), "policy"), defaults), notes=str(raw.get("notes", "")))


def parse_manual_lock_file(raw: Mapping[str, object]) -> ManualLockFile:
    locks_raw = raw.get("locks", [])
    if not isinstance(locks_raw, Sequence) or isinstance(locks_raw, (str, bytes)):
        raise ManualLockError("locks must be a list")
    defaults = _optional_mapping(raw.get("defaults"), "defaults")
    locks = tuple(parse_manual_lock(_require_mapping(item, "lock"), defaults) for item in locks_raw)
    return ManualLockFile(version=str(raw.get("version", LOCK_VERSION)), sequence_id=str(raw.get("sequence_id", "")), sequence_plan_ref=str(raw.get("sequence_plan_ref", "")), source_audio_ref=str(raw.get("source_audio_ref", "")), fps=int(raw.get("fps", 40)), timebase=str(raw.get("timebase", "ms")), locks=locks)


def _interval(lock: ManualLock, *, padded: bool = False) -> tuple[int, int] | None:
    return lock.resolved_shadow_window if padded else lock.raw_interval


def locks_touch_at_boundary(left: ManualLock, right: ManualLock) -> bool:
    left_window = _interval(left)
    right_window = _interval(right)
    if left_window is None or right_window is None:
        return False
    return left_window[1] == right_window[0] or right_window[1] == left_window[0]


def locks_overlap(left: ManualLock, right: ManualLock, *, padded: bool = False) -> bool:
    left_window = _interval(left, padded=padded)
    right_window = _interval(right, padded=padded)
    if left_window is None or right_window is None:
        return False
    left_start, left_end = left_window
    right_start, right_end = right_window
    return left_start < right_end and right_start < left_end


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ManualLockError(f"{label} must be an object")
    return value


def _optional_mapping(value: object, label: str) -> Mapping[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ManualLockError(f"{label} must be an object")
    return value
