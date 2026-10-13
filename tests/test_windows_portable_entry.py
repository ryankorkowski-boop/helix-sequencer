"""Portable entrypoint routing tests; no native Windows machine is required."""
from __future__ import annotations

import sys
import types
from unittest.mock import patch

import windows_portable_entry


def test_cli_dispatch_preserves_engine_args():
    captured = []
    fake = types.ModuleType("core.sequence_builder")

    def stub():
        captured.append(sys.argv[:])
        return 7

    fake.main = stub
    with patch.dict(sys.modules, {"core.sequence_builder": fake}):
        with patch.object(sys, "argv", ["HelixCLI.exe", "--helix-cli", "--profile", "master", "--", "--audio", "song.wav"]):
            assert windows_portable_entry.main() == 7
    assert captured == [["HelixCLI.exe", "--profile", "master", "--", "--audio", "song.wav"]]


def test_helixville_dispatch_preserves_output_path():
    captured = []
    fake = types.ModuleType("tools.build_helixville_layout")

    def stub():
        captured.append(sys.argv[:])
        return 0

    fake.main = stub
    with patch.dict(sys.modules, {"tools.build_helixville_layout": fake}):
        with patch.object(sys, "argv", ["HelixCLI.exe", "--helix-build-helixville", "--output-dir", "C:/show"]):
            assert windows_portable_entry.main() == 0
    assert captured == [["HelixCLI.exe", "--output-dir", "C:/show"]]


def test_gui_dispatch_is_default():
    called = []
    fake = types.ModuleType("gui_launcher")
    fake.main = lambda: called.append(True) or 0
    with patch.dict(sys.modules, {"gui_launcher": fake}):
        with patch.object(sys, "argv", ["Helix.exe"]):
            assert windows_portable_entry.main() == 0
    assert called == [True]


def test_remote_worker_dispatch_preserves_private_job_path():
    captured=[]
    fake=types.ModuleType("tools.desktop_remote_worker")
    fake.main=lambda:captured.append(sys.argv[:]) or 0
    with patch.dict(sys.modules,{"tools.desktop_remote_worker":fake}):
        with patch.object(sys,"argv",["HelixCLI.exe","--helix-remote-worker","C:/private/job"]):
            assert windows_portable_entry.main()==0
    assert captured==[["HelixCLI.exe","C:/private/job"]]
