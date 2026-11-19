"""Existing project donation destinations, shared by both launchers."""
import json
from pathlib import Path
import sys


def links():
    root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
    return json.loads((root/'config/support_links.json').read_text())
