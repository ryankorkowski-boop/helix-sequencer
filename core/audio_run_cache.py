"""Explicit, process-local audio analysis reuse for multi-layout sequencing."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")


class AudioRunCache:
    """One source/config per instance; layout routing is never cached.

    A fresh instance belongs to one source-hash-verified song. Return copies for
    analyses whose layout-specific section profiles are subsequently assigned.
    Nothing is loaded from pickle or an unverified basename-only disk cache.
    """

    def __init__(self, source_sha256: str):
        self.source_sha256 = source_sha256
        self.configuration: tuple | None = None
        self.values: dict[str, object] = {}
        self.hits: dict[str, int] = {}

    def get(self, stage: str, factory: Callable[[], T], *, copy_result: bool = False) -> T:
        if stage not in self.values:
            self.values[stage] = factory()
        else:
            self.hits[stage] = self.hits.get(stage, 0) + 1
        value = self.values[stage]
        return deepcopy(value) if copy_result else value

    def validate_source(self, path: Path) -> None:
        if hashlib.sha256(path.read_bytes()).hexdigest() != self.source_sha256:
            raise ValueError('Audio cache belongs to a different source recording')

    def validate_configuration(self, configuration: tuple) -> None:
        if self.configuration is None:
            self.configuration = configuration
        elif self.configuration != configuration:
            raise ValueError('Audio cache belongs to a different analysis configuration')
