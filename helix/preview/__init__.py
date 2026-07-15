"""Helix lightweight preview simulation package.

Provides timeline-driven preview rendering helpers without requiring xLights.
"""

from .renderer import FrameRenderer
from .timeline import Timeline, TimelineEvent
from .simulator import PreviewConfig, PreviewSimulator
from .layout import PreviewChannel, PreviewLayout
from .effect_adapter import EffectPlacement, EffectPreviewAdapter

__all__ = [
    "FrameRenderer",
    "Timeline",
    "TimelineEvent",
    "PreviewConfig",
    "PreviewSimulator",
    "PreviewChannel",
    "PreviewLayout",
    "EffectPlacement",
    "EffectPreviewAdapter",
]
