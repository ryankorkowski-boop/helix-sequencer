"""Shared customer guidance and truthful licensing information.

The instruction manual and legal text have one source: the files packaged in the
Android app. The desktop GUI and the Windows portable build read the same files,
so the two applications cannot drift apart.
"""
from __future__ import annotations

import sys
from pathlib import Path

TAGLINE = 'Audio in. Lights out.'
_ASSETS = Path('android/app/src/main/assets')


def _shared_text(name: str) -> str:
    roots = [Path(__file__).resolve().parent]
    if getattr(sys, 'frozen', False):
        executable = Path(sys.executable).resolve().parent
        roots += [executable, executable / '_internal']
        if getattr(sys, '_MEIPASS', None):
            roots.append(Path(sys._MEIPASS))
    for root in roots:
        candidate = root / _ASSETS / name
        if candidate.is_file():
            return candidate.read_text(encoding='utf-8')
    raise FileNotFoundError(f'Missing shared help asset: {_ASSETS / name}')


INSTRUCTIONS = _shared_text('helix_instructions.txt')
LEGAL = _shared_text('helix_legal.txt')
