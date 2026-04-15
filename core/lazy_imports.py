from __future__ import annotations

from importlib import import_module
from types import ModuleType


class LazyModule:
    def __init__(self, module_name: str) -> None:
        self._module_name = module_name
        self._module: ModuleType | None = None

    def _load(self) -> ModuleType:
        if self._module is None:
            self._module = import_module(self._module_name)
        return self._module

    def __getattr__(self, item: str):
        return getattr(self._load(), item)

    def __repr__(self) -> str:
        return f"LazyModule({self._module_name!r})"


_OPTIONAL_CACHE: dict[str, ModuleType | None] = {}


def optional_import(module_name: str) -> ModuleType | None:
    if module_name not in _OPTIONAL_CACHE:
        try:
            _OPTIONAL_CACHE[module_name] = import_module(module_name)
        except Exception:
            _OPTIONAL_CACHE[module_name] = None
    return _OPTIONAL_CACHE[module_name]
