from __future__ import annotations

import importlib
import inspect
from typing import Any, Callable, Iterable, Sequence

from core.engine_coordinator import (
    AudioAnalysisContext,
    EngineCoordinator,
    EngineEffectCandidate,
    LayoutProp,
)


class _BaseLazyAdapter:
    """Fault-isolated lazy adapter normalizing sub-engine output into EngineEffectCandidate."""

    engine_id: str = ""
    default_role: str = "motion"
    allowed_roles: tuple[str, ...] = ("base", "texture", "motion", "accent", "focus")
    module_candidates: tuple[str, ...] = ()
    callable_names: tuple[str, ...] = (
        "generate_candidates",
        "generate_effects",
        "plan_effects",
        "build_effects",
        "run",
    )

    def __init__(
        self,
        *,
        enabled: bool = True,
        target_callable: Callable[..., Any] | None = None,
    ) -> None:
        self.enabled = enabled
        self._target_callable = target_callable

    def _resolve_callable(self) -> Callable[..., Any] | None:
        if self._target_callable is not None:
            return self._target_callable
        for module_name in self.module_candidates:
            try:
                module = importlib.import_module(module_name)
            except Exception:
                continue
            for fn_name in self.callable_names:
                fn = getattr(module, fn_name, None)
                if callable(fn):
                    return fn
        return None

    def _safe_invoke(
        self,
        fn: Callable[..., Any],
        context: AudioAnalysisContext,
        props: Sequence[LayoutProp],
    ) -> Any:
        try:
            sig = inspect.signature(fn)
            params = sig.parameters
            accepts_var_pos = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params.values())
            accepts_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
            positional_count = sum(
                1
                for p in params.values()
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            )
            if accepts_var_pos or positional_count >= 2:
                return fn(context, props)
            if "context" in params and "props" in params:
                return fn(context=context, props=props)
            if accepts_var_kw:
                return fn(context=context, props=props)
            return None
        except Exception:
            return None

    def _normalize_role(self, raw_role: Any) -> str:
        role = str(raw_role or self.default_role).strip().lower()
        if role in self.allowed_roles:
            return role
        return self.default_role

    def _normalize_item(self, item: Any) -> EngineEffectCandidate | None:
        if isinstance(item, EngineEffectCandidate):
            role = self._normalize_role(item.role)
            if item.engine_id == self.engine_id and item.role == role:
                return item
            return EngineEffectCandidate(
                engine_id=self.engine_id,
                prop_id=item.prop_id,
                role=role,
                effect_type=item.effect_type,
                start_ms=item.start_ms,
                end_ms=item.end_ms,
                score=item.score,
                layer_index=item.layer_index,
                snap_to_beat=item.snap_to_beat,
                params=dict(item.params),
                metadata=dict(item.metadata),
            )

        if isinstance(item, dict):
            prop_id = item.get("prop_id")
            effect_type = item.get("effect_type") or item.get("effect") or "wash"
            start_ms = item.get("start_ms")
            end_ms = item.get("end_ms")
            if not prop_id or start_ms is None or end_ms is None:
                return None
            return EngineEffectCandidate(
                engine_id=self.engine_id,
                prop_id=str(prop_id),
                role=self._normalize_role(item.get("role")),
                effect_type=str(effect_type),
                start_ms=int(start_ms),
                end_ms=int(end_ms),
                score=float(item.get("score", 1.0)),
                layer_index=int(item.get("layer_index", 0)),
                snap_to_beat=bool(item.get("snap_to_beat", True)),
                params=dict(item.get("params") or {}),
                metadata=dict(item.get("metadata") or {}),
            )

        prop_id = getattr(item, "prop_id", None)
        start_ms = getattr(item, "start_ms", None)
        end_ms = getattr(item, "end_ms", None)
        if not prop_id or start_ms is None or end_ms is None:
            return None
        effect_type = getattr(item, "effect_type", None) or getattr(item, "effect", None) or "wash"
        return EngineEffectCandidate(
            engine_id=self.engine_id,
            prop_id=str(prop_id),
            role=self._normalize_role(getattr(item, "role", None)),
            effect_type=str(effect_type),
            start_ms=int(start_ms),
            end_ms=int(end_ms),
            score=float(getattr(item, "score", 1.0)),
            layer_index=int(getattr(item, "layer_index", 0)),
            snap_to_beat=bool(getattr(item, "snap_to_beat", True)),
            params=dict(getattr(item, "params", None) or {}),
            metadata=dict(getattr(item, "metadata", None) or {}),
        )

    def generate_candidates(
        self,
        context: AudioAnalysisContext,
        props: Sequence[LayoutProp],
    ) -> list[EngineEffectCandidate]:
        if not self.enabled:
            return []
        fn = self._resolve_callable()
        if fn is None:
            return []
        raw = self._safe_invoke(fn, context, props)
        if raw is None:
            return []
        try:
            items = list(raw)
        except TypeError:
            return []

        normalized: list[EngineEffectCandidate] = []
        for item in items:
            try:
                candidate = self._normalize_item(item)
            except Exception:
                continue
            if candidate is not None and candidate.end_ms > candidate.start_ms:
                normalized.append(candidate)
        return normalized


