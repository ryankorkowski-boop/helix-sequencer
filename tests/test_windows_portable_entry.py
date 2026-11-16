"""The portable CLI binary must not accidentally open the GUI."""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import patch

import windows_portable_entry


def test_named_cli_binary_dispatches_to_worker_without_flag():
    worker = ModuleType("core.sequence_builder")
    observed = []
    def fake_worker():
        observed.append(list(sys.argv))
        return 17
    worker.main = fake_worker
    with patch.object(sys, "argv", ["HelixCLI.exe", "--help"]), patch.dict(sys.modules, {"core.sequence_builder": worker}):
        assert windows_portable_entry.main() == 17
    assert observed == [["HelixCLI.exe", "--help"]]


def test_explicit_cli_flag_preserves_legacy_dispatch():
    worker = ModuleType("core.sequence_builder")
    observed = []
    def fake_worker():
        observed.append(list(sys.argv))
        return 0
    worker.main = fake_worker
    with patch.object(sys, "argv", ["Helix.exe", "--helix-cli", "--help"]), patch.dict(sys.modules, {"core.sequence_builder": worker}):
        assert windows_portable_entry.main() == 0
    assert observed == [["Helix.exe", "--help"]]


def test_named_cli_binary_accepts_legacy_selector_from_palette_runner():
    worker = ModuleType("core.sequence_builder")
    observed = []
    def fake_worker():
        observed.append(list(sys.argv))
        return 0
    worker.main = fake_worker
    args = ["HelixCLI.exe", "--helix-cli", "--profile", "master", "--", "--audio", "tone.wav"]
    with patch.object(sys, "argv", args), patch.dict(sys.modules, {"core.sequence_builder": worker}):
        assert windows_portable_entry.main() == 0
    assert observed == [["HelixCLI.exe", "--profile", "master", "--", "--audio", "tone.wav"]]
