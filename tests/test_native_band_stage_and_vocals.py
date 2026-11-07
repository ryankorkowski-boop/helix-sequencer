"""Regression checks for owner-rejected native band composition and vocal evidence.

These checks run without downloading large source media or invoking xLights.
They protect the staging and audit plumbing; visual/audio acceptance remains manual.
"""
from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / 'tools' / 'native_source_pose_band.py'


def _prepare_source() -> str:
    source = SOURCE.read_text(encoding='utf-8')
    ast.parse(source)
    return source


def test_keyboard_is_not_staged_on_drummer():
    source = _prepare_source()
    assert "PIANO=(25,28,65) if legacy_xylophone else (-30,28,65)" in source
    assert "positions['PIANO']" in source and "positions['DRUMMER']" in source
    assert "Native keyboard stage overlaps the drummer" in source


def test_source_timed_harmony_mouth_activity_is_reported():
    source = _prepare_source()
    assert "if role not in ('lead','harmony')" in source
    assert "name.startswith('MOUTH_')" in source
    assert "vocal_visibility_audit=vocal_audit" in source
    assert "harmony singer has no active source-timed mouth parts" in source


def test_native_keyboard_has_individually_addressable_note_parts():
    source = _prepare_source()
    assert "prefix='NOTE_MIDI_'" in source
    assert "overlapping native channels" in source
    assert "instrument_visibility_audit=instrument_audit" in source