class CoreBaseAdapter(_BaseLazyAdapter):
    engine_id = "core_base"
    default_role = "base"
    allowed_roles = ("base",)
    module_candidates = ("core.base_engine", "core.core_base")


class HelixIntentAdapter(_BaseLazyAdapter):
    engine_id = "helix_intent"
    default_role = "base"
    allowed_roles = ("base", "texture", "motion")
    module_candidates = ("core.helix_intent", "core.intent_engine", "helix_intent")


class ChronoflowAdapter(_BaseLazyAdapter):
    engine_id = "chronoflow"
    default_role = "motion"
    allowed_roles = ("texture", "motion")
    module_candidates = ("core.chronoflow", "chronoflow")


class HelixualizerAdapter(_BaseLazyAdapter):
    engine_id = "helixualizer"
    default_role = "texture"
    allowed_roles = ("texture", "motion", "accent")
    module_candidates = ("core.helixualizer", "helixualizer")


class HardkorAdapter(_BaseLazyAdapter):
    engine_id = "hardkor_engine"
    default_role = "accent"
    allowed_roles = ("accent", "focus")
    module_candidates = ("core.hardkor_engine", "core.hardkor", "hardkor")


class MatrixIntelligenceAdapter(_BaseLazyAdapter):
    engine_id = "matrix_intelligence"
    default_role = "focus"
    allowed_roles = ("texture", "accent", "focus")
    module_candidates = ("core.matrix_intelligence", "matrix_intelligence")


class SnowmanBandAdapter(_BaseLazyAdapter):
    engine_id = "snowman_band"
    default_role = "motion"
    allowed_roles = ("motion", "accent")
    module_candidates = ("core.snowman_band", "core.ac_band_event_compiler", "snowman_band")


class PianoEffectAdapter(_BaseLazyAdapter):
    engine_id = "piano_effect"
    default_role = "accent"
    allowed_roles = ("motion", "accent", "focus")
    module_candidates = ("core.piano_effect", "piano_effect")


class DrumEffectsAdapter(_BaseLazyAdapter):
    engine_id = "drum_effects"
    default_role = "accent"
    allowed_roles = ("accent", "focus")
    module_candidates = ("core.drum_effects", "drum_effects")


class BirdsongAdapter(_BaseLazyAdapter):
    engine_id = "birdsong"
    default_role = "texture"
    allowed_roles = ("texture", "accent", "focus")
    module_candidates = ("core.birdsong", "birdsong")


DEFAULT_ADAPTER_CLASSES: tuple[type[_BaseLazyAdapter], ...] = (
    CoreBaseAdapter,
    HelixIntentAdapter,
    ChronoflowAdapter,
    HelixualizerAdapter,
    HardkorAdapter,
    MatrixIntelligenceAdapter,
    SnowmanBandAdapter,
    PianoEffectAdapter,
    DrumEffectsAdapter,
    BirdsongAdapter,
)


def register_default_adapters(
    coordinator: EngineCoordinator,
    enabled_engines: Iterable[str] | None = None,
) -> list[str]:
    """Register all default lazy sub-engine adapters on an EngineCoordinator."""
    enabled_set = {str(e).strip() for e in enabled_engines} if enabled_engines is not None else None
    registered: list[str] = []
    for adapter_cls in DEFAULT_ADAPTER_CLASSES:
        if enabled_set is not None and adapter_cls.engine_id not in enabled_set:
            continue
        adapter = adapter_cls(enabled=True)
        coordinator.register_adapter(adapter)
        registered.append(adapter.engine_id)
    return registered
