"""Legacy 256-channel AC sequencing core.

This package is intentionally isolated from the larger Helix engine so it can
be copied into a small standalone repo later.
"""

from .channel_map import LEGACY_CHANNELS, NOTE_TO_MODEL, build_legacy_channel_map
from .planner import EffectEvent, build_demo_plan
from .xsq_writer import write_xsq

__all__ = [
    "LEGACY_CHANNELS",
    "NOTE_TO_MODEL",
    "build_legacy_channel_map",
    "EffectEvent",
    "build_demo_plan",
    "write_xsq",
]
