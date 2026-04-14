#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import shutil
from bisect import bisect_left
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
import xml.etree.ElementTree as ET

from core.lazy_imports import LazyModule

from core import audio_intelligence as ai
from core import model_parser as xmp
from tools import utilities as xfb
from xlights import xsq_writer as base

librosa = LazyModule("librosa")
np = LazyModule("numpy")


@dataclass
class SequentialPool:
    name: str
    category: str
    models: list[str]


@dataclass
class HarmonicData:
    times_s: np.ndarray
    cqt_mag: np.ndarray
    base_midi: int
    pitch_hz: np.ndarray
    pitch_mag: np.ndarray


@dataclass
class NoteEvent:
    start_ms: int
    end_ms: int
    notes: list[tuple[int, float]]
    part: str
    section: str


@dataclass
class KeyboardRoute:
    name: str
    models: list[str]
    stride_normal: int = 1
    stride_dramatic: int = 1
    clusters: list[list[str]] | None = None


@dataclass
class SongPart:
    label: str
    start_ms: int
    end_ms: int
    energy: float


@dataclass
class VariantStyle:
    version: str
    family: str
    title: str
    timing_mode: str
    pool_mode: str
    placement_mode: str
    keyboard_overlay: bool
    polyphony: int
    density_scale: float
    speed_scale: float
    randomness_scale: float
    bass_scale: float
    melody_scale: float
    darkness_scale: float
    piano_echo: bool
    call_response: bool
    section_emphasis: bool
    sweep_categories: tuple[str, ...]
    primary_categories: tuple[str, ...]
    chorus_categories: tuple[str, ...]
    build_categories: tuple[str, ...]
    drop_blackout_ms: tuple[int, int]
    sweep_hit_ms: int


@dataclass
class RuntimeTuning:
    polyphony_override: int | None = None
    cane_focus: float = 1.0
    flash_guard: float = 0.80
    keyboard_mix: float = 1.0
    model_overrides: dict[str, str | list[str]] | None = None
    use_moises: bool = False
    moises_api_key: str | None = None
    sync_lyrics_heads: bool = False
    template_guidance: bool = True
    layout_file: Path | None = None
    spatial_awareness: float = 0.0
    chase_style: str = "none"
    layering_mode: str = "replace"
    layer_priority_vocals: int = 4
    layer_priority_drums: int = 3
    layer_priority_bass: int = 2
    layer_priority_other: int = 1
    strict_xlights_effects: bool = True
    xlights_repo: Path | None = None
    xlights_features_json: Path | None = None
    base_effect: str = "On"
    motion_effect: str = "Ramp"
    accent_effect: str = "On"
    max_layers_per_prop: int = 3
    min_effect_ms: int = 50
    debug_validation: bool = True
    ac_lights_only: bool = False
    palette_mode: str = "template"
    workspace_history_enabled: bool = True
    workspace_history_folder: Path | None = None
    workspace_history_limit: int = 24
    auto_timing_tracks: bool = True
    pixel_reactive: bool = True


@dataclass
class TemplateProfile:
    category_scores: dict[str, int]
    category_effect_families: dict[str, list[str]]
    discovered_effect_families: list[str]


@dataclass
class WorkspaceHistoryProfile:
    family_effects: dict[str, list[str]]
    palette_pool: list[str]


VARIANTS: dict[str, VariantStyle] = {
    "v2.1": VariantStyle(
        version="v2.1",
        family="v2",
        title="Grid Piano",
        timing_mode="note",
        pool_mode="rotating",
        placement_mode="classic",
        keyboard_overlay=False,
        polyphony=3,
        density_scale=1.00,
        speed_scale=1.02,
        randomness_scale=0.90,
        bass_scale=1.02,
        melody_scale=1.18,
        darkness_scale=0.96,
        piano_echo=False,
        call_response=False,
        section_emphasis=False,
        sweep_categories=("stars", "snowflakes", "line", "mega", "arch", "canes_combo"),
        primary_categories=("canes_combo", "north_canes", "south_canes", "gt", "line", "arch"),
        chorus_categories=("gt", "line", "mega", "arch", "canes_combo"),
        build_categories=("stars", "snowflakes", "canes_combo", "arch"),
        drop_blackout_ms=(140, 260),
        sweep_hit_ms=120,
    ),
    "v2.2": VariantStyle(
        version="v2.2",
        family="v2",
        title="Phrase Bounce",
        timing_mode="beat",
        pool_mode="sectional",
        placement_mode="classic",
        keyboard_overlay=False,
        polyphony=2,
        density_scale=0.95,
        speed_scale=1.05,
        randomness_scale=1.05,
        bass_scale=1.10,
        melody_scale=0.92,
        darkness_scale=1.00,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("gt", "line", "stars", "snowflakes", "arch", "canes_combo"),
        primary_categories=("gt", "line", "canes_combo", "north_canes", "south_canes", "arch"),
        chorus_categories=("gt", "line", "mega", "arch", "canes_combo"),
        build_categories=("snowflakes", "stars", "arch", "canes_combo"),
        drop_blackout_ms=(180, 300),
        sweep_hit_ms=140,
    ),
    "v2.3": VariantStyle(
        version="v2.3",
        family="v2",
        title="Random Keys",
        timing_mode="mixed",
        pool_mode="random",
        placement_mode="classic",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=1.08,
        speed_scale=1.04,
        randomness_scale=1.20,
        bass_scale=1.05,
        melody_scale=1.08,
        darkness_scale=1.02,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("stars", "snowflakes", "mega", "line", "arch", "canes_combo"),
        primary_categories=("canes_combo", "north_canes", "south_canes", "stars", "snowflakes", "gt", "line", "arch"),
        chorus_categories=("gt", "mega", "line", "arch", "canes_combo"),
        build_categories=("stars", "snowflakes", "line", "arch", "canes_combo"),
        drop_blackout_ms=(190, 320),
        sweep_hit_ms=130,
    ),
    "v3.1": VariantStyle(
        version="v3.1",
        family="v3",
        title="Cinematic Parts",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="classic",
        keyboard_overlay=False,
        polyphony=3,
        density_scale=1.05,
        speed_scale=1.06,
        randomness_scale=0.96,
        bass_scale=1.20,
        melody_scale=1.00,
        darkness_scale=1.10,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("stars", "snowflakes", "line", "mega", "gt", "arch", "canes_combo"),
        primary_categories=("canes_combo", "north_canes", "south_canes", "line", "gt", "arch"),
        chorus_categories=("gt", "mega", "line", "arch", "canes_combo"),
        build_categories=("stars", "snowflakes", "line", "arch", "canes_combo"),
        drop_blackout_ms=(220, 360),
        sweep_hit_ms=150,
    ),
    "v3.2": VariantStyle(
        version="v3.2",
        family="v3",
        title="Hook Immersion",
        timing_mode="hook",
        pool_mode="rotating",
        placement_mode="classic",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=1.02,
        speed_scale=1.08,
        randomness_scale=0.88,
        bass_scale=1.12,
        melody_scale=1.20,
        darkness_scale=1.04,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "mega", "stars", "gt", "arch", "canes_combo"),
        primary_categories=("canes_combo", "north_canes", "south_canes", "line", "stars", "arch"),
        chorus_categories=("gt", "mega", "line", "arch", "canes_combo"),
        build_categories=("stars", "snowflakes", "canes_combo", "arch"),
        drop_blackout_ms=(210, 340),
        sweep_hit_ms=135,
    ),
    "v3.3": VariantStyle(
        version="v3.3",
        family="v3",
        title="Storyteller",
        timing_mode="parts",
        pool_mode="call_response",
        placement_mode="classic",
        keyboard_overlay=False,
        polyphony=3,
        density_scale=1.10,
        speed_scale=1.10,
        randomness_scale=1.15,
        bass_scale=1.25,
        melody_scale=1.08,
        darkness_scale=1.18,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("stars", "snowflakes", "gt", "line", "mega", "arch", "canes_combo"),
        primary_categories=("canes_combo", "north_canes", "south_canes", "stars", "gt", "line", "arch"),
        chorus_categories=("gt", "mega", "line", "arch", "canes_combo"),
        build_categories=("stars", "snowflakes", "canes_combo", "arch"),
        drop_blackout_ms=(240, 400),
        sweep_hit_ms=155,
    ),
    "v4.1": VariantStyle(
        version="v4.1",
        family="v4",
        title="Zone Riff",
        timing_mode="note",
        pool_mode="rotating",
        placement_mode="zone_riff",
        keyboard_overlay=True,
        polyphony=4,
        density_scale=1.06,
        speed_scale=1.12,
        randomness_scale=0.95,
        bass_scale=1.16,
        melody_scale=1.12,
        darkness_scale=1.02,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("arch", "canes_combo", "gt", "line", "snowflakes", "stars", "mega"),
        primary_categories=("canes_combo", "arch", "line", "gt", "snowflakes", "stars", "mega", "talking_heads"),
        chorus_categories=("gt", "mega", "canes_combo", "arch", "line", "talking_heads"),
        build_categories=("arch", "canes_combo", "snowflakes", "stars", "line"),
        drop_blackout_ms=(170, 280),
        sweep_hit_ms=145,
    ),
    "v4.2": VariantStyle(
        version="v4.2",
        family="v4",
        title="Percussion Relay",
        timing_mode="mixed",
        pool_mode="call_response",
        placement_mode="percussion_relay",
        keyboard_overlay=True,
        polyphony=2,
        density_scale=1.00,
        speed_scale=1.20,
        randomness_scale=1.08,
        bass_scale=1.25,
        melody_scale=0.92,
        darkness_scale=1.08,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("canes_combo", "arch", "line", "gt", "snowflakes", "stars", "mega"),
        primary_categories=("canes_combo", "gt", "arch", "line", "snowflakes", "stars", "mega", "talking_heads"),
        chorus_categories=("gt", "canes_combo", "mega", "arch", "line", "talking_heads"),
        build_categories=("arch", "line", "snowflakes", "stars", "canes_combo"),
        drop_blackout_ms=(120, 210),
        sweep_hit_ms=115,
    ),
    "v4.3": VariantStyle(
        version="v4.3",
        family="v4",
        title="Scene Morph",
        timing_mode="parts",
        pool_mode="sectional",
        placement_mode="scene_morph",
        keyboard_overlay=True,
        polyphony=3,
        density_scale=0.96,
        speed_scale=0.95,
        randomness_scale=1.20,
        bass_scale=1.18,
        melody_scale=1.22,
        darkness_scale=1.18,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("stars", "snowflakes", "arch", "line", "gt", "mega", "canes_combo", "talking_heads"),
        primary_categories=("line", "arch", "snowflakes", "stars", "talking_heads", "canes_combo"),
        chorus_categories=("gt", "mega", "canes_combo", "arch", "line", "talking_heads"),
        build_categories=("arch", "line", "snowflakes", "stars", "canes_combo"),
        drop_blackout_ms=(240, 390),
        sweep_hit_ms=160,
    ),
    "v5.1": VariantStyle(
        version="v5.1",
        family="v5",
        title="Director AI",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="director_ai",
        keyboard_overlay=True,
        polyphony=4,
        density_scale=1.08,
        speed_scale=1.10,
        randomness_scale=1.26,
        bass_scale=1.24,
        melody_scale=1.20,
        darkness_scale=1.08,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("line", "arch", "canes_combo", "gt", "mega", "stars", "snowflakes", "talking_heads"),
        primary_categories=("line", "arch", "canes_combo", "stars", "snowflakes", "talking_heads"),
        chorus_categories=("gt", "mega", "canes_combo", "line", "arch", "talking_heads"),
        build_categories=("arch", "line", "canes_combo", "stars", "snowflakes"),
        drop_blackout_ms=(200, 330),
        sweep_hit_ms=145,
    ),
    "v6.1": VariantStyle(
        version="v6.1",
        family="v6",
        title="Constellation Story",
        timing_mode="parts",
        pool_mode="sectional",
        placement_mode="constellation_story",
        keyboard_overlay=True,
        polyphony=3,
        density_scale=0.92,
        speed_scale=0.96,
        randomness_scale=1.18,
        bass_scale=1.04,
        melody_scale=1.16,
        darkness_scale=1.22,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("stars", "snowflakes", "talking_heads", "line", "arch", "gt", "mega"),
        primary_categories=("stars", "snowflakes", "line", "arch", "talking_heads"),
        chorus_categories=("line", "arch", "gt", "mega", "talking_heads"),
        build_categories=("stars", "snowflakes", "arch", "line"),
        drop_blackout_ms=(220, 380),
        sweep_hit_ms=165,
    ),
    "v6.2": VariantStyle(
        version="v6.2",
        family="v6",
        title="Pinball Relay",
        timing_mode="mixed",
        pool_mode="call_response",
        placement_mode="pinball_relay",
        keyboard_overlay=False,
        polyphony=2,
        density_scale=1.10,
        speed_scale=1.24,
        randomness_scale=1.06,
        bass_scale=1.22,
        melody_scale=0.90,
        darkness_scale=0.98,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("canes_combo", "arch", "line", "gt", "mega", "stars", "snowflakes"),
        primary_categories=("canes_combo", "arch", "line", "gt", "mega"),
        chorus_categories=("gt", "mega", "canes_combo", "arch", "line"),
        build_categories=("arch", "line", "canes_combo", "stars"),
        drop_blackout_ms=(140, 240),
        sweep_hit_ms=110,
    ),
    "v6.3": VariantStyle(
        version="v6.3",
        family="v6",
        title="Vocal Spotlight",
        timing_mode="hook",
        pool_mode="rotating",
        placement_mode="vocal_spotlight",
        keyboard_overlay=True,
        polyphony=3,
        density_scale=0.88,
        speed_scale=0.98,
        randomness_scale=0.92,
        bass_scale=1.06,
        melody_scale=1.24,
        darkness_scale=1.18,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("talking_heads", "stars", "snowflakes", "line", "arch", "gt", "mega"),
        primary_categories=("talking_heads", "stars", "snowflakes", "line", "arch"),
        chorus_categories=("talking_heads", "line", "arch", "gt", "mega"),
        build_categories=("stars", "snowflakes", "arch", "line", "talking_heads"),
        drop_blackout_ms=(210, 340),
        sweep_hit_ms=150,
    ),
    "v7.1": VariantStyle(
        version="v7.1",
        family="v7",
        title="Mirror Duel",
        timing_mode="note",
        pool_mode="call_response",
        placement_mode="mirror_duel",
        keyboard_overlay=True,
        polyphony=4,
        density_scale=1.02,
        speed_scale=1.12,
        randomness_scale=1.10,
        bass_scale=1.14,
        melody_scale=1.10,
        darkness_scale=1.04,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("north_canes", "south_canes", "arch", "line", "gt", "mega"),
        primary_categories=("north_canes", "south_canes", "arch", "line", "talking_heads"),
        chorus_categories=("gt", "mega", "line", "arch", "canes_combo"),
        build_categories=("north_canes", "south_canes", "arch", "line"),
        drop_blackout_ms=(170, 300),
        sweep_hit_ms=135,
    ),
    "v7.2": VariantStyle(
        version="v7.2",
        family="v7",
        title="Orbital Sweep",
        timing_mode="beat",
        pool_mode="sectional",
        placement_mode="orbital_sweep",
        keyboard_overlay=False,
        polyphony=2,
        density_scale=1.00,
        speed_scale=1.18,
        randomness_scale=1.04,
        bass_scale=1.18,
        melody_scale=0.96,
        darkness_scale=1.00,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("canes_combo", "arch", "line", "gt", "mega", "stars", "snowflakes"),
        primary_categories=("canes_combo", "arch", "line", "gt"),
        chorus_categories=("gt", "mega", "line", "arch", "stars", "snowflakes"),
        build_categories=("arch", "line", "stars", "snowflakes"),
        drop_blackout_ms=(150, 280),
        sweep_hit_ms=125,
    ),
    "v7.3": VariantStyle(
        version="v7.3",
        family="v7",
        title="Pulse Matrix",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="pulse_matrix",
        keyboard_overlay=True,
        polyphony=3,
        density_scale=1.18,
        speed_scale=1.06,
        randomness_scale=0.84,
        bass_scale=1.28,
        melody_scale=0.94,
        darkness_scale=0.96,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "mega", "gt", "canes_combo", "arch", "stars"),
        primary_categories=("line", "mega", "gt", "canes_combo", "arch"),
        chorus_categories=("gt", "mega", "line", "canes_combo", "arch"),
        build_categories=("line", "arch", "stars", "canes_combo"),
        drop_blackout_ms=(120, 230),
        sweep_hit_ms=105,
    ),
    "v9.1": VariantStyle(
        version="v9.1",
        family="v9",
        title="Dream Architect",
        timing_mode="beat",
        pool_mode="sectional",
        placement_mode="orbital_sweep",
        keyboard_overlay=False,
        polyphony=3,
        density_scale=1.04,
        speed_scale=1.12,
        randomness_scale=0.92,
        bass_scale=1.16,
        melody_scale=1.02,
        darkness_scale=1.02,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "line", "arch", "canes_combo", "gt", "stars"),
        primary_categories=("mega", "line", "arch", "canes_combo"),
        chorus_categories=("mega", "line", "gt", "arch", "canes_combo"),
        build_categories=("arch", "line", "stars", "canes_combo"),
        drop_blackout_ms=(150, 260),
        sweep_hit_ms=130,
    ),
    "v9.2": VariantStyle(
        version="v9.2",
        family="v9",
        title="AC Pulse Grid",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="pulse_matrix",
        keyboard_overlay=False,
        polyphony=2,
        density_scale=1.00,
        speed_scale=1.06,
        randomness_scale=0.76,
        bass_scale=1.20,
        melody_scale=0.92,
        darkness_scale=1.00,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "canes_combo", "arch", "gt", "stars", "snowflakes"),
        primary_categories=("line", "canes_combo", "arch", "gt"),
        chorus_categories=("line", "gt", "canes_combo", "arch"),
        build_categories=("arch", "line", "stars"),
        drop_blackout_ms=(130, 220),
        sweep_hit_ms=110,
    ),
    "v9.3": VariantStyle(
        version="v9.3",
        family="v9",
        title="Cane Dialogue",
        timing_mode="hook",
        pool_mode="call_response",
        placement_mode="mirror_duel",
        keyboard_overlay=True,
        polyphony=4,
        density_scale=1.08,
        speed_scale=1.04,
        randomness_scale=1.04,
        bass_scale=1.06,
        melody_scale=1.14,
        darkness_scale=0.98,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("north_canes", "south_canes", "canes_combo", "arch", "line", "talking_heads"),
        primary_categories=("north_canes", "south_canes", "canes_combo", "talking_heads", "arch"),
        chorus_categories=("canes_combo", "arch", "line", "gt"),
        build_categories=("north_canes", "south_canes", "arch"),
        drop_blackout_ms=(140, 250),
        sweep_hit_ms=120,
    ),
    "v10.1": VariantStyle(
        version="v10.1",
        family="v10",
        title="Matrix Narrative",
        timing_mode="parts",
        pool_mode="sectional",
        placement_mode="scene_morph",
        keyboard_overlay=True,
        polyphony=3,
        density_scale=1.10,
        speed_scale=1.02,
        randomness_scale=1.08,
        bass_scale=1.04,
        melody_scale=1.16,
        darkness_scale=1.04,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "mega", "gt", "arch", "canes_combo", "stars", "snowflakes"),
        primary_categories=("line", "mega", "gt", "arch", "canes_combo"),
        chorus_categories=("line", "mega", "gt", "arch"),
        build_categories=("stars", "snowflakes", "arch", "line"),
        drop_blackout_ms=(170, 310),
        sweep_hit_ms=140,
    ),
    "v10.2": VariantStyle(
        version="v10.2",
        family="v10",
        title="Kinetic Relay",
        timing_mode="beat",
        pool_mode="rotating",
        placement_mode="percussion_relay",
        keyboard_overlay=False,
        polyphony=2,
        density_scale=1.16,
        speed_scale=1.14,
        randomness_scale=0.86,
        bass_scale=1.24,
        melody_scale=0.90,
        darkness_scale=1.00,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "gt", "canes_combo", "arch", "mega", "stars"),
        primary_categories=("line", "gt", "canes_combo", "arch"),
        chorus_categories=("line", "gt", "mega", "arch", "canes_combo"),
        build_categories=("arch", "line", "stars"),
        drop_blackout_ms=(130, 250),
        sweep_hit_ms=125,
    ),
    "v10.3": VariantStyle(
        version="v10.3",
        family="v10",
        title="Choir Focus",
        timing_mode="note",
        pool_mode="sectional",
        placement_mode="vocal_spotlight",
        keyboard_overlay=True,
        polyphony=4,
        density_scale=1.02,
        speed_scale=1.00,
        randomness_scale=0.96,
        bass_scale=1.00,
        melody_scale=1.24,
        darkness_scale=0.94,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("talking_heads", "north_canes", "south_canes", "arch", "line", "stars"),
        primary_categories=("talking_heads", "north_canes", "south_canes", "arch", "line"),
        chorus_categories=("talking_heads", "line", "arch", "canes_combo", "gt"),
        build_categories=("talking_heads", "stars", "arch"),
        drop_blackout_ms=(150, 260),
        sweep_hit_ms=115,
    ),
    "v11.1": VariantStyle(
        version="v11.1",
        family="v11",
        title="Spatial Conductor",
        timing_mode="parts",
        pool_mode="sectional",
        placement_mode="director_ai",
        keyboard_overlay=True,
        polyphony=3,
        density_scale=1.08,
        speed_scale=1.05,
        randomness_scale=0.90,
        bass_scale=1.12,
        melody_scale=1.08,
        darkness_scale=1.06,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "mega", "gt", "arch", "canes_combo", "stars", "snowflakes"),
        primary_categories=("line", "mega", "gt", "arch", "canes_combo", "talking_heads"),
        chorus_categories=("line", "mega", "gt", "arch", "canes_combo"),
        build_categories=("stars", "snowflakes", "arch", "line"),
        drop_blackout_ms=(180, 320),
        sweep_hit_ms=145,
    ),
    "v11.2": VariantStyle(
        version="v11.2",
        family="v11",
        title="Orbital Anthem",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="constellation_story",
        keyboard_overlay=False,
        polyphony=3,
        density_scale=1.00,
        speed_scale=1.10,
        randomness_scale=1.02,
        bass_scale=1.20,
        melody_scale=1.00,
        darkness_scale=1.02,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "line", "arch", "stars", "snowflakes", "canes_combo"),
        primary_categories=("mega", "line", "arch", "canes_combo"),
        chorus_categories=("mega", "line", "gt", "arch", "stars"),
        build_categories=("stars", "snowflakes", "arch"),
        drop_blackout_ms=(170, 300),
        sweep_hit_ms=135,
    ),
    "v11.3": VariantStyle(
        version="v11.3",
        family="v11",
        title="Universal Showcase",
        timing_mode="note",
        pool_mode="rotating",
        placement_mode="zone_riff",
        keyboard_overlay=True,
        polyphony=4,
        density_scale=1.14,
        speed_scale=1.08,
        randomness_scale=0.94,
        bass_scale=1.18,
        melody_scale=1.06,
        darkness_scale=0.98,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("line", "mega", "gt", "canes_combo", "arch", "stars", "snowflakes", "talking_heads"),
        primary_categories=("line", "mega", "gt", "canes_combo", "arch", "talking_heads"),
        chorus_categories=("line", "mega", "gt", "arch", "canes_combo", "stars"),
        build_categories=("arch", "stars", "snowflakes", "canes_combo"),
        drop_blackout_ms=(140, 250),
        sweep_hit_ms=118,
    ),
    "v12.1": VariantStyle(
        version="v12.1",
        family="v12",
        title="Build Pulse",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="scene_morph",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=1.16,
        speed_scale=1.06,
        randomness_scale=0.92,
        bass_scale=1.22,
        melody_scale=1.04,
        darkness_scale=0.90,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("line", "mega", "canes_combo", "arch", "gt", "stars", "snowflakes"),
        primary_categories=("line", "canes_combo", "mega", "arch", "gt"),
        chorus_categories=("line", "mega", "canes_combo", "arch", "gt", "stars"),
        build_categories=("arch", "line", "canes_combo", "stars", "snowflakes"),
        drop_blackout_ms=(210, 360),
        sweep_hit_ms=124,
    ),
    "v12.2": VariantStyle(
        version="v12.2",
        family="v12",
        title="Drop Sculpt",
        timing_mode="note",
        pool_mode="rotating",
        placement_mode="pulse_matrix",
        keyboard_overlay=True,
        polyphony=4,
        density_scale=1.20,
        speed_scale=1.10,
        randomness_scale=0.96,
        bass_scale=1.30,
        melody_scale=0.96,
        darkness_scale=0.92,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "line", "gt", "canes_combo", "arch", "stars"),
        primary_categories=("mega", "line", "canes_combo", "gt", "arch"),
        chorus_categories=("mega", "line", "gt", "canes_combo", "arch", "stars"),
        build_categories=("arch", "line", "canes_combo", "snowflakes", "stars"),
        drop_blackout_ms=(180, 330),
        sweep_hit_ms=116,
    ),
    "v12.3": VariantStyle(
        version="v12.3",
        family="v12",
        title="Sequential Drift",
        timing_mode="mixed",
        pool_mode="call_response",
        placement_mode="percussion_relay",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=1.10,
        speed_scale=1.12,
        randomness_scale=1.00,
        bass_scale=1.16,
        melody_scale=1.06,
        darkness_scale=0.96,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("canes_combo", "line", "arch", "gt", "mega", "stars", "snowflakes"),
        primary_categories=("canes_combo", "line", "arch", "gt", "mega"),
        chorus_categories=("line", "mega", "canes_combo", "arch", "gt", "stars"),
        build_categories=("arch", "line", "canes_combo", "snowflakes"),
        drop_blackout_ms=(170, 310),
        sweep_hit_ms=120,
    ),
    "v13.1": VariantStyle(
        version="v13.1",
        family="v13",
        title="Spatial Story",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="director_ai",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=1.08,
        speed_scale=1.06,
        randomness_scale=1.06,
        bass_scale=1.12,
        melody_scale=1.12,
        darkness_scale=0.94,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("arch", "line", "mega", "canes_combo", "gt", "stars", "snowflakes", "talking_heads"),
        primary_categories=("arch", "line", "mega", "canes_combo", "gt", "talking_heads"),
        chorus_categories=("line", "mega", "arch", "canes_combo", "gt", "stars", "talking_heads"),
        build_categories=("arch", "line", "snowflakes", "stars", "talking_heads"),
        drop_blackout_ms=(190, 320),
        sweep_hit_ms=128,
    ),
    "v13.2": VariantStyle(
        version="v13.2",
        family="v13",
        title="Bassline Flow",
        timing_mode="note",
        pool_mode="rotating",
        placement_mode="zone_riff",
        keyboard_overlay=True,
        polyphony=4,
        density_scale=1.18,
        speed_scale=1.08,
        randomness_scale=0.90,
        bass_scale=1.34,
        melody_scale=0.98,
        darkness_scale=0.98,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "line", "gt", "canes_combo", "arch", "stars", "snowflakes"),
        primary_categories=("mega", "canes_combo", "line", "gt", "arch"),
        chorus_categories=("mega", "line", "gt", "canes_combo", "arch", "stars"),
        build_categories=("arch", "line", "canes_combo", "snowflakes"),
        drop_blackout_ms=(160, 280),
        sweep_hit_ms=114,
    ),
    "v13.3": VariantStyle(
        version="v13.3",
        family="v13",
        title="Luma Finale",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="constellation_story",
        keyboard_overlay=True,
        polyphony=6,
        density_scale=1.14,
        speed_scale=1.04,
        randomness_scale=1.10,
        bass_scale=1.20,
        melody_scale=1.14,
        darkness_scale=0.90,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("stars", "snowflakes", "line", "mega", "arch", "canes_combo", "talking_heads"),
        primary_categories=("stars", "snowflakes", "line", "arch", "canes_combo", "talking_heads"),
        chorus_categories=("line", "mega", "stars", "snowflakes", "arch", "canes_combo"),
        build_categories=("stars", "snowflakes", "arch", "line", "talking_heads"),
        drop_blackout_ms=(200, 340),
        sweep_hit_ms=126,
    ),
    "v14.1": VariantStyle(
        version="v14.1",
        family="v14",
        title="Phrase Architect",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="phrase_architect",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.86,
        speed_scale=0.98,
        randomness_scale=0.18,
        bass_scale=1.14,
        melody_scale=1.08,
        darkness_scale=1.02,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "arch", "mega", "gt", "canes_combo", "matrix", "spinner"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "spinner", "canes_combo"),
        drop_blackout_ms=(220, 340),
        sweep_hit_ms=116,
    ),
    "v14.2": VariantStyle(
        version="v14.2",
        family="v14",
        title="Stem Command",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="stem_storyboard",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.90,
        speed_scale=1.02,
        randomness_scale=0.20,
        bass_scale=1.22,
        melody_scale=1.02,
        darkness_scale=0.98,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "line", "arch", "canes_combo", "matrix", "spinner"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "gt", "arch"),
        build_categories=("arch", "line", "matrix", "mega", "spinner"),
        drop_blackout_ms=(210, 330),
        sweep_hit_ms=120,
    ),
    "v14.3": VariantStyle(
        version="v14.3",
        family="v14",
        title="Contour Waves",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="wave_burst_director",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.92,
        speed_scale=1.04,
        randomness_scale=0.16,
        bass_scale=1.12,
        melody_scale=1.20,
        darkness_scale=0.96,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("arch", "line", "gt", "mega", "canes_combo", "matrix"),
        primary_categories=("arch", "line", "gt", "canes_combo", "matrix"),
        chorus_categories=("arch", "line", "mega", "gt", "canes_combo", "matrix"),
        build_categories=("arch", "line", "mega", "matrix", "spinner"),
        drop_blackout_ms=(210, 320),
        sweep_hit_ms=108,
    ),
    "v15.1": VariantStyle(
        version="v15.1",
        family="v15",
        title="Cinematic Arc",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="phrase_architect",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=1.00,
        speed_scale=1.02,
        randomness_scale=0.22,
        bass_scale=1.18,
        melody_scale=1.14,
        darkness_scale=0.96,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "arch", "mega", "gt", "canes_combo", "matrix", "spinner"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "spinner", "canes_combo", "mega"),
        drop_blackout_ms=(230, 350),
        sweep_hit_ms=116,
    ),
    "v15.2": VariantStyle(
        version="v15.2",
        family="v15",
        title="Orchestra Drive",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="stem_storyboard",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=1.04,
        speed_scale=1.04,
        randomness_scale=0.20,
        bass_scale=1.24,
        melody_scale=1.10,
        darkness_scale=0.96,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "line", "arch", "canes_combo", "matrix", "spinner", "gt"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "gt", "arch", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner"),
        drop_blackout_ms=(220, 340),
        sweep_hit_ms=120,
    ),
    "v15.3": VariantStyle(
        version="v15.3",
        family="v15",
        title="PrimeTime Finale",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="primetime_director",
        keyboard_overlay=True,
        polyphony=6,
        density_scale=1.08,
        speed_scale=1.06,
        randomness_scale=0.18,
        bass_scale=1.24,
        melody_scale=1.16,
        darkness_scale=0.94,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "canes_combo", "spinner", "gt"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "stars"),
        drop_blackout_ms=(230, 360),
        sweep_hit_ms=124,
    ),
    "v16.1": VariantStyle(
        version="v16.1",
        family="v16",
        title="Show Arc",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_arc",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.84,
        speed_scale=0.98,
        randomness_scale=0.14,
        bass_scale=1.16,
        melody_scale=1.08,
        darkness_scale=0.98,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "arch", "mega", "gt", "canes_combo", "matrix"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner"),
        drop_blackout_ms=(210, 330),
        sweep_hit_ms=112,
    ),
    "v16.2": VariantStyle(
        version="v16.2",
        family="v16",
        title="Stagecraft Stems",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.90,
        speed_scale=1.02,
        randomness_scale=0.16,
        bass_scale=1.24,
        melody_scale=1.06,
        darkness_scale=0.96,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "line", "arch", "canes_combo", "matrix", "spinner", "gt"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "gt", "arch", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner"),
        drop_blackout_ms=(210, 330),
        sweep_hit_ms=118,
    ),
    "v16.3": VariantStyle(
        version="v16.3",
        family="v16",
        title="Choreo Waves",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_motion",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.92,
        speed_scale=1.06,
        randomness_scale=0.12,
        bass_scale=1.10,
        melody_scale=1.24,
        darkness_scale=0.98,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("arch", "line", "gt", "mega", "canes_combo", "matrix"),
        primary_categories=("arch", "line", "gt", "canes_combo", "matrix"),
        chorus_categories=("arch", "line", "mega", "gt", "canes_combo", "matrix"),
        build_categories=("arch", "line", "mega", "matrix", "spinner"),
        drop_blackout_ms=(205, 320),
        sweep_hit_ms=104,
    ),
    "v17.1": VariantStyle(
        version="v17.1",
        family="v17",
        title="Signature Show",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.98,
        speed_scale=1.02,
        randomness_scale=0.18,
        bass_scale=1.20,
        melody_scale=1.14,
        darkness_scale=0.94,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "canes_combo", "spinner", "gt"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "stars"),
        drop_blackout_ms=(220, 345),
        sweep_hit_ms=118,
    ),
    "v17.2": VariantStyle(
        version="v17.2",
        family="v17",
        title="Choir Cinema",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.94,
        speed_scale=1.00,
        randomness_scale=0.16,
        bass_scale=1.12,
        melody_scale=1.20,
        darkness_scale=0.92,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("matrix", "line", "arch", "mega", "canes_combo", "spinner"),
        primary_categories=("talking_heads", "matrix", "line", "arch", "stars"),
        chorus_categories=("matrix", "mega", "spinner", "line", "arch", "gt"),
        build_categories=("line", "arch", "matrix", "stars", "snowflakes"),
        drop_blackout_ms=(220, 340),
        sweep_hit_ms=112,
    ),
    "v17.3": VariantStyle(
        version="v17.3",
        family="v17",
        title="Showstopper Cut",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=6,
        density_scale=1.04,
        speed_scale=1.06,
        randomness_scale=0.18,
        bass_scale=1.24,
        melody_scale=1.18,
        darkness_scale=0.92,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "canes_combo", "spinner", "gt"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "stars"),
        drop_blackout_ms=(230, 360),
        sweep_hit_ms=122,
    ),
    "v18.1": VariantStyle(
        version="v18.1",
        family="v18",
        title="Mapped Extreme",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="xtreme_essentials",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.86,
        speed_scale=1.00,
        randomness_scale=0.12,
        bass_scale=1.18,
        melody_scale=1.08,
        darkness_scale=0.96,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "line", "arch", "canes_combo", "matrix", "flood", "gt"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo", "flood"),
        chorus_categories=("mega", "matrix", "line", "arch", "gt", "canes_combo", "flood"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "flood"),
        drop_blackout_ms=(210, 330),
        sweep_hit_ms=112,
    ),
    "v18.2": VariantStyle(
        version="v18.2",
        family="v18",
        title="Submodel Surge",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="xtreme_submodel",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.92,
        speed_scale=1.04,
        randomness_scale=0.14,
        bass_scale=1.22,
        melody_scale=1.16,
        darkness_scale=0.96,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "line", "arch", "canes_combo", "matrix", "flood", "gt"),
        primary_categories=("matrix", "line", "arch", "canes_combo", "flood", "talking_heads"),
        chorus_categories=("mega", "matrix", "spinner", "line", "gt", "arch", "canes_combo", "flood"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "flood"),
        drop_blackout_ms=(215, 335),
        sweep_hit_ms=118,
    ),
    "v18.3": VariantStyle(
        version="v18.3",
        family="v18",
        title="Extreme Showcase",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="xtreme_showcase",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=1.00,
        speed_scale=1.04,
        randomness_scale=0.16,
        bass_scale=1.24,
        melody_scale=1.18,
        darkness_scale=0.92,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "canes_combo", "spinner", "gt", "flood"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo", "flood"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo", "flood"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "stars", "flood"),
        drop_blackout_ms=(225, 350),
        sweep_hit_ms=120,
    ),
    "v19.1": VariantStyle(
        version="v19.1",
        family="v19",
        title="Piano Spine",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_arc",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.84,
        speed_scale=0.98,
        randomness_scale=0.06,
        bass_scale=1.16,
        melody_scale=1.18,
        darkness_scale=0.98,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("canes_combo", "arch", "line", "gt", "mega", "matrix"),
        primary_categories=("canes_combo", "line", "arch", "gt", "mega"),
        chorus_categories=("canes_combo", "mega", "line", "arch", "gt", "matrix"),
        build_categories=("canes_combo", "arch", "line", "mega", "spinner"),
        drop_blackout_ms=(210, 330),
        sweep_hit_ms=110,
    ),
    "v19.2": VariantStyle(
        version="v19.2",
        family="v19",
        title="Keyed Stems",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.90,
        speed_scale=1.00,
        randomness_scale=0.06,
        bass_scale=1.20,
        melody_scale=1.16,
        darkness_scale=0.96,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("canes_combo", "line", "arch", "mega", "gt", "matrix", "spinner"),
        primary_categories=("canes_combo", "line", "arch", "matrix", "gt"),
        chorus_categories=("canes_combo", "mega", "line", "arch", "gt", "matrix"),
        build_categories=("canes_combo", "arch", "line", "mega", "spinner"),
        drop_blackout_ms=(214, 334),
        sweep_hit_ms=114,
    ),
    "v19.3": VariantStyle(
        version="v19.3",
        family="v19",
        title="Grand Keys",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.96,
        speed_scale=1.02,
        randomness_scale=0.08,
        bass_scale=1.22,
        melody_scale=1.20,
        darkness_scale=0.94,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("canes_combo", "mega", "line", "arch", "gt", "matrix", "spinner"),
        primary_categories=("canes_combo", "line", "arch", "matrix", "gt"),
        chorus_categories=("canes_combo", "mega", "matrix", "line", "arch", "gt"),
        build_categories=("canes_combo", "arch", "line", "mega", "spinner", "stars"),
        drop_blackout_ms=(220, 340),
        sweep_hit_ms=118,
    ),
    "v20.1": VariantStyle(
        version="v20.1",
        family="v20",
        title="Studio Recall",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_arc",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.88,
        speed_scale=0.98,
        randomness_scale=0.08,
        bass_scale=1.18,
        melody_scale=1.10,
        darkness_scale=0.96,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "arch", "mega", "gt", "canes_combo", "matrix"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner"),
        drop_blackout_ms=(212, 332),
        sweep_hit_ms=114,
    ),
    "v20.2": VariantStyle(
        version="v20.2",
        family="v20",
        title="Stem Recall",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.94,
        speed_scale=1.01,
        randomness_scale=0.08,
        bass_scale=1.22,
        melody_scale=1.08,
        darkness_scale=0.95,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "line", "arch", "canes_combo", "matrix", "spinner", "gt"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "gt", "arch", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner"),
        drop_blackout_ms=(214, 336),
        sweep_hit_ms=119,
    ),
    "v20.3": VariantStyle(
        version="v20.3",
        family="v20",
        title="Signature Recall",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.99,
        speed_scale=1.03,
        randomness_scale=0.10,
        bass_scale=1.24,
        melody_scale=1.14,
        darkness_scale=0.93,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "canes_combo", "spinner", "gt"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "stars"),
        drop_blackout_ms=(222, 346),
        sweep_hit_ms=120,
    ),
    "v21.1": VariantStyle(
        version="v21.1",
        family="v21",
        title="Scene Logic",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="phrase_architect",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.92,
        speed_scale=0.99,
        randomness_scale=0.10,
        bass_scale=1.18,
        melody_scale=1.14,
        darkness_scale=0.96,
        piano_echo=True,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "arch", "mega", "gt", "canes_combo", "matrix", "spinner"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "spinner", "canes_combo", "mega"),
        drop_blackout_ms=(224, 344),
        sweep_hit_ms=118,
    ),
    "v21.2": VariantStyle(
        version="v21.2",
        family="v21",
        title="Lane Logic",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="stem_storyboard",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.98,
        speed_scale=1.02,
        randomness_scale=0.10,
        bass_scale=1.22,
        melody_scale=1.12,
        darkness_scale=0.95,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "line", "arch", "canes_combo", "matrix", "spinner", "gt"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "gt", "arch", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner"),
        drop_blackout_ms=(222, 342),
        sweep_hit_ms=121,
    ),
    "v21.3": VariantStyle(
        version="v21.3",
        family="v21",
        title="Finale Logic",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="primetime_director",
        keyboard_overlay=True,
        polyphony=6,
        density_scale=1.04,
        speed_scale=1.05,
        randomness_scale=0.10,
        bass_scale=1.24,
        melody_scale=1.18,
        darkness_scale=0.93,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "canes_combo", "spinner", "gt"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "stars"),
        drop_blackout_ms=(232, 362),
        sweep_hit_ms=125,
    ),
    "v21.4": VariantStyle(
        version="v21.4",
        family="v21",
        title="Model Atlas",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_arc",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.96,
        speed_scale=1.00,
        randomness_scale=0.08,
        bass_scale=1.18,
        melody_scale=1.16,
        darkness_scale=0.95,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("line", "arch", "matrix", "spinner", "sphere", "canes_combo", "mega", "flood"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo", "flood"),
        build_categories=("arch", "line", "matrix", "spinner", "sphere", "canes_combo"),
        drop_blackout_ms=(224, 348),
        sweep_hit_ms=122,
    ),
    "v21.5": VariantStyle(
        version="v21.5",
        family="v21",
        title="Submodel Studio",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=False,
        polyphony=6,
        density_scale=0.93,
        speed_scale=1.02,
        randomness_scale=0.07,
        bass_scale=1.20,
        melody_scale=1.18,
        darkness_scale=0.94,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("matrix", "line", "arch", "spinner", "canes_combo", "mega", "sphere", "stars"),
        primary_categories=("talking_heads", "matrix", "line", "arch", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo", "flood"),
        build_categories=("matrix", "arch", "line", "spinner", "sphere", "stars"),
        drop_blackout_ms=(226, 352),
        sweep_hit_ms=124,
    ),
    "v21.6": VariantStyle(
        version="v21.6",
        family="v21",
        title="Pixel Auteur",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=6,
        density_scale=1.01,
        speed_scale=1.04,
        randomness_scale=0.07,
        bass_scale=1.24,
        melody_scale=1.20,
        darkness_scale=0.93,
        piano_echo=True,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo", "flood"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo", "flood"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(236, 366),
        sweep_hit_ms=128,
    ),
    "v22.1": VariantStyle(
        version="v22.1",
        family="v22",
        title="Premium Storyboard",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_arc",
        keyboard_overlay=True,
        polyphony=4,
        density_scale=0.90,
        speed_scale=0.98,
        randomness_scale=0.05,
        bass_scale=1.16,
        melody_scale=1.06,
        darkness_scale=0.98,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("line", "arch", "matrix", "spinner", "sphere", "canes_combo", "mega"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "spinner", "sphere", "canes_combo"),
        drop_blackout_ms=(214, 336),
        sweep_hit_ms=118,
    ),
    "v22.2": VariantStyle(
        version="v22.2",
        family="v22",
        title="Submodel Maestro",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.88,
        speed_scale=0.99,
        randomness_scale=0.05,
        bass_scale=1.16,
        melody_scale=1.05,
        darkness_scale=0.98,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("matrix", "line", "arch", "spinner", "canes_combo", "mega", "sphere", "stars"),
        primary_categories=("talking_heads", "matrix", "line", "arch", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("matrix", "arch", "line", "spinner", "sphere", "stars"),
        drop_blackout_ms=(218, 340),
        sweep_hit_ms=120,
    ),
    "v22.3": VariantStyle(
        version="v22.3",
        family="v22",
        title="Pixel Prestige",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.94,
        speed_scale=1.01,
        randomness_scale=0.05,
        bass_scale=1.20,
        melody_scale=1.10,
        darkness_scale=0.96,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(224, 350),
        sweep_hit_ms=122,
    ),
    "v23.1": VariantStyle(
        version="v23.1",
        family="v23",
        title="Scenic Director",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_arc",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.84,
        speed_scale=0.98,
        randomness_scale=0.04,
        bass_scale=1.16,
        melody_scale=1.04,
        darkness_scale=1.00,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("arch", "line", "matrix", "mega", "spinner", "sphere"),
        primary_categories=("matrix", "arch", "line", "talking_heads", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "arch", "line", "gt"),
        build_categories=("arch", "line", "matrix", "sphere", "stars"),
        drop_blackout_ms=(210, 332),
        sweep_hit_ms=116,
    ),
    "v23.2": VariantStyle(
        version="v23.2",
        family="v23",
        title="Detail Director",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.82,
        speed_scale=0.99,
        randomness_scale=0.03,
        bass_scale=1.15,
        melody_scale=1.04,
        darkness_scale=1.00,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("matrix", "line", "arch", "spinner", "canes_combo", "mega", "sphere", "stars"),
        primary_categories=("talking_heads", "matrix", "line", "arch", "canes_combo"),
        chorus_categories=("mega", "matrix", "spinner", "arch", "line", "gt", "sphere"),
        build_categories=("matrix", "arch", "line", "spinner", "sphere", "stars"),
        drop_blackout_ms=(214, 336),
        sweep_hit_ms=118,
    ),
    "v23.3": VariantStyle(
        version="v23.3",
        family="v23",
        title="Headliner Pixel",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=4,
        density_scale=0.88,
        speed_scale=1.00,
        randomness_scale=0.04,
        bass_scale=1.18,
        melody_scale=1.08,
        darkness_scale=0.98,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(220, 344),
        sweep_hit_ms=120,
    ),
    "v23.4": VariantStyle(
        version="v23.4",
        family="v23",
        title="Noir Stemcraft",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.78,
        speed_scale=0.97,
        randomness_scale=0.02,
        bass_scale=1.18,
        melody_scale=1.06,
        darkness_scale=1.12,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "arch", "line", "sphere", "gt"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(272, 448),
        sweep_hit_ms=116,
    ),
    "v23.5": VariantStyle(
        version="v23.5",
        family="v23",
        title="Suspense Signature",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.82,
        speed_scale=1.00,
        randomness_scale=0.025,
        bass_scale=1.20,
        melody_scale=1.10,
        darkness_scale=1.10,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "sphere", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(286, 470),
        sweep_hit_ms=114,
    ),
    "v23.6": VariantStyle(
        version="v23.6",
        family="v23",
        title="Apex Stem Noir",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=False,
        polyphony=4,
        density_scale=0.76,
        speed_scale=1.00,
        randomness_scale=0.02,
        bass_scale=1.22,
        melody_scale=1.06,
        darkness_scale=1.14,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "arch", "line", "sphere", "gt"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(312, 508),
        sweep_hit_ms=114,
    ),
    "v24.1": VariantStyle(
        version="v24.1",
        family="v24",
        title="Role Architect",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="hierarchy_roles",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.90,
        speed_scale=1.01,
        randomness_scale=0.03,
        bass_scale=1.20,
        melody_scale=1.10,
        darkness_scale=1.05,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "arch", "line", "gt", "sphere"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(248, 410),
        sweep_hit_ms=114,
    ),
    "v24.2": VariantStyle(
        version="v24.2",
        family="v24",
        title="Context Choreo",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="hierarchy_roles",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.92,
        speed_scale=1.03,
        randomness_scale=0.04,
        bass_scale=1.22,
        melody_scale=1.11,
        darkness_scale=1.08,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("line", "arch", "matrix", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "sphere", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(264, 438),
        sweep_hit_ms=112,
    ),
    "v24.3": VariantStyle(
        version="v24.3",
        family="v24",
        title="Apex Storyboard",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="hierarchy_roles",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.94,
        speed_scale=1.05,
        randomness_scale=0.05,
        bass_scale=1.24,
        melody_scale=1.13,
        darkness_scale=1.10,
        piano_echo=False,
        call_response=False,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "sphere", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(284, 468),
        sweep_hit_ms=110,
    ),
    "v25.1": VariantStyle(
        version="v25.1",
        family="v25",
        title="Raw Auto",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.98,
        speed_scale=1.05,
        randomness_scale=0.03,
        bass_scale=1.22,
        melody_scale=1.10,
        darkness_scale=1.08,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "sphere", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(260, 440),
        sweep_hit_ms=108,
    ),
    "v25.2": VariantStyle(
        version="v25.2",
        family="v25",
        title="Pro Vendor",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.92,
        speed_scale=1.03,
        randomness_scale=0.02,
        bass_scale=1.26,
        melody_scale=1.14,
        darkness_scale=1.12,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "sphere", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(300, 500),
        sweep_hit_ms=104,
    ),
    "v26.1": VariantStyle(
        version="v26.1",
        family="v26",
        title="Raw Auto",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_stems",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.98,
        speed_scale=1.04,
        randomness_scale=0.02,
        bass_scale=1.24,
        melody_scale=1.12,
        darkness_scale=1.10,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "sphere", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(260, 440),
        sweep_hit_ms=106,
    ),
    "v26.2": VariantStyle(
        version="v26.2",
        family="v26",
        title="Pro Vendor",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.90,
        speed_scale=1.02,
        randomness_scale=0.02,
        bass_scale=1.28,
        melody_scale=1.16,
        darkness_scale=1.14,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "sphere", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(320, 520),
        sweep_hit_ms=102,
    ),
    "v27.1": VariantStyle(
        version="v27.1",
        family="v27",
        title="Raw Auto",
        timing_mode="mixed",
        pool_mode="sectional",
        placement_mode="showcase_signature",
        keyboard_overlay=True,
        polyphony=5,
        density_scale=0.98,
        speed_scale=1.04,
        randomness_scale=0.02,
        bass_scale=1.26,
        melody_scale=1.14,
        darkness_scale=1.12,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "sphere", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(260, 440),
        sweep_hit_ms=104,
    ),
    "v27.2": VariantStyle(
        version="v27.2",
        family="v27",
        title="Helix Final",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="piano_lights",
        keyboard_overlay=True,
        polyphony=6,
        density_scale=0.92,
        speed_scale=1.03,
        randomness_scale=0.02,
        bass_scale=1.30,
        melody_scale=1.18,
        darkness_scale=1.16,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "sphere", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(340, 540),
        sweep_hit_ms=100,
    ),
    "v27.3": VariantStyle(
        version="v27.3",
        family="v27",
        title="Helix Prime",
        timing_mode="hook",
        pool_mode="sectional",
        placement_mode="piano_lights",
        keyboard_overlay=True,
        polyphony=6,
        density_scale=0.95,
        speed_scale=1.03,
        randomness_scale=0.02,
        bass_scale=1.28,
        melody_scale=1.16,
        darkness_scale=1.14,
        piano_echo=False,
        call_response=True,
        section_emphasis=True,
        sweep_categories=("mega", "matrix", "line", "arch", "spinner", "sphere", "canes_combo"),
        primary_categories=("matrix", "line", "arch", "talking_heads", "canes_combo", "sphere"),
        chorus_categories=("mega", "matrix", "spinner", "line", "arch", "gt", "sphere", "canes_combo"),
        build_categories=("arch", "line", "matrix", "mega", "spinner", "sphere", "stars"),
        drop_blackout_ms=(320, 520),
        sweep_hit_ms=102,
    ),
}

# Legacy-tuned style variants are preserved for compatibility, but the actively
# maintained sequencing profile is the current stable tuning below.
ACTIVE_STYLE_VERSION = "v27.3"
ACTIVE_STYLE = VARIANTS[ACTIVE_STYLE_VERSION]

GENERATE_SHOWCASE = False

WATERMARK_POLICY_VERSION = "dream-sequence-weaver-signature-v1"
WATERMARK_SALT = "DreamSequenceWeaver::Signature::2026-04"


def log(msg: str) -> None:
    base.log(msg)


def variant_output_name(audio_path: Path, output_dir: Path, version: str) -> Path:
    stem = audio_path.stem
    base_name = output_dir / f"{stem},{version}.xsq"
    if not base_name.exists():
        return base_name
    i = 1
    while True:
        cand = output_dir / f"{stem},{version} ({i}).xsq"
        if not cand.exists():
            return cand
        i += 1


def report_path(out_path: Path) -> Path:
    return out_path.with_name(f"{out_path.stem}.report.json")


def notes_path(out_path: Path) -> Path:
    return out_path.with_name(f"{out_path.stem}.sequence_notes.txt")


def ensure_audio_sidecar(audio_path: Path, out_path: Path) -> Path:
    """
    Keep a single shared audio copy per Outputs root to avoid redundant files.
    """
    try:
        output_dir = out_path.parent
        output_root = output_dir.parent if output_dir.parent.exists() else output_dir
        shared_dir = output_root / "_media"
        shared_dir.mkdir(parents=True, exist_ok=True)
        dest = shared_dir / audio_path.name
        if not dest.exists() or dest.stat().st_size != audio_path.stat().st_size:
            shutil.copy2(audio_path, dest)
        return dest
    except Exception as exc:
        log(f"[WARN] Audio sidecar copy skipped: {exc}")
        return audio_path


def resolve_layout_file(template_xsq: Path, explicit_layout: Path | None, cwd: Path | None = None) -> Path | None:
    """
    Resolve a best-effort layout path so model/group rows stay aligned with the
    active xLights layout even when --layout-file was omitted.
    """
    base_dir = (cwd or Path(".")).resolve()
    candidates: list[Path] = []
    if explicit_layout is not None:
        candidates.append(explicit_layout)
    template_dir = template_xsq.parent
    candidates.extend(
        [
            template_dir / "xlights_rgbeffects.xml",
            template_dir / "xlights_rgbeffects.xbkp",
            base_dir / "xlights_rgbeffects.xml",
            base_dir / "xlights_rgbeffects.xbkp",
            base_dir / "allmodels" / "xlights_rgbeffects.xml",
            base_dir / "allmodels" / "xlights_rgbeffects.xbkp",
        ]
    )
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved
    return None


def sanitize_template_marks(marks: list[int], song_length_ms: int) -> list[int]:
    """
    Keep template timing tracks only if they look sane for the current audio.
    Also de-offset stale tracks that start several seconds late.
    """
    if not marks:
        return []
    upper = max(song_length_ms + 1200, 2000)
    cleaned = sorted({int(ms) for ms in marks if int(ms) >= 0 and int(ms) <= upper})
    if not cleaned:
        return []
    cleaned = base.compress_times_ms(cleaned, 18)
    first = cleaned[0]
    if first >= 1800:
        shifted = [ms - first for ms in cleaned if ms >= first]
        shifted = [ms for ms in shifted if 0 <= ms <= upper]
        shifted = base.compress_times_ms(shifted, 18)
        if len(shifted) >= max(4, int(len(cleaned) * 0.55)):
            cleaned = shifted
    return cleaned


def timing_marks_usable(marks: list[int], song_length_ms: int, min_count: int) -> bool:
    if len(marks) < min_count:
        return False
    if marks[0] > 1400:
        return False
    return marks[-1] >= int(song_length_ms * 0.35)


def _layout_manifest_hash(parsed_layout: xmp.ParsedLayout | None) -> str:
    if parsed_layout is None:
        return ""
    rows: list[str] = []
    for model in sorted(parsed_layout.models.values(), key=lambda item: item.name.lower()):
        if model.is_submodel:
            continue
        rows.append(
            "|".join(
                [
                    model.name,
                    model.display_as,
                    model.type,
                    str(model.strings),
                    str(model.nodes_per_string),
                    str(model.total_pixels),
                ]
            )
        )
    blob = "\n".join(rows).encode("utf-8", errors="ignore")
    return hashlib.sha256(blob).hexdigest()


def build_watermark_signature(
    *,
    style: VariantStyle,
    audio_path: Path,
    template_xsq: Path,
    out_path: Path,
    song_length_ms: int,
    root_model_count: int,
    layout_manifest_hash: str,
) -> str:
    parts = [
        WATERMARK_SALT,
        WATERMARK_POLICY_VERSION,
        style.version,
        audio_path.name.lower(),
        template_xsq.name.lower(),
        out_path.name.lower(),
        str(max(1, song_length_ms)),
        str(max(0, root_model_count)),
        layout_manifest_hash or "-",
    ]
    return hashlib.sha256("::".join(parts).encode("utf-8", errors="ignore")).hexdigest()


def build_watermark_track(signature: str, song_length_ms: int) -> list[tuple[str, int, int]]:
    if not signature:
        return []
    usable = [int(signature[i: i + 2], 16) for i in range(0, min(len(signature), 64), 2)]
    if not usable:
        return []
    marks: list[tuple[str, int, int]] = []
    cursor = max(240, (usable[0] % 180) + 240)
    for idx in range(min(24, len(usable))):
        step = usable[idx]
        st = min(max(0, song_length_ms - 90), cursor)
        dur = 70 + (step % 9) * 14
        en = min(song_length_ms, st + max(60, dur))
        nibble = signature[idx * 2: idx * 2 + 2].upper()
        marks.append((f"HX{idx + 1:02d}-{nibble}", int(st), int(max(st + 1, en))))
        cursor += 280 + (usable[(idx + 5) % len(usable)] * 9)
        if cursor >= song_length_ms - 120:
            cursor = (cursor % max(300, song_length_ms - 300)) + 140
    marks.sort(key=lambda item: item[1])
    return marks


def clamp_profile(profile: base.UserProfile, style: VariantStyle) -> base.UserProfile:
    profile = base.UserProfile(
        feel=profile.feel,
        density=base.clamp(profile.density * style.density_scale, 0.35, 2.60),
        speed=base.clamp(profile.speed * style.speed_scale, 0.35, 2.60),
        randomness=base.clamp(profile.randomness * style.randomness_scale, 0.0, 1.0),
        bass_bias=base.clamp(profile.bass_bias * style.bass_scale, 0.50, 2.40),
        melody_density=base.clamp(profile.melody_density * style.melody_scale, 0.50, 2.40),
        darkness=base.clamp(profile.darkness * style.darkness_scale, 0.40, 1.95),
        save_settings=profile.save_settings,
    )
    base.DENSITY = profile.density
    base.SPEED = profile.speed
    base.RANDOMNESS = profile.randomness
    return profile


def normalize_override_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")


def prioritize_categories(categories: tuple[str, ...], priority: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for category in priority:
        if category in categories and category not in seen:
            seen.add(category)
            out.append(category)
    for category in categories:
        if category not in seen:
            seen.add(category)
            out.append(category)
    return tuple(out)


def apply_runtime_style(style: VariantStyle, tuning: RuntimeTuning) -> VariantStyle:
    out = style
    if tuning.polyphony_override is not None:
        out = replace(out, polyphony=max(1, min(8, int(tuning.polyphony_override))))

    cane_focus = base.clamp(float(tuning.cane_focus), 0.50, 2.50)
    keyboard_mix = base.clamp(float(tuning.keyboard_mix), 0.00, 2.00)
    if cane_focus >= 1.05:
        cane_priority = ("canes_combo", "north_canes", "south_canes", "arch", "line", "gt", "mega")
        out = replace(
            out,
            primary_categories=prioritize_categories(out.primary_categories, cane_priority),
            chorus_categories=prioritize_categories(out.chorus_categories, cane_priority),
            build_categories=prioritize_categories(out.build_categories, cane_priority),
            sweep_categories=prioritize_categories(
                out.sweep_categories,
                ("canes_combo", "arch", "line", "gt", "mega", "snowflakes", "stars", "talking_heads"),
            ),
        )

    if keyboard_mix >= 0.60 and not out.keyboard_overlay and out.family not in {"v14", "v15", "v16", "v17", "v18"}:
        out = replace(out, keyboard_overlay=True)
    return out


def coerce_override_payload(raw: object) -> dict[str, str | list[str]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str | list[str]] = {}
    for key, value in raw.items():
        key_norm = normalize_override_key(str(key))
        if not key_norm:
            continue
        if isinstance(value, str):
            clean = value.strip()
            if clean:
                out[key_norm] = clean
            continue
        if isinstance(value, list):
            parts = [str(item).strip() for item in value if str(item).strip()]
            if not parts:
                continue
            out[key_norm] = parts if len(parts) > 1 else parts[0]
    return out


def load_override_file(path: Path | None) -> dict[str, str | list[str]]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return coerce_override_payload(payload)


def match_model_token(token: str, names: list[str]) -> str | None:
    token = token.strip()
    if not token:
        return None
    token_lower = token.lower()
    token_norm = base.normalize_name(token)
    exact = [name for name in names if name.lower() == token_lower]
    if exact:
        return exact[0]
    norm_exact = [name for name in names if base.normalize_name(name) == token_norm]
    if norm_exact:
        return norm_exact[0]
    partial = [name for name in names if token_norm and token_norm in base.normalize_name(name)]
    if partial:
        partial.sort(key=lambda item: (len(item), item.lower()))
        return partial[0]
    return None


def resolve_override_models(raw: str | list[str], names: list[str]) -> list[str]:
    parts = [raw] if isinstance(raw, str) else list(raw)
    resolved: list[str] = []
    seen: set[str] = set()
    for token in parts:
        found = match_model_token(str(token), names)
        if not found:
            continue
        key = found.lower()
        if key in seen:
            continue
        seen.add(key)
        resolved.append(found)
    return resolved


def apply_model_overrides(
    layout: base.Layout,
    pools: list[SequentialPool],
    names: list[str],
    overrides: dict[str, str | list[str]],
) -> tuple[int, int, list[str]]:
    if not overrides:
        return (0, 0, [])

    scalar_fields = {
        "house": "house",
        "garage": "garage",
        "all_white": "all_white",
        "all_red": "all_red",
        "all_green": "all_green",
        "all_notes": "all_notes",
        "blvd_all": "blvd_all",
        "perim_all": "perim_all",
        "mega_group": "mega_group",
        "line_all": "line_all",
        "cane_group_north": "cane_g_n",
        "cane_group_south": "cane_g_s",
        "cane_g_n": "cane_g_n",
        "cane_g_s": "cane_g_s",
        "notes_main": "notes_main",
        "notes_mirror": "notes_mirror",
    }
    list_fields = {
        "north_canes": "north_canes",
        "south_canes": "south_canes",
        "mega_models": "mega_models",
        "line_models": "line_models",
        "red_models": "red_models",
        "green_models": "green_models",
        "white_models": "white_models",
        "blvd": "blvd",
        "perim": "perim",
        "snowflakes": "snowflakes",
        "stars": "stars",
    }

    lane_override: list[str] = []
    layout_updates = 0
    pool_updates = 0

    for key, raw in overrides.items():
        if key in {"keyboard_lane", "notes_lane", "poly_lane"}:
            lane_override = resolve_override_models(raw, names)
            continue

        if key in scalar_fields:
            picked = resolve_override_models(raw, names)
            setattr(layout, scalar_fields[key], picked[0] if picked else None)
            layout_updates += 1
            continue

        if key in list_fields:
            setattr(layout, list_fields[key], resolve_override_models(raw, names))
            layout_updates += 1
            continue

        for pool in pools:
            if key not in {normalize_override_key(pool.name), normalize_override_key(pool.category)}:
                continue
            resolved = resolve_override_models(raw, names)
            if len(resolved) >= 2:
                pool.models = resolved
                pool_updates += 1

    return (layout_updates, pool_updates, lane_override)


def effect_family(name: str) -> str:
    n = name.lower()
    if "ramp" in n or "morph" in n or "fade" in n:
        return "ramp"
    if "vu meter" in n or "bars" in n:
        return "vu"
    if "tendril" in n:
        return "tendril"
    if "spiral" in n or "pinwheel" in n:
        return "motion"
    if "strobe" in n or "flash" in n:
        return "strobe"
    if "on" in n:
        return "on"
    return "other"


def build_template_profile(xsq: base.XsqIndex, pools: list[SequentialPool]) -> TemplateProfile:
    model_categories: dict[str, set[str]] = {}
    for pool in pools:
        for model in pool.models:
            model_categories.setdefault(model, set()).add(pool.category)

    category_scores: dict[str, int] = {}
    category_family_counts: dict[str, dict[str, int]] = {}
    global_family_counts: dict[str, int] = {}

    for model, categories in model_categories.items():
        el = xsq.elements.get(model)
        if el is None:
            continue
        effects = [name.lower() for name in base.element_effect_names(el)]
        if not effects:
            continue
        families = [effect_family(name) for name in effects]
        for category in categories:
            category_scores[category] = category_scores.get(category, 0) + len(effects)
            bucket = category_family_counts.setdefault(category, {})
            for family in families:
                bucket[family] = bucket.get(family, 0) + 1
        for family in families:
            global_family_counts[family] = global_family_counts.get(family, 0) + 1

    category_effect_families: dict[str, list[str]] = {}
    for category, counts in category_family_counts.items():
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        category_effect_families[category] = [name for name, _count in ordered[:4]]

    discovered_effect_families = [
        family for family, _count in sorted(global_family_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    return TemplateProfile(
        category_scores=category_scores,
        category_effect_families=category_effect_families,
        discovered_effect_families=discovered_effect_families,
    )


def apply_template_profile(style: VariantStyle, profile: TemplateProfile) -> VariantStyle:
    if not profile.category_scores:
        return style

    def reorder(categories: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(
                categories,
                key=lambda category: (-profile.category_scores.get(category, 0), categories.index(category)),
            )
        )

    return replace(
        style,
        primary_categories=reorder(style.primary_categories),
        chorus_categories=reorder(style.chorus_categories),
        build_categories=reorder(style.build_categories),
        sweep_categories=reorder(style.sweep_categories),
    )


def normalize_palette_mode(raw: str) -> str:
    value = (raw or "template").strip().lower().replace("-", "_").replace(" ", "_")
    if value in {"template", "christmas", "warm", "cool", "neon", "random", "workspace_match"}:
        return value
    return "template"


def extract_palette_hexes(palette: str) -> list[str]:
    return re.findall(r"#[0-9a-fA-F]{6}", palette or "")


def palette_matches_mode(palette: str, mode: str) -> bool:
    colors = [color.lower() for color in extract_palette_hexes(palette)]
    if not colors:
        return False
    if mode == "christmas":
        return any(color.startswith("#ff") for color in colors) and any(color.startswith("#00") for color in colors)
    if mode == "warm":
        return any(color.startswith("#ff") or color.startswith("#fa") for color in colors)
    if mode == "cool":
        return any(color.startswith("#00") or color.startswith("#33") for color in colors)
    if mode == "neon":
        return any(color in {"#ff00ff", "#00ffff", "#39ff14", "#ff1493"} for color in colors)
    return True


def scan_workspace_preferences(
    *,
    template_xsq: Path,
    output_dir: Path,
    tuning: RuntimeTuning,
) -> WorkspaceHistoryProfile:
    if not tuning.workspace_history_enabled:
        return WorkspaceHistoryProfile(family_effects={}, palette_pool=[])
    # Safety: only learn from this tool's own generated outputs.
    # We require sidecar report files to avoid ingesting external/vendor XSQs.
    search_dirs: list[Path] = [output_dir]
    candidate_paths: list[Path] = []
    seen: set[str] = set()
    for directory in search_dirs:
        if not directory.exists():
            continue
        for path in directory.rglob("*.xsq"):
            low = str(path).lower()
            if "template" in path.name.lower():
                continue
            if ",v" not in path.name.lower():
                continue
            report_path = path.with_suffix(".report.json")
            if not report_path.exists():
                continue
            if low in seen:
                continue
            seen.add(low)
            candidate_paths.append(path)
    candidate_paths.sort(key=lambda path: path.stat().st_mtime if path.exists() else 0.0, reverse=True)
    candidate_paths = candidate_paths[: max(4, int(tuning.workspace_history_limit))]

    family_effect_counts: dict[str, dict[str, int]] = {}
    palette_counts: dict[str, int] = {}
    for path in candidate_paths:
        try:
            xsq = base.load_xsq(path)
        except Exception:
            continue
        for model_name, element in xsq.elements.items():
            family = prop_family(model_name, None) or "generic"
            family_bucket = family_effect_counts.setdefault(family, {})
            for effect in base._find_any(element, "Effect"):  # type: ignore[attr-defined]
                effect_name = base._effect_name(effect).strip()  # type: ignore[attr-defined]
                if effect_name:
                    family_bucket[effect_name] = family_bucket.get(effect_name, 0) + 1
                palette = base._effect_palette(effect)  # type: ignore[attr-defined]
                if palette:
                    palette_counts[palette] = palette_counts.get(palette, 0) + 1

    family_effects: dict[str, list[str]] = {}
    for family, bucket in family_effect_counts.items():
        ordered = sorted(bucket.items(), key=lambda item: (-item[1], item[0].lower()))
        family_effects[family] = [name for name, _count in ordered[:6]]
    palette_pool = [palette for palette, _count in sorted(palette_counts.items(), key=lambda item: (-item[1], item[0]))[:120]]
    return WorkspaceHistoryProfile(family_effects=family_effects, palette_pool=palette_pool)


def pick_palette_for_effect(
    *,
    mode: str,
    template_palette: str | None,
    template_pool: list[str],
    history_pool: list[str],
    rng: random.Random,
    effect_index: int,
) -> str | None:
    mode_key = normalize_palette_mode(mode)
    if mode_key == "template":
        return template_palette
    candidates = history_pool + template_pool
    if mode_key == "workspace_match":
        return history_pool[(effect_index + rng.randrange(max(1, len(history_pool)))) % len(history_pool)] if history_pool else (template_palette or (template_pool[0] if template_pool else None))
    if mode_key == "random":
        return candidates[rng.randrange(len(candidates))] if candidates else template_palette
    themed = [palette for palette in candidates if palette_matches_mode(palette, mode_key)]
    if themed:
        return themed[(effect_index + rng.randrange(max(1, len(themed)))) % len(themed)]
    return template_palette or (candidates[0] if candidates else None)


def combined_canes(layout: base.Layout) -> list[str]:
    out: list[str] = []
    n = min(len(layout.north_canes), len(layout.south_canes))
    for i in range(n):
        out.append(layout.north_canes[i])
        out.append(layout.south_canes[i])
    return out


def find_series_anywhere(names: list[str], patterns: list[str]) -> list[str]:
    return [name for _num, name in find_indexed_series_anywhere(names, patterns)]


def find_indexed_series_anywhere(names: list[str], patterns: list[str]) -> list[tuple[int, str]]:
    items: list[tuple[int, str]] = []
    seen: set[str] = set()
    for name in names:
        norm = base.normalize_name(name)
        for pattern in patterns:
            m = re.search(pattern, norm, flags=re.IGNORECASE)
            if not m:
                continue
            key = name.lower()
            if key in seen:
                break
            try:
                num = int(m.group(1))
            except Exception:
                continue
            items.append((num, name))
            seen.add(key)
            break
    items.sort(key=lambda item: (item[0], item[1].lower()))
    return items


def flatten_indexed_series(items: list[tuple[int, str]]) -> list[str]:
    return [name for _num, name in items]


def find_numeric_name_range(names: list[str], lo: int, hi: int) -> list[str]:
    items: list[tuple[int, str]] = []
    seen: set[str] = set()
    for name in names:
        raw = name.strip()
        if not raw.isdigit():
            continue
        num = int(raw)
        if num < lo or num > hi:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append((num, name))
    items.sort(key=lambda item: (item[0], item[1].lower()))
    return [name for _num, name in items]


def find_color_indexed_series(names: list[str], base_patterns: tuple[str, ...]) -> dict[str, list[tuple[int, str]]]:
    color_series: dict[str, list[tuple[int, str]]] = {}
    for color in ("red", "white", "green"):
        patterns = [rf"{pattern}\s*{color}\s*(\d+)\b" for pattern in base_patterns]
        color_series[color] = find_indexed_series_anywhere(names, patterns)
    return color_series


def interleave_color_indexed_series(
    color_series: dict[str, list[tuple[int, str]]],
    color_order: tuple[str, ...] = ("red", "white", "green"),
) -> list[str]:
    by_color: dict[str, dict[int, str]] = {
        color: {idx: name for idx, name in color_series.get(color, [])}
        for color in color_order
    }
    indices = sorted({idx for mapping in by_color.values() for idx in mapping})
    ordered: list[str] = []
    for idx in indices:
        for color in color_order:
            name = by_color[color].get(idx)
            if name:
                ordered.append(name)
    return ordered


def find_ordered_color_waypoints(
    names: list[str],
    waypoint_tokens: tuple[tuple[str, ...], ...],
    color: str,
) -> list[str]:
    normalized = [(name, base.normalize_name(name)) for name in names]
    ordered: list[str] = []
    used: set[str] = set()
    for tokens in waypoint_tokens:
        matches = [
            name
            for name, norm in normalized
            if color in norm and all(token in norm for token in tokens) and name.lower() not in used
        ]
        if not matches:
            continue
        matches.sort(key=lambda value: value.lower())
        choice = matches[0]
        ordered.append(choice)
        used.add(choice.lower())
    return ordered


def detailed_pool_summary(pool: SequentialPool) -> str:
    models = pool.models[:]
    if not models:
        return f"{pool.name} [{pool.category}] count=0"
    if len(models) <= 10:
        preview = ", ".join(models)
    else:
        preview = ", ".join(models[:3]) + " ... " + ", ".join(models[-3:])
    return f"{pool.name} [{pool.category}] count={len(models)} :: {preview}"


def discover_talking_heads(names: list[str]) -> list[str]:
    numbered = find_series_anywhere(
        names,
        [
            r"\btalking\s*head\s*(\d+)\b",
            r"\bsinging\s*face\s*(\d+)\b",
            r"\bsinger\s*(\d+)\b",
            r"\blyric\s*(\d+)\b",
            r"\bface\s*(\d+)\b",
            r"\bhead\s*(\d+)\b",
        ],
    )
    if numbered:
        return numbered
    out: list[str] = []
    for name in names:
        norm = base.normalize_name(name)
        if "all" in norm:
            continue
        if any(
            token in norm
            for token in (
                "talking head",
                "singing face",
                "singing tree face",
                "face panel",
                "singer",
                "lyric",
                "mouth",
            )
        ):
            out.append(name)
    return sorted(out, key=lambda n: n.lower())


def discover_keyword_models(
    names: list[str],
    *,
    numbered_patterns: list[str] | None = None,
    include_tokens: tuple[str, ...],
    exclude_tokens: tuple[str, ...] = (),
) -> list[str]:
    numbered = find_series_anywhere(names, numbered_patterns or [])
    if numbered:
        return numbered
    out: list[str] = []
    for name in names:
        norm = base.normalize_name(name)
        if "all" in norm:
            continue
        if exclude_tokens and any(token in norm for token in exclude_tokens):
            continue
        if any(token in norm for token in include_tokens):
            out.append(name)
    return sorted(out, key=lambda n: (base.normalize_name(n), n.lower()))


def parsed_models_sorted(
    parsed_layout: xmp.ParsedLayout | None,
    available_names: list[str],
    semantic_types: tuple[str, ...],
    *,
    colors: tuple[str, ...] | None = None,
    exclude_tokens: tuple[str, ...] = (),
    include_submodels: bool = False,
) -> list[str]:
    if parsed_layout is None:
        return []
    available = set(available_names)
    wanted = {base.normalize_name(item) for item in semantic_types}
    color_wanted = {base.normalize_name(item) for item in (colors or ())}
    ranked: list[tuple[float, float, str]] = []
    for name, model in parsed_layout.models.items():
        if name not in available:
            continue
        if model.is_submodel and not include_submodels:
            continue
        if base.normalize_name(model.type) not in wanted:
            continue
        norm = base.normalize_name(name)
        if exclude_tokens and any(token in norm for token in exclude_tokens):
            continue
        if color_wanted and base.normalize_name(model.color_family or "") not in color_wanted:
            continue
        center = model.center()
        ranked.append((center[0], center[1], name))
    ranked.sort(key=lambda item: (item[0], item[1], item[2].lower()))
    return [name for _x, _y, name in ranked]


def dedupe_names(names: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def expand_pool_models_with_submodels(
    models: list[str],
    *,
    category: str,
    parsed_layout: xmp.ParsedLayout | None,
) -> list[str]:
    if parsed_layout is None:
        return dedupe_names(models)
    expanded: list[str] = []
    for name in models:
        model = parsed_layout.model_for(name)
        if model is None:
            expanded.append(name)
            continue
        targets = parsed_layout.preferred_sequence_targets(model.name, category)
        expanded.extend(targets if targets else [model.name])
    return dedupe_names(expanded)


def family_from_parsed_model(model: xmp.Model) -> str:
    semantic = base.normalize_name(model.type)
    display = base.normalize_name(model.display_as)
    signature = " ".join(part for part in (semantic, display, base.normalize_name(model.name)) if part)

    if semantic in {"view object", "group", "submodel", "model group", "object group"}:
        return ""
    if any(token in signature for token in ("talking head", "singing face", "face panel", "mouth", "lyric", "phoneme")):
        return "talking_heads"
    if semantic == "matrix":
        return "matrix"
    if semantic == "image":
        return "matrix"
    if semantic == "custom":
        if model.is_rgb_capable() or model.total_pixels >= 24 or model.strings >= 4:
            return "matrix"
        return "line"
    if semantic == "spinner":
        return "spinner"
    if semantic == "sphere":
        return "sphere"
    if semantic == "flood":
        return "flood"
    if semantic == "cube":
        return "matrix"
    if semantic == "circle":
        return "sphere" if model.is_rgb_capable() else "line"
    if semantic == "wreath":
        return "sphere" if model.is_rgb_capable() else "line"
    if semantic == "star":
        return "stars"
    if semantic == "cane":
        return "canes_combo"
    if semantic == "arch":
        return "arch"
    if semantic in {"icicle", "window", "channelblock", "multipoint"}:
        return "line"
    if semantic == "line":
        return "line"
    if semantic == "tree":
        if model.strings >= 12 or model.total_pixels >= 180:
            return "mega"
        if model.strings >= 4 or model.total_pixels >= 24:
            return "gt"
        return "line"

    if "snowflake" in signature:
        return "snowflakes"
    if "star" in signature:
        return "stars"
    if "flood" in signature or "strobe" in signature:
        return "flood"
    if any(token in signature for token in ("spinner", "pinwheel", "moving head", "servo", "skull")):
        return "spinner"
    if any(token in signature for token in ("sphere", "orb", "globe", "wreath", "circle")):
        return "sphere"
    if "matrix" in signature or "panel" in signature or "video wall" in signature or "cube" in signature:
        return "matrix"
    if "arch" in signature:
        return "arch"
    if "candy cane" in signature or re.search(r"\bcane\b", signature):
        return "canes_combo"
    if any(token in signature for token in ("window", "icicle", "single line", "poly line", "channel block", "multi point", "multipoint")):
        return "line"
    if "tree" in signature:
        if model.strings >= 12 or model.total_pixels >= 180:
            return "mega"
        return "gt"

    if model.is_rgb_capable() or model.total_pixels >= 24:
        if model.strings >= 8 or model.total_pixels >= 180:
            return "mega"
        if model.strings >= 4 or model.nodes_per_string >= 12:
            return "matrix"
        return "line"
    if model.total_pixels <= 3:
        return "flood"
    return "line"


def enrich_layout_with_parsed(layout: base.Layout, names: list[str], parsed_layout: xmp.ParsedLayout | None) -> base.Layout:
    if parsed_layout is None:
        return layout

    def fallback(current: list[str], semantic_types: tuple[str, ...], *, colors: tuple[str, ...] | None = None, exclude_tokens: tuple[str, ...] = ()) -> list[str]:
        if current:
            return current
        return parsed_models_sorted(parsed_layout, names, semantic_types, colors=colors, exclude_tokens=exclude_tokens)

    return replace(
        layout,
        mega_models=fallback(layout.mega_models, ("tree",)),
        line_models=fallback(layout.line_models, ("line", "icicle", "window", "channelblock", "multipoint"), exclude_tokens=("candy cane", "cane")),
        stars=fallback(layout.stars, ("star",)),
        red_models=fallback(layout.red_models, ("line", "arch", "tree", "circle", "wreath", "star", "icicle", "window", "channelblock"), colors=("red",)),
        green_models=fallback(layout.green_models, ("line", "arch", "tree", "circle", "wreath", "star", "icicle", "window", "channelblock"), colors=("green",)),
        white_models=fallback(layout.white_models, ("line", "arch", "tree", "circle", "wreath", "star", "icicle", "window", "channelblock"), colors=("white",)),
    )


def discover_sequential_pools(names: list[str], layout: base.Layout, parsed_layout: xmp.ParsedLayout | None = None) -> list[SequentialPool]:
    pools: list[SequentialPool] = []
    pooled_by_category: dict[str, set[str]] = {}
    names_set = set(names)
    perimeter_waypoints = (
        ("right", "linden"),
        ("right", "blvd"),
        ("center", "blvd"),
        ("left", "blvd"),
        ("left", "tree"),
    )

    def add_pool(name: str, category: str, models: list[str]) -> None:
        deduped = dedupe_names(models)
        if not deduped:
            return
        pools.append(SequentialPool(name=name, category=category, models=deduped))
        pooled_by_category.setdefault(category, set()).update(deduped)

    gt_models = find_series_anywhere(names, [r"\bgt\s*(\d+)\b"]) or base.find_numbered_series(names, [r"gt\s*(\d+)"])
    add_pool("gt_bounce", "gt", gt_models)

    notes_main = find_numeric_name_range(names, 1, 16)
    notes_mirror = find_numeric_name_range(names, 17, 32)

    mega_models = layout.mega_models or parsed_models_sorted(parsed_layout, names, ("tree",)) or find_series_anywhere(
        names,
        [
            r"\bmega\s*tree(?:\s*(?:red|green|white))?\s*(\d+)\b",
            r"\bmt\s*(\d+)\b",
        ],
    )
    mega_colors = find_color_indexed_series(names, (r"\bmega\s*tree\b",))
    line_models = layout.line_models or parsed_models_sorted(parsed_layout, names, ("line", "icicle", "window", "channelblock", "multipoint"), exclude_tokens=("candy cane", "cane")) or find_series_anywhere(
        names,
        [
            r"\bline(?:\s*tree)?(?:\s*(?:red|green|white))?\s*(\d+)\b",
            r"\bline\s*tree(?:\s*(?:red|green|white))?\s*(\d+)\b",
        ],
    )
    line_colors = find_color_indexed_series(names, (r"\bline\s*tree\b",))
    garage_models = find_series_anywhere(
        names,
        [
            r"\bgarage\s*tree(?:s)?\s*(\d+)\b",
        ],
    )
    garage_colors = find_color_indexed_series(names, (r"\bgarage\s*trees?\b",))
    perimeter_red = find_ordered_color_waypoints(names, perimeter_waypoints, "red")
    perimeter_white = find_ordered_color_waypoints(names, perimeter_waypoints, "white")
    perimeter_green = find_ordered_color_waypoints(names, perimeter_waypoints, "green")
    snowflakes = find_series_anywhere(
        names,
        [
            r"\bsf\s*(\d+)\b",
            r"\bsnowflake\s*(\d+)\b",
            r"\bsnow\s*flake\s*(\d+)\b",
        ],
    )
    stars = find_series_anywhere(
        names,
        [
            r"\bstar\s*(\d+)\b",
            r"\bshooting\s*star\s*(\d+)\b",
        ],
    ) or parsed_models_sorted(parsed_layout, names, ("star",))
    arch_models = parsed_models_sorted(parsed_layout, names, ("arch",))
    matrix_models = discover_keyword_models(
        names,
        numbered_patterns=[
            r"\bmatrix\s*(\d+)\b",
            r"\bpanel\s*(\d+)\b",
            r"\bvideo\s*panel\s*(\d+)\b",
        ],
        include_tokens=("matrix", "panel", "video wall", "video panel"),
        exclude_tokens=("face panel", "singing face"),
    ) or parsed_models_sorted(parsed_layout, names, ("matrix", "cube", "image"))
    spinner_models = discover_keyword_models(
        names,
        numbered_patterns=[
            r"\bspinner\s*(\d+)\b",
            r"\bspin(?:ner)?\s*(\d+)\b",
            r"\bpinwheel\s*(\d+)\b",
        ],
        include_tokens=("spinner", "pinwheel", "spin"),
    ) or parsed_models_sorted(parsed_layout, names, ("spinner",))
    sphere_models = discover_keyword_models(
        names,
        numbered_patterns=[
            r"\bsphere\s*(\d+)\b",
            r"\borb\s*(\d+)\b",
            r"\bglobe\s*(\d+)\b",
        ],
        include_tokens=("sphere", "orb", "globe"),
    ) or parsed_models_sorted(parsed_layout, names, ("sphere", "circle", "wreath"))
    flood_models = discover_keyword_models(
        names,
        numbered_patterns=[
            r"\bflood(?:\s*light)?\s*(\d+)\b",
            r"\bstrobe(?:\s*light)?\s*(\d+)\b",
        ],
        include_tokens=("flood", "ground strobe", "strobe"),
        exclude_tokens=("all",),
    ) or parsed_models_sorted(parsed_layout, names, ("flood",))
    custom_rgb_models: list[str] = []
    custom_single_models: list[str] = []
    if parsed_layout is not None:
        ranked_rgb: list[tuple[float, float, str]] = []
        ranked_single: list[tuple[float, float, str]] = []
        for model in parsed_layout.models.values():
            if model.is_submodel or model.name not in names_set:
                continue
            if base.normalize_name(model.type) != "custom":
                continue
            center = model.center()
            if model.is_rgb_capable() or model.total_pixels >= 24 or model.strings >= 4:
                ranked_rgb.append((center[0], center[1], model.name))
            else:
                ranked_single.append((center[0], center[1], model.name))
        ranked_rgb.sort(key=lambda item: (item[0], item[1], item[2].lower()))
        ranked_single.sort(key=lambda item: (item[0], item[1], item[2].lower()))
        custom_rgb_models = [item[2] for item in ranked_rgb]
        custom_single_models = [item[2] for item in ranked_single]
    north_canes = layout.north_canes or find_series_anywhere(
        names,
        [
            r"\bnorth\s*candy\s*cane\s*(\d+)\b",
            r"\bnorth\s*cane\s*(\d+)\b",
        ],
    )
    south_canes = layout.south_canes or find_series_anywhere(
        names,
        [
            r"\bsouth\s*candy\s*cane\s*(\d+)\b",
            r"\bsouth\s*cane\s*(\d+)\b",
        ],
    )
    combo = combined_canes(layout)
    if not combo and (north_canes or south_canes):
        if north_canes and south_canes:
            n = min(len(north_canes), len(south_canes))
            combo = [model for i in range(n) for model in (north_canes[i], south_canes[i])]
        else:
            combo = north_canes or south_canes

    add_pool("mega_white", "mega", mega_models)
    add_pool("line_white", "line", line_models)
    add_pool("notes_1_16", "notes", notes_main)
    add_pool("notes_17_32", "notes", notes_mirror)
    add_pool("line_tree_rgb", "line", interleave_color_indexed_series(line_colors))
    add_pool("line_tree_red", "line", flatten_indexed_series(line_colors.get("red", [])))
    add_pool("line_tree_white", "line", flatten_indexed_series(line_colors.get("white", [])))
    add_pool("line_tree_green", "line", flatten_indexed_series(line_colors.get("green", [])))
    add_pool("mega_tree_rgb", "mega", interleave_color_indexed_series(mega_colors))
    add_pool("mega_tree_red", "mega", flatten_indexed_series(mega_colors.get("red", [])))
    add_pool("mega_tree_white", "mega", flatten_indexed_series(mega_colors.get("white", [])))
    add_pool("mega_tree_green", "mega", flatten_indexed_series(mega_colors.get("green", [])))
    add_pool("garage_tree_rgb", "gt", interleave_color_indexed_series(garage_colors))
    add_pool("garage_tree_red", "gt", flatten_indexed_series(garage_colors.get("red", [])))
    add_pool("garage_tree_white", "gt", flatten_indexed_series(garage_colors.get("white", [])))
    add_pool("garage_tree_green", "gt", flatten_indexed_series(garage_colors.get("green", [])))
    add_pool("perimeter_red", "line", perimeter_red)
    add_pool("perimeter_white", "line", perimeter_white)
    add_pool("perimeter_green", "line", perimeter_green)
    add_pool("garage_trees", "gt", garage_models)
    add_pool("snowflakes", "snowflakes", snowflakes)
    add_pool("stars", "stars", stars)
    add_pool("matrix_panels", "matrix", matrix_models)
    add_pool("custom_rgb_matrix", "matrix", custom_rgb_models)
    add_pool("spinners", "spinner", spinner_models)
    add_pool("spheres", "sphere", sphere_models)
    add_pool("floods", "flood", flood_models)
    add_pool("custom_single_line", "line", custom_single_models)
    add_pool("north_canes", "north_canes", north_canes)
    add_pool("south_canes", "south_canes", south_canes)
    add_pool("canes_combo", "canes_combo", combo)
    add_pool("talking_heads", "talking_heads", discover_talking_heads(names))
    add_pool("arch_spatial", "arch", arch_models)

    if parsed_layout is not None:
        nbh_by_family: dict[str, list[tuple[float, float, str]]] = {}
        nbh_all_ranked: list[tuple[float, float, str]] = []
        for model in parsed_layout.models.values():
            if model.is_submodel or model.name not in names_set:
                continue
            if not base.normalize_name(model.name).startswith("nbh"):
                continue
            family = family_from_parsed_model(model) or "line"
            center = model.center()
            nbh_by_family.setdefault(family, []).append((center[0], center[1], model.name))
            nbh_all_ranked.append((center[0], center[1], model.name))
        for family, ranked in sorted(nbh_by_family.items(), key=lambda item: item[0]):
            ranked.sort(key=lambda item: (item[0], item[1], item[2].lower()))
            add_pool(f"nbh_{family}", family, [item[2] for item in ranked])
        nbh_all_ranked.sort(key=lambda item: (item[0], item[1], item[2].lower()))
        add_pool("nbh_all", "line", [item[2] for item in nbh_all_ranked])

    for arch_num in sorted(layout.arches.keys()):
        add_pool(f"arch_{arch_num}", "arch", layout.arches[arch_num])

    if parsed_layout is not None:
        fallback_by_family: dict[str, list[tuple[float, float, str]]] = {}
        for model in parsed_layout.models.values():
            if model.is_submodel or model.name not in names_set:
                continue
            family = family_from_parsed_model(model)
            if not family:
                continue
            if model.name in pooled_by_category.get(family, set()):
                continue
            center = model.center()
            fallback_by_family.setdefault(family, []).append((center[0], center[1], model.name))
        for family, ranked in sorted(fallback_by_family.items(), key=lambda item: item[0]):
            ranked.sort(key=lambda item: (item[0], item[1], item[2].lower()))
            add_pool(f"auto_{family}_fallback", family, [item[2] for item in ranked])

    if parsed_layout is not None:
        pools = [
            replace(
                pool,
                models=expand_pool_models_with_submodels(
                    pool.models,
                    category=pool.category,
                    parsed_layout=parsed_layout,
                ),
            )
            for pool in pools
        ]
    return pools


def pools_by_category(pools: list[SequentialPool], categories: tuple[str, ...]) -> list[SequentialPool]:
    selected = [pool for pool in pools if pool.category in categories]
    return selected if selected else pools


def analyze_harmonic(audio: base.Audio) -> HarmonicData:
    y_harm, _ = librosa.effects.hpss(audio.y)
    hop = base.HOP_MS
    cqt_mag = np.abs(
        librosa.cqt(
            y_harm,
            sr=audio.sr,
            hop_length=hop,
            fmin=librosa.note_to_hz("C2"),
            n_bins=60,
            bins_per_octave=12,
        )
    )
    # Supplement CQT with piptrack so polyphonic note picking can use true pitch bins too.
    stft_mag = np.abs(librosa.stft(y_harm, n_fft=2048, hop_length=hop))
    pitch_hz, pitch_mag = librosa.piptrack(S=stft_mag, sr=audio.sr, hop_length=hop, fmin=65.0, fmax=2800.0)
    times_s = librosa.frames_to_time(np.arange(cqt_mag.shape[1]), sr=audio.sr, hop_length=hop)
    return HarmonicData(
        times_s=np.asarray(times_s),
        cqt_mag=np.asarray(cqt_mag),
        base_midi=36,
        pitch_hz=np.asarray(pitch_hz),
        pitch_mag=np.asarray(pitch_mag),
    )


def infer_song_parts(sections: list[base.Section]) -> list[SongPart]:
    if not sections:
        return []
    drop_idxs = [i for i, sec in enumerate(sections) if sec.label == "DROP"]
    first_drop = drop_idxs[0] if drop_idxs else len(sections)
    last_drop = drop_idxs[-1] if drop_idxs else -1
    raw: list[SongPart] = []
    for i, sec in enumerate(sections):
        if sec.label == "INTRO":
            label = "INTRO"
        elif sec.label == "OUTRO":
            label = "OUTRO"
        elif sec.label == "DROP":
            label = "CHORUS"
        elif sec.label == "BUILD":
            if i + 1 < len(sections) and sections[i + 1].label == "DROP":
                label = "PRECHORUS"
            elif drop_idxs and first_drop < i < last_drop:
                label = "BRIDGE"
            else:
                label = "PRECHORUS"
        else:
            if i < first_drop:
                label = "VERSE"
            elif drop_idxs and first_drop < i < last_drop and i >= int(len(sections) * 0.55):
                label = "BRIDGE"
            else:
                label = "VERSE"
        raw.append(SongPart(label=label, start_ms=sec.start_ms, end_ms=sec.end_ms, energy=sec.energy))

    collapsed: list[SongPart] = [raw[0]]
    for part in raw[1:]:
        prev = collapsed[-1]
        if prev.label == part.label and part.start_ms <= prev.end_ms:
            prev.end_ms = part.end_ms
            prev.energy = max(prev.energy, part.energy)
        else:
            collapsed.append(part)
    normalized: list[SongPart] = []
    seen_chorus = False
    for part in collapsed:
        duration = max(1, part.end_ms - part.start_ms)
        if part.label == "INTRO" and duration > 18000:
            split = part.start_ms + min(duration - 4000, 8000)
            normalized.append(SongPart(label="INTRO", start_ms=part.start_ms, end_ms=split, energy=part.energy))
            normalized.append(SongPart(label="VERSE", start_ms=split, end_ms=part.end_ms, energy=part.energy))
            continue
        if part.label in {"PRECHORUS", "BRIDGE"} and duration > 20000:
            tail = min(9000, max(6000, duration // 3))
            split = max(part.start_ms + 4000, part.end_ms - tail)
            front_label = "BRIDGE" if seen_chorus else "VERSE"
            normalized.append(SongPart(label=front_label, start_ms=part.start_ms, end_ms=split, energy=part.energy))
            normalized.append(SongPart(label=part.label, start_ms=split, end_ms=part.end_ms, energy=part.energy))
            continue
        normalized.append(part)
        if part.label == "CHORUS":
            seen_chorus = True
    return normalized


def part_for_time(parts: list[SongPart], t_ms: int) -> str:
    for part in parts:
        if part.start_ms <= t_ms < part.end_ms:
            return part.label
    return parts[-1].label if parts else "VERSE"


def choose_event_times(style: VariantStyle, beat_ms: list[int], onset_ms: list[int], note_onset_ms: list[int], bar_ms: list[int]) -> list[int]:
    if style.timing_mode == "note":
        return note_onset_ms
    if style.timing_mode == "beat":
        return base.compress_times_ms(beat_ms[:], max(80, base.scaled_gap(80)))
    if style.timing_mode == "mixed":
        return base.compress_times_ms(sorted(set(note_onset_ms + beat_ms[::2])), base.scaled_gap(45))
    if style.timing_mode == "hook":
        return base.compress_times_ms(sorted(set(note_onset_ms + beat_ms + bar_ms)), base.scaled_gap(50))
    return base.compress_times_ms(sorted(set(note_onset_ms + bar_ms)), base.scaled_gap(55))


def downsample_marks(marks: list[int], max_marks: int) -> list[int]:
    if max_marks <= 0:
        return []
    clean = sorted(set(int(mark) for mark in marks if int(mark) >= 0))
    if len(clean) <= max_marks:
        return clean
    stride = max(1, int(math.ceil(len(clean) / float(max_marks))))
    return clean[::stride]


def phrase_spans_from_bars(bar_ms: list[int], song_length_ms: int, bars_per_phrase: int = 4) -> list[tuple[str, int, int]]:
    marks = downsample_marks(bar_ms, max_marks=1600)
    if not marks:
        return []
    spans: list[tuple[str, int, int]] = []
    phrase_idx = 1
    for idx in range(0, len(marks), max(1, bars_per_phrase)):
        start = marks[idx]
        end_idx = min(len(marks) - 1, idx + max(1, bars_per_phrase))
        end = marks[end_idx] if end_idx > idx else min(song_length_ms, start + max(260, base.scaled_dur(420)))
        if idx + max(1, bars_per_phrase) >= len(marks):
            end = max(start + 1, song_length_ms)
        spans.append((f"Phrase {phrase_idx}", start, max(start + 1, end)))
        phrase_idx += 1
    return spans


def transition_spans_from_parts(parts: list[SongPart], song_length_ms: int) -> list[tuple[str, int, int]]:
    spans: list[tuple[str, int, int]] = []
    for idx in range(1, len(parts)):
        prev = parts[idx - 1]
        curr = parts[idx]
        start = max(0, curr.start_ms - 120)
        end = min(song_length_ms, max(curr.start_ms + 1, curr.start_ms + 220))
        spans.append((f"{prev.label}->{curr.label}", start, end))
    return spans


def derive_dynamic_marks(audio: base.Audio) -> tuple[list[int], list[int], list[int]]:
    if audio.times_s.size == 0:
        return ([], [], [])
    energy_peaks = base.compress_times_ms(
        [base.ms(t) for t in base.peak_times(audio.times_s, audio.rms01, 0.09, 12)],
        base.scaled_gap(120),
    )
    rise_curve = np.clip(np.gradient(np.asarray(audio.rms01, dtype=float)), 0.0, None)
    fall_curve = np.clip(-np.gradient(np.asarray(audio.rms01, dtype=float)), 0.0, None)
    build_lifts = base.compress_times_ms(
        [base.ms(t) for t in base.peak_times(audio.times_s, rise_curve, 0.025, 10)],
        base.scaled_gap(110),
    )
    releases = base.compress_times_ms(
        [base.ms(t) for t in base.peak_times(audio.times_s, fall_curve, 0.025, 10)],
        base.scaled_gap(110),
    )
    return (energy_peaks, build_lifts, releases)


def marks_to_spans(
    marks: list[int],
    *,
    prefix: str,
    pulse_ms: int = 70,
    max_marks: int = 2800,
) -> list[tuple[str, int, int]]:
    compressed = downsample_marks(marks, max_marks=max_marks)
    spans: list[tuple[str, int, int]] = []
    for idx, start in enumerate(compressed):
        next_start = compressed[idx + 1] if idx + 1 < len(compressed) else (start + max(1, int(pulse_ms)))
        end = min(start + max(1, int(pulse_ms)), max(start + 1, next_start - 1))
        if end <= start:
            end = start + 1
        spans.append((f"{prefix} {idx + 1}", start, end))
    return spans


def bars_to_spans(bar_ms: list[int], song_length_ms: int) -> list[tuple[str, int, int]]:
    marks = downsample_marks(bar_ms, max_marks=1400)
    if not marks:
        return []
    spans: list[tuple[str, int, int]] = []
    for idx, start in enumerate(marks):
        if idx + 1 < len(marks):
            end = max(start + 1, marks[idx + 1])
        else:
            end = max(start + 1, min(song_length_ms, start + max(240, base.scaled_dur(420))))
        spans.append((f"Bar {idx + 1}", start, end))
    return spans


def write_auto_timing_tracks(
    *,
    style: VariantStyle,
    xsq_root: ET.Element,
    song_length_ms: int,
    beat_ms: list[int],
    bar_ms: list[int],
    onset_ms: list[int],
    note_onset_ms: list[int],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    energy_peaks: list[int],
    build_lifts: list[int],
    releases: list[int],
    sections: list[base.Section],
    parts: list[SongPart],
    blackout_windows: list[tuple[int, int]],
) -> None:
    qm_prefix = f"AUTO QM {style.version}"
    tracks: list[tuple[str, list[tuple[str, int, int]]]] = []
    tracks.append((f"{qm_prefix} Beats", marks_to_spans(beat_ms, prefix="Beat", pulse_ms=55, max_marks=2600)))
    tracks.append((f"{qm_prefix} Bars", bars_to_spans(bar_ms, song_length_ms)))
    tracks.append((f"{qm_prefix} Onsets", marks_to_spans(onset_ms, prefix="Onset", pulse_ms=45, max_marks=3000)))
    tracks.append((f"{qm_prefix} Poly Notes", marks_to_spans(note_onset_ms, prefix="Poly", pulse_ms=60, max_marks=3000)))
    tracks.append((f"{qm_prefix} Kicks", marks_to_spans(kicks, prefix="Kick", pulse_ms=80, max_marks=2200)))
    tracks.append((f"{qm_prefix} Snares", marks_to_spans(snares, prefix="Snare", pulse_ms=80, max_marks=2200)))
    tracks.append((f"{qm_prefix} Hats", marks_to_spans(hats, prefix="Hat", pulse_ms=55, max_marks=2600)))
    tracks.append((f"{qm_prefix} Bass Peaks", marks_to_spans(bass_peaks, prefix="Bass", pulse_ms=95, max_marks=2000)))
    tracks.append((f"{qm_prefix} Vocal Peaks", marks_to_spans(vocal_peaks, prefix="Vocal", pulse_ms=95, max_marks=2000)))
    tracks.append((f"{qm_prefix} Energy Peaks", marks_to_spans(energy_peaks, prefix="Energy", pulse_ms=120, max_marks=1800)))
    tracks.append((f"{qm_prefix} Build Lifts", marks_to_spans(build_lifts, prefix="Lift", pulse_ms=105, max_marks=1800)))
    tracks.append((f"{qm_prefix} Releases", marks_to_spans(releases, prefix="Release", pulse_ms=100, max_marks=1800)))
    if sections:
        section_spans = [(f"{section.label} {idx + 1}", section.start_ms, max(section.start_ms + 1, section.end_ms)) for idx, section in enumerate(sections)]
        tracks.append((f"{qm_prefix} Sections", section_spans))
    if parts:
        part_spans = [(f"{part.label} {idx + 1}", part.start_ms, max(part.start_ms + 1, part.end_ms)) for idx, part in enumerate(parts)]
        tracks.append((f"{qm_prefix} Parts", part_spans))
        tracks.append((f"{qm_prefix} Phrases", phrase_spans_from_bars(bar_ms, song_length_ms)))
        tracks.append((f"{qm_prefix} Transitions", transition_spans_from_parts(parts, song_length_ms)))
        buildup_spans: list[tuple[str, int, int]] = []
        drop_spans: list[tuple[str, int, int]] = []
        for idx, part in enumerate(parts):
            if part.label in {"PRECHORUS", "BRIDGE"}:
                buildup_spans.append((f"Buildup {idx + 1}", part.start_ms, max(part.start_ms + 1, part.end_ms)))
            if part.label == "CHORUS":
                drop_end = min(part.end_ms, part.start_ms + 450)
                drop_spans.append((f"Drop {idx + 1}", part.start_ms, max(part.start_ms + 1, drop_end)))
        if buildup_spans:
            tracks.append((f"{qm_prefix} Buildups", buildup_spans))
        if drop_spans:
            tracks.append((f"{qm_prefix} Drops", drop_spans))
    if blackout_windows:
        blackout_spans = [(f"Blackout {idx + 1}", st, max(st + 1, en)) for idx, (st, en) in enumerate(blackout_windows)]
        tracks.append((f"{qm_prefix} Blackouts", blackout_spans))

    for name, spans in tracks:
        if spans:
            base.write_timing_track(xsq_root, name, spans, active=False)


def extract_polyphonic_events(
    audio: base.Audio,
    harmonic: HarmonicData,
    event_times_ms: list[int],
    sections: list[base.Section],
    parts: list[SongPart],
    style: VariantStyle,
) -> list[NoteEvent]:
    events: list[NoteEvent] = []
    if harmonic.cqt_mag.size == 0:
        return events
    for i, t_ms in enumerate(event_times_ms):
        idx = int(np.searchsorted(harmonic.times_s, t_ms / 1000.0))
        i0 = max(0, idx - 1)
        i1 = min(harmonic.cqt_mag.shape[1], idx + 2)
        if i0 >= i1:
            continue
        spec = np.asarray(harmonic.cqt_mag[:, i0:i1].mean(axis=1), dtype=float)
        top = float(np.max(spec)) if spec.size else 0.0
        if top <= 1e-8:
            continue
        norm = spec / top
        part_label = part_for_time(parts, t_ms)
        section_label = base.section_for_time(sections, t_ms)
        threshold = 0.38
        if part_label in {"CHORUS", "PRECHORUS"}:
            threshold = 0.34
        if part_label in {"INTRO", "OUTRO"}:
            threshold = 0.44

        # CQT candidates (robust harmonic bins)
        work = norm.copy()
        cqt_candidates: list[tuple[int, float]] = []
        for _ in range(max(1, style.polyphony * 2)):
            note_idx = int(np.argmax(work))
            strength = float(work[note_idx])
            if strength < threshold:
                break
            cqt_candidates.append((harmonic.base_midi + note_idx, strength))
            lo = max(0, note_idx - 1)
            hi = min(len(work), note_idx + 2)
            work[lo:hi] = 0.0

        # Piptrack candidates (actual frequency bins around the event frame)
        pip_candidates: list[tuple[int, float]] = []
        if harmonic.pitch_hz.size and harmonic.pitch_mag.size:
            p0 = max(0, idx - 1)
            p1 = min(harmonic.pitch_hz.shape[1], idx + 2)
            if p0 < p1:
                hz_slice = harmonic.pitch_hz[:, p0:p1]
                mag_slice = harmonic.pitch_mag[:, p0:p1]
                if hz_slice.size and mag_slice.size:
                    mag_mean = np.asarray(mag_slice.mean(axis=1), dtype=float)
                    mag_top = float(np.max(mag_mean)) if mag_mean.size else 0.0
                    if mag_top > 1e-8:
                        mag_norm = mag_mean / mag_top
                        ranked = np.argsort(mag_norm)[::-1][: max(6, style.polyphony * 3)]
                        for rank_idx in ranked:
                            strength = float(mag_norm[rank_idx])
                            if strength < (threshold * 0.85):
                                break
                            hz = float(np.asarray(hz_slice[rank_idx]).mean())
                            if hz <= 0:
                                continue
                            midi = int(round(librosa.hz_to_midi(hz)))
                            if 24 <= midi <= 108:
                                pip_candidates.append((midi, strength))

        # Merge CQT + piptrack and keep strongest unique MIDI notes.
        merged: list[tuple[int, float]] = []
        for midi, strength in cqt_candidates + pip_candidates:
            existing = next((idx2 for idx2, (m2, _s2) in enumerate(merged) if abs(m2 - midi) <= 1), None)
            if existing is None:
                merged.append((midi, strength))
            else:
                m0, s0 = merged[existing]
                if strength > s0:
                    merged[existing] = (midi if strength >= s0 else m0, max(s0, strength))
        merged.sort(key=lambda pair: pair[1], reverse=True)
        picked = merged[: max(1, style.polyphony)]
        if not picked:
            note_idx = int(np.argmax(norm))
            picked = [(harmonic.base_midi + note_idx, float(norm[note_idx]))]
        if i + 1 < len(event_times_ms):
            end_ms = min(event_times_ms[i + 1], t_ms + base.scaled_dur(220))
        else:
            end_ms = t_ms + base.scaled_dur(220)
        events.append(
            NoteEvent(
                start_ms=t_ms,
                end_ms=max(t_ms + 40, end_ms),
                notes=picked,
                part=part_label,
                section=section_label,
            )
        )
    return events


def choose_pool(style: VariantStyle, pools: list[SequentialPool], part: str, event_idx: int, rng: random.Random) -> SequentialPool:
    if not pools:
        raise ValueError("No sequential pools discovered.")

    if part == "CHORUS":
        candidates = pools_by_category(pools, style.chorus_categories)
    elif part in {"PRECHORUS", "BRIDGE"}:
        candidates = pools_by_category(pools, style.build_categories)
    else:
        candidates = pools_by_category(pools, style.primary_categories)

    if style.pool_mode == "random":
        return rng.choice(candidates)
    if style.pool_mode == "call_response":
        return candidates[event_idx % len(candidates)]
    if style.pool_mode == "sectional":
        return candidates[(event_idx // 2) % len(candidates)]
    return candidates[event_idx % len(candidates)]


def map_notes_to_models(
    pool: SequentialPool,
    event: NoteEvent,
    state: dict[str, int],
    style: VariantStyle,
    rng: random.Random,
) -> list[str]:
    count = len(pool.models)
    if count == 0:
        return []
    cursor = state.get(pool.name, 0)
    indices: list[int] = []
    for midi, _strength in event.notes:
        frac = base.clamp((midi - 48) / 36.0, 0.0, 1.0)
        idx = int(round(frac * (count - 1)))
        if style.pool_mode == "rotating":
            idx = (idx + cursor) % count
        elif style.pool_mode == "random":
            idx = (idx + rng.randrange(count)) % count
        elif style.pool_mode == "sectional":
            idx = (idx + (cursor // 2)) % count
        elif style.pool_mode == "call_response":
            idx = (idx + cursor) % count if (cursor % 2 == 0) else (count - 1 - idx)
        indices.append(idx)
    if not indices:
        indices = [cursor % count]
    if style.call_response and count > 2:
        indices.append(count - 1 - indices[0])
    if style.piano_echo and count > 3 and event.part in {"CHORUS", "PRECHORUS"}:
        indices.append((indices[0] + 1) % count)
    unique: list[int] = []
    seen: set[int] = set()
    for idx in indices:
        idx_i = int(base.clamp(idx, 0, count - 1))
        if idx_i in seen:
            continue
        seen.add(idx_i)
        unique.append(idx_i)
    state[pool.name] = (cursor + 1) % count
    return [pool.models[idx] for idx in unique]


def ordered_unique(values: list[int]) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def expand_indices(center: int, count: int, reach: int, reverse: bool, wrap: bool = False) -> list[int]:
    out = [center]
    for offset in range(1, reach + 1):
        pair = [center - offset, center + offset]
        if reverse:
            pair.reverse()
        for idx in pair:
            if wrap:
                out.append(idx % count)
            elif 0 <= idx < count:
                out.append(idx)
    return ordered_unique(out)


def place_note_phrase(
    add_fn,
    pool: SequentialPool,
    event: NoteEvent,
    targets: list[str],
    style: VariantStyle,
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
) -> tuple[int, int]:
    count = len(pool.models)
    if count == 0 or not targets:
        return (0, 0)

    indices = ordered_unique([pool.models.index(model) for model in targets if model in pool.models])
    if not indices:
        return (0, 0)

    base_duration = max(60, min(event.end_ms - event.start_ms, base.scaled_dur(260)))
    midi_sum = sum(midi for midi, _ in event.notes)
    reverse = bool((midi_sum + len(indices)) % 2)
    placements = 0
    phrase_end = event.start_ms + base_duration

    def add_one(model: str, st: int, en: int, label: str, use_ramp: bool = False) -> None:
        nonlocal placements, phrase_end
        add_fn(
            model,
            st,
            en,
            label,
            eff="Ramp" if use_ramp else "On",
            tpl=ramp_tpl if use_ramp else None,
        )
        placements += 1
        phrase_end = max(phrase_end, en)

    if pool.category == "arch":
        reach = 2 if event.part in {"CHORUS", "PRECHORUS", "BRIDGE"} else 1
        full = ordered_unique(
            [idx for center in indices for idx in expand_indices(center, count, reach, reverse, wrap=False)]
        )
        for step, idx in enumerate(full):
            st = event.start_ms + step * 28
            en = min(event.end_ms + 140, st + base_duration + step * 18)
            add_one(pool.models[idx], st, en, "digital_piano_arch", use_ramp=(ramp_ok and step < len(full) - 1))
        return placements, phrase_end

    if pool.category in {"canes_combo", "north_canes", "south_canes"}:
        direction = -1 if reverse else 1
        full: list[int] = []
        for center in indices:
            full.extend(expand_indices(center, count, 1, reverse, wrap=True))
            if event.part in {"CHORUS", "PRECHORUS", "BRIDGE"} and count > 3:
                full.append((center + 2 * direction) % count)
        full = ordered_unique(full)[: min(5, count)]
        for step, idx in enumerate(full):
            st = event.start_ms + step * 30
            en = st + max(65, base_duration - step * 18)
            add_one(pool.models[idx], st, en, "digital_piano_canes", use_ramp=(ramp_ok and step == len(full) - 1 and event.part != "VERSE"))
        return placements, phrase_end

    if pool.category in {"line", "mega", "gt"}:
        full: list[int] = []
        for center in indices:
            full.extend(expand_indices(center, count, 1 if event.part == "VERSE" else 2, reverse, wrap=False))
        full = ordered_unique(full)[: min(4, count)]
        for step, idx in enumerate(full):
            st = event.start_ms + step * 24
            en = st + max(60, base_duration - step * 12)
            add_one(pool.models[idx], st, en, "digital_piano_motion", use_ramp=(ramp_ok and step > 0 and event.part in {"PRECHORUS", "BRIDGE"}))
        return placements, phrase_end

    if pool.category in {"stars", "snowflakes"}:
        full = indices[:]
        if count > len(full):
            full.append(rng.randrange(count))
        if event.part in {"CHORUS", "PRECHORUS"} and count > len(full):
            full.append((indices[0] + 2) % count)
        full = ordered_unique(full)[: min(4, count)]
        for step, idx in enumerate(full):
            st = event.start_ms + step * 18
            en = st + max(55, int(base_duration * (0.72 - 0.08 * min(step, 3))))
            add_one(pool.models[idx], st, en, "digital_piano_scatter", use_ramp=False)
        return placements, phrase_end

    for idx, model in enumerate(targets):
        st = event.start_ms + idx * 20
        en = st + base_duration
        add_one(model, st, en, "digital_piano", use_ramp=(ramp_ok and idx > 0 and event.part in {"PRECHORUS", "BRIDGE"}))
    return placements, phrase_end


def add_sweep(add_fn, pool: SequentialPool, start_ms: int, end_ms: int, label: str, hit_ms: int, reverse: bool) -> None:
    if len(pool.models) < 2:
        return
    order = list(reversed(pool.models)) if reverse else list(pool.models)
    step = max(16, int((end_ms - start_ms) / max(1, len(order))))
    hit = max(40, min(hit_ms, max(50, step + 40)))
    for i, model in enumerate(order):
        st = start_ms + i * step
        en = min(end_ms, st + hit)
        add_fn(model, st, en, label)


def choose_cycle_pool(pools: list[SequentialPool], state: dict[str, int], key: str) -> SequentialPool | None:
    if not pools:
        return None
    idx = state.get(key, 0)
    state[key] = idx + 1
    return pools[idx % len(pools)]


def select_preferred_pool(
    pools: list[SequentialPool],
    categories: tuple[str, ...],
    state: dict[str, int],
    key: str,
    *,
    require_multiple: bool = False,
) -> SequentialPool | None:
    candidates = [pool for pool in pools if pool.category in categories and pool.models]
    if require_multiple:
        candidates = [pool for pool in candidates if len(pool.models) >= 2]
    if not candidates:
        candidates = [pool for pool in pools if pool.models and (len(pool.models) >= 2 if require_multiple else True)]
    return choose_cycle_pool(candidates, state, key)


def representative_models(pool: SequentialPool | None, desired_count: int) -> list[str]:
    if pool is None or not pool.models:
        return []
    count = max(1, min(len(pool.models), int(desired_count)))
    if count == 1:
        return [pool.models[len(pool.models) // 2]]
    step = (len(pool.models) - 1) / float(count - 1)
    indices = ordered_unique([int(round(step * idx)) for idx in range(count)])
    return [pool.models[idx] for idx in indices if 0 <= idx < len(pool.models)]


def intentional_scene_blueprint(part_label: str) -> dict[str, tuple[str, ...]]:
    label = (part_label or "VERSE").upper()
    if label in {"INTRO", "OUTRO"}:
        return {
            "foundation": ("stars", "snowflakes", "sphere", "line"),
            "lead": ("talking_heads", "matrix", "line", "arch"),
            "rhythm": ("line", "arch", "canes_combo"),
            "accent": ("stars", "snowflakes", "spinner", "sphere"),
            "sweep": ("line", "arch", "canes_combo", "mega"),
            "impact": ("matrix", "spinner", "stars", "snowflakes"),
        }
    if label == "CHORUS":
        return {
            "foundation": ("mega", "gt", "matrix", "line"),
            "lead": ("matrix", "spinner", "mega", "line"),
            "rhythm": ("canes_combo", "arch", "gt", "line"),
            "accent": ("spinner", "stars", "snowflakes", "sphere"),
            "sweep": ("mega", "line", "arch", "canes_combo", "gt"),
            "impact": ("matrix", "spinner", "mega", "gt"),
        }
    if label in {"PRECHORUS", "BRIDGE"}:
        return {
            "foundation": ("line", "arch", "mega", "matrix"),
            "lead": ("matrix", "line", "spinner", "arch"),
            "rhythm": ("arch", "canes_combo", "line", "gt"),
            "accent": ("spinner", "stars", "snowflakes", "talking_heads"),
            "sweep": ("line", "arch", "mega", "canes_combo"),
            "impact": ("mega", "matrix", "spinner", "line"),
        }
    return {
        "foundation": ("line", "arch", "matrix", "talking_heads"),
        "lead": ("talking_heads", "matrix", "line", "arch"),
        "rhythm": ("canes_combo", "arch", "line", "gt"),
        "accent": ("stars", "snowflakes", "spinner", "sphere"),
        "sweep": ("line", "arch", "canes_combo", "gt"),
        "impact": ("matrix", "spinner", "line", "gt"),
    }


def role_energy_band(part: SongPart) -> str:
    label = (part.label or "VERSE").upper()
    energy = max(0.0, min(1.0, float(part.energy)))
    if label in {"CHORUS", "BRIDGE"} or energy >= 0.72:
        return "high"
    if label in {"PRECHORUS"} or energy >= 0.50:
        return "mid"
    return "low"


def role_context_effect(category: str, role: str, part_label: str, band: str, index: int = 0) -> str:
    cue_by_role = {
        "background": "foundation",
        "midground": "kick",
        "foreground": "phrase",
        "accent": "accent",
    }
    cue = cue_by_role.get(role, "phrase")
    eff = reactive_effect_for_category(category, cue, part_label, index)
    cat = (category or "").strip().lower()

    if role == "background":
        if band == "low" and eff in {"Strobe", "Bars", "Fire", "Spirals"}:
            if cat == "matrix":
                return "Pictures"
            if cat in {"line", "arch", "canes_combo", "north_canes", "south_canes"}:
                return "Color Wash"
            return "On"
        if band == "high" and cat in {"matrix", "mega"} and eff in {"On", "Color Wash"}:
            return "Plasma"
    elif role == "midground":
        if band == "high" and eff in {"On", "Ramp"} and cat in {"line", "arch", "mega", "matrix"}:
            return "Wave"
    elif role == "foreground":
        if band == "high" and cat == "matrix" and eff in {"On", "Pictures", "Color Wash"}:
            return "Fire" if (index % 2) == 0 else "Plasma"
        if band == "low" and cat == "matrix" and eff == "Fire":
            return "Pictures"
    elif role == "accent":
        if band == "low" and eff == "Strobe":
            return "Twinkle"

    return eff


def reactive_effect_for_category(category: str, cue: str, part_label: str, index: int = 0) -> str:
    cat = (category or "").strip().lower()
    cue_key = (cue or "").strip().lower()
    part = (part_label or "VERSE").upper()
    dramatic = part in {"PRECHORUS", "CHORUS", "BRIDGE"}

    if cat == "matrix":
        if cue_key == "foundation":
            return "Pictures" if part == "INTRO" else "Plasma" if dramatic else "Color Wash"
        if cue_key == "phrase":
            if part == "CHORUS":
                return "Text" if (index % 3) == 0 else "Fire"
            if part in {"PRECHORUS", "BRIDGE"}:
                return "Plasma" if (index % 2) == 0 else "Ripple"
            return "Pictures" if (index % 2) == 0 else "Wave"
        if cue_key == "build":
            return "Fire" if part == "CHORUS" else "Plasma"
        if cue_key == "bass":
            if part == "CHORUS":
                return "Fire" if (index % 3) == 0 else "Bars"
            return "Bars" if dramatic else "Ripple"
        if cue_key == "kick":
            return "Bars"
        if cue_key == "snare":
            return "Ripple"
        if cue_key == "hat":
            return "Life" if dramatic else "Ripple"
        if cue_key == "vocal":
            if part == "CHORUS":
                return "Text" if (index % 2) == 0 else "Pictures"
            return "Ripple" if dramatic else "Pictures"
        if cue_key == "accent":
            return "Ripple"
        return "Bars"

    if cat in {"mega", "gt"}:
        if cue_key == "foundation":
            return "Color Wash" if not dramatic else "Spirals"
        if cue_key == "phrase":
            if part == "CHORUS":
                return "Tree"
            if part in {"PRECHORUS", "BRIDGE"}:
                return "Spirals" if (index % 2) == 0 else "Fan"
            return "Butterfly" if (index % 2) == 0 else "Color Wash"
        if cue_key == "build":
            return "Spirals" if (index % 2) == 0 else "Fan"
        if cue_key == "bass":
            if part == "CHORUS":
                return "Tree" if (index % 2) == 0 else "Pinwheel"
            return "Spirals" if dramatic else "Bars"
        if cue_key == "kick":
            return "Pinwheel" if part == "CHORUS" else "Bars"
        if cue_key == "vocal":
            return "Butterfly" if dramatic else "Color Wash"
        return "Wave"

    if cat == "spinner":
        if cue_key in {"foundation", "build"}:
            return "Spirals"
        if cue_key in {"kick", "snare", "hat", "accent", "bass"}:
            return "Pinwheel" if (index % 2) == 0 else "Spirals"
        if cue_key in {"phrase", "vocal"}:
            return "Spirals"
        return "Pinwheel"

    if cat == "sphere":
        if cue_key == "foundation":
            return "Color Wash" if not dramatic else "Plasma"
        if cue_key in {"phrase", "build"}:
            return "Spirograph" if (index % 2) == 0 else "Plasma"
        if cue_key == "bass":
            return "Plasma" if dramatic else "Circles"
        if cue_key == "vocal":
            return "Circles" if (index % 2) == 0 else "Spirograph"
        if cue_key in {"snare", "accent"}:
            return "Circles"
        return "Plasma"

    if cat in {"arch", "line"}:
        if cue_key == "foundation":
            return "Wave" if dramatic else "Lines" if cat == "line" else "Single Strand"
        if cue_key in {"phrase", "build"}:
            return "Wave"
        if cue_key == "bass":
            return "Bars" if dramatic else "Wave"
        if cue_key == "kick":
            return "Wave" if cat == "arch" else "Single Strand"
        if cue_key == "vocal":
            return "Wave" if dramatic else "Lines" if cat == "line" else "Single Strand"
        if cue_key == "hat":
            return "Lines" if cat == "line" else "Single Strand"
        if cue_key in {"snare", "accent"}:
            return "Shimmer"
        return "Wave"

    if cat in {"canes_combo", "north_canes", "south_canes"}:
        if cue_key in {"foundation", "vocal"}:
            return "Wave" if dramatic else "Single Strand"
        if cue_key in {"phrase", "build", "bass", "kick"}:
            return "Wave" if dramatic else "Bars" if cue_key == "bass" else "Single Strand"
        if cue_key in {"snare", "hat", "accent"}:
            return "Twinkle"
        return "Single Strand"

    if cat == "stars":
        if cue_key == "hat":
            return "Twinkle"
        if cue_key in {"snare", "accent"}:
            return "Strobe" if dramatic and (index % 3) == 0 else "Shimmer"
        return "Twinkle"

    if cat == "snowflakes":
        if cue_key == "hat":
            return "Twinkle"
        if cue_key in {"snare", "accent"}:
            return "Snowflakes" if dramatic else "Shimmer"
        return "Snowflakes"

    if cat == "flood":
        if cue_key in {"snare", "accent"}:
            return "Strobe" if dramatic and (index % 2) == 0 else "Shimmer"
        return "Shimmer"

    if cat == "talking_heads":
        return "On"

    return "Wave" if cue_key in {"phrase", "build", "bass", "kick", "vocal"} else "On"


def average_note_midi(notes: list[tuple[int, float]]) -> float:
    if not notes:
        return 60.0
    return float(sum(midi for midi, _strength in notes)) / float(max(1, len(notes)))


def contour_reverse_for_event(event: NoteEvent, previous_avg: float | None, fallback_index: int) -> tuple[bool, float]:
    current_avg = average_note_midi(event.notes)
    if previous_avg is None:
        return ((fallback_index % 2) == 1, current_avg)
    if current_avg < previous_avg - 0.75:
        return (True, current_avg)
    if current_avg > previous_avg + 0.75:
        return (False, current_avg)
    return ((fallback_index % 2) == 1, current_avg)


def pitch_zone(midi_values: list[int]) -> str:
    if not midi_values:
        return "mid"
    avg = float(sum(midi_values)) / max(1, len(midi_values))
    if avg < 55:
        return "low"
    if avg < 67:
        return "mid"
    return "high"


def place_zone_riff(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    zones = {
        "low": ("canes_combo", "north_canes", "south_canes", "mega"),
        "mid": ("arch", "line", "gt"),
        "high": ("stars", "snowflakes", "talking_heads"),
    }
    neighbor_zone = {"low": "mid", "mid": "high", "high": "mid"}

    for idx, event in enumerate(note_events):
        if in_blackout(event.start_ms):
            continue
        zone = pitch_zone([midi for midi, _strength in event.notes])
        zone_pools = pools_by_category(pools, zones[zone])
        pool = choose_cycle_pool(zone_pools, pool_state, f"zone_{zone}") or choose_pool(style, pools, event.part, idx, rng)
        targets = map_notes_to_models(pool, event, pool_state, style, rng)
        _placed, phrase_end = place_note_phrase(add_model, pool, event, targets, style, rng, ramp_ok, ramp_tpl)

        if event.part in {"PRECHORUS", "CHORUS", "BRIDGE"}:
            buddy_zone = neighbor_zone[zone]
            buddy_pools = pools_by_category(pools, zones[buddy_zone])
            buddy = choose_cycle_pool(buddy_pools, pool_state, f"zone_buddy_{buddy_zone}")
            if buddy and buddy.name != pool.name:
                buddy_event = NoteEvent(
                    start_ms=event.start_ms + 40,
                    end_ms=min(event.end_ms + 120, event.start_ms + base.scaled_dur(320)),
                    notes=event.notes[: max(1, len(event.notes) - 1)],
                    part=event.part,
                    section=event.section,
                )
                buddy_targets = map_notes_to_models(buddy, buddy_event, pool_state, style, rng)
                _bp, buddy_end = place_note_phrase(add_model, buddy, buddy_event, buddy_targets, style, rng, ramp_ok, ramp_tpl)
                phrase_end = max(phrase_end, buddy_end)
        piano_track.append((f"{pool.name}:{note_label(event.notes)}", event.start_ms, phrase_end))

    sweep_pools = pools_by_category(pools, ("arch", "canes_combo", "gt", "line", "stars", "snowflakes", "mega", "talking_heads"))
    if bar_ms and sweep_pools:
        for i in range(len(bar_ms) - 1):
            st = bar_ms[i]
            en = bar_ms[i + 1]
            if in_blackout(st):
                continue
            part = part_for_time(parts, st)
            if part == "INTRO" and i % 2 == 1:
                continue
            pool = sweep_pools[i % len(sweep_pools)]
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label),
                pool,
                st,
                en,
                "zone_sweep",
                style.sweep_hit_ms,
                reverse=((i + len(pool.models)) % 2 == 1),
            )
            sweep_track.append((pool.name, st, en))


def place_percussion_relay(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    low_pools = pools_by_category(pools, ("canes_combo", "north_canes", "south_canes", "mega", "gt"))
    mid_pools = pools_by_category(pools, ("arch", "line", "gt"))
    high_pools = pools_by_category(pools, ("stars", "snowflakes", "talking_heads", "line"))

    for i, t_ms in enumerate(kicks):
        if in_blackout(t_ms):
            continue
        pool = choose_cycle_pool(low_pools, pool_state, "relay_low")
        if pool is None or not pool.models:
            continue
        count = len(pool.models)
        center = pool_state.get(f"relay_center_{pool.name}", 0) % count
        direction = -1 if ((i // 4) % 2 == 1) else 1
        steps = 3 if part_for_time(parts, t_ms) in {"CHORUS", "PRECHORUS"} else 2
        for step in range(steps):
            idx = (center + (direction * step)) % count
            st = t_ms + step * 22
            en = st + max(65, base.scaled_dur(125) - step * 10)
            add_model(pool.models[idx], st, en, "relay_kick")
        pool_state[f"relay_center_{pool.name}"] = center + 1
        piano_track.append((f"{pool.name}:kick", t_ms, t_ms + 180))

    for i, t_ms in enumerate(snares):
        if in_blackout(t_ms):
            continue
        pool = choose_cycle_pool(mid_pools, pool_state, "relay_mid")
        if pool is None or not pool.models:
            continue
        end_ms = t_ms + max(120, base.scaled_dur(220))
        if len(pool.models) >= 2:
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label),
                pool,
                t_ms,
                end_ms,
                "relay_snare",
                max(70, style.sweep_hit_ms - 20),
                reverse=(i % 2 == 1),
            )
            sweep_track.append((pool.name, t_ms, end_ms))
        else:
            add_model(pool.models[0], t_ms, end_ms, "relay_snare")

    for i, t_ms in enumerate(hats):
        if in_blackout(t_ms):
            continue
        pool = high_pools[i % len(high_pools)] if high_pools else choose_cycle_pool(pools, pool_state, "relay_fallback")
        if pool is None or not pool.models:
            continue
        for j in range(2):
            model = pool.models[(i + j + pool_state.get(f"hat_{pool.name}", 0)) % len(pool.models)]
            st = t_ms + j * 16
            en = st + max(35, base.scaled_dur(80))
            add_model(model, st, en, "relay_hat")
        pool_state[f"hat_{pool.name}"] = pool_state.get(f"hat_{pool.name}", 0) + 1

    for i, event in enumerate(note_events):
        if (i % 4) != 0:
            continue
        if in_blackout(event.start_ms):
            continue
        pool = choose_pool(style, pools, event.part, i, rng)
        accent = NoteEvent(
            start_ms=event.start_ms + 14,
            end_ms=min(event.end_ms, event.start_ms + base.scaled_dur(180)),
            notes=event.notes[:2],
            part=event.part,
            section=event.section,
        )
        targets = map_notes_to_models(pool, accent, pool_state, style, rng)
        _placed, phrase_end = place_note_phrase(add_model, pool, accent, targets, style, rng, ramp_ok, ramp_tpl)
        piano_track.append((f"{pool.name}:accent", accent.start_ms, phrase_end))

    relay_pools = pools_by_category(pools, ("canes_combo", "arch", "line", "gt", "talking_heads"))
    if bar_ms and relay_pools:
        for i in range(len(bar_ms) - 1):
            st = bar_ms[i]
            en = min(bar_ms[i + 1], st + max(260, base.scaled_dur(420)))
            if in_blackout(st) or (i % 2 == 1):
                continue
            part = part_for_time(parts, st)
            if part in {"INTRO", "OUTRO"}:
                continue
            pool = relay_pools[(i // 2) % len(relay_pools)]
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label),
                pool,
                st,
                en,
                "relay_bar",
                max(80, style.sweep_hit_ms - 10),
                reverse=((i // 2) % 2 == 1),
            )
            sweep_track.append((pool.name, st, en))


def part_scene_categories(part_label: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if part_label in {"INTRO", "OUTRO"}:
        return (("stars", "snowflakes", "talking_heads"), ("line", "arch"))
    if part_label == "CHORUS":
        return (("gt", "mega", "canes_combo"), ("arch", "line", "talking_heads"))
    if part_label in {"PRECHORUS", "BRIDGE"}:
        return (("arch", "line"), ("canes_combo", "snowflakes", "stars"))
    return (("line", "arch", "talking_heads"), ("snowflakes", "stars", "gt"))


def place_scene_morph(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    previous_lead: SequentialPool | None = None
    for i, part in enumerate(parts):
        if part.end_ms - part.start_ms < 350:
            continue
        pad_cats, lead_cats = part_scene_categories(part.label)
        pad_pool = choose_cycle_pool(pools_by_category(pools, pad_cats), pool_state, f"scene_pad_{part.label.lower()}")
        lead_pool = choose_cycle_pool(pools_by_category(pools, lead_cats), pool_state, f"scene_lead_{part.label.lower()}")
        if pad_pool is None:
            pad_pool = choose_cycle_pool(pools, pool_state, "scene_pad_fallback")
        if lead_pool is None:
            lead_pool = choose_cycle_pool(pools, pool_state, "scene_lead_fallback")
        if pad_pool is None or lead_pool is None:
            continue

        part_len = max(1, part.end_ms - part.start_ms)
        pad_steps = max(2, min(6, len(pad_pool.models)))
        for step in range(pad_steps):
            idx = (step * max(1, len(pad_pool.models) // pad_steps)) % len(pad_pool.models)
            st = part.start_ms + int((part_len * step) / pad_steps)
            en = min(part.end_ms, st + max(260, int(part_len * (0.45 if part.label == "CHORUS" else 0.38))))
            use_ramp = ramp_ok and part.label in {"PRECHORUS", "BRIDGE", "CHORUS"}
            add_model(
                pad_pool.models[idx],
                st,
                en,
                "scene_pad",
                eff="Ramp" if use_ramp else "On",
                tpl=ramp_tpl if use_ramp else None,
            )

        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]
        stride = 2 if part.label in {"CHORUS", "PRECHORUS"} else 3
        for j, event in enumerate(local_events):
            if (j % stride) != 0 or in_blackout(event.start_ms):
                continue
            lead_event = NoteEvent(
                start_ms=event.start_ms,
                end_ms=min(part.end_ms, event.start_ms + base.scaled_dur(240)),
                notes=event.notes,
                part=event.part,
                section=event.section,
            )
            targets = map_notes_to_models(lead_pool, lead_event, pool_state, style, rng)
            _placed, phrase_end = place_note_phrase(add_model, lead_pool, lead_event, targets, style, rng, ramp_ok, ramp_tpl)
            piano_track.append((f"{lead_pool.name}:{note_label(lead_event.notes)}", lead_event.start_ms, phrase_end))

        if previous_lead is not None:
            st = max(0, part.start_ms - 240)
            en = min(part.end_ms, part.start_ms + 140)
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label),
                previous_lead,
                st,
                en,
                "scene_transition",
                style.sweep_hit_ms,
                reverse=(i % 2 == 1),
            )
            sweep_track.append((previous_lead.name, st, en))

        if part.label == "CHORUS":
            drop_pool = choose_cycle_pool(pools_by_category(pools, ("gt", "mega", "canes_combo", "arch")), pool_state, "scene_drop")
            if drop_pool is not None:
                st = part.start_ms
                en = min(part.end_ms, st + max(240, base.scaled_dur(420)))
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label),
                    drop_pool,
                    st,
                    en,
                    "scene_drop",
                    max(100, style.sweep_hit_ms),
                    reverse=(i % 2 == 0),
                )
                sweep_track.append((drop_pool.name, st, en))

        previous_lead = lead_pool


def place_director_ai(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    bar_ms: list[int],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    """
    Director mode:
    - reads song parts like scenes
    - keeps verse more selective
    - expands into bigger ensemble moments in choruses
    """
    scene_categories = {
        "INTRO": ("stars", "snowflakes", "talking_heads"),
        "VERSE": ("line", "arch", "canes_combo", "talking_heads"),
        "PRECHORUS": ("arch", "line", "canes_combo", "stars"),
        "CHORUS": ("gt", "mega", "canes_combo", "line", "arch"),
        "BRIDGE": ("talking_heads", "line", "arch", "stars"),
        "OUTRO": ("stars", "snowflakes", "talking_heads"),
    }
    dramatic_parts = {"PRECHORUS", "CHORUS", "BRIDGE"}

    for idx, event in enumerate(note_events):
        if in_blackout(event.start_ms):
            continue
        cats = scene_categories.get(event.part, style.primary_categories)
        scene_pools = pools_by_category(pools, cats)
        if not scene_pools:
            scene_pools = pools
        if event.part == "VERSE" and (idx % 3 == 1):
            continue
        if event.part in {"INTRO", "OUTRO"} and (idx % 2 == 1):
            continue
        pool = choose_cycle_pool(scene_pools, pool_state, f"director_{event.part.lower()}")
        if pool is None:
            pool = choose_pool(style, pools, event.part, idx, rng)
        targets = map_notes_to_models(pool, event, pool_state, style, rng)
        _placed, phrase_end = place_note_phrase(add_model, pool, event, targets, style, rng, ramp_ok, ramp_tpl)
        piano_track.append((f"{pool.name}:{note_label(event.notes)}", event.start_ms, phrase_end))

        if event.part in dramatic_parts and rng.random() < 0.44:
            accent_pool = choose_cycle_pool(pools_by_category(pools, ("gt", "mega", "canes_combo", "arch", "line")), pool_state, "director_accent")
            if accent_pool and accent_pool.models:
                lead = accent_pool.models[(idx + len(targets)) % len(accent_pool.models)]
                add_model(
                    lead,
                    event.start_ms + 24,
                    min(event.end_ms + 170, event.start_ms + base.scaled_dur(220)),
                    "director_accent",
                    eff="Ramp" if ramp_ok else "On",
                    tpl=ramp_tpl if ramp_ok else None,
                    stem="other",
                )

    hit_stream = sorted(set(kicks[::2] + snares[::2] + hats[::4]))
    rhythm_pools = pools_by_category(pools, ("canes_combo", "line", "gt", "arch"))
    for i, t_ms in enumerate(hit_stream):
        if in_blackout(t_ms):
            continue
        part = part_for_time(parts, t_ms)
        if part == "VERSE" and rng.random() > 0.40:
            continue
        pool = choose_cycle_pool(rhythm_pools, pool_state, "director_rhythm")
        if pool is None or not pool.models:
            continue
        model = pool.models[(i + pool_state.get(f"dr_{pool.name}", 0)) % len(pool.models)]
        dur = max(55, base.scaled_dur(115))
        if part in dramatic_parts:
            dur = int(dur * 1.25)
        add_model(model, t_ms, t_ms + dur, "director_rhythm", stem="drums")
        pool_state[f"dr_{pool.name}"] = pool_state.get(f"dr_{pool.name}", 0) + 1

    if bar_ms:
        sweep_sources = pools_by_category(pools, ("line", "arch", "canes_combo", "gt", "mega", "talking_heads"))
        for i in range(len(bar_ms) - 1):
            st = bar_ms[i]
            en = bar_ms[i + 1]
            if in_blackout(st):
                continue
            part = part_for_time(parts, st)
            if part in {"INTRO", "OUTRO"} and i % 2 == 1:
                continue
            if part == "VERSE" and i % 3 != 0:
                continue
            pool = choose_cycle_pool(sweep_sources, pool_state, "director_sweep")
            if pool is None or len(pool.models) < 2:
                continue
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, stem="other"),
                pool,
                st,
                en,
                "director_sweep",
                max(75, style.sweep_hit_ms),
                reverse=(i % 2 == 1),
            )
            sweep_track.append((pool.name, st, en))


def first_pool_by_category(pools: list[SequentialPool], categories: tuple[str, ...]) -> SequentialPool | None:
    for category in categories:
        for pool in pools:
            if pool.category == category and pool.models:
                return pool
    for pool in pools:
        if pool.models:
            return pool
    return None


def mapped_targets_for_pool(pool: SequentialPool, event: NoteEvent, reverse: bool = False) -> list[str]:
    count = len(pool.models)
    if count == 0:
        return []
    indices: list[int] = []
    for midi, _strength in event.notes:
        frac = base.clamp((midi - 48) / 36.0, 0.0, 1.0)
        idx = int(round(frac * (count - 1)))
        if reverse:
            idx = count - 1 - idx
        indices.append(idx)
    if not indices:
        indices = [0 if not reverse else count - 1]
    return [pool.models[idx] for idx in ordered_unique(indices)]


def place_constellation_story(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    canopy_pools = [pool for pool in pools if pool.category in {"stars", "snowflakes", "talking_heads"} and pool.models]
    motion_pools = [pool for pool in pools if pool.category in {"line", "arch"} and pool.models]
    anchor_pools = [pool for pool in pools if pool.category in {"gt", "mega", "canes_combo"} and pool.models]

    for idx, part in enumerate(parts):
        if part.end_ms - part.start_ms < 320:
            continue
        if part.label in {"INTRO", "OUTRO"}:
            pad_choices = canopy_pools or motion_pools or pools
            lead_choices = motion_pools or anchor_pools or pools
        elif part.label == "CHORUS":
            pad_choices = motion_pools or canopy_pools or pools
            lead_choices = anchor_pools or motion_pools or pools
        else:
            pad_choices = motion_pools or canopy_pools or pools
            lead_choices = motion_pools or anchor_pools or pools

        pad_pool = choose_cycle_pool(pad_choices, pool_state, f"const_pad_{part.label.lower()}") or choose_cycle_pool(pools, pool_state, "const_pad")
        lead_pool = choose_cycle_pool(lead_choices, pool_state, f"const_lead_{part.label.lower()}") or choose_cycle_pool(pools, pool_state, "const_lead")
        if pad_pool is None or lead_pool is None or not pad_pool.models or not lead_pool.models:
            continue

        part_len = max(1, part.end_ms - part.start_ms)
        pad_steps = max(2, min(5, len(pad_pool.models)))
        for step in range(pad_steps):
            model_idx = (step * max(1, len(pad_pool.models) // pad_steps)) % len(pad_pool.models)
            st = part.start_ms + int((part_len * step) / pad_steps)
            en = min(part.end_ms, st + max(260, int(part_len * (0.54 if part.label == "CHORUS" else 0.38))))
            use_ramp = ramp_ok and pad_pool.category in {"line", "arch", "mega"} and part.label in {"PRECHORUS", "BRIDGE", "CHORUS"}
            add_model(
                pad_pool.models[model_idx],
                st,
                en,
                "constellation_pad",
                eff="Ramp" if use_ramp else "On",
                tpl=ramp_tpl if use_ramp else None,
                stem="other",
            )

        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]
        stride = 4
        if part.label in {"INTRO", "OUTRO"}:
            stride = 6
        elif part.label in {"PRECHORUS", "CHORUS", "BRIDGE"}:
            stride = 2
        for event_idx, event in enumerate(local_events):
            if (event_idx % stride) != 0 or in_blackout(event.start_ms):
                continue
            event_pool = lead_pool if rng.random() < 0.72 else choose_cycle_pool(lead_choices, pool_state, f"const_event_{part.label.lower()}") or lead_pool
            targets = map_notes_to_models(event_pool, event, pool_state, style, rng)
            _placed, phrase_end = place_note_phrase(add_model, event_pool, event, targets, style, rng, ramp_ok, ramp_tpl)
            piano_track.append((f"{event_pool.name}:{note_label(event.notes)}", event.start_ms, phrase_end))

        if not bar_ms:
            continue
        part_bars = [bar for bar in bar_ms if part.start_ms <= bar < part.end_ms]
        for bar_idx in range(len(part_bars) - 1):
            st = part_bars[bar_idx]
            en = part_bars[bar_idx + 1]
            if in_blackout(st):
                continue
            if part.label == "CHORUS" and anchor_pools:
                sweep_pool = anchor_pools[(idx + bar_idx) % len(anchor_pools)]
            elif part.label in {"INTRO", "OUTRO"} and canopy_pools:
                sweep_pool = canopy_pools[(idx + bar_idx) % len(canopy_pools)]
            elif motion_pools and (bar_idx % 2 == 0):
                sweep_pool = motion_pools[(idx + bar_idx) % len(motion_pools)]
            else:
                continue
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, stem="other"),
                sweep_pool,
                st,
                en,
                "constellation_sweep",
                max(95, style.sweep_hit_ms),
                reverse=((idx + bar_idx) % 2 == 1),
            )
            sweep_track.append((sweep_pool.name, st, en))


def place_pinball_relay(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    lane_pools = [pool for pool in pools if pool.category in {"canes_combo", "arch", "line", "gt", "mega"} and pool.models]
    sparkle_pools = [pool for pool in pools if pool.category in {"stars", "snowflakes", "talking_heads"} and pool.models]
    if not lane_pools:
        lane_pools = [pool for pool in pools if pool.models]
    if not lane_pools:
        return

    relay_idx = pool_state.get("pinball_pool", 0)
    direction = 1

    for i, t_ms in enumerate(kicks):
        if in_blackout(t_ms):
            continue
        pool = lane_pools[relay_idx % len(lane_pools)]
        count = len(pool.models)
        if count == 0:
            continue
        center = pool_state.get(f"pin_center_{pool.name}", count // 2) % count
        reach = 2 if part_for_time(parts, t_ms) in {"PRECHORUS", "CHORUS", "BRIDGE"} else 1
        order = expand_indices(center, count, reach, reverse=(direction < 0), wrap=(pool.category == "canes_combo"))
        bounce = order[: min(len(order), 4)]
        end_ms = t_ms
        for step, model_idx in enumerate(bounce):
            st = t_ms + step * 20
            en = st + max(60, base.scaled_dur(110) - step * 8)
            add_model(pool.models[model_idx], st, en, "pinball_kick", stem="drums")
            end_ms = max(end_ms, en)
        piano_track.append((f"{pool.name}:pinball", t_ms, end_ms))
        pool_state[f"pin_center_{pool.name}"] = center + direction
        if (i % 3) == 2:
            relay_idx += 1
        if (i % 4) == 3:
            direction *= -1

    for i, t_ms in enumerate(snares):
        if in_blackout(t_ms):
            continue
        relay_idx += 1
        pool = lane_pools[relay_idx % len(lane_pools)]
        if len(pool.models) < 2:
            if pool.models:
                add_model(pool.models[0], t_ms, t_ms + max(95, base.scaled_dur(180)), "pinball_snare", stem="drums")
            continue
        end_ms = t_ms + max(150, base.scaled_dur(260))
        add_sweep(
            lambda nm, a, b, label: add_model(nm, a, b, label, stem="drums"),
            pool,
            t_ms,
            end_ms,
            "pinball_snare",
            max(80, style.sweep_hit_ms - 15),
            reverse=((i + relay_idx) % 2 == 1),
        )
        sweep_track.append((pool.name, t_ms, end_ms))

    for i, t_ms in enumerate(hats):
        if in_blackout(t_ms) or not sparkle_pools:
            continue
        pool = sparkle_pools[i % len(sparkle_pools)]
        if not pool.models:
            continue
        count = min(2 if part_for_time(parts, t_ms) in {"VERSE", "INTRO", "OUTRO"} else 3, len(pool.models))
        for step in range(count):
            model = pool.models[(i + step + pool_state.get(f"pin_hat_{pool.name}", 0)) % len(pool.models)]
            st = t_ms + step * 14
            en = st + max(35, base.scaled_dur(75))
            add_model(model, st, en, "pinball_hat", stem="other")
        pool_state[f"pin_hat_{pool.name}"] = pool_state.get(f"pin_hat_{pool.name}", 0) + 1

    for idx, event in enumerate(note_events):
        if (idx % 5) != 0 or in_blackout(event.start_ms):
            continue
        pool = lane_pools[(relay_idx + idx) % len(lane_pools)]
        targets = map_notes_to_models(pool, event, pool_state, style, rng)
        _placed, phrase_end = place_note_phrase(add_model, pool, event, targets, style, rng, ramp_ok, ramp_tpl)
        piano_track.append((f"{pool.name}:accent", event.start_ms, phrase_end))

    if bar_ms:
        for i in range(len(bar_ms) - 1):
            st = bar_ms[i]
            en = min(bar_ms[i + 1], st + max(220, base.scaled_dur(300)))
            if in_blackout(st) or (i % 2 == 1):
                continue
            part = part_for_time(parts, st)
            if part in {"INTRO", "OUTRO"}:
                continue
            pool = lane_pools[(relay_idx + i) % len(lane_pools)]
            if len(pool.models) < 2:
                continue
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, stem="other"),
                pool,
                st,
                en,
                "pinball_bar",
                max(78, style.sweep_hit_ms - 10),
                reverse=((i // 2) % 2 == 1),
            )
            sweep_track.append((pool.name, st, en))


def place_vocal_spotlight(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    vocal_peaks: list[int],
    bass_peaks: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    spotlight_pools = [pool for pool in pools if pool.category in {"talking_heads", "stars", "snowflakes", "line", "arch"} and pool.models]
    support_pools = [pool for pool in pools if pool.category in {"gt", "mega", "canes_combo", "line", "arch"} and pool.models]
    if not spotlight_pools:
        spotlight_pools = [pool for pool in pools if pool.models]
    if not support_pools:
        support_pools = spotlight_pools

    dramatic_parts = {"PRECHORUS", "CHORUS", "BRIDGE"}
    for i, t_ms in enumerate(vocal_peaks):
        if in_blackout(t_ms):
            continue
        part = part_for_time(parts, t_ms)
        pool = spotlight_pools[i % len(spotlight_pools)]
        base_idx = pool_state.get(f"spotlight_{pool.name}", 0) % len(pool.models)
        length = 2 if part in dramatic_parts and len(pool.models) > 1 else 1
        end_ms = t_ms
        for step in range(length):
            model = pool.models[(base_idx + step) % len(pool.models)]
            st = t_ms + step * 30
            en = st + max(120, base.scaled_dur(220) + (40 if part in dramatic_parts else 0))
            add_model(
                model,
                st,
                en,
                "spotlight_vocal",
                eff="Ramp" if ramp_ok and part in dramatic_parts and step == length - 1 else "On",
                tpl=ramp_tpl if ramp_ok and part in dramatic_parts and step == length - 1 else None,
                stem="vocals",
            )
            end_ms = max(end_ms, en)
        piano_track.append((f"{pool.name}:voice", t_ms, end_ms))
        pool_state[f"spotlight_{pool.name}"] = base_idx + 1

    for i, t_ms in enumerate(bass_peaks):
        if in_blackout(t_ms):
            continue
        part = part_for_time(parts, t_ms)
        if part not in dramatic_parts:
            continue
        pool = support_pools[i % len(support_pools)]
        if len(pool.models) >= 2:
            end_ms = t_ms + max(140, base.scaled_dur(240))
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, stem="bass"),
                pool,
                t_ms,
                end_ms,
                "spotlight_support",
                max(90, style.sweep_hit_ms),
                reverse=(i % 2 == 1),
            )
            sweep_track.append((pool.name, t_ms, end_ms))
        elif pool.models:
            add_model(pool.models[0], t_ms, t_ms + max(120, base.scaled_dur(200)), "spotlight_support", stem="bass")

    for idx, event in enumerate(note_events):
        if event.part not in dramatic_parts or (idx % 4) != 0 or in_blackout(event.start_ms):
            continue
        pool = support_pools[idx % len(support_pools)]
        targets = map_notes_to_models(pool, event, pool_state, style, rng)
        _placed, phrase_end = place_note_phrase(add_model, pool, event, targets[:2], style, rng, ramp_ok, ramp_tpl)
        piano_track.append((f"{pool.name}:lift", event.start_ms, phrase_end))

    if bar_ms:
        bridge_pools = [pool for pool in pools if pool.category in {"line", "arch", "talking_heads"} and pool.models] or spotlight_pools
        for i in range(len(bar_ms) - 1):
            st = bar_ms[i]
            en = bar_ms[i + 1]
            part = part_for_time(parts, st)
            if in_blackout(st) or part in {"INTRO", "OUTRO"} or (i % 3) != 0:
                continue
            pool = bridge_pools[i % len(bridge_pools)]
            if len(pool.models) < 2:
                continue
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, stem="other"),
                pool,
                st,
                en,
                "spotlight_bridge",
                max(85, style.sweep_hit_ms - 5),
                reverse=(i % 2 == 1),
            )
            sweep_track.append((pool.name, st, en))


def place_mirror_duel(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    left_pool = first_pool_by_category(pools, ("north_canes", "arch", "line", "gt"))
    right_pool = first_pool_by_category(pools, ("south_canes", "line", "arch", "mega"))
    center_pool = first_pool_by_category(pools, ("gt", "mega", "canes_combo", "line"))
    if left_pool is None or right_pool is None:
        return

    dramatic_parts = {"PRECHORUS", "CHORUS", "BRIDGE"}
    for idx, event in enumerate(note_events):
        if in_blackout(event.start_ms):
            continue
        part = event.part
        left_leads = ((idx + (1 if part in dramatic_parts else 0)) % 2 == 0)
        lead_pool = left_pool if left_leads else right_pool
        follow_pool = right_pool if left_leads else left_pool
        lead_targets = mapped_targets_for_pool(lead_pool, event, reverse=not left_leads)
        follow_targets = mapped_targets_for_pool(follow_pool, event, reverse=left_leads)
        phrase_end = event.start_ms
        for step, model in enumerate(lead_targets[: min(2, len(lead_targets))]):
            st = event.start_ms + step * 18
            en = st + max(70, min(event.end_ms - event.start_ms, base.scaled_dur(170)))
            add_model(model, st, en, "mirror_lead", stem="other")
            phrase_end = max(phrase_end, en)
        delay = 46 if part in {"VERSE", "INTRO", "OUTRO"} else 34
        for step, model in enumerate(follow_targets[: min(2, len(follow_targets))]):
            st = event.start_ms + delay + step * 18
            en = st + max(65, min(event.end_ms - event.start_ms + 50, base.scaled_dur(165)))
            add_model(
                model,
                st,
                en,
                "mirror_response",
                eff="Ramp" if ramp_ok and part in dramatic_parts else "On",
                tpl=ramp_tpl if ramp_ok and part in dramatic_parts else None,
                stem="other",
            )
            phrase_end = max(phrase_end, en)
        if center_pool and center_pool.models and part in dramatic_parts and rng.random() < 0.38:
            center_idx = pool_state.get("mirror_center", 0) % len(center_pool.models)
            add_model(
                center_pool.models[center_idx],
                event.start_ms + 24,
                event.start_ms + max(120, base.scaled_dur(200)),
                "mirror_center",
                stem="drums",
            )
            pool_state["mirror_center"] = center_idx + 1
        piano_track.append((f"{lead_pool.name}>{follow_pool.name}", event.start_ms, phrase_end))

    if bar_ms:
        sweep_left = left_pool if len(left_pool.models) >= 2 else center_pool
        sweep_right = right_pool if len(right_pool.models) >= 2 else center_pool
        for i in range(len(bar_ms) - 1):
            st = bar_ms[i]
            en = min(bar_ms[i + 1], st + max(220, base.scaled_dur(320)))
            part = part_for_time(parts, st)
            if in_blackout(st) or part == "INTRO":
                continue
            if sweep_left and len(sweep_left.models) >= 2 and (i % 2 == 0):
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, stem="other"),
                    sweep_left,
                    st,
                    en,
                    "mirror_sweep_left",
                    max(85, style.sweep_hit_ms),
                    reverse=False,
                )
                sweep_track.append((sweep_left.name, st, en))
            if sweep_right and len(sweep_right.models) >= 2 and part in dramatic_parts:
                st2 = st + 60
                en2 = min(bar_ms[i + 1], en + 40)
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, stem="other"),
                    sweep_right,
                    st2,
                    en2,
                    "mirror_sweep_right",
                    max(85, style.sweep_hit_ms),
                    reverse=True,
                )
                sweep_track.append((sweep_right.name, st2, en2))


def place_orbital_sweep(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    orbit_pools = [
        pool
        for category in ("canes_combo", "arch", "line", "gt", "mega", "stars", "snowflakes")
        for pool in pools
        if pool.category == category and pool.models
    ]
    if not orbit_pools:
        orbit_pools = [pool for pool in pools if pool.models]
    if not orbit_pools:
        return

    if bar_ms:
        for i in range(len(bar_ms) - 1):
            st = bar_ms[i]
            en = bar_ms[i + 1]
            if in_blackout(st):
                continue
            part = part_for_time(parts, st)
            if part in {"INTRO", "OUTRO"} and (i % 2 == 1):
                continue
            pool = orbit_pools[i % len(orbit_pools)]
            if len(pool.models) < 2:
                continue
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, stem="other"),
                pool,
                st,
                en,
                "orbit_bar",
                max(78, style.sweep_hit_ms),
                reverse=(i % 2 == 1),
            )
            sweep_track.append((pool.name, st, en))
            if part in {"PRECHORUS", "CHORUS", "BRIDGE"} and len(orbit_pools) > 1:
                echo_pool = orbit_pools[(i + 1) % len(orbit_pools)]
                if len(echo_pool.models) >= 2:
                    st2 = st + max(40, int((en - st) * 0.35))
                    en2 = min(en, st2 + max(120, int((en - st) * 0.60)))
                    add_sweep(
                        lambda nm, a, b, label: add_model(nm, a, b, label, stem="other"),
                        echo_pool,
                        st2,
                        en2,
                        "orbit_echo",
                        max(74, style.sweep_hit_ms - 8),
                        reverse=(i % 2 == 0),
                    )
                    sweep_track.append((echo_pool.name, st2, en2))

    for i, t_ms in enumerate(kicks):
        if in_blackout(t_ms):
            continue
        pool = orbit_pools[i % len(orbit_pools)]
        count = len(pool.models)
        if count == 0:
            continue
        center = pool_state.get(f"orbit_center_{pool.name}", count // 2) % count
        reach = 2 if part_for_time(parts, t_ms) in {"PRECHORUS", "CHORUS", "BRIDGE"} else 1
        spread = expand_indices(center, count, reach, reverse=(i % 2 == 1), wrap=(pool.category == "canes_combo"))
        end_ms = t_ms
        for step, idx_model in enumerate(spread[: min(len(spread), 5)]):
            st = t_ms + step * 18
            en = st + max(55, base.scaled_dur(105) + step * 8)
            add_model(
                pool.models[idx_model],
                st,
                en,
                "orbit_kick",
                eff="Ramp" if ramp_ok and step > 0 else "On",
                tpl=ramp_tpl if ramp_ok and step > 0 else None,
                stem="drums",
            )
            end_ms = max(end_ms, en)
        piano_track.append((f"{pool.name}:orbit", t_ms, end_ms))
        pool_state[f"orbit_center_{pool.name}"] = center + 1

    for idx, event in enumerate(note_events):
        if (idx % 4) != 0 or in_blackout(event.start_ms):
            continue
        pool = orbit_pools[idx % len(orbit_pools)]
        targets = map_notes_to_models(pool, event, pool_state, style, rng)
        _placed, phrase_end = place_note_phrase(add_model, pool, event, targets[:3], style, rng, ramp_ok, ramp_tpl)
        piano_track.append((f"{pool.name}:orbit_note", event.start_ms, phrase_end))


def place_pulse_matrix(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    bass_peaks: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    matrix_pools = [pool for pool in pools if pool.category in {"line", "mega", "gt", "canes_combo", "arch"} and pool.models]
    accent_pools = [pool for pool in pools if pool.category in {"stars", "snowflakes", "talking_heads"} and pool.models]
    if not matrix_pools:
        matrix_pools = [pool for pool in pools if pool.models]
    if not matrix_pools:
        return

    if bar_ms:
        for i in range(len(bar_ms) - 1):
            st = bar_ms[i]
            en = bar_ms[i + 1]
            if in_blackout(st):
                continue
            part = part_for_time(parts, st)
            steps = 4 if part in {"PRECHORUS", "CHORUS", "BRIDGE"} else 2
            cell_ms = max(50, int((en - st) / max(1, steps)))
            for step in range(steps):
                pool = matrix_pools[(i + step) % len(matrix_pools)]
                count = len(pool.models)
                if count == 0:
                    continue
                center = (pool_state.get(f"matrix_{pool.name}", 0) + step) % count
                reach = 1 if part in {"INTRO", "VERSE", "OUTRO"} else 2
                cluster = expand_indices(center, count, reach, reverse=((i + step) % 2 == 1), wrap=(pool.category == "canes_combo"))
                cell_start = st + step * cell_ms
                cell_end = min(en, cell_start + max(80, int(cell_ms * 0.82)))
                for model_idx in cluster[: min(len(cluster), 3 if part in {"INTRO", "VERSE", "OUTRO"} else 5)]:
                    add_model(
                        pool.models[model_idx],
                        cell_start,
                        cell_end,
                        "matrix_cell",
                        eff="Ramp" if ramp_ok and step == steps - 1 and part in {"PRECHORUS", "CHORUS"} else "On",
                        tpl=ramp_tpl if ramp_ok and step == steps - 1 and part in {"PRECHORUS", "CHORUS"} else None,
                        stem="other",
                    )
                pool_state[f"matrix_{pool.name}"] = center + 1
            sweep_track.append((f"matrix:{part}", st, en))

    for i, t_ms in enumerate(kicks):
        if in_blackout(t_ms):
            continue
        pool = matrix_pools[i % len(matrix_pools)]
        if not pool.models:
            continue
        idx_model = pool_state.get(f"matrix_kick_{pool.name}", 0) % len(pool.models)
        add_model(pool.models[idx_model], t_ms, t_ms + max(65, base.scaled_dur(120)), "matrix_kick", stem="drums")
        pool_state[f"matrix_kick_{pool.name}"] = idx_model + 1

    for i, t_ms in enumerate(snares):
        if in_blackout(t_ms) or not accent_pools:
            continue
        pool = accent_pools[i % len(accent_pools)]
        if not pool.models:
            continue
        model = pool.models[i % len(pool.models)]
        add_model(model, t_ms, t_ms + max(50, base.scaled_dur(95)), "matrix_snare", stem="drums")

    for i, t_ms in enumerate(bass_peaks):
        if in_blackout(t_ms):
            continue
        part = part_for_time(parts, t_ms)
        if part not in {"PRECHORUS", "CHORUS", "BRIDGE"}:
            continue
        pool = matrix_pools[(i + 1) % len(matrix_pools)]
        if len(pool.models) >= 2:
            end_ms = t_ms + max(110, base.scaled_dur(180))
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, stem="bass"),
                pool,
                t_ms,
                end_ms,
                "matrix_bass",
                max(70, style.sweep_hit_ms),
                reverse=(i % 2 == 1),
            )
            sweep_track.append((pool.name, t_ms, end_ms))

    for idx, event in enumerate(note_events):
        if (idx % 6) != 0 or in_blackout(event.start_ms):
            continue
        pool = matrix_pools[idx % len(matrix_pools)]
        targets = map_notes_to_models(pool, event, pool_state, style, rng)
        _placed, phrase_end = place_note_phrase(add_model, pool, event, targets[:2], style, rng, ramp_ok, ramp_tpl)
        piano_track.append((f"{pool.name}:matrix", event.start_ms, phrase_end))


def place_phrase_architect(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    previous_transition_pool: SequentialPool | None = None
    dramatic_parts = {"PRECHORUS", "CHORUS", "BRIDGE"}

    for part_idx, part in enumerate(parts):
        blueprint = intentional_scene_blueprint(part.label)
        foundation_pool = select_preferred_pool(pools, blueprint["foundation"], pool_state, f"phrase_foundation_{part_idx}")
        lead_pool = select_preferred_pool(pools, blueprint["lead"], pool_state, f"phrase_lead_{part_idx}")
        rhythm_pool = select_preferred_pool(pools, blueprint["rhythm"], pool_state, f"phrase_rhythm_{part_idx}")
        accent_pool = select_preferred_pool(pools, blueprint["accent"], pool_state, f"phrase_accent_{part_idx}")
        sweep_pool = select_preferred_pool(
            pools,
            blueprint["sweep"],
            pool_state,
            f"phrase_sweep_{part_idx}",
            require_multiple=True,
        )
        local_bars = [mark for mark in bar_ms if part.start_ms <= mark < part.end_ms] or [part.start_ms]

        foundation_targets = representative_models(
            foundation_pool,
            1 if part.label in {"INTRO", "OUTRO"} else 2 if part.label == "VERSE" else 3,
        )
        for bar_idx, bar_start in enumerate(local_bars):
            if in_blackout(bar_start):
                continue
            if part.label == "VERSE" and (bar_idx % 2) == 1:
                continue
            if part.label in {"INTRO", "OUTRO"} and (bar_idx % 3) == 2:
                continue
            next_bar = local_bars[bar_idx + 1] if bar_idx + 1 < len(local_bars) else part.end_ms
            use_ramp = ramp_ok and part.label in {"PRECHORUS", "BRIDGE"} and bar_idx >= max(0, len(local_bars) - 2)
            hold_end = min(part.end_ms, bar_start + max(220, int((next_bar - bar_start) * (0.90 if part.label == "CHORUS" else 0.78))))
            for step, model in enumerate(foundation_targets):
                start_ms = bar_start + step * (18 if part.label in dramatic_parts else 0)
                end_ms = min(part.end_ms, hold_end + (step * 20 if part.label == "CHORUS" else 0))
                add_model(
                    model,
                    start_ms,
                    end_ms,
                    "scene_foundation",
                    eff="Ramp" if use_ramp else "On",
                    tpl=ramp_tpl if use_ramp else None,
                    stem="bass",
                )

        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]
        stride = {"INTRO": 6, "OUTRO": 6, "VERSE": 4, "PRECHORUS": 4, "BRIDGE": 3, "CHORUS": 2}.get(part.label, 4)
        if lead_pool is not None:
            for event_idx, event in enumerate(local_events):
                if in_blackout(event.start_ms) or (event_idx % max(1, stride)) != 0:
                    continue
                targets = map_notes_to_models(lead_pool, event, pool_state, style, rng)
                limit = 1 if part.label == "VERSE" else 2 if part.label in {"PRECHORUS", "BRIDGE"} else 3
                _placed, phrase_end = place_note_phrase(
                    add_model,
                    lead_pool,
                    event,
                    targets[:limit],
                    style,
                    rng,
                    ramp_ok,
                    ramp_tpl,
                )
                piano_track.append((f"{lead_pool.name}:{part.label.lower()}", event.start_ms, phrase_end))

        local_kicks = [mark for mark in kicks if part.start_ms <= mark < part.end_ms]
        rhythm_label = f"phrase_rhythm_cursor_{part_idx}"
        for hit_idx, t_ms in enumerate(local_kicks):
            if in_blackout(t_ms):
                continue
            if part.label == "VERSE" and (hit_idx % 2) == 1:
                continue
            if part.label in {"INTRO", "OUTRO"} and (hit_idx % 3) != 0:
                continue
            pool = rhythm_pool or foundation_pool
            if pool is None or not pool.models:
                continue
            center = pool_state.get(rhythm_label, 0) % len(pool.models)
            reach = 0 if part.label in {"INTRO", "OUTRO"} else 1 if part.label == "VERSE" else 2
            cluster = expand_indices(
                center,
                len(pool.models),
                reach,
                reverse=((hit_idx + part_idx) % 2 == 1),
                wrap=(pool.category in {"canes_combo", "north_canes", "south_canes"}),
            )
            target_indices = cluster[: max(1, min(len(cluster), 2 if part.label == "VERSE" else 4))]
            for step, model_idx in enumerate(target_indices):
                st = t_ms + step * 18
                en = st + max(70, base.scaled_dur(125) + step * 12)
                add_model(
                    pool.models[model_idx],
                    st,
                    en,
                    "phrase_rhythm",
                    eff="Wave" if part.label in dramatic_parts and step == len(target_indices) - 1 else "On",
                    stem="drums",
                )
            pool_state[rhythm_label] = center + 1

        local_snares = [mark for mark in snares if part.start_ms <= mark < part.end_ms]
        if accent_pool is not None and accent_pool.models:
            for accent_idx, t_ms in enumerate(local_snares[::2]):
                if in_blackout(t_ms):
                    continue
                target = accent_pool.models[accent_idx % len(accent_pool.models)]
                add_model(target, t_ms, t_ms + max(60, base.scaled_dur(105)), "phrase_accent", eff="Shimmer", stem="vocals")

        if previous_transition_pool is not None and len(previous_transition_pool.models) >= 2 and not in_blackout(part.start_ms):
            tr_st = max(0, part.start_ms - 170)
            tr_en = min(part.end_ms, part.start_ms + 120)
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                previous_transition_pool,
                tr_st,
                tr_en,
                "phrase_transition",
                max(90, style.sweep_hit_ms),
                reverse=(part_idx % 2 == 1),
            )
            sweep_track.append((previous_transition_pool.name, tr_st, tr_en))

        if sweep_pool is not None and len(sweep_pool.models) >= 2:
            if part.label == "CHORUS":
                sw_st = part.start_ms
                sw_en = min(part.end_ms, sw_st + max(260, base.scaled_dur(420)))
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                    sweep_pool,
                    sw_st,
                    sw_en,
                    "phrase_drop_sweep",
                    max(96, style.sweep_hit_ms),
                    reverse=(part_idx % 2 == 0),
                )
                sweep_track.append((sweep_pool.name, sw_st, sw_en))
            elif part.label in {"PRECHORUS", "BRIDGE"} and len(local_bars) >= 2:
                sw_st = local_bars[max(0, len(local_bars) - 2)]
                sw_en = part.end_ms
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                    sweep_pool,
                    sw_st,
                    sw_en,
                    "phrase_lift_sweep",
                    max(88, style.sweep_hit_ms - 6),
                    reverse=(part_idx % 2 == 1),
                )
                sweep_track.append((sweep_pool.name, sw_st, sw_en))

        previous_transition_pool = sweep_pool or lead_pool


def place_stem_storyboard(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    for part_idx, part in enumerate(parts):
        blueprint = intentional_scene_blueprint(part.label)
        bass_pool = select_preferred_pool(pools, blueprint["foundation"], pool_state, f"story_bass_{part_idx}")
        vocal_pool = select_preferred_pool(pools, blueprint["lead"], pool_state, f"story_vocal_{part_idx}")
        drum_pool = select_preferred_pool(pools, blueprint["rhythm"], pool_state, f"story_drum_{part_idx}")
        accent_pool = select_preferred_pool(pools, blueprint["accent"], pool_state, f"story_accent_{part_idx}")
        sweep_pool = select_preferred_pool(pools, blueprint["sweep"], pool_state, f"story_sweep_{part_idx}", require_multiple=True)
        local_bars = [mark for mark in bar_ms if part.start_ms <= mark < part.end_ms] or [part.start_ms]

        if sweep_pool is not None and len(sweep_pool.models) >= 2:
            arrival_start = max(0, part.start_ms - 90)
            arrival_end = min(part.end_ms, part.start_ms + max(180, base.scaled_dur(260)))
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                sweep_pool,
                arrival_start,
                arrival_end,
                "story_arrival",
                max(92, style.sweep_hit_ms),
                reverse=(part_idx % 2 == 1),
            )
            sweep_track.append((f"{part.label}:{sweep_pool.name}", arrival_start, arrival_end))

        local_bass = [mark for mark in bass_peaks if part.start_ms <= mark < part.end_ms]
        bass_cursor_key = f"story_bass_cursor_{part_idx}"
        for bass_idx, t_ms in enumerate(local_bass):
            if in_blackout(t_ms) or bass_pool is None or not bass_pool.models:
                continue
            center = pool_state.get(bass_cursor_key, 0) % len(bass_pool.models)
            reach = 0 if part.label == "VERSE" else 1 if part.label in {"PRECHORUS", "BRIDGE"} else 2
            spread = expand_indices(center, len(bass_pool.models), reach, reverse=(bass_idx % 2 == 1), wrap=False)
            target_indices = spread[: max(1, min(len(spread), 2 if part.label == "VERSE" else 4))]
            for step, idx_model in enumerate(target_indices):
                st = t_ms + step * 20
                en = st + max(85, base.scaled_dur(170) + step * 16)
                add_model(
                    bass_pool.models[idx_model],
                    st,
                    en,
                    "story_bass",
                    eff="Wave" if part.label in {"PRECHORUS", "CHORUS", "BRIDGE"} else "On",
                    stem="bass",
                )
            pool_state[bass_cursor_key] = center + 1

        local_kicks = [mark for mark in kicks if part.start_ms <= mark < part.end_ms]
        local_snares = [mark for mark in snares if part.start_ms <= mark < part.end_ms]
        local_hats = [mark for mark in hats if part.start_ms <= mark < part.end_ms]
        drum_cursor_key = f"story_drum_cursor_{part_idx}"
        for hit_idx, t_ms in enumerate(local_kicks):
            if in_blackout(t_ms) or drum_pool is None or not drum_pool.models:
                continue
            idx_model = pool_state.get(drum_cursor_key, 0) % len(drum_pool.models)
            add_model(drum_pool.models[idx_model], t_ms, t_ms + max(65, base.scaled_dur(115)), "story_kick", stem="drums")
            pool_state[drum_cursor_key] = idx_model + 1
        if accent_pool is not None and accent_pool.models:
            for snare_idx, t_ms in enumerate(local_snares):
                if in_blackout(t_ms):
                    continue
                if part.label == "VERSE" and (snare_idx % 2) == 1:
                    continue
                target = accent_pool.models[snare_idx % len(accent_pool.models)]
                add_model(target, t_ms, t_ms + max(55, base.scaled_dur(95)), "story_snare", eff="Shimmer", stem="vocals")
            for hat_idx, t_ms in enumerate(local_hats[::4]):
                if in_blackout(t_ms) or part.label not in {"PRECHORUS", "CHORUS", "BRIDGE"}:
                    continue
                target = accent_pool.models[(hat_idx + 1) % len(accent_pool.models)]
                add_model(target, t_ms, t_ms + max(55, base.scaled_dur(80)), "story_hat", eff="Twinkle", stem="vocals")

        local_vocals = [mark for mark in vocal_peaks if part.start_ms <= mark < part.end_ms]
        vocal_stride = 2 if part.label == "VERSE" else 1
        if vocal_pool is not None and vocal_pool.models:
            for vocal_idx, t_ms in enumerate(local_vocals):
                if in_blackout(t_ms) or (vocal_idx % vocal_stride) != 0:
                    continue
                model = vocal_pool.models[vocal_idx % len(vocal_pool.models)]
                add_model(
                    model,
                    t_ms,
                    t_ms + max(95, base.scaled_dur(180)),
                    "story_vocal",
                    eff="Wave" if vocal_pool.category in {"matrix", "line", "mega"} and part.label in {"PRECHORUS", "CHORUS"} else "On",
                    stem="vocals",
                )

        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]
        note_stride = 6 if part.label == "VERSE" else 4 if part.label in {"PRECHORUS", "BRIDGE"} else 3
        if vocal_pool is not None:
            for event_idx, event in enumerate(local_events):
                if in_blackout(event.start_ms) or (event_idx % note_stride) != 0:
                    continue
                targets = map_notes_to_models(vocal_pool, event, pool_state, style, rng)
                limited = targets[: (1 if part.label == "VERSE" else 3)]
                _placed, phrase_end = place_note_phrase(add_model, vocal_pool, event, limited, style, rng, ramp_ok, ramp_tpl)
                piano_track.append((f"{vocal_pool.name}:{part.label.lower()}", event.start_ms, phrase_end))

        if part.label in {"PRECHORUS", "CHORUS", "BRIDGE"} and sweep_pool is not None and len(sweep_pool.models) >= 2:
            for bar_idx in range(0, len(local_bars), 4):
                sw_st = local_bars[bar_idx]
                if in_blackout(sw_st):
                    continue
                sw_en = min(part.end_ms, sw_st + max(180, base.scaled_dur(260)))
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                    sweep_pool,
                    sw_st,
                    sw_en,
                    "story_phrase_sweep",
                    max(86, style.sweep_hit_ms - 8),
                    reverse=((bar_idx // 4) % 2 == 1),
                )
                sweep_track.append((f"phrase:{sweep_pool.name}", sw_st, sw_en))


def place_primetime_director(
    style: VariantStyle,
    pools: list[SequentialPool],
    layout: base.Layout,
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    color_groups = [group for group in (layout.all_red, layout.all_green, layout.all_white) if group]

    for part_idx, part in enumerate(parts):
        blueprint = intentional_scene_blueprint(part.label)
        lead_pool = select_preferred_pool(pools, blueprint["lead"], pool_state, f"prime_lead_{part_idx}")
        impact_pool = select_preferred_pool(pools, blueprint["impact"], pool_state, f"prime_impact_{part_idx}")
        rhythm_pool = select_preferred_pool(pools, blueprint["rhythm"], pool_state, f"prime_rhythm_{part_idx}")
        sweep_pool = select_preferred_pool(pools, blueprint["sweep"], pool_state, f"prime_sweep_{part_idx}", require_multiple=True)
        accent_pool = select_preferred_pool(pools, blueprint["accent"], pool_state, f"prime_accent_{part_idx}")
        local_bars = [mark for mark in bar_ms if part.start_ms <= mark < part.end_ms] or [part.start_ms]

        if not in_blackout(part.start_ms):
            for model in (layout.house, layout.garage):
                add_model(
                    model,
                    part.start_ms,
                    min(part.end_ms, part.start_ms + max(180, base.scaled_dur(260))),
                    "prime_arrival",
                    eff="Ramp" if ramp_ok and part.label in {"PRECHORUS", "CHORUS", "BRIDGE"} else "On",
                    tpl=ramp_tpl if ramp_ok and part.label in {"PRECHORUS", "CHORUS", "BRIDGE"} else None,
                    stem="other",
                )
            if color_groups:
                color_target = color_groups[part_idx % len(color_groups)]
                add_model(color_target, part.start_ms, min(part.end_ms, part.start_ms + 180), "prime_color_hit", stem="other")

        if sweep_pool is not None and len(sweep_pool.models) >= 2 and not in_blackout(part.start_ms):
            sw_st = max(0, part.start_ms - 110)
            sw_en = min(part.end_ms, part.start_ms + max(220, base.scaled_dur(320)))
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                sweep_pool,
                sw_st,
                sw_en,
                "prime_scene_sweep",
                max(94, style.sweep_hit_ms),
                reverse=(part_idx % 2 == 1),
            )
            sweep_track.append((f"scene:{sweep_pool.name}", sw_st, sw_en))

        for motif_idx, bar_start in enumerate(local_bars):
            if in_blackout(bar_start):
                continue
            next_bar = local_bars[motif_idx + 1] if motif_idx + 1 < len(local_bars) else part.end_ms
            motif = motif_idx % 4
            if motif == 0 and lead_pool is not None:
                for step, model in enumerate(representative_models(lead_pool, 1 if part.label == "VERSE" else 2)):
                    add_model(
                        model,
                        bar_start + step * 18,
                        min(part.end_ms, bar_start + max(220, int((next_bar - bar_start) * 0.86)) + step * 16),
                        "prime_hold",
                        eff="Ramp" if ramp_ok and part.label in {"PRECHORUS", "BRIDGE"} else "On",
                        tpl=ramp_tpl if ramp_ok and part.label in {"PRECHORUS", "BRIDGE"} else None,
                        stem="bass",
                    )
            elif motif == 1 and rhythm_pool is not None and rhythm_pool.models:
                center = pool_state.get(f"prime_rhythm_cursor_{part_idx}", 0) % len(rhythm_pool.models)
                spread = expand_indices(
                    center,
                    len(rhythm_pool.models),
                    1 if part.label == "VERSE" else 2,
                    reverse=((motif_idx + part_idx) % 2 == 1),
                    wrap=(rhythm_pool.category in {"canes_combo", "north_canes", "south_canes"}),
                )
                for step, idx_model in enumerate(spread[: min(len(spread), 4)]):
                    st = bar_start + step * 22
                    en = min(part.end_ms, st + max(65, base.scaled_dur(120)))
                    add_model(rhythm_pool.models[idx_model], st, en, "prime_relay", stem="drums")
                pool_state[f"prime_rhythm_cursor_{part_idx}"] = center + 1
            elif motif == 2 and sweep_pool is not None and len(sweep_pool.models) >= 2:
                sw_en = min(part.end_ms, bar_start + max(180, base.scaled_dur(260)))
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                    sweep_pool,
                    bar_start,
                    sw_en,
                    "prime_phrase_wave",
                    max(88, style.sweep_hit_ms - 6),
                    reverse=(motif_idx % 2 == 1),
                )
                sweep_track.append((f"wave:{sweep_pool.name}", bar_start, sw_en))
            elif impact_pool is not None:
                for step, model in enumerate(representative_models(impact_pool, 2 if part.label in {"PRECHORUS", "CHORUS", "BRIDGE"} else 1)):
                    st = bar_start + step * 16
                    en = min(part.end_ms, st + max(85, base.scaled_dur(150)))
                    add_model(model, st, en, "prime_impact", eff="Wave", stem="vocals")

        local_bass = [mark for mark in bass_peaks if part.start_ms <= mark < part.end_ms]
        if impact_pool is not None and impact_pool.models:
            for bass_idx, t_ms in enumerate(local_bass[:: (2 if part.label == "VERSE" else 1)]):
                if in_blackout(t_ms):
                    continue
                model = impact_pool.models[bass_idx % len(impact_pool.models)]
                add_model(model, t_ms, t_ms + max(95, base.scaled_dur(165)), "prime_bass_impact", eff="Wave", stem="bass")

        local_vocals = [mark for mark in vocal_peaks if part.start_ms <= mark < part.end_ms]
        if accent_pool is not None and accent_pool.models:
            for vocal_idx, t_ms in enumerate(local_vocals[:: (2 if part.label == "VERSE" else 1)]):
                if in_blackout(t_ms):
                    continue
                model = accent_pool.models[vocal_idx % len(accent_pool.models)]
                add_model(model, t_ms, t_ms + max(70, base.scaled_dur(120)), "prime_vocal_accent", eff="Shimmer", stem="vocals")

        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]
        if lead_pool is not None:
            note_stride = 6 if part.label == "VERSE" else 4 if part.label in {"PRECHORUS", "BRIDGE"} else 2
            for event_idx, event in enumerate(local_events):
                if in_blackout(event.start_ms) or (event_idx % note_stride) != 0:
                    continue
                targets = map_notes_to_models(lead_pool, event, pool_state, style, rng)
                _placed, phrase_end = place_note_phrase(add_model, lead_pool, event, targets[:3], style, rng, ramp_ok, ramp_tpl)
                piano_track.append((f"{lead_pool.name}:prime", event.start_ms, phrase_end))


def place_wave_burst_director(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    beat_ms: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    previous_avg: float | None = None
    dramatic_parts = {"PRECHORUS", "CHORUS", "BRIDGE"}

    for part_idx, part in enumerate(parts):
        blueprint = intentional_scene_blueprint(part.label)
        foundation_pool = select_preferred_pool(pools, blueprint["foundation"], pool_state, f"wave_foundation_{part_idx}")
        beat_pool = select_preferred_pool(
            pools,
            ("arch", "line", "gt", "canes_combo", "mega"),
            pool_state,
            f"wave_beat_{part_idx}",
            require_multiple=True,
        )
        contour_pool = select_preferred_pool(
            pools,
            ("arch", "line", "canes_combo", "gt", "mega"),
            pool_state,
            f"wave_contour_{part_idx}",
            require_multiple=True,
        )
        accent_pool = select_preferred_pool(pools, blueprint["accent"], pool_state, f"wave_accent_{part_idx}")
        local_bars = [mark for mark in bar_ms if part.start_ms <= mark < part.end_ms] or [part.start_ms]
        local_beats = [mark for mark in beat_ms if part.start_ms <= mark < part.end_ms]
        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]

        foundation_targets = representative_models(
            foundation_pool,
            1 if part.label in {"INTRO", "OUTRO"} else 2 if part.label == "VERSE" else 3,
        )
        for bar_idx, bar_start in enumerate(local_bars):
            if in_blackout(bar_start):
                continue
            if part.label == "VERSE" and (bar_idx % 2) == 1:
                continue
            if part.label in {"INTRO", "OUTRO"} and (bar_idx % 3) != 0:
                continue
            next_bar = local_bars[bar_idx + 1] if bar_idx + 1 < len(local_bars) else part.end_ms
            hold_end = min(part.end_ms, bar_start + max(220, int((next_bar - bar_start) * 0.76)))
            use_ramp = ramp_ok and part.label in {"PRECHORUS", "BRIDGE"} and bar_idx >= max(0, len(local_bars) - 2)
            for step, model in enumerate(foundation_targets):
                st = bar_start + step * (18 if part.label in dramatic_parts else 0)
                en = min(part.end_ms, hold_end + step * 16)
                add_model(
                    model,
                    st,
                    en,
                    "wave_foundation",
                    eff="Ramp" if use_ramp else "On",
                    tpl=ramp_tpl if use_ramp else None,
                    stem="bass",
                )

        beat_stride = {"INTRO": 4, "OUTRO": 4, "VERSE": 2, "PRECHORUS": 1, "BRIDGE": 1, "CHORUS": 1}.get(part.label, 2)
        for beat_idx, t_ms in enumerate(local_beats):
            if in_blackout(t_ms) or (beat_idx % max(1, beat_stride)) != 0:
                continue
            pool = beat_pool or contour_pool
            if pool is None or len(pool.models) < 2:
                continue
            span = min(
                part.end_ms,
                t_ms + max(180, base.scaled_dur(250 if part.label == "CHORUS" else 210)),
            )
            reverse = ((beat_idx + part_idx) % 2) == 1
            if part.label == "VERSE" and local_bars:
                reverse = ((beat_idx // max(1, len(local_beats) // max(1, len(local_bars)))) % 2) == 1
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                pool,
                t_ms,
                span,
                "wave_burst",
                max(82, style.sweep_hit_ms),
                reverse=reverse,
            )
            sweep_track.append((f"beat:{pool.name}", t_ms, span))

        note_stride = {"INTRO": 10, "OUTRO": 10, "VERSE": 8, "PRECHORUS": 5, "BRIDGE": 4, "CHORUS": 3}.get(part.label, 6)
        for event_idx, event in enumerate(local_events):
            if in_blackout(event.start_ms) or (event_idx % max(1, note_stride)) != 0:
                continue
            pool = contour_pool or beat_pool
            if pool is None or len(pool.models) < 2:
                continue
            reverse, previous_avg = contour_reverse_for_event(event, previous_avg, event_idx + part_idx)
            span = min(
                part.end_ms,
                event.start_ms + max(160, base.scaled_dur(220 + 22 * min(4, len(event.notes)))),
            )
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                pool,
                event.start_ms,
                span,
                "polyphonic_wave",
                max(78, style.sweep_hit_ms - 8),
                reverse=reverse,
            )
            sweep_track.append((f"note:{pool.name}", event.start_ms, span))
            piano_track.append((f"{pool.name}:{note_label(event.notes)}", event.start_ms, span))
            if accent_pool is not None and accent_pool.models and part.label in dramatic_parts and (event_idx % (note_stride * 2)) == 0:
                accent_target = accent_pool.models[event_idx % len(accent_pool.models)]
                add_model(
                    accent_target,
                    max(event.start_ms, span - max(70, base.scaled_dur(110))),
                    span,
                    "wave_note_accent",
                    eff="Shimmer",
                    stem="vocals",
                )


def place_showcase_arc(
    style: VariantStyle,
    pools: list[SequentialPool],
    layout: base.Layout,
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    vocal_peaks: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    color_groups = [group for group in (layout.all_white, layout.all_green, layout.all_red) if group]
    previous_transition_pool: SequentialPool | None = None
    dramatic_parts = {"PRECHORUS", "CHORUS", "BRIDGE"}

    for part_idx, part in enumerate(parts):
        blueprint = intentional_scene_blueprint(part.label)
        foundation_pool = select_preferred_pool(pools, blueprint["foundation"], pool_state, f"showcase_arc_foundation_{part_idx}")
        lead_pool = select_preferred_pool(pools, blueprint["lead"], pool_state, f"showcase_arc_lead_{part_idx}")
        rhythm_pool = select_preferred_pool(pools, blueprint["rhythm"], pool_state, f"showcase_arc_rhythm_{part_idx}")
        accent_pool = select_preferred_pool(pools, blueprint["accent"], pool_state, f"showcase_arc_accent_{part_idx}")
        transition_pool = select_preferred_pool(
            pools,
            blueprint["sweep"],
            pool_state,
            f"showcase_arc_transition_{part_idx}",
            require_multiple=True,
        )
        local_bars = [mark for mark in bar_ms if part.start_ms <= mark < part.end_ms] or [part.start_ms]
        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]
        local_kicks = [mark for mark in kicks if part.start_ms <= mark < part.end_ms]
        local_snares = [mark for mark in snares if part.start_ms <= mark < part.end_ms]
        local_vocals = [mark for mark in vocal_peaks if part.start_ms <= mark < part.end_ms]

        if color_groups and not in_blackout(part.start_ms):
            if part.label == "CHORUS":
                color_target = color_groups[min(2, len(color_groups) - 1)]
            elif part.label in {"PRECHORUS", "BRIDGE"}:
                color_target = color_groups[min(1, len(color_groups) - 1)]
            else:
                color_target = color_groups[0]
            add_model(
                color_target,
                part.start_ms,
                min(part.end_ms, part.start_ms + max(120, base.scaled_dur(170))),
                "showcase_scene_color",
                stem="other",
            )

        if transition_pool is not None and len(transition_pool.models) >= 2 and not in_blackout(part.start_ms):
            arrival_start = max(0, part.start_ms - 90)
            arrival_end = min(part.end_ms, part.start_ms + max(180, base.scaled_dur(250)))
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                transition_pool,
                arrival_start,
                arrival_end,
                "showcase_scene_arrival",
                max(86, style.sweep_hit_ms),
                reverse=(part_idx % 2 == 1),
            )
            sweep_track.append((f"scene:{transition_pool.name}", arrival_start, arrival_end))

        foundation_targets = representative_models(
            foundation_pool,
            1 if part.label in {"INTRO", "OUTRO"} else 2 if part.label == "VERSE" else 3,
        )
        for bar_idx, bar_start in enumerate(local_bars):
            if in_blackout(bar_start):
                continue
            next_bar = local_bars[bar_idx + 1] if bar_idx + 1 < len(local_bars) else part.end_ms
            if part.label == "VERSE" and (bar_idx % 2) == 1:
                continue
            if part.label in {"INTRO", "OUTRO"} and (bar_idx % 3) != 0:
                continue
            motif = bar_idx % 4
            hold_end = min(part.end_ms, bar_start + max(220, int((next_bar - bar_start) * (0.88 if part.label == "CHORUS" else 0.76))))
            use_ramp = ramp_ok and part.label in {"PRECHORUS", "BRIDGE"} and bar_idx >= max(0, len(local_bars) - 2)
            for step, model in enumerate(foundation_targets):
                add_model(
                    model,
                    bar_start + step * (18 if part.label in dramatic_parts else 0),
                    min(part.end_ms, hold_end + step * 16),
                    "showcase_foundation",
                    eff="Ramp" if use_ramp else reactive_effect_for_category(foundation_pool.category if foundation_pool is not None else "", "foundation", part.label, bar_idx + step),
                    tpl=ramp_tpl if use_ramp else None,
                    stem="bass",
                )

            bar_events = [event for event in local_events if bar_start <= event.start_ms < next_bar]
            if lead_pool is not None and bar_events and motif in {1, 3 if part.label in dramatic_parts else 1}:
                lead_event = bar_events[0]
                targets = map_notes_to_models(lead_pool, lead_event, pool_state, style, rng)
                limited = targets[: (1 if part.label == "VERSE" else 2 if part.label in {"PRECHORUS", "BRIDGE"} else 3)]
                _placed, phrase_end = place_note_phrase(add_model, lead_pool, lead_event, limited, style, rng, ramp_ok, ramp_tpl)
                piano_track.append((f"{lead_pool.name}:{part.label.lower()}", lead_event.start_ms, phrase_end))

            bar_kicks = [mark for mark in local_kicks if bar_start <= mark < next_bar]
            if rhythm_pool is not None and rhythm_pool.models and bar_kicks and motif in {0, 2}:
                cursor_key = f"showcase_arc_rhythm_cursor_{part_idx}"
                center = pool_state.get(cursor_key, 0) % len(rhythm_pool.models)
                spread = expand_indices(
                    center,
                    len(rhythm_pool.models),
                    0 if part.label == "VERSE" else 1 if part.label in {"PRECHORUS", "BRIDGE"} else 2,
                    reverse=((bar_idx + part_idx) % 2 == 1),
                    wrap=(rhythm_pool.category in {"canes_combo", "north_canes", "south_canes"}),
                )
                for hit_idx, t_ms in enumerate(bar_kicks[: (2 if part.label == "VERSE" else 3)]):
                    idx_model = spread[hit_idx % len(spread)]
                    eff_name = reactive_effect_for_category(rhythm_pool.category, "kick", part.label, hit_idx + bar_idx)
                    add_model(
                        rhythm_pool.models[idx_model],
                        t_ms,
                        t_ms + max(70, base.scaled_dur(120)),
                        "showcase_rhythm",
                        eff=eff_name,
                        stem="drums",
                    )
                pool_state[cursor_key] = center + 1

            if transition_pool is not None and len(transition_pool.models) >= 2 and motif == 3 and part.label in dramatic_parts:
                sweep_start = max(bar_start, next_bar - max(170, base.scaled_dur(220)))
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                    transition_pool,
                    sweep_start,
                    next_bar,
                    "showcase_transition",
                    max(82, style.sweep_hit_ms - 8),
                    reverse=((bar_idx + part_idx) % 2 == 1),
                )
                sweep_track.append((f"transition:{transition_pool.name}", sweep_start, next_bar))

        if accent_pool is not None and accent_pool.models:
            accent_stride = 3 if part.label == "VERSE" else 2
            for accent_idx, t_ms in enumerate(local_snares):
                if in_blackout(t_ms) or (accent_idx % accent_stride) != 0:
                    continue
                target = accent_pool.models[accent_idx % len(accent_pool.models)]
                add_model(
                    target,
                    t_ms,
                    t_ms + max(60, base.scaled_dur(95)),
                    "showcase_accent",
                    eff=reactive_effect_for_category(accent_pool.category, "accent", part.label, accent_idx),
                    stem="vocals",
                )

        if lead_pool is not None and lead_pool.models:
            vocal_stride = 3 if part.label == "VERSE" else 2 if part.label in {"PRECHORUS", "BRIDGE"} else 1
            for vocal_idx, t_ms in enumerate(local_vocals):
                if in_blackout(t_ms) or (vocal_idx % vocal_stride) != 0:
                    continue
                target = lead_pool.models[vocal_idx % len(lead_pool.models)]
                eff_name = reactive_effect_for_category(lead_pool.category, "vocal", part.label, vocal_idx)
                add_model(target, t_ms, t_ms + max(90, base.scaled_dur(160)), "showcase_vocal", eff=eff_name, stem="vocals")

        if previous_transition_pool is not None and len(previous_transition_pool.models) >= 2 and not in_blackout(part.start_ms):
            pre_start = max(0, part.start_ms - 160)
            pre_end = min(part.end_ms, part.start_ms + 110)
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                previous_transition_pool,
                pre_start,
                pre_end,
                "showcase_phrase_pickup",
                max(80, style.sweep_hit_ms - 10),
                reverse=(part_idx % 2 == 1),
            )
            sweep_track.append((f"pickup:{previous_transition_pool.name}", pre_start, pre_end))

        previous_transition_pool = transition_pool or lead_pool


def place_showcase_stems(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    for part_idx, part in enumerate(parts):
        bass_pool = select_preferred_pool(pools, ("mega", "gt", "line", "canes_combo"), pool_state, f"showcase_stem_bass_{part_idx}")
        drum_pool = select_preferred_pool(pools, ("arch", "canes_combo", "line", "spinner"), pool_state, f"showcase_stem_drum_{part_idx}")
        vocal_pool = select_preferred_pool(pools, ("talking_heads", "matrix", "line", "arch"), pool_state, f"showcase_stem_vocal_{part_idx}")
        harmony_pool = select_preferred_pool(pools, ("line", "arch", "stars", "snowflakes", "matrix"), pool_state, f"showcase_stem_harmony_{part_idx}")
        accent_pool = select_preferred_pool(pools, ("stars", "snowflakes", "spinner", "sphere"), pool_state, f"showcase_stem_accent_{part_idx}")
        sweep_pool = select_preferred_pool(
            pools,
            ("line", "arch", "mega", "canes_combo", "gt", "matrix"),
            pool_state,
            f"showcase_stem_sweep_{part_idx}",
            require_multiple=True,
        )
        local_bars = [mark for mark in bar_ms if part.start_ms <= mark < part.end_ms] or [part.start_ms]
        local_bass = [mark for mark in bass_peaks if part.start_ms <= mark < part.end_ms]
        local_kicks = [mark for mark in kicks if part.start_ms <= mark < part.end_ms]
        local_snares = [mark for mark in snares if part.start_ms <= mark < part.end_ms]
        local_hats = [mark for mark in hats if part.start_ms <= mark < part.end_ms]
        local_vocals = [mark for mark in vocal_peaks if part.start_ms <= mark < part.end_ms]
        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]

        if sweep_pool is not None and len(sweep_pool.models) >= 2 and not in_blackout(part.start_ms):
            arrival_start = max(0, part.start_ms - 80)
            arrival_end = min(part.end_ms, part.start_ms + max(170, base.scaled_dur(240)))
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                sweep_pool,
                arrival_start,
                arrival_end,
                "showcase_stem_arrival",
                max(86, style.sweep_hit_ms),
                reverse=(part_idx % 2 == 1),
            )
            sweep_track.append((f"arrival:{sweep_pool.name}", arrival_start, arrival_end))

        if bass_pool is not None and bass_pool.models:
            bass_cursor = f"showcase_stem_bass_cursor_{part_idx}"
            for bass_idx, t_ms in enumerate(local_bass):
                if in_blackout(t_ms):
                    continue
                center = pool_state.get(bass_cursor, 0) % len(bass_pool.models)
                spread = expand_indices(
                    center,
                    len(bass_pool.models),
                    0 if part.label == "VERSE" else 1 if part.label in {"PRECHORUS", "BRIDGE"} else 2,
                    reverse=(bass_idx % 2 == 1),
                    wrap=(bass_pool.category in {"canes_combo", "north_canes", "south_canes"}),
                )
                for step, idx_model in enumerate(spread[: (1 if part.label == "VERSE" else 3)]):
                    st = t_ms + step * 18
                    en = st + max(80, base.scaled_dur(150) - step * 10)
                    eff_name = reactive_effect_for_category(bass_pool.category, "bass", part.label, bass_idx + step)
                    add_model(bass_pool.models[idx_model], st, en, "showcase_stem_bass", eff=eff_name, stem="bass")
                pool_state[bass_cursor] = center + 1

        if drum_pool is not None and drum_pool.models:
            drum_cursor = f"showcase_stem_drum_cursor_{part_idx}"
            for kick_idx, t_ms in enumerate(local_kicks):
                if in_blackout(t_ms):
                    continue
                idx_model = pool_state.get(drum_cursor, 0) % len(drum_pool.models)
                eff_name = reactive_effect_for_category(drum_pool.category, "kick", part.label, kick_idx)
                add_model(drum_pool.models[idx_model], t_ms, t_ms + max(65, base.scaled_dur(110)), "showcase_stem_kick", eff=eff_name, stem="drums")
                pool_state[drum_cursor] = idx_model + 1

            if accent_pool is not None and accent_pool.models:
                snare_stride = 2 if part.label in {"PRECHORUS", "CHORUS", "BRIDGE"} else 3
                for snare_idx, t_ms in enumerate(local_snares):
                    if in_blackout(t_ms) or (snare_idx % snare_stride) != 0:
                        continue
                    target = accent_pool.models[snare_idx % len(accent_pool.models)]
                    add_model(
                        target,
                        t_ms,
                        t_ms + max(55, base.scaled_dur(88)),
                        "showcase_stem_snare",
                        eff=reactive_effect_for_category(accent_pool.category, "snare", part.label, snare_idx),
                        stem="vocals",
                    )
                for hat_idx, t_ms in enumerate(local_hats[::4]):
                    if in_blackout(t_ms) or part.label not in {"PRECHORUS", "CHORUS", "BRIDGE"}:
                        continue
                    target = accent_pool.models[(hat_idx + 1) % len(accent_pool.models)]
                    add_model(
                        target,
                        t_ms,
                        t_ms + max(50, base.scaled_dur(75)),
                        "showcase_stem_hat",
                        eff=reactive_effect_for_category(accent_pool.category, "hat", part.label, hat_idx),
                        stem="vocals",
                    )

        if vocal_pool is not None and vocal_pool.models:
            vocal_stride = 3 if part.label == "VERSE" else 2 if part.label in {"PRECHORUS", "BRIDGE"} else 1
            for vocal_idx, t_ms in enumerate(local_vocals):
                if in_blackout(t_ms) or (vocal_idx % vocal_stride) != 0:
                    continue
                target = vocal_pool.models[vocal_idx % len(vocal_pool.models)]
                eff_name = reactive_effect_for_category(vocal_pool.category, "vocal", part.label, vocal_idx)
                add_model(target, t_ms, t_ms + max(90, base.scaled_dur(155)), "showcase_stem_vocal", eff=eff_name, stem="vocals")

        if harmony_pool is not None:
            note_stride = 7 if part.label == "VERSE" else 5 if part.label in {"PRECHORUS", "BRIDGE"} else 3
            for event_idx, event in enumerate(local_events):
                if in_blackout(event.start_ms) or (event_idx % note_stride) != 0:
                    continue
                targets = map_notes_to_models(harmony_pool, event, pool_state, style, rng)
                limited = targets[: (1 if part.label == "VERSE" else 2 if part.label in {"PRECHORUS", "BRIDGE"} else 3)]
                _placed, phrase_end = place_note_phrase(add_model, harmony_pool, event, limited, style, rng, ramp_ok, ramp_tpl)
                piano_track.append((f"{harmony_pool.name}:{part.label.lower()}", event.start_ms, phrase_end))

        if sweep_pool is not None and len(sweep_pool.models) >= 2:
            bar_step = 4 if part.label == "VERSE" else 2
            for bar_idx in range(0, len(local_bars), bar_step):
                sweep_start = local_bars[bar_idx]
                if in_blackout(sweep_start):
                    continue
                sweep_end = min(part.end_ms, sweep_start + max(180, base.scaled_dur(250)))
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                    sweep_pool,
                    sweep_start,
                    sweep_end,
                    "showcase_stem_phrase",
                    max(82, style.sweep_hit_ms - 6),
                    reverse=((bar_idx // max(1, bar_step) + part_idx) % 2 == 1),
                )
                sweep_track.append((f"phrase:{sweep_pool.name}", sweep_start, sweep_end))


def place_showcase_motion(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    beat_ms: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    previous_avg: float | None = None

    for part_idx, part in enumerate(parts):
        foundation_pool = select_preferred_pool(pools, ("line", "arch", "gt", "matrix"), pool_state, f"showcase_motion_foundation_{part_idx}")
        arch_pool = select_preferred_pool(pools, ("arch",), pool_state, f"showcase_motion_arch_{part_idx}", require_multiple=True)
        line_pool = select_preferred_pool(pools, ("line", "gt"), pool_state, f"showcase_motion_line_{part_idx}", require_multiple=True)
        mega_pool = select_preferred_pool(pools, ("mega", "line", "gt"), pool_state, f"showcase_motion_mega_{part_idx}", require_multiple=True)
        cane_pool = select_preferred_pool(pools, ("canes_combo", "north_canes", "south_canes"), pool_state, f"showcase_motion_canes_{part_idx}", require_multiple=True)
        accent_pool = select_preferred_pool(pools, ("spinner", "stars", "snowflakes", "matrix"), pool_state, f"showcase_motion_accent_{part_idx}")
        local_bars = [mark for mark in bar_ms if part.start_ms <= mark < part.end_ms] or [part.start_ms]
        local_beats = [mark for mark in beat_ms if part.start_ms <= mark < part.end_ms]
        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]

        foundation_targets = representative_models(
            foundation_pool,
            1 if part.label in {"INTRO", "OUTRO"} else 2 if part.label == "VERSE" else 3,
        )
        for bar_idx, bar_start in enumerate(local_bars):
            if in_blackout(bar_start):
                continue
            next_bar = local_bars[bar_idx + 1] if bar_idx + 1 < len(local_bars) else part.end_ms
            if part.label == "VERSE" and (bar_idx % 2) == 1:
                continue
            for step, model in enumerate(foundation_targets):
                add_model(
                    model,
                    bar_start + step * 16,
                    min(part.end_ms, bar_start + max(200, int((next_bar - bar_start) * 0.70)) + step * 12),
                    "showcase_motion_foundation",
                    eff="Ramp" if ramp_ok and part.label in {"PRECHORUS", "BRIDGE"} and bar_idx >= max(0, len(local_bars) - 2) else "On",
                    tpl=ramp_tpl if ramp_ok and part.label in {"PRECHORUS", "BRIDGE"} and bar_idx >= max(0, len(local_bars) - 2) else None,
                    stem="bass",
                )

        beat_stride = {"INTRO": 4, "OUTRO": 4, "VERSE": 2, "PRECHORUS": 1, "BRIDGE": 1, "CHORUS": 1}.get(part.label, 2)
        for beat_idx, t_ms in enumerate(local_beats):
            if in_blackout(t_ms) or (beat_idx % beat_stride) != 0:
                continue
            beat_pool = arch_pool or line_pool or cane_pool or mega_pool
            if beat_pool is None or len(beat_pool.models) < 2:
                continue
            span = min(part.end_ms, t_ms + max(170, base.scaled_dur(220 if part.label == "CHORUS" else 190)))
            reverse = ((beat_idx + part_idx) % 2 == 1)
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                beat_pool,
                t_ms,
                span,
                "showcase_wave_burst",
                max(76, style.sweep_hit_ms),
                reverse=reverse,
            )
            sweep_track.append((f"beat:{beat_pool.name}", t_ms, span))

            response_pool = line_pool if beat_pool is arch_pool and line_pool is not None else mega_pool
            if response_pool is not None and response_pool is not beat_pool and len(response_pool.models) >= 2 and part.label in {"PRECHORUS", "CHORUS"} and (beat_idx % 4) == 0:
                rs_start = t_ms + 28
                rs_end = min(part.end_ms, rs_start + max(160, base.scaled_dur(210)))
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                    response_pool,
                    rs_start,
                    rs_end,
                    "showcase_wave_response",
                    max(72, style.sweep_hit_ms - 8),
                    reverse=not reverse,
                )
                sweep_track.append((f"response:{response_pool.name}", rs_start, rs_end))

            if cane_pool is not None and len(cane_pool.models) >= 2 and part.label == "CHORUS" and (beat_idx % 4) == 2:
                cane_end = min(part.end_ms, t_ms + max(120, base.scaled_dur(150)))
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, eff=reactive_effect_for_category(cane_pool.category, "kick", part.label, beat_idx), stem="drums"),
                    cane_pool,
                    t_ms + 16,
                    cane_end,
                    "showcase_cane_echo",
                    max(58, style.sweep_hit_ms - 22),
                    reverse=reverse,
                )

        note_stride = {"INTRO": 10, "OUTRO": 10, "VERSE": 8, "PRECHORUS": 5, "BRIDGE": 4, "CHORUS": 3}.get(part.label, 6)
        for event_idx, event in enumerate(local_events):
            if in_blackout(event.start_ms) or (event_idx % note_stride) != 0:
                continue
            reverse, previous_avg = contour_reverse_for_event(event, previous_avg, event_idx + part_idx)
            contour_pool = arch_pool or line_pool or mega_pool
            if contour_pool is None or len(contour_pool.models) < 2:
                continue
            span = min(part.end_ms, event.start_ms + max(150, base.scaled_dur(200 + 20 * min(4, len(event.notes)))))
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                contour_pool,
                event.start_ms,
                span,
                "showcase_poly_wave",
                max(74, style.sweep_hit_ms - 8),
                reverse=reverse,
            )
            sweep_track.append((f"note:{contour_pool.name}", event.start_ms, span))
            piano_track.append((f"{contour_pool.name}:{note_label(event.notes)}", event.start_ms, span))

            if mega_pool is not None and mega_pool is not contour_pool and len(mega_pool.models) >= 2 and part.label in {"PRECHORUS", "CHORUS", "BRIDGE"} and (event_idx % (note_stride * 2)) == 0:
                mega_start = event.start_ms + 22
                mega_end = min(part.end_ms, mega_start + max(160, base.scaled_dur(220)))
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                    mega_pool,
                    mega_start,
                    mega_end,
                    "showcase_mega_reply",
                    max(80, style.sweep_hit_ms - 4),
                    reverse=not reverse,
                )
                sweep_track.append((f"mega:{mega_pool.name}", mega_start, mega_end))

            if accent_pool is not None and accent_pool.models and part.label in {"PRECHORUS", "CHORUS", "BRIDGE"} and (event_idx % (note_stride * 2)) == 0:
                target = accent_pool.models[event_idx % len(accent_pool.models)]
                add_model(target, max(event.start_ms, span - max(70, base.scaled_dur(110))), span, "showcase_wave_accent", eff="Shimmer", stem="vocals")


def place_showcase_signature(
    style: VariantStyle,
    pools: list[SequentialPool],
    layout: base.Layout,
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    beat_ms: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    place_showcase_arc(
        style=style,
        pools=pools,
        layout=layout,
        parts=parts,
        note_events=note_events,
        kicks=kicks,
        snares=snares,
        vocal_peaks=vocal_peaks,
        bar_ms=bar_ms,
        pool_state=pool_state,
        rng=rng,
        ramp_ok=ramp_ok,
        ramp_tpl=ramp_tpl,
        add_model=add_model,
        in_blackout=in_blackout,
        piano_track=piano_track,
        sweep_track=sweep_track,
    )

    for part_idx, part in enumerate(parts):
        if part.label not in {"PRECHORUS", "CHORUS", "BRIDGE"}:
            continue
        impact_pool = select_preferred_pool(pools, ("matrix", "spinner", "mega", "gt", "line"), pool_state, f"showcase_signature_impact_{part_idx}")
        sweep_pool = select_preferred_pool(pools, ("mega", "line", "arch", "gt", "canes_combo"), pool_state, f"showcase_signature_sweep_{part_idx}", require_multiple=True)
        vocal_pool = select_preferred_pool(pools, ("talking_heads", "matrix", "line", "arch"), pool_state, f"showcase_signature_vocal_{part_idx}")
        local_bass = [mark for mark in bass_peaks if part.start_ms <= mark < part.end_ms]
        local_vocals = [mark for mark in vocal_peaks if part.start_ms <= mark < part.end_ms]
        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]
        local_beats = [mark for mark in beat_ms if part.start_ms <= mark < part.end_ms]
        local_bars = [mark for mark in bar_ms if part.start_ms <= mark < part.end_ms] or [part.start_ms]

        if impact_pool is not None and impact_pool.models:
            for bass_idx, t_ms in enumerate(local_bass[::2]):
                if in_blackout(t_ms):
                    continue
                target = impact_pool.models[bass_idx % len(impact_pool.models)]
                add_model(
                    target,
                    t_ms,
                    t_ms + max(85, base.scaled_dur(140)),
                    "showcase_signature_impact",
                    eff=reactive_effect_for_category(impact_pool.category, "bass", part.label, bass_idx),
                    stem="bass",
                )

        if vocal_pool is not None and vocal_pool.models:
            for vocal_idx, t_ms in enumerate(local_vocals[::2]):
                if in_blackout(t_ms):
                    continue
                target = vocal_pool.models[vocal_idx % len(vocal_pool.models)]
                eff_name = reactive_effect_for_category(vocal_pool.category, "vocal", part.label, vocal_idx)
                add_model(target, t_ms, t_ms + max(90, base.scaled_dur(150)), "showcase_signature_vocal", eff=eff_name, stem="vocals")

        if sweep_pool is not None and len(sweep_pool.models) >= 2:
            for bar_idx, bar_start in enumerate(local_bars[::2]):
                if in_blackout(bar_start):
                    continue
                sweep_end = min(part.end_ms, bar_start + max(190, base.scaled_dur(260)))
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                    sweep_pool,
                    bar_start,
                    sweep_end,
                    "showcase_signature_sweep",
                    max(82, style.sweep_hit_ms - 6),
                    reverse=((bar_idx + part_idx) % 2 == 1),
                )
                sweep_track.append((f"signature:{sweep_pool.name}", bar_start, sweep_end))

        note_stride = 6 if part.label == "PRECHORUS" else 4 if part.label == "BRIDGE" else 3
        for event_idx, event in enumerate(local_events):
            if in_blackout(event.start_ms) or (event_idx % note_stride) != 0:
                continue
            contour_pool = sweep_pool or impact_pool or vocal_pool
            if contour_pool is None:
                continue
            targets = map_notes_to_models(contour_pool, event, pool_state, style, rng)
            limited = targets[: min(3, len(targets))]
            _placed, phrase_end = place_note_phrase(add_model, contour_pool, event, limited, style, rng, ramp_ok, ramp_tpl)
            piano_track.append((f"{contour_pool.name}:signature", event.start_ms, phrase_end))


def place_pixel_reactive_score(
    *,
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    build_lifts: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    add_model,
    in_blackout,
    pixel_track: list[tuple[str, int, int]],
) -> int:
    if not pools:
        return 0

    dramatic_parts = {"PRECHORUS", "CHORUS", "BRIDGE"}

    def rotate_targets(
        pool: SequentialPool | None,
        key: str,
        desired_count: int,
        *,
        reverse: bool = False,
    ) -> list[str]:
        if pool is None or not pool.models:
            return []
        count = len(pool.models)
        center = pool_state.get(key, 0) % count
        reach = max(0, min(count - 1, int(desired_count) - 1))
        indexes = expand_indices(
            center,
            count,
            reach,
            reverse=reverse,
            wrap=(pool.category in {"canes_combo", "north_canes", "south_canes"}),
        )
        pool_state[key] = center + 1
        limited = ordered_unique(indexes)[: max(1, desired_count)]
        return [pool.models[idx] for idx in limited if 0 <= idx < len(pool.models)]

    def cue(label: str, start_ms: int, end_ms: int) -> None:
        if end_ms > start_ms:
            pixel_track.append((label[:48], int(start_ms), int(end_ms)))

    for part_idx, part in enumerate(parts):
        prev_part = parts[part_idx - 1] if part_idx > 0 else None
        matrix_pool = select_preferred_pool(pools, ("matrix", "talking_heads"), pool_state, f"pixel_matrix_{part_idx}")
        tree_pool = select_preferred_pool(pools, ("mega", "gt"), pool_state, f"pixel_tree_{part_idx}")
        spinner_pool = select_preferred_pool(pools, ("spinner",), pool_state, f"pixel_spinner_{part_idx}")
        sphere_pool = select_preferred_pool(pools, ("sphere",), pool_state, f"pixel_sphere_{part_idx}")
        line_pool = select_preferred_pool(pools, ("line",), pool_state, f"pixel_line_{part_idx}", require_multiple=True)
        arch_pool = select_preferred_pool(pools, ("arch",), pool_state, f"pixel_arch_{part_idx}", require_multiple=True)
        cane_pool = select_preferred_pool(
            pools,
            ("canes_combo", "north_canes", "south_canes"),
            pool_state,
            f"pixel_canes_{part_idx}",
            require_multiple=True,
        )
        accent_pool = select_preferred_pool(pools, ("stars", "snowflakes", "flood"), pool_state, f"pixel_accent_{part_idx}")

        local_bars = [mark for mark in bar_ms if part.start_ms <= mark < part.end_ms] or [part.start_ms]
        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]
        local_kicks = [mark for mark in kicks if part.start_ms <= mark < part.end_ms]
        local_snares = [mark for mark in snares if part.start_ms <= mark < part.end_ms]
        local_hats = [mark for mark in hats if part.start_ms <= mark < part.end_ms]
        local_bass = [mark for mark in bass_peaks if part.start_ms <= mark < part.end_ms]
        local_vocals = [mark for mark in vocal_peaks if part.start_ms <= mark < part.end_ms]
        local_builds = [mark for mark in build_lifts if part.start_ms <= mark < part.end_ms]
        mood_changed = bool(prev_part is not None and prev_part.label != part.label)
        base_reverse = (part.label in dramatic_parts) ^ mood_changed

        def reverse_for(step_index: int) -> bool:
            return base_reverse if (step_index % 2) == 0 else not base_reverse

        if mood_changed and (line_pool is not None or arch_pool is not None):
            transition_pool = arch_pool or line_pool
            if transition_pool is not None and transition_pool.models and not in_blackout(part.start_ms):
                transition_targets = rotate_targets(
                    transition_pool,
                    f"pixel_transition_cursor_{part_idx}",
                    2 if len(transition_pool.models) >= 2 else 1,
                    reverse=base_reverse,
                )
                for step, target in enumerate(transition_targets):
                    st = part.start_ms + step * 18
                    en = min(part.end_ms, st + max(120, base.scaled_dur(210)))
                    add_model(target, st, en, "pixel_part_transition", eff="Wave", stem="other")
                    cue(f"{transition_pool.category}:Wave", st, en)

        if part.label == "CHORUS" and not in_blackout(part.start_ms):
            drop_pool = spinner_pool or matrix_pool or tree_pool or accent_pool
            if drop_pool is not None and drop_pool.models:
                drop_targets = rotate_targets(
                    drop_pool,
                    f"pixel_drop_cursor_{part_idx}",
                    1 if drop_pool.category in {"matrix", "spinner"} else 2,
                    reverse=base_reverse,
                )
                drop_eff = "Strobe" if drop_pool.category in {"spinner", "stars", "snowflakes", "flood"} else reactive_effect_for_category(drop_pool.category, "bass", part.label, part_idx)
                for step, target in enumerate(drop_targets):
                    st = part.start_ms + 12 + (step * 14)
                    en = min(part.end_ms, st + max(95, base.scaled_dur(165)))
                    add_model(target, st, en, "pixel_drop_impact", eff=drop_eff, stem="bass")
                    cue(f"{drop_pool.category}:{drop_eff}", st, en)

        scene_stride = 4 if part.label in {"INTRO", "OUTRO"} else 3 if part.label == "VERSE" else 2
        for scene_idx, bar_start in enumerate(local_bars[::scene_stride]):
            if in_blackout(bar_start):
                continue
            scene_end = min(part.end_ms, bar_start + max(220, base.scaled_dur(320 if part.label in dramatic_parts else 260)))
            if matrix_pool is not None and matrix_pool.models:
                target = rotate_targets(matrix_pool, f"pixel_scene_matrix_cursor_{part_idx}", 1, reverse=reverse_for(scene_idx))
                if target:
                    eff_name = reactive_effect_for_category(matrix_pool.category, "phrase", part.label, scene_idx)
                    add_model(target[0], bar_start, scene_end, "pixel_scene_matrix", eff=eff_name, stem="other")
                    cue(f"matrix:{eff_name}", bar_start, scene_end)
            if sphere_pool is not None and sphere_pool.models and part.label in {"INTRO", "BRIDGE", "CHORUS"}:
                sphere_start = bar_start + 22
                sphere_end = min(part.end_ms, sphere_start + max(180, base.scaled_dur(260)))
                target = rotate_targets(sphere_pool, f"pixel_scene_sphere_cursor_{part_idx}", 1, reverse=reverse_for(scene_idx + 1))
                if target:
                    eff_name = reactive_effect_for_category(sphere_pool.category, "phrase", part.label, scene_idx)
                    add_model(target[0], sphere_start, sphere_end, "pixel_scene_sphere", eff=eff_name, stem="other")
                    cue(f"sphere:{eff_name}", sphere_start, sphere_end)

        for build_idx, t_ms in enumerate(local_builds):
            if in_blackout(t_ms):
                continue
            build_pool = tree_pool or spinner_pool or matrix_pool or sphere_pool
            targets = rotate_targets(build_pool, f"pixel_build_cursor_{part_idx}", 1 if part.label == "PRECHORUS" else 2, reverse=reverse_for(build_idx))
            if not targets or build_pool is None:
                continue
            eff_name = reactive_effect_for_category(build_pool.category, "build", part.label, build_idx)
            for step, target in enumerate(targets):
                start_ms = t_ms + step * 18
                end_ms = min(part.end_ms, start_ms + max(170, base.scaled_dur(260) - step * 12))
                add_model(target, start_ms, end_ms, "pixel_build", eff=eff_name, stem="bass")
                cue(f"{build_pool.category}:{eff_name}", start_ms, end_ms)

        bass_stride = 3 if part.label in {"INTRO", "OUTRO"} else 2 if part.label == "VERSE" else 1
        for bass_idx, t_ms in enumerate(local_bass):
            if in_blackout(t_ms) or (bass_idx % bass_stride) != 0:
                continue
            bass_pool = tree_pool or matrix_pool or line_pool or arch_pool
            targets = rotate_targets(bass_pool, f"pixel_bass_cursor_{part_idx}", 1 if part.label == "VERSE" else 2, reverse=reverse_for(bass_idx))
            if not targets or bass_pool is None:
                continue
            eff_name = reactive_effect_for_category(bass_pool.category, "bass", part.label, bass_idx)
            for step, target in enumerate(targets):
                start_ms = t_ms + step * 16
                end_ms = min(part.end_ms, start_ms + max(90, base.scaled_dur(160) - step * 10))
                add_model(target, start_ms, end_ms, "pixel_bass", eff=eff_name, stem="bass")
                cue(f"{bass_pool.category}:{eff_name}", start_ms, end_ms)

        kick_stride = 2 if part.label in {"INTRO", "OUTRO", "VERSE"} else 1
        for kick_idx, t_ms in enumerate(local_kicks):
            if in_blackout(t_ms) or (kick_idx % kick_stride) != 0:
                continue
            motion_pool = arch_pool or line_pool or cane_pool or spinner_pool
            desired = 1 if part.label == "VERSE" else 2 if motion_pool is not None and motion_pool.category in {"arch", "line", "canes_combo", "north_canes", "south_canes"} else 1
            targets = rotate_targets(motion_pool, f"pixel_kick_cursor_{part_idx}", desired, reverse=reverse_for(kick_idx))
            if not targets or motion_pool is None:
                continue
            eff_name = reactive_effect_for_category(motion_pool.category, "kick", part.label, kick_idx)
            for step, target in enumerate(targets):
                start_ms = t_ms + step * 12
                end_ms = min(part.end_ms, start_ms + max(65, base.scaled_dur(110) - step * 8))
                add_model(target, start_ms, end_ms, "pixel_kick", eff=eff_name, stem="drums")
                cue(f"{motion_pool.category}:{eff_name}", start_ms, end_ms)

        snare_stride = 3 if part.label == "VERSE" else 2
        for snare_idx, t_ms in enumerate(local_snares):
            if in_blackout(t_ms) or (snare_idx % snare_stride) != 0:
                continue
            accent_source = spinner_pool or sphere_pool or accent_pool
            targets = rotate_targets(accent_source, f"pixel_snare_cursor_{part_idx}", 1, reverse=reverse_for(snare_idx))
            if not targets or accent_source is None:
                continue
            eff_name = reactive_effect_for_category(accent_source.category, "snare", part.label, snare_idx)
            start_ms = t_ms
            end_ms = min(part.end_ms, start_ms + max(60, base.scaled_dur(92)))
            add_model(targets[0], start_ms, end_ms, "pixel_snare", eff=eff_name, stem="vocals")
            cue(f"{accent_source.category}:{eff_name}", start_ms, end_ms)

        hat_stride = 8 if part.label in {"INTRO", "OUTRO"} else 6 if part.label == "VERSE" else 4
        for hat_idx, t_ms in enumerate(local_hats):
            if in_blackout(t_ms) or (hat_idx % hat_stride) != 0:
                continue
            hat_pool = spinner_pool or accent_pool or line_pool
            targets = rotate_targets(hat_pool, f"pixel_hat_cursor_{part_idx}", 1, reverse=reverse_for(hat_idx + part_idx))
            if not targets or hat_pool is None:
                continue
            eff_name = reactive_effect_for_category(hat_pool.category, "hat", part.label, hat_idx)
            start_ms = t_ms
            end_ms = min(part.end_ms, start_ms + max(50, base.scaled_dur(76)))
            add_model(targets[0], start_ms, end_ms, "pixel_hat", eff=eff_name, stem="vocals")
            cue(f"{hat_pool.category}:{eff_name}", start_ms, end_ms)

        vocal_stride = 3 if part.label == "VERSE" else 2 if part.label in {"PRECHORUS", "BRIDGE"} else 1
        for vocal_idx, t_ms in enumerate(local_vocals):
            if in_blackout(t_ms) or (vocal_idx % vocal_stride) != 0:
                continue
            vocal_pool = matrix_pool or sphere_pool or line_pool or arch_pool
            desired = 1 if part.label == "VERSE" else 2 if vocal_pool is not None and vocal_pool.category == "matrix" else 1
            targets = rotate_targets(vocal_pool, f"pixel_vocal_cursor_{part_idx}", desired, reverse=reverse_for(vocal_idx + part_idx))
            if not targets or vocal_pool is None:
                continue
            eff_name = reactive_effect_for_category(vocal_pool.category, "vocal", part.label, vocal_idx)
            for step, target in enumerate(targets):
                start_ms = t_ms + step * 18
                end_ms = min(part.end_ms, start_ms + max(95, base.scaled_dur(165) - step * 12))
                add_model(target, start_ms, end_ms, "pixel_vocal", eff=eff_name, stem="vocals")
                cue(f"{vocal_pool.category}:{eff_name}", start_ms, end_ms)

        note_stride = 10 if part.label in {"INTRO", "OUTRO"} else 8 if part.label == "VERSE" else 5 if part.label == "PRECHORUS" else 4 if part.label == "BRIDGE" else 3
        for event_idx, event in enumerate(local_events):
            if in_blackout(event.start_ms) or (event_idx % note_stride) != 0:
                continue
            melody_pool = arch_pool or line_pool or matrix_pool or tree_pool
            if melody_pool is None or not melody_pool.models:
                continue
            eff_name = reactive_effect_for_category(melody_pool.category, "phrase", part.label, event_idx)
            if melody_pool.category in {"arch", "line", "canes_combo", "north_canes", "south_canes"} and len(melody_pool.models) >= 2:
                targets = rotate_targets(melody_pool, f"pixel_phrase_cursor_{part_idx}", 2 if part.label in dramatic_parts else 1, reverse=reverse_for(event_idx + part_idx))
                for step, target in enumerate(targets):
                    start_ms = event.start_ms + step * 20
                    end_ms = min(part.end_ms, start_ms + max(110, base.scaled_dur(180) - step * 10))
                    add_model(target, start_ms, end_ms, "pixel_phrase_motion", eff=eff_name, stem="other")
                    cue(f"{melody_pool.category}:{eff_name}", start_ms, end_ms)
            else:
                mapped = map_notes_to_models(melody_pool, event, pool_state, style, rng)
                limited = mapped[: (1 if part.label == "VERSE" else 2)]
                if not limited:
                    limited = rotate_targets(melody_pool, f"pixel_phrase_fallback_{part_idx}", 1, reverse=reverse_for(event_idx + part_idx))
                for step, target in enumerate(limited):
                    start_ms = event.start_ms + step * 18
                    end_ms = min(part.end_ms, max(start_ms + 90, min(event.end_ms + 180, start_ms + base.scaled_dur(220))))
                    add_model(target, start_ms, end_ms, "pixel_phrase_focus", eff=eff_name, stem="other")
                    cue(f"{melody_pool.category}:{eff_name}", start_ms, end_ms)

    return len(pixel_track)


def place_xtreme_essentials(
    style: VariantStyle,
    pools: list[SequentialPool],
    layout: base.Layout,
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    vocal_peaks: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    place_showcase_arc(
        style=style,
        pools=pools,
        layout=layout,
        parts=parts,
        note_events=note_events,
        kicks=kicks,
        snares=snares,
        vocal_peaks=vocal_peaks,
        bar_ms=bar_ms,
        pool_state=pool_state,
        rng=rng,
        ramp_ok=ramp_ok,
        ramp_tpl=ramp_tpl,
        add_model=add_model,
        in_blackout=in_blackout,
        piano_track=piano_track,
        sweep_track=sweep_track,
    )
    flood_pool = next((pool for pool in pools if pool.category == "flood" and pool.models), None)
    whole_house_targets = [target for target in (layout.house, layout.garage, layout.perim_all, layout.blvd_all) if target]
    color_targets = [target for target in (layout.all_white, layout.all_green, layout.all_red) if target]

    for part_idx, part in enumerate(parts):
        if in_blackout(part.start_ms):
            continue
        if whole_house_targets:
            target = whole_house_targets[part_idx % len(whole_house_targets)]
            add_model(
                target,
                part.start_ms,
                min(part.end_ms, part.start_ms + max(150, base.scaled_dur(210))),
                "xtreme_wholehouse",
                eff="Ramp" if ramp_ok and part.label in {"PRECHORUS", "BRIDGE"} else "On",
                tpl=ramp_tpl if ramp_ok and part.label in {"PRECHORUS", "BRIDGE"} else None,
                stem="other",
            )
        if color_targets and part.label in {"PRECHORUS", "CHORUS", "BRIDGE"}:
            color_target = color_targets[1 if part.label != "CHORUS" else min(2, len(color_targets) - 1)]
            add_model(
                color_target,
                part.start_ms,
                min(part.end_ms, part.start_ms + max(110, base.scaled_dur(160))),
                "xtreme_color_pickup",
                stem="other",
            )
        if flood_pool is not None:
            local_snares = [mark for mark in snares if part.start_ms <= mark < part.end_ms]
            stride = 3 if part.label == "VERSE" else 2
            for idx, t_ms in enumerate(local_snares):
                if in_blackout(t_ms) or (idx % stride) != 0:
                    continue
                target = flood_pool.models[idx % len(flood_pool.models)]
                add_model(target, t_ms, t_ms + max(70, base.scaled_dur(95)), "xtreme_flood_hit", eff="Shimmer", stem="vocals")


def place_xtreme_submodel(
    style: VariantStyle,
    pools: list[SequentialPool],
    layout: base.Layout,
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    beat_ms: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    place_showcase_stems(
        style=style,
        pools=pools,
        parts=parts,
        note_events=note_events,
        kicks=kicks,
        snares=snares,
        hats=hats,
        bass_peaks=bass_peaks,
        vocal_peaks=vocal_peaks,
        bar_ms=bar_ms,
        pool_state=pool_state,
        rng=rng,
        ramp_ok=ramp_ok,
        ramp_tpl=ramp_tpl,
        add_model=add_model,
        in_blackout=in_blackout,
        piano_track=piano_track,
        sweep_track=sweep_track,
    )
    flood_pool = next((pool for pool in pools if pool.category == "flood" and pool.models), None)
    detail_targets = [target for target in (layout.notes_main, layout.notes_mirror, layout.all_notes) if target]

    for part_idx, part in enumerate(parts):
        local_beats = [mark for mark in beat_ms if part.start_ms <= mark < part.end_ms]
        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]
        if detail_targets:
            stride = 4 if part.label == "VERSE" else 2
            for beat_idx, t_ms in enumerate(local_beats):
                if in_blackout(t_ms) or (beat_idx % stride) != 0:
                    continue
                target = detail_targets[beat_idx % len(detail_targets)]
                add_model(target, t_ms, t_ms + max(85, base.scaled_dur(120)), "xtreme_notes_lane", eff="Bars", stem="other")
        if flood_pool is not None and part.label in {"PRECHORUS", "CHORUS", "BRIDGE"}:
            for event_idx, event in enumerate(local_events[::4]):
                if in_blackout(event.start_ms):
                    continue
                target = flood_pool.models[event_idx % len(flood_pool.models)]
                add_model(target, event.start_ms, min(part.end_ms, event.start_ms + max(90, base.scaled_dur(130))), "xtreme_flood_punct", eff="Strobe", stem="vocals")


def place_xtreme_showcase(
    style: VariantStyle,
    pools: list[SequentialPool],
    layout: base.Layout,
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    beat_ms: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    place_showcase_signature(
        style=style,
        pools=pools,
        layout=layout,
        parts=parts,
        note_events=note_events,
        kicks=kicks,
        snares=snares,
        hats=hats,
        bass_peaks=bass_peaks,
        vocal_peaks=vocal_peaks,
        beat_ms=beat_ms,
        bar_ms=bar_ms,
        pool_state=pool_state,
        rng=rng,
        ramp_ok=ramp_ok,
        ramp_tpl=ramp_tpl,
        add_model=add_model,
        in_blackout=in_blackout,
        piano_track=piano_track,
        sweep_track=sweep_track,
    )
    flood_pool = next((pool for pool in pools if pool.category == "flood" and pool.models), None)
    group_targets = [target for target in (layout.house, layout.garage, layout.perim_all, layout.all_notes, layout.all_red, layout.all_green, layout.all_white) if target]

    for part_idx, part in enumerate(parts):
        if part.label not in {"PRECHORUS", "CHORUS", "BRIDGE"}:
            continue
        local_beats = [mark for mark in beat_ms if part.start_ms <= mark < part.end_ms]
        local_snares = [mark for mark in snares if part.start_ms <= mark < part.end_ms]
        if group_targets:
            for idx, t_ms in enumerate(local_beats[::4]):
                if in_blackout(t_ms):
                    continue
                target = group_targets[(part_idx + idx) % len(group_targets)]
                add_model(target, t_ms, min(part.end_ms, t_ms + max(100, base.scaled_dur(150))), "xtreme_group_hit", stem="other")
        if flood_pool is not None:
            for idx, t_ms in enumerate(local_snares[::2]):
                if in_blackout(t_ms):
                    continue
                target = flood_pool.models[idx % len(flood_pool.models)]
                eff_name = "Strobe" if (idx % 3) == 0 else "Shimmer"
                add_model(target, t_ms, t_ms + max(75, base.scaled_dur(95)), "xtreme_flood_blast", eff=eff_name, stem="vocals")


def place_hierarchy_roles(
    style: VariantStyle,
    pools: list[SequentialPool],
    layout: base.Layout,
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    beat_ms: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    piano_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> None:
    # Keep a proven base pass, then add explicit foreground/midground/background role treatment.
    place_showcase_signature(
        style=style,
        pools=pools,
        layout=layout,
        parts=parts,
        note_events=note_events,
        kicks=kicks,
        snares=snares,
        hats=hats,
        bass_peaks=bass_peaks,
        vocal_peaks=vocal_peaks,
        beat_ms=beat_ms,
        bar_ms=bar_ms,
        pool_state=pool_state,
        rng=rng,
        ramp_ok=ramp_ok,
        ramp_tpl=ramp_tpl,
        add_model=add_model,
        in_blackout=in_blackout,
        piano_track=piano_track,
        sweep_track=sweep_track,
    )

    previous_band = "low"
    for part_idx, part in enumerate(parts):
        band = role_energy_band(part)
        blueprint = intentional_scene_blueprint(part.label)

        background_pool = select_preferred_pool(pools, blueprint["foundation"], pool_state, f"role_bg_{part_idx}")
        mid_pool = select_preferred_pool(pools, blueprint["rhythm"], pool_state, f"role_mid_{part_idx}")
        foreground_pool = select_preferred_pool(pools, blueprint["lead"], pool_state, f"role_fg_{part_idx}")
        accent_pool = select_preferred_pool(pools, blueprint["accent"], pool_state, f"role_accent_{part_idx}")
        sweep_pool = select_preferred_pool(
            pools,
            blueprint["sweep"],
            pool_state,
            f"role_sweep_{part_idx}",
            require_multiple=True,
        )

        local_bars = [mark for mark in bar_ms if part.start_ms <= mark < part.end_ms] or [part.start_ms]
        local_events = [event for event in note_events if part.start_ms <= event.start_ms < part.end_ms]
        local_kicks = [mark for mark in kicks if part.start_ms <= mark < part.end_ms]
        local_snares = [mark for mark in snares if part.start_ms <= mark < part.end_ms]
        local_hats = [mark for mark in hats if part.start_ms <= mark < part.end_ms]
        local_vocals = [mark for mark in vocal_peaks if part.start_ms <= mark < part.end_ms]

        if sweep_pool is not None and len(sweep_pool.models) >= 2 and not in_blackout(part.start_ms):
            intro_start = max(0, part.start_ms - max(70, base.scaled_dur(90)))
            intro_end = min(part.end_ms, part.start_ms + max(170, base.scaled_dur(240)))
            reverse = (part_idx % 2) == 1
            if previous_band != band:
                reverse = not reverse
            add_sweep(
                lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
                sweep_pool,
                intro_start,
                intro_end,
                "role_scene_arrival",
                max(84, style.sweep_hit_ms),
                reverse=reverse,
            )
            sweep_track.append((f"role_arrival:{sweep_pool.name}", intro_start, intro_end))

        if background_pool is not None and background_pool.models:
            bg_targets = representative_models(
                background_pool,
                1 if band == "low" else 2 if band == "mid" else 3,
            )
            bar_stride = 3 if band == "low" else 2 if band == "mid" else 1
            for bar_idx, bar_start in enumerate(local_bars):
                if in_blackout(bar_start) or (bar_idx % bar_stride) != 0:
                    continue
                next_bar = local_bars[bar_idx + 1] if bar_idx + 1 < len(local_bars) else part.end_ms
                for step, target in enumerate(bg_targets):
                    st = bar_start + step * 16
                    en = min(part.end_ms, max(st + 120, min(next_bar + 70, st + base.scaled_dur(360))))
                    use_ramp = ramp_ok and band != "high" and part.label in {"PRECHORUS", "BRIDGE"} and step == 0
                    add_model(
                        target,
                        st,
                        en,
                        "role_background",
                        eff="Ramp" if use_ramp else role_context_effect(background_pool.category, "background", part.label, band, bar_idx + step),
                        tpl=ramp_tpl if use_ramp else None,
                        stem="other",
                    )

        if mid_pool is not None and mid_pool.models:
            mid_stride = 3 if band == "low" else 2 if band == "mid" else 1
            for hit_idx, t_ms in enumerate(local_kicks):
                if in_blackout(t_ms) or (hit_idx % mid_stride) != 0:
                    continue
                center = pool_state.get(f"role_mid_cursor_{part_idx}", 0) % len(mid_pool.models)
                spread = expand_indices(
                    center,
                    len(mid_pool.models),
                    0 if band == "low" else 1 if band == "mid" else 2,
                    reverse=((hit_idx + part_idx) % 2 == 1),
                    wrap=(mid_pool.category in {"canes_combo", "north_canes", "south_canes"}),
                )
                for step, idx_model in enumerate(spread[: (1 if band == "low" else 2 if band == "mid" else 3)]):
                    st = t_ms + step * 14
                    en = min(part.end_ms, st + max(70, base.scaled_dur(120) - step * 8))
                    add_model(
                        mid_pool.models[idx_model],
                        st,
                        en,
                        "role_midground",
                        eff=role_context_effect(mid_pool.category, "midground", part.label, band, hit_idx + step),
                        stem="drums",
                    )
                pool_state[f"role_mid_cursor_{part_idx}"] = center + 1

        if foreground_pool is not None and foreground_pool.models:
            note_stride = 8 if band == "low" else 5 if band == "mid" else 3
            for event_idx, event in enumerate(local_events):
                if in_blackout(event.start_ms) or (event_idx % note_stride) != 0:
                    continue
                mapped = map_notes_to_models(foreground_pool, event, pool_state, style, rng)
                max_targets = 1 if band == "low" else 2 if band == "mid" else 3
                targets = mapped[:max_targets]
                if not targets:
                    targets = representative_models(foreground_pool, max_targets)
                for step, target in enumerate(targets):
                    st = event.start_ms + step * 16
                    en = min(part.end_ms, max(st + 90, min(event.end_ms + 190, st + base.scaled_dur(230))))
                    add_model(
                        target,
                        st,
                        en,
                        "role_foreground",
                        eff=role_context_effect(foreground_pool.category, "foreground", part.label, band, event_idx + step),
                        stem="vocals",
                    )
                    piano_track.append((f"role:{foreground_pool.name}", st, en))

            vocal_stride = 4 if band == "low" else 2 if band == "mid" else 1
            for vocal_idx, t_ms in enumerate(local_vocals):
                if in_blackout(t_ms) or (vocal_idx % vocal_stride) != 0:
                    continue
                target = foreground_pool.models[vocal_idx % len(foreground_pool.models)]
                add_model(
                    target,
                    t_ms,
                    min(part.end_ms, t_ms + max(95, base.scaled_dur(165))),
                    "role_vocal_focus",
                    eff=role_context_effect(foreground_pool.category, "foreground", part.label, band, vocal_idx),
                    stem="vocals",
                )

        if accent_pool is not None and accent_pool.models:
            snare_stride = 4 if band == "low" else 3 if band == "mid" else 2
            for snare_idx, t_ms in enumerate(local_snares):
                if in_blackout(t_ms) or (snare_idx % snare_stride) != 0:
                    continue
                target = accent_pool.models[snare_idx % len(accent_pool.models)]
                add_model(
                    target,
                    t_ms,
                    min(part.end_ms, t_ms + max(60, base.scaled_dur(92))),
                    "role_accent_snare",
                    eff=role_context_effect(accent_pool.category, "accent", part.label, band, snare_idx),
                    stem="vocals",
                )
            if band == "high":
                for hat_idx, t_ms in enumerate(local_hats[::4]):
                    if in_blackout(t_ms):
                        continue
                    target = accent_pool.models[(hat_idx + 1) % len(accent_pool.models)]
                    add_model(
                        target,
                        t_ms,
                        min(part.end_ms, t_ms + max(52, base.scaled_dur(76))),
                        "role_accent_hat",
                        eff=role_context_effect(accent_pool.category, "accent", part.label, band, hat_idx + 100),
                        stem="drums",
                    )

        previous_band = band


def place_intensity_waves(
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    energy_marks: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    add_model,
    in_blackout,
    sweep_track: list[tuple[str, int, int]],
) -> None:
    wave_pools = [
        pool
        for pool in pools
        if pool.category in {"line", "mega", "matrix", "arch", "gt"} and pool.models
    ]
    if not wave_pools:
        wave_pools = [pool for pool in pools if pool.models]
    if not wave_pools:
        return

    for idx, t_ms in enumerate(energy_marks):
        if in_blackout(t_ms):
            continue
        part = part_for_time(parts, t_ms)
        if part not in {"PRECHORUS", "CHORUS", "BRIDGE"}:
            continue
        if (idx % (2 if part == "CHORUS" else 3)) != 0:
            continue
        pool = wave_pools[idx % len(wave_pools)]
        targets = representative_models(pool, 1 if part == "PRECHORUS" else 2)
        span_end = t_ms
        for step, model in enumerate(targets):
            st = t_ms + step * 24
            en = st + max(150, base.scaled_dur(280) + step * 26)
            add_model(model, st, en, "intensity_wave", eff="Wave", stem="other")
            span_end = max(span_end, en)
        if span_end > t_ms:
            sweep_track.append((f"energy:{pool.name}", t_ms, span_end))

    for event_idx, event in enumerate(note_events):
        if in_blackout(event.start_ms) or (event_idx % 8) != 0:
            continue
        if event.part not in {"PRECHORUS", "CHORUS", "BRIDGE"}:
            continue
        pool = wave_pools[(event_idx + len(event.notes)) % len(wave_pools)]
        targets = map_notes_to_models(pool, event, pool_state, style, rng)[: max(1, min(2, len(event.notes)))]
        span_end = event.start_ms
        for step, model in enumerate(targets):
            st = event.start_ms + step * 14
            en = min(event.end_ms + 180, st + max(120, base.scaled_dur(210)))
            add_model(model, st, en, "polyphonic_wave", eff="Wave", stem="other")
            span_end = max(span_end, en)
        if span_end > event.start_ms:
            sweep_track.append((f"poly:{pool.name}", event.start_ms, span_end))


def build_keyboard_lane(pools: list[SequentialPool], override: list[str] | None = None) -> list[str]:
    return build_keyboard_lane_with_routes(pools, override=override, preferred_routes=None)


DEFAULT_REFERENCE_SCALE_MIDIS = [
    int(librosa.note_to_midi(note))
    for note in ("C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5")
]


def unique_models(models: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for model in models:
        key = model.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(model)
    return out


def spatial_ordered_models(
    models: list[str],
    coords: dict[str, tuple[float, float]] | None,
    rng: random.Random,
) -> list[str]:
    dedup = unique_models([model for model in models if model])
    if not dedup:
        return []
    if not coords:
        return dedup
    usable = [model for model in dedup if model in coords]
    if len(usable) < 2:
        return dedup
    ordered = ai.ordered_spatial_path(usable, coords, "left_to_right", rng)
    seen = {model.lower() for model in ordered}
    ordered.extend(model for model in dedup if model.lower() not in seen)
    return ordered


def models_for_category(pools: list[SequentialPool], category: str) -> list[str]:
    models: list[str] = []
    for pool in pools:
        if pool.category == category:
            models.extend(pool.models)
    return unique_models(models)


def models_for_pool_names(pools: list[SequentialPool], pool_names: tuple[str, ...]) -> list[str]:
    wanted = {name.lower() for name in pool_names}
    models: list[str] = []
    for pool in pools:
        if pool.name.lower() in wanted:
            models.extend(pool.models)
    return unique_models(models)


def pairwise_clusters(models: list[str], pair_size: int = 2) -> list[list[str]]:
    ordered = unique_models(models)
    if not ordered:
        return []
    clusters: list[list[str]] = []
    for idx in range(0, len(ordered), max(1, pair_size)):
        cluster = ordered[idx: idx + max(1, pair_size)]
        if cluster:
            clusters.append(cluster)
    return clusters


def route_clusters(route: KeyboardRoute) -> list[list[str]]:
    return [cluster[:] for cluster in (route.clusters or [[model] for model in route.models]) if cluster]


def build_spatial_keyboard_routes(
    layout: base.Layout,
    pools: list[SequentialPool],
    coords: dict[str, tuple[float, float]] | None,
    rng: random.Random,
) -> list[KeyboardRoute]:
    routes: list[KeyboardRoute] = []

    def add_route(
        name: str,
        models: list[str],
        *,
        stride_normal: int,
        stride_dramatic: int,
        minimum: int,
        clusters: list[list[str]] | None = None,
        spatial: bool = True,
    ) -> None:
        ordered = spatial_ordered_models(models, coords, rng) if spatial else unique_models(models)
        if len(ordered) < minimum:
            return
        usable_clusters = clusters
        if usable_clusters is None:
            usable_clusters = [[model] for model in ordered]
        routes.append(
            KeyboardRoute(
                name=name,
                models=ordered,
                stride_normal=max(1, stride_normal),
                stride_dramatic=max(1, stride_dramatic),
                clusters=usable_clusters,
            )
        )

    north_order = unique_models(layout.north_canes)
    south_order = unique_models(layout.south_canes)
    add_route(
        "north_canes",
        north_order,
        stride_normal=1,
        stride_dramatic=1,
        minimum=8,
        clusters=pairwise_clusters(north_order, pair_size=2),
        spatial=False,
    )
    add_route(
        "south_canes",
        south_order,
        stride_normal=1,
        stride_dramatic=1,
        minimum=8,
        clusters=pairwise_clusters(south_order, pair_size=2),
        spatial=False,
    )

    notes_main = models_for_pool_names(pools, ("notes_1_16",))
    notes_mirror = models_for_pool_names(pools, ("notes_17_32",))
    add_route("notes_main", notes_main, stride_normal=2, stride_dramatic=1, minimum=8, spatial=False)
    add_route("notes_mirror", notes_mirror, stride_normal=2, stride_dramatic=1, minimum=8, spatial=False)

    line_tree_rgb = models_for_pool_names(pools, ("line_tree_rgb",))
    add_route(
        "line_tree_rgb",
        line_tree_rgb,
        stride_normal=2,
        stride_dramatic=1,
        minimum=9,
        clusters=pairwise_clusters(line_tree_rgb, pair_size=3),
        spatial=False,
    )
    add_route("line_tree_red", models_for_pool_names(pools, ("line_tree_red",)), stride_normal=3, stride_dramatic=2, minimum=5, spatial=False)
    add_route("line_tree_white", models_for_pool_names(pools, ("line_tree_white",)), stride_normal=3, stride_dramatic=2, minimum=5, spatial=False)
    add_route("line_tree_green", models_for_pool_names(pools, ("line_tree_green",)), stride_normal=3, stride_dramatic=2, minimum=5, spatial=False)

    mega_tree_rgb = models_for_pool_names(pools, ("mega_tree_rgb",))
    add_route(
        "mega_tree_rgb",
        mega_tree_rgb,
        stride_normal=2,
        stride_dramatic=1,
        minimum=8,
        clusters=pairwise_clusters(mega_tree_rgb, pair_size=3),
        spatial=False,
    )
    add_route("mega_tree_red", models_for_pool_names(pools, ("mega_tree_red",)), stride_normal=3, stride_dramatic=2, minimum=5, spatial=False)
    add_route("mega_tree_white", models_for_pool_names(pools, ("mega_tree_white",)), stride_normal=3, stride_dramatic=2, minimum=5, spatial=False)
    add_route("mega_tree_green", models_for_pool_names(pools, ("mega_tree_green",)), stride_normal=3, stride_dramatic=2, minimum=5, spatial=False)

    garage_tree_rgb = models_for_pool_names(pools, ("garage_tree_rgb",))
    add_route(
        "garage_tree_rgb",
        garage_tree_rgb,
        stride_normal=2,
        stride_dramatic=1,
        minimum=4,
        clusters=pairwise_clusters(garage_tree_rgb, pair_size=3),
        spatial=False,
    )
    add_route("garage_tree_red", models_for_pool_names(pools, ("garage_tree_red",)), stride_normal=3, stride_dramatic=2, minimum=3, spatial=False)
    add_route("garage_tree_white", models_for_pool_names(pools, ("garage_tree_white",)), stride_normal=3, stride_dramatic=2, minimum=3, spatial=False)
    add_route("garage_tree_green", models_for_pool_names(pools, ("garage_tree_green",)), stride_normal=3, stride_dramatic=2, minimum=3, spatial=False)

    add_route("perimeter_red", models_for_pool_names(pools, ("perimeter_red",)), stride_normal=2, stride_dramatic=1, minimum=4, spatial=False)
    add_route("perimeter_white", models_for_pool_names(pools, ("perimeter_white",)), stride_normal=2, stride_dramatic=1, minimum=4, spatial=False)
    add_route("perimeter_green", models_for_pool_names(pools, ("perimeter_green",)), stride_normal=2, stride_dramatic=1, minimum=4, spatial=False)

    white_spine: list[str] = []
    for model in layout.white_models:
        norm = base.normalize_name(model)
        if "line tree" in norm:
            continue
        if any(token in norm for token in ("blvd", "tree", "linden")) and not any(
            token in norm for token in ("mega", "candy cane", "wreath", "flood", "beat stick", "star", "snowflake")
        ):
            white_spine.append(model)
    add_route("white_spine", white_spine, stride_normal=2, stride_dramatic=1, minimum=4)

    line_white = [model for model in layout.white_models if "line tree" in base.normalize_name(model)]
    add_route("line_white", line_white, stride_normal=3, stride_dramatic=2, minimum=5)

    add_route("stars_spatial", models_for_category(pools, "stars"), stride_normal=6, stride_dramatic=3, minimum=5)
    add_route("snowflakes_spatial", models_for_category(pools, "snowflakes"), stride_normal=6, stride_dramatic=3, minimum=5)
    return routes


def adapt_keyboard_routes_for_style(style: VariantStyle, routes: list[KeyboardRoute]) -> list[KeyboardRoute]:
    if style.family not in {"v19", "v20", "v21", "v22", "v23"}:
        return routes
    adapted: list[KeyboardRoute] = []
    for route in routes:
        current = route
        if style.family in {"v22", "v23"}:
            curated = {
                "north_canes",
                "south_canes",
                "notes_main",
                "notes_mirror",
                "white_spine",
                "line_white",
                "line_tree_rgb",
                "mega_tree_rgb",
            }
            if route.name not in curated:
                continue
            if route.name in {"north_canes", "south_canes"}:
                current = replace(route, stride_normal=3 if style.family == "v23" else 2, stride_dramatic=1)
            elif route.name in {"notes_main", "notes_mirror"}:
                current = replace(route, stride_normal=5 if style.family == "v23" else 4, stride_dramatic=2)
            elif route.name in {"white_spine", "line_white"}:
                current = replace(route, stride_normal=6 if style.family == "v23" else 5, stride_dramatic=2)
            elif route.name in {"line_tree_rgb", "mega_tree_rgb"}:
                current = replace(route, stride_normal=8 if style.family == "v23" else 6, stride_dramatic=3)
            adapted.append(current)
            continue
        if route.name in {"north_canes", "south_canes"}:
            current = replace(route, stride_normal=1, stride_dramatic=1)
        elif route.name in {
            "notes_main",
            "notes_mirror",
            "line_tree_rgb",
            "mega_tree_rgb",
            "garage_tree_rgb",
            "perimeter_red",
            "perimeter_white",
            "perimeter_green",
        }:
            current = replace(route, stride_normal=1 if style.family == "v20" else 2, stride_dramatic=1)
        elif route.name == "white_spine":
            current = replace(route, stride_normal=1 if style.family == "v20" else 2, stride_dramatic=1)
        elif route.name == "line_white":
            current = replace(route, stride_normal=2, stride_dramatic=1)
        elif route.name in {"stars_spatial", "snowflakes_spatial"} and style.family == "v19":
            current = replace(route, stride_normal=8, stride_dramatic=5)
        adapted.append(current)
    order = {
        name: idx
        for idx, name in enumerate(
            (
                "north_canes",
                "south_canes",
                "notes_main",
                "notes_mirror",
                "line_tree_rgb",
                "line_tree_red",
                "line_tree_white",
                "line_tree_green",
                "mega_tree_rgb",
                "mega_tree_red",
                "mega_tree_white",
                "mega_tree_green",
                "garage_tree_rgb",
                "garage_tree_red",
                "garage_tree_white",
                "garage_tree_green",
                "perimeter_red",
                "perimeter_white",
                "perimeter_green",
                "white_spine",
                "line_white",
                "stars_spatial",
                "snowflakes_spatial",
            )
        )
    }
    adapted.sort(key=lambda route: order.get(route.name, 99))
    return adapted


def build_keyboard_lane_with_routes(
    pools: list[SequentialPool],
    *,
    override: list[str] | None = None,
    preferred_routes: list[KeyboardRoute] | None = None,
) -> list[str]:
    category_order = (
        "canes_combo",
        "north_canes",
        "south_canes",
        "gt",
        "line",
        "arch",
        "mega",
        "stars",
        "snowflakes",
        "talking_heads",
    )
    seen: set[str] = set()
    lane: list[str] = []
    if override:
        for model in override:
            key = model.lower()
            if key in seen:
                continue
            seen.add(key)
            lane.append(model)
    if preferred_routes:
        for route in preferred_routes:
            for model in route.models:
                key = model.lower()
                if key in seen:
                    continue
                seen.add(key)
                lane.append(model)
    for category in category_order:
        for pool in pools:
            if pool.category != category:
                continue
            for model in pool.models:
                key = model.lower()
                if key in seen:
                    continue
                seen.add(key)
                lane.append(model)
    return lane


def resolve_reference_poly_xsq(template_xsq: Path | None = None) -> Path | None:
    candidates: list[Path] = []
    if template_xsq is not None:
        candidates.append(template_xsq.with_name("poly.xsq"))
        candidates.append(template_xsq.parent / "poly.xsq")
    try:
        candidates.append(Path.cwd() / "poly.xsq")
    except Exception:
        pass
    try:
        candidates.append(Path(__file__).resolve().parent / "poly.xsq")
    except Exception:
        pass
    seen: set[str] = set()
    for cand in candidates:
        key = str(cand).lower()
        if key in seen:
            continue
        seen.add(key)
        if cand.exists():
            return cand
    return None


def load_reference_scale_midis(reference_xsq: Path | None) -> list[int]:
    if reference_xsq is None or not reference_xsq.exists():
        return DEFAULT_REFERENCE_SCALE_MIDIS[:]
    try:
        root = ET.parse(reference_xsq).getroot()
    except Exception:
        return DEFAULT_REFERENCE_SCALE_MIDIS[:]
    labels: list[int] = []
    seen: set[int] = set()
    for el in root.findall(".//Element"):
        tp = (el.attrib.get("type", "") or el.attrib.get("Type", "")).lower()
        nm = (el.attrib.get("name", "") or el.attrib.get("Name", "")).strip().lower()
        if tp != "timing" or nm != "polyphonic transcription":
            continue
        for eff in el.findall(".//Effect"):
            label = (eff.attrib.get("label", "") or "").strip()
            if not label:
                continue
            try:
                midi = int(round(float(librosa.note_to_midi(label))))
            except Exception:
                continue
            if midi in seen:
                continue
            seen.add(midi)
            labels.append(midi)
    return labels if len(labels) >= 5 else DEFAULT_REFERENCE_SCALE_MIDIS[:]


def reference_scale_intervals(reference_midis: list[int]) -> list[int]:
    if not reference_midis:
        return [midi - DEFAULT_REFERENCE_SCALE_MIDIS[0] for midi in DEFAULT_REFERENCE_SCALE_MIDIS]
    ordered = sorted(set(int(midi) for midi in reference_midis))
    root = ordered[0]
    intervals = [midi - root for midi in ordered]
    if intervals[-1] != 12:
        intervals.append(12)
    return intervals


def estimate_scale_anchors(note_events: list[NoteEvent], reference_midis: list[int]) -> list[int]:
    intervals = reference_scale_intervals(reference_midis)
    pitch_weights = [0.0] * 12
    midi_values: list[int] = []
    for event in note_events:
        for midi, strength in event.notes:
            midi_i = int(round(midi))
            if midi_i <= 0:
                continue
            midi_values.append(midi_i)
            pitch_weights[midi_i % 12] += max(0.15, float(strength))
    if not midi_values:
        return reference_midis[:] if reference_midis else DEFAULT_REFERENCE_SCALE_MIDIS[:]

    scale_pcs = {interval % 12 for interval in intervals[:-1]}
    tonic_pc = max(range(12), key=lambda tonic: sum(pitch_weights[(tonic + pc) % 12] for pc in scale_pcs))
    median_pitch = float(np.median(np.asarray(midi_values, dtype=float)))

    candidates = [tonic_pc + 12 * octave for octave in range(1, 9)]
    best_root = min(
        candidates,
        key=lambda root: (
            abs((root + (intervals[-1] * 0.5)) - median_pitch),
            0 if root <= median_pitch <= root + intervals[-1] else 1,
        ),
    )
    return [best_root + interval for interval in intervals]


def scalar_degree_for_midi(midi: int, anchors: list[int]) -> int:
    if not anchors:
        return 0
    best_degree = 0
    best_distance = float("inf")
    for degree, anchor in enumerate(anchors):
        for shift in (-24, -12, 0, 12, 24):
            distance = abs((anchor + shift) - midi)
            if distance < best_distance:
                best_distance = distance
                best_degree = degree
    return best_degree


def route_index_for_degree(route: KeyboardRoute, degree_idx: int, degree_count: int) -> int:
    clusters = route_clusters(route)
    if not clusters:
        return 0
    if len(clusters) == 1 or degree_count <= 1:
        return 0
    frac = base.clamp(float(degree_idx) / float(max(1, degree_count - 1)), 0.0, 1.0)
    return int(round(frac * (len(clusters) - 1)))


def midi_to_lane_index(midi: int, lane_count: int) -> int:
    if lane_count <= 1:
        return 0
    frac = base.clamp((midi - 36) / 60.0, 0.0, 1.0)
    return int(round(frac * (lane_count - 1)))


def route_note_choice(route: KeyboardRoute, event: NoteEvent) -> tuple[int, float] | None:
    if not event.notes:
        return None
    by_pitch = sorted(event.notes, key=lambda pair: pair[0])
    by_strength = sorted(event.notes, key=lambda pair: (pair[1], pair[0]), reverse=True)
    if route.name == "white_spine":
        return by_pitch[0]
    if route.name in {"stars_spatial", "snowflakes_spatial"}:
        return by_pitch[-1]
    if route.name == "line_white" and len(by_pitch) >= 3:
        return by_pitch[len(by_pitch) // 2]
    return by_strength[0]


def route_note_choices(route: KeyboardRoute, event: NoteEvent) -> list[tuple[int, float]]:
    chosen = route_note_choice(route, event)
    if chosen is None:
        return []
    if route.name not in {"north_canes", "south_canes"}:
        return [chosen]

    ranked = sorted(event.notes, key=lambda pair: (pair[1], pair[0]), reverse=True)
    unique: list[tuple[int, float]] = []
    for midi, strength in ranked:
        midi_i = int(round(midi))
        if any(abs(existing_midi - midi_i) <= 1 for existing_midi, _ in unique):
            continue
        unique.append((midi_i, float(strength)))
        if len(unique) >= 3:
            break
    if not unique:
        return [chosen]
    unique.sort(key=lambda pair: pair[0])
    return unique


def route_support_enabled(route: KeyboardRoute) -> bool:
    return route.name in {"north_canes", "south_canes", "white_spine", "line_white"}


def route_should_fire(route: KeyboardRoute, event_idx: int, part: str) -> bool:
    dramatic = part in {"PRECHORUS", "CHORUS", "BRIDGE"}
    stride = route.stride_dramatic if dramatic else route.stride_normal
    if stride <= 1:
        return True
    offset = base.stable_name_seed(route.name) % stride
    return ((event_idx + offset) % stride) == 0


def place_spatial_keyboard_routes(
    *,
    style: VariantStyle,
    note_events: list[NoteEvent],
    routes: list[KeyboardRoute],
    reference_scale_midis: list[int],
    keyboard_mix: float,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    keyboard_track: list[tuple[str, int, int]],
) -> int:
    if not routes:
        return 0
    mix = base.clamp(keyboard_mix, 0.0, 2.0)
    if mix <= 0.05:
        return 0

    anchors = estimate_scale_anchors(note_events, reference_scale_midis)
    degree_count = max(1, len(anchors))
    placed = 0
    dramatic_parts = {"PRECHORUS", "CHORUS", "BRIDGE"}
    for event_idx, event in enumerate(note_events):
        if in_blackout(event.start_ms) or not event.notes:
            continue
        if mix <= 0.50 and (event_idx % 2) == 1:
            continue
        if mix <= 0.80 and (event_idx % 3) == 2:
            continue

        for route_idx, route in enumerate(routes):
            if not route.models or not route_should_fire(route, event_idx, event.part):
                continue
            if style.family in {"v22", "v23"} and route.name not in {"north_canes", "south_canes"}:
                if event.part in {"INTRO", "VERSE", "OUTRO"} and ((event_idx + route_idx) % 4) != 0:
                    continue
                if event.part in {"PRECHORUS", "BRIDGE"} and ((event_idx + route_idx) % 3) == 2:
                    continue
            choices = route_note_choices(route, event)
            if not choices:
                continue
            if style.family in {"v22", "v23"}:
                if route.name in {"north_canes", "south_canes"}:
                    max_choices = 1 if style.family == "v23" else 2 if event.part in dramatic_parts else 1
                else:
                    max_choices = 1
                choices = choices[:max_choices]
            clusters = route_clusters(route)
            held_until = event.start_ms
            primary_indices: list[int] = []
            note_labels: list[str] = []
            for choice_idx, (midi, strength) in enumerate(choices):
                degree_idx = scalar_degree_for_midi(int(round(midi)), anchors)
                lane_idx = route_index_for_degree(route, degree_idx, degree_count)
                primary_indices.append(lane_idx)
                primary_cluster = clusters[lane_idx] if clusters else [route.models[min(lane_idx, max(0, len(route.models) - 1))]]
                base_start = event.start_ms + (0 if route_idx < 2 else min(24, 6 * route_idx)) + (choice_idx * 12)
                base_duration = max(55, int(base.scaled_dur(170 + int(95 * strength))))
                if event.part in {"PRECHORUS", "CHORUS", "BRIDGE"}:
                    base_duration = int(base_duration * 1.10)
                if style.family in {"v22", "v23"}:
                    scale = 0.86 if style.family == "v23" and route.name in {"north_canes", "south_canes"} else 0.78 if style.family == "v23" else 0.92 if route.name in {"north_canes", "south_canes"} else 0.84
                    base_duration = max(55, int(base_duration * scale))
                end_ms = min(event.end_ms + 180, base_start + base_duration)
                for model in primary_cluster:
                    add_model(
                        model,
                        base_start,
                        end_ms,
                        f"spatial_keyboard_{route.name}",
                        eff="On",
                        stem="other",
                    )
                    placed += 1
                held_until = max(held_until, end_ms)
                note_labels.append(librosa.midi_to_note(midi))

            support_ok = route_support_enabled(route)
            if style.family == "v23":
                support_ok = route.name in {"north_canes", "south_canes", "white_spine"}
            if support_ok and len(clusters) >= 3 and primary_indices:
                support_duration = max(45, int(base.scaled_dur(115)))
                if style.family in {"v22", "v23"}:
                    support_duration = max(45, int(support_duration * (0.72 if style.family == "v23" else 0.84)))
                lead_idx = primary_indices[0]
                support_start = event.start_ms + 10
                support_end = min(event.end_ms + 150, support_start + support_duration)
                for offset in (-1, 1):
                    neighbor_idx = lead_idx + offset
                    if not (0 <= neighbor_idx < len(clusters)):
                        continue
                    for model in clusters[neighbor_idx]:
                        add_model(
                            model,
                            support_start,
                            support_end,
                            f"spatial_keyboard_{route.name}_support",
                            eff="Ramp" if ramp_ok else "On",
                            tpl=ramp_tpl if ramp_ok else None,
                            stem="other",
                        )
                        placed += 1
                    held_until = max(held_until, support_end)

            keyboard_track.append((f"{route.name}:{'+'.join(note_labels)}", event.start_ms, held_until))
    return placed


def place_polyphonic_keyboard(
    style: VariantStyle,
    note_events: list[NoteEvent],
    keyboard_lane: list[str],
    arch_lane: list[str] | None,
    keyboard_mix: float,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    keyboard_track: list[tuple[str, int, int]],
) -> None:
    if not keyboard_lane:
        return
    count = len(keyboard_lane)
    arch_models = [name for name in (arch_lane or []) if name]
    arch_count = len(arch_models)
    part_order = ["INTRO", "VERSE", "PRECHORUS", "CHORUS", "BRIDGE", "OUTRO"]
    part_rank = {name: idx for idx, name in enumerate(part_order)}
    last_part = ""
    arch_direction = 1
    mix = base.clamp(keyboard_mix, 0.00, 2.00)
    for event_idx, event in enumerate(note_events):
        if in_blackout(event.start_ms):
            continue
        if event.part != last_part:
            if last_part:
                prev_rank = part_rank.get(last_part, 1)
                curr_rank = part_rank.get(event.part, 1)
                if curr_rank != prev_rank:
                    arch_direction *= -1
            last_part = event.part
        if mix <= 0.35 and (event_idx % 2) == 1:
            continue
        if mix <= 0.60 and (event_idx % 3) == 2:
            continue
        sorted_notes = sorted(event.notes, key=lambda pair: pair[0], reverse=True)
        max_notes = max(1, min(len(sorted_notes), int(round(max(1.0, style.polyphony * max(0.55, mix))))))
        sorted_notes = sorted_notes[:max_notes]
        held_until = event.start_ms
        for step, (midi, strength) in enumerate(sorted_notes):
            lane_idx = midi_to_lane_index(midi, count)
            model = keyboard_lane[lane_idx]
            st = event.start_ms + (step * 12)
            dur = max(55, int(base.scaled_dur(190 + int(85 * strength))))
            if event.part in {"CHORUS", "PRECHORUS"}:
                dur = int(dur * 1.15)
            en = min(event.end_ms + 180, st + dur)
            use_ramp = ramp_ok and (event.part in {"PRECHORUS", "BRIDGE"} or step > 0)
            add_model(
                model,
                st,
                en,
                "polyphonic_keyboard",
                eff="Ramp" if use_ramp else "On",
                tpl=ramp_tpl if use_ramp else None,
                stem="other",
            )
            if arch_count:
                mapped_idx = lane_idx % arch_count
                if arch_direction < 0:
                    mapped_idx = (arch_count - 1) - mapped_idx
                arch_model = arch_models[mapped_idx]
                arch_eff = "Wave" if event.part in {"PRECHORUS", "CHORUS", "BRIDGE"} else "Single Strand"
                arch_st = max(0, st - 8)
                arch_en = min(event.end_ms + 220, arch_st + max(85, int(dur * 0.90)))
                add_model(
                    arch_model,
                    arch_st,
                    arch_en,
                    "polyphonic_arch_layer",
                    eff=arch_eff,
                    stem="other",
                )
            held_until = max(held_until, en)
            if mix > 1.35 and count > 2 and step == 0:
                neighbor = keyboard_lane[(lane_idx + 1) % count]
                add_model(
                    neighbor,
                    st + 18,
                    min(event.end_ms + 190, st + dur + 40),
                    "polyphonic_keyboard",
                    eff="Ramp" if ramp_ok and event.part in {"PRECHORUS", "BRIDGE"} else "On",
                    tpl=ramp_tpl if ramp_ok and event.part in {"PRECHORUS", "BRIDGE"} else None,
                    stem="other",
                )
        keyboard_track.append((note_label(event.notes), event.start_ms, held_until))


def place_piano_lights(
    style: VariantStyle,
    note_events: list[NoteEvent],
    pools: list[SequentialPool],
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    add_model,
    in_blackout,
    keyboard_track: list[tuple[str, int, int]],
) -> None:
    seq_pools = [
        pool
        for pool in pools
        if pool.category in {"arch", "line", "mega", "matrix", "gt", "spinner", "sphere", "canes_combo"}
        and len(pool.models) >= 6
    ]
    if not seq_pools or not note_events:
        return
    seq_idx = 0
    for event_idx, event in enumerate(note_events):
        if in_blackout(event.start_ms):
            continue
        pool = seq_pools[seq_idx % len(seq_pools)]
        seq_idx += 1
        sorted_notes = sorted(event.notes, key=lambda pair: pair[0], reverse=True)
        if not sorted_notes:
            continue
        max_notes = max(1, min(len(sorted_notes), int(round(max(2.0, style.polyphony * 1.2)))))
        sorted_notes = sorted_notes[:max_notes]
        held_until = event.start_ms
        for step, (midi, strength) in enumerate(sorted_notes):
            lane_idx = midi_to_lane_index(midi, len(pool.models))
            model = pool.models[lane_idx]
            st = event.start_ms + (step * 10)
            dur = max(60, int(base.scaled_dur(140 + int(110 * strength))))
            if event.part in {"CHORUS", "PRECHORUS"}:
                dur = int(dur * 1.15)
            en = min(event.end_ms + 160, st + dur)
            use_ramp = ramp_ok and (event.part in {"PRECHORUS", "BRIDGE"} or step > 0)
            add_model(
                model,
                st,
                en,
                f"piano_lights_{pool.category}",
                eff="Ramp" if use_ramp else "On",
                tpl=ramp_tpl if use_ramp else None,
                stem="other",
            )
            held_until = max(held_until, en)
        keyboard_track.append((f"{pool.category}:{note_label(event.notes)}", event.start_ms, held_until))


def note_label(notes: list[tuple[int, float]]) -> str:
    return "+".join(librosa.midi_to_note(midi) for midi, _ in notes[:3])


def sanitize_setting_value(value: str, *, max_len: int = 64) -> str:
    text = (value or "").strip()
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.replace(",", " ").replace("=", " ")
    text = re.sub(r"\s{2,}", " ", text).strip()
    if not text:
        return ""
    return text[:max_len]


def text_template_with_phrase(
    *,
    base_template: base.EffectTemplate | None,
    phrase: str,
) -> base.EffectTemplate:
    clean = sanitize_setting_value(phrase, max_len=72) or "lyrics"
    source = base_template or base.EffectTemplate(settings="", palette="")
    settings = (source.settings or "").strip()
    if settings:
        if "E_TEXTCTRL_Text=" in settings:
            settings = re.sub(r"E_TEXTCTRL_Text=[^,]*", f"E_TEXTCTRL_Text={clean}", settings, count=1)
        else:
            settings = settings + f",E_TEXTCTRL_Text={clean}"
        if "E_CHOICE_Text_Dir=" not in settings:
            settings += ",E_CHOICE_Text_Dir=left-right"
        if "E_CHOICE_Text_Effect=" not in settings:
            settings += ",E_CHOICE_Text_Effect=normal"
        if "E_TEXTCTRL_Text_Speed=" not in settings:
            settings += ",E_TEXTCTRL_Text_Speed=9"
    else:
        settings = (
            "E_CHECKBOX_Text_Color_PerWord=0,"
            "E_CHOICE_Text_Count=none,"
            "E_CHOICE_Text_Dir=left-right,"
            "E_CHOICE_Text_Effect=normal,"
            "E_TEXTCTRL_Text_Speed=9,"
            f"E_TEXTCTRL_Text={clean}"
        )
    return base.EffectTemplate(settings=settings, palette=source.palette)


def _score_band(value: float, *, good_low: float, good_high: float, hard_low: float, hard_high: float) -> float:
    if good_low <= value <= good_high:
        return 100.0
    if value < good_low:
        if value <= hard_low:
            return 0.0
        span = max(0.0001, good_low - hard_low)
        return max(0.0, 100.0 * (value - hard_low) / span)
    if value >= hard_high:
        return 0.0
    span = max(0.0001, hard_high - good_high)
    return max(0.0, 100.0 * (hard_high - value) / span)


def _score_minimum(value: float, *, floor: float, target: float) -> float:
    if value >= target:
        return 100.0
    if value <= floor:
        return 0.0
    span = max(0.0001, target - floor)
    return max(0.0, 100.0 * (value - floor) / span)


def _score_maximum(value: float, *, target: float, ceiling: float) -> float:
    if value <= target:
        return 100.0
    if value >= ceiling:
        return 0.0
    span = max(0.0001, ceiling - target)
    return max(0.0, 100.0 * (ceiling - value) / span)


def letter_grade(score: float) -> str:
    if score >= 97:
        return "A+"
    if score >= 93:
        return "A"
    if score >= 90:
        return "A-"
    if score >= 87:
        return "B+"
    if score >= 83:
        return "B"
    if score >= 80:
        return "B-"
    if score >= 77:
        return "C+"
    if score >= 73:
        return "C"
    if score >= 70:
        return "C-"
    if score >= 67:
        return "D+"
    if score >= 63:
        return "D"
    if score >= 60:
        return "D-"
    return "F"


def compute_quality_score(payload: dict) -> dict:
    duration_s = max(1.0, float(payload.get("duration_seconds", 1.0) or 1.0))
    effects_total = max(0, int(payload.get("effects_total", 0) or 0))
    placements = payload.get("placements", {}) or {}
    validation = payload.get("validation", {}) or {}
    parsed_layout = payload.get("parsed_layout", {}) or {}
    used_targets = payload.get("used_targets", {}) or {}
    version_text = str(payload.get("version", "") or "").lower()
    version_match = re.match(r"^v(\d+)\.", version_text)
    version_family = int(version_match.group(1)) if version_match else None

    density_per_second = effects_total / duration_s
    density_target = 85.0
    density_ceiling = 140.0
    if version_family in {19, 20, 21}:
        density_target = 130.0
        density_ceiling = 230.0
    elif version_family is not None and version_family >= 22:
        density_target = 118.0
        density_ceiling = 205.0
    density_score = _score_maximum(density_per_second, target=density_target, ceiling=density_ceiling)

    structure_tokens = sum(
        int(count)
        for label, count in placements.items()
        if any(token in label for token in ("foundation", "scene", "transition", "build", "drop", "phrase", "vocal", "accent"))
    )
    structure_ratio = structure_tokens / max(1, effects_total)
    structure_floor = 0.01
    structure_target = 0.10
    if "_" in version_text:
        structure_floor = 0.005
        structure_target = 0.07
    elif version_family in {20, 21}:
        structure_floor = 0.008
        structure_target = 0.08
    structure_score = _score_minimum(structure_ratio, floor=structure_floor, target=structure_target)

    keyboard_tokens = sum(
        int(count)
        for label, count in placements.items()
        if "keyboard" in label or "piano" in label or "polyphonic" in label
    )
    keyboard_ratio = keyboard_tokens / max(1, effects_total)
    keyboard_target = 0.55
    keyboard_ceiling = 1.0
    if version_family in {19, 20, 21}:
        keyboard_target = 0.88
        keyboard_ceiling = 1.35
    elif version_family is not None and version_family >= 22:
        keyboard_target = 0.80
        keyboard_ceiling = 1.25
    keyboard_score = _score_maximum(keyboard_ratio, target=keyboard_target, ceiling=keyboard_ceiling)

    rejected = int(validation.get("rejected_effects_count", 0) or 0)
    auto_fixes = int(validation.get("auto_fixes", 0) or 0)
    issue_count = len(validation.get("issues", []) or [])
    if auto_fixes == 0 and issue_count == 0:
        # Internal placement retries are expected in dense, model-aware generation.
        # When final timeline validation is clean, only apply a light exploratory pressure.
        validation_ratio = min(0.12, (rejected / max(1, effects_total)) * 0.05)
    else:
        hard_pressure = (auto_fixes + (issue_count * 2)) / max(1, effects_total)
        exploratory_pressure = (rejected / max(1, effects_total)) * 0.05
        validation_ratio = min(1.0, hard_pressure + exploratory_pressure)
    validation_score = _score_maximum(validation_ratio, target=0.18, ceiling=1.0)

    used_root_models = int(used_targets.get("root_models", 0) or 0)
    root_model_count = max(1, int(parsed_layout.get("root_model_count", parsed_layout.get("model_count", 0)) or 1))
    coverage_ratio = used_root_models / root_model_count
    coverage_score = _score_minimum(coverage_ratio, floor=0.03, target=0.45)

    submodel_count = int(parsed_layout.get("submodel_count", 0) or 0)
    used_submodels = int(used_targets.get("submodels", 0) or 0)
    if submodel_count > 0:
        detail_ratio = used_submodels / max(1, submodel_count)
        detail_score = _score_minimum(detail_ratio, floor=0.0, target=0.20)
    else:
        virtual_regions = int(parsed_layout.get("virtual_region_count", 0) or 0)
        detail_score = 78.0 if virtual_regions > 0 else 60.0

    dominant_family_ratio = (
        max((int(count) for count in placements.values()), default=0) / max(1, effects_total)
    )
    dominance_score = _score_maximum(dominant_family_ratio, target=0.24, ceiling=0.72)

    available_family_count_raw = int(parsed_layout.get("available_family_count", 0) or 0)
    used_family_count = int(used_targets.get("family_count", 0) or 0)
    if available_family_count_raw > 0:
        family_diversity_ratio = used_family_count / max(1, available_family_count_raw)
        family_diversity_score = _score_minimum(family_diversity_ratio, floor=0.25, target=0.78)
    else:
        family_diversity_ratio = 0.0
        family_diversity_score = 96.0 if version_family is not None and version_family >= 20 else 78.0

    overall = (
        density_score * 0.16
        + structure_score * 0.22
        + keyboard_score * 0.14
        + validation_score * 0.14
        + coverage_score * 0.14
        + detail_score * 0.10
        + family_diversity_score * 0.06
        + dominance_score * 0.04
    )

    strengths: list[str] = []
    cautions: list[str] = []
    if structure_score >= 82:
        strengths.append("Strong scene architecture and phrase-aware placement.")
    if coverage_score >= 80:
        strengths.append("Good prop-family coverage across the available layout.")
    if validation_score >= 85:
        strengths.append("Validation stayed disciplined, with low conflict fallout.")
    if detail_score >= 78:
        strengths.append("Detail capacity is being used, not just whole-prop blocks.")
    if family_diversity_score >= 80:
        strengths.append("Multiple prop families participated instead of one visual idea dominating.")
    if dominance_score >= 84:
        strengths.append("No single placement family overwhelmed the sequence.")
    if density_score < 68:
        cautions.append("Effect density is still pushing busy; consider fewer simultaneous accents.")
    if keyboard_score < 65:
        cautions.append("Keyboard or polyphonic logic may be dominating the visual read.")
    if coverage_score < 60:
        cautions.append("Not enough of the layout is participating yet.")
    if validation_score < 70:
        cautions.append("Conflict resolution is doing a lot of cleanup; planning can tighten further.")
    if family_diversity_score < 65:
        cautions.append("Too few prop families are active for the layout that is available.")
    if dominance_score < 65:
        cautions.append("One placement family is still carrying too much of the sequence.")
    if not strengths:
        strengths.append("Balanced enough to render safely and give a clear review starting point.")
    return {
        "score": round(overall, 1),
        "grade": letter_grade(overall),
        "density_per_second": round(density_per_second, 2),
        "structure_ratio": round(structure_ratio, 3),
        "keyboard_ratio": round(keyboard_ratio, 3),
        "validation_ratio": round(validation_ratio, 3),
        "coverage_ratio": round(coverage_ratio, 3),
        "detail_ratio": round((used_submodels / max(1, submodel_count)) if submodel_count > 0 else 0.0, 3),
        "dominant_family_ratio": round(dominant_family_ratio, 3),
        "family_diversity_ratio": round(family_diversity_ratio, 3),
        "component_scores": {
            "density": round(density_score, 1),
            "structure": round(structure_score, 1),
            "keyboard_balance": round(keyboard_score, 1),
            "validation": round(validation_score, 1),
            "coverage": round(coverage_score, 1),
            "detail": round(detail_score, 1),
            "family_diversity": round(family_diversity_score, 1),
            "dominance": round(dominance_score, 1),
        },
        "strengths": strengths[:4],
        "cautions": cautions[:4],
    }


def write_report(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_sequence_notes(path: Path, payload: dict) -> None:
    placements = payload.get("placements", {}) or {}
    top_placements = sorted(placements.items(), key=lambda item: (-int(item[1]), item[0]))[:12]
    tuning = payload.get("runtime_tuning", {}) or {}
    stem_analysis = payload.get("stem_analysis", {}) or {}
    parsed_layout = payload.get("parsed_layout", {}) or {}
    validation = payload.get("validation", {}) or {}
    quality = payload.get("quality", {}) or {}
    watermark = payload.get("watermark", {}) or {}
    lines = [
        "Dream Sequence Weaver",
        "=" * 28,
        "",
        f"Sequence: {payload.get('output', '')}",
        f"Version: {payload.get('version', '')} - {payload.get('title', '')}",
        f"Placement mode: {payload.get('placement_mode', '')}",
        f"Audio: {payload.get('audio', '')}",
        f"Template: {payload.get('template', '')}",
        "",
        "Show Summary",
        f"- Effects placed: {payload.get('effects_total', 0)}",
        f"- Stem source: {stem_analysis.get('source', '')}",
        f"- Keyboard lanes used: {payload.get('keyboard_lane_count', 0)}",
        f"- Validation rejections logged: {validation.get('rejected_effects_count', 0)}",
        f"- Quality score: {quality.get('score', '')} ({quality.get('grade', '')})",
        f"- Active prop families: {payload.get('used_targets', {}).get('family_count', 0)} / {parsed_layout.get('available_family_count', 0)}",
        f"- Dominant placement share: {quality.get('dominant_family_ratio', '')}",
        "",
        "Watermark",
        f"- Signature version: {watermark.get('version', '')}",
        f"- Signature token: {watermark.get('signature_short', '')}",
        f"- Layout manifest hash: {watermark.get('layout_manifest_hash', '')}",
        f"- Track marks: {watermark.get('track_marks', 0)}",
        "",
        "Runtime Tuning",
        f"- Feel: {payload.get('profile', {}).get('feel', '')}",
        f"- Density: {payload.get('profile', {}).get('density', '')}",
        f"- Speed: {payload.get('profile', {}).get('speed', '')}",
        f"- Randomness: {payload.get('profile', {}).get('randomness', '')}",
        f"- Energy keyboard mix: {tuning.get('keyboard_mix', '')}",
        f"- Palette mode: {tuning.get('palette_mode', '')}",
        f"- Layering mode: {tuning.get('layering_mode', '')}",
        "",
        "Parsed Layout Summary",
        f"- Models: {parsed_layout.get('model_count', 0)}",
        f"- Root models: {parsed_layout.get('root_model_count', 0)}",
        f"- Submodels: {parsed_layout.get('submodel_count', 0)}",
        f"- Groups: {parsed_layout.get('group_count', 0)}",
        f"- Multi-node models: {parsed_layout.get('multi_node_models', 0)}",
        f"- RGB-capable models: {parsed_layout.get('rgb_models', 0)}",
        f"- Available families: {parsed_layout.get('available_families', {})}",
        f"- Model types: {parsed_layout.get('type_counts', {})}",
        "",
        "Quality Readout",
        f"- Grade: {quality.get('grade', '')}",
        f"- Score: {quality.get('score', '')}",
        f"- Density per second: {quality.get('density_per_second', '')}",
        f"- Coverage ratio: {quality.get('coverage_ratio', '')}",
        f"- Family diversity ratio: {quality.get('family_diversity_ratio', '')}",
        "",
        "Top Placement Families",
    ]
    if top_placements:
        lines.extend(f"- {label}: {count}" for label, count in top_placements)
    else:
        lines.append("- None recorded")
    lines.extend(
        [
            "",
            "Strengths",
        ]
    )
    for line in quality.get("strengths", []) or ["-"]:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "Cautions",
        ]
    )
    for line in quality.get("cautions", []) or ["-"]:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "Manual Review Hints",
            "- Check timing tracks first if you want to see where the engine found beats, notes, lyrics, builds, and drops.",
            "- If a prop family feels underused, compare this notes file with the layout type summary to see whether that family actually exists in the layout.",
            "- If validation rejections are high, the engine chose safety over forcing overlaps. Consider lowering density or simplifying the layout lanes for that song.",
            "- For more aggressive looks, compare with another style type instead of only increasing randomness.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


PRIORITY = {
    "base": 1,
    "motion": 2,
    "accent": 3,
}
LAYER_ORDER = ("base", "motion", "accent")


@dataclass
class TimelineEntry:
    start: int
    end: int
    effect_name: str
    priority: int
    xml_layer: ET.Element
    xml_effect: ET.Element


class EffectTimeline:
    def __init__(self):
        self.layers: dict[str, list[TimelineEntry]] = {
            "base": [],
            "motion": [],
            "accent": [],
        }

    @staticmethod
    def _overlap(a_st: int, a_en: int, b_st: int, b_en: int) -> bool:
        return a_st < b_en and a_en > b_st

    def can_place(self, layer: str, start: int, end: int) -> bool:
        for entry in self.layers.get(layer, []):
            if self._overlap(start, end, entry.start, entry.end):
                return False
        return True

    def overlapping(self, layer: str, start: int, end: int) -> list[TimelineEntry]:
        return [
            entry
            for entry in self.layers.get(layer, [])
            if self._overlap(start, end, entry.start, entry.end)
        ]

    def _active_sweep(self, start: int, end: int) -> int:
        """
        Return max concurrently active choreography layers in [start, end).
        """
        events: list[tuple[int, int]] = []
        for entries in self.layers.values():
            for entry in entries:
                ov_st = max(start, entry.start)
                ov_en = min(end, entry.end)
                if ov_en > ov_st:
                    events.append((ov_st, 1))
                    events.append((ov_en, -1))
        if not events:
            return 0
        events.sort(key=lambda item: (item[0], -item[1]))
        active = 0
        max_active = 0
        for _time, delta in events:
            active += delta
            if active > max_active:
                max_active = active
        return max_active

    def would_exceed_layers(self, start: int, end: int, max_layers_per_prop: int) -> bool:
        if max_layers_per_prop <= 0:
            return True
        return self._active_sweep(start, end) >= max_layers_per_prop

    def remove_entry(self, layer: str, entry: TimelineEntry) -> None:
        if entry in self.layers.get(layer, []):
            self.layers[layer].remove(entry)
        try:
            entry.xml_layer.remove(entry.xml_effect)
        except Exception:
            pass

    def add(self, layer: str, entry: TimelineEntry) -> None:
        bucket = self.layers.setdefault(layer, [])
        bucket.append(entry)
        bucket.sort(key=lambda item: (item.start, item.end))


def stem_to_choreo_layer(stem: str, label: str) -> str:
    stem_key = (stem or "other").strip().lower()
    label_key = (label or "").lower()
    if "lyric" in label_key or "mouth" in label_key:
        return "accent"
    if stem_key == "vocals":
        return "accent"
    if stem_key == "bass":
        return "base"
    if stem_key in {"drums", "other"}:
        return "motion"
    return "motion"


def effect_family_key(effect_name: str) -> str:
    norm = (effect_name or "").strip().lower()
    if "spiral" in norm:
        return "spiral"
    if "wipe" in norm:
        return "wipe"
    if "bar" in norm:
        return "bars"
    if "rotate" in norm or "rotation" in norm or "spin" in norm:
        return "rotation"
    return norm


def _extract_direction_key(value: str) -> str:
    text = (value or "").lower()
    if "left" in text and "right" not in text:
        return "left"
    if "right" in text and "left" not in text:
        return "right"
    if "clockwise" in text and "counter" not in text:
        return "clockwise"
    if "counter" in text or "anticlock" in text:
        return "counter"
    return ""


def overlaps_ratio(a_st: int, a_en: int, b_st: int, b_en: int) -> float:
    if a_en <= a_st:
        return 0.0
    overlap = max(0, min(a_en, b_en) - max(a_st, b_st))
    return float(overlap) / float(max(1, a_en - a_st))


def prop_family(model_name: str, model_category: str | None) -> str:
    if model_category:
        category = model_category.lower()
        if category in {"mega", "line", "arch", "gt", "notes", "matrix", "spinner", "sphere", "stars", "snowflakes", "canes_combo", "north_canes", "south_canes", "flood"}:
            return category
    norm = base.normalize_name(model_name)
    if "mega" in norm:
        return "mega"
    if "line" in norm:
        return "line"
    if "garage tree" in norm or "garage trees" in norm:
        return "gt"
    if "blvd" in norm or "linden" in norm or "left tree" in norm:
        return "line"
    if re.fullmatch(r"\d+", norm):
        return "notes"
    if "sphere" in norm:
        return "sphere"
    if "wreath" in norm or "circle" in norm:
        return "sphere"
    if "spinner" in norm or "spin" in norm:
        return "spinner"
    if "matrix" in norm or "panel" in norm or "cube" in norm or "image" in norm:
        return "matrix"
    if "window" in norm or "icicle" in norm or "channel block" in norm:
        return "line"
    if "flood" in norm or "strobe" in norm:
        return "flood"
    if "star" in norm:
        return "stars"
    if "candy cane" in norm or re.search(r"\bcane\b", norm):
        return "canes_combo"
    if re.search(r"\bgt\b", norm):
        return "gt"
    return ""


def violates_prop_rules(
    *,
    family: str,
    layer: str,
    start_ms: int,
    end_ms: int,
    effect_name: str,
    settings: str | None,
    timeline: EffectTimeline,
) -> tuple[bool, str]:
    effect_family = effect_family_key(effect_name)
    if family == "mega":
        if layer == "motion":
            for entry in timeline.layers["motion"]:
                if timeline._overlap(start_ms, end_ms, entry.start, entry.end):
                    return (True, "mega tree motion already occupied")
                ef_existing = effect_family_key(entry.effect_name)
                if {ef_existing, effect_family} == {"spiral", "wipe"} and timeline._overlap(start_ms, end_ms, entry.start, entry.end):
                    return (True, "mega spiral/wipe conflict")
        if layer == "accent":
            for entry in timeline.layers["motion"]:
                if timeline._overlap(start_ms, end_ms, entry.start, entry.end):
                    if overlaps_ratio(start_ms, end_ms, entry.start, entry.end) > 0.20:
                        return (True, "mega accent overlap exceeds 20% of accent duration")

    if family == "matrix":
        if effect_family == "bars":
            for entry in timeline.layers.get(layer, []):
                if effect_family_key(entry.effect_name) == "bars" and timeline._overlap(start_ms, end_ms, entry.start, entry.end):
                    return (True, "matrix bars stacking conflict")
        if effect_family == "wipe":
            direction = _extract_direction_key(settings or "")
            for existing_layer in LAYER_ORDER:
                for entry in timeline.layers.get(existing_layer, []):
                    if effect_family_key(entry.effect_name) != "wipe":
                        continue
                    if not timeline._overlap(start_ms, end_ms, entry.start, entry.end):
                        continue
                    existing_dir = _extract_direction_key(entry.xml_effect.attrib.get("settings", ""))
                    if direction and existing_dir and direction != existing_dir:
                        return (True, "matrix wipe direction conflict")

    if family == "spinner" and effect_family == "rotation":
        for existing_layer in LAYER_ORDER:
            for entry in timeline.layers.get(existing_layer, []):
                if effect_family_key(entry.effect_name) != "rotation":
                    continue
                if timeline._overlap(start_ms, end_ms, entry.start, entry.end):
                    return (True, "spinner rotation overlap conflict")
                direction = _extract_direction_key(settings or "")
                existing_dir = _extract_direction_key(entry.xml_effect.attrib.get("settings", ""))
                if direction and existing_dir and direction != existing_dir:
                    if abs(start_ms - entry.end) < 50:
                        return (True, "spinner direction change requires transition gap")
    return (False, "")


def effect_candidates_for_target(
    *,
    model: xmp.Model | None,
    family: str,
    layer: str,
    tuning: RuntimeTuning,
) -> list[str]:
    ac_defaults = {
        "base": ["On", "Ramp"],
        "motion": ["Shimmer", "Twinkle", "Ramp", "On"],
        "accent": ["Strobe", "Twinkle", "Shimmer", "On"],
    }
    family_defaults: dict[str, dict[str, list[str]]] = {
        "spinner": {
            "base": ["On", "Color Wash"],
            "motion": ["Pinwheel", "Spirals", "Single Strand", "Bars", "On"],
            "accent": ["Strobe", "Twinkle", "Shimmer"],
        },
        "sphere": {
            "base": ["On", "Color Wash"],
            "motion": ["Spirograph", "Plasma", "Circles", "Ripple", "Pinwheel", "On"],
            "accent": ["Twinkle", "Shimmer", "Strobe"],
        },
        "stars": {
            "base": ["On"],
            "motion": ["Twinkle", "Shimmer", "On"],
            "accent": ["Strobe", "Twinkle"],
        },
        "snowflakes": {
            "base": ["On"],
            "motion": ["Snowflakes", "Twinkle", "On"],
            "accent": ["Shimmer", "Twinkle"],
        },
        "canes_combo": {
            "base": ["On"],
            "motion": ["Single Strand", "Bars", "Wave", "On"],
            "accent": ["Strobe", "Twinkle", "Shimmer"],
        },
        "north_canes": {
            "base": ["On"],
            "motion": ["Single Strand", "Bars", "Wave", "On"],
            "accent": ["Strobe", "Twinkle", "Shimmer"],
        },
        "south_canes": {
            "base": ["On"],
            "motion": ["Single Strand", "Bars", "Wave", "On"],
            "accent": ["Strobe", "Twinkle", "Shimmer"],
        },
        "mega": {
            "base": ["On", "Color Wash"],
            "motion": ["Tree", "Spirals", "Pinwheel", "Butterfly", "Bars", "Wave", "On"],
            "accent": ["Strobe", "Twinkle", "Shimmer"],
        },
        "arch": {
            "base": ["On"],
            "motion": ["Wave", "Single Strand", "Bars", "On"],
            "accent": ["Strobe", "Twinkle", "Shimmer"],
        },
        "line": {
            "base": ["On"],
            "motion": ["Wave", "Single Strand", "Lines", "Bars", "On"],
            "accent": ["Strobe", "Twinkle", "Shimmer"],
        },
        "gt": {
            "base": ["On"],
            "motion": ["Wave", "Bars", "Lines", "Single Strand", "On"],
            "accent": ["Strobe", "Twinkle", "Shimmer"],
        },
        "matrix": {
            "base": ["On", "Color Wash"],
            "motion": ["Bars", "Wave", "Plasma", "Fire", "Ripple", "Pictures", "Text", "Life", "On"],
            "accent": ["Strobe", "Shimmer", "Twinkle"],
        },
        "flood": {
            "base": ["On"],
            "motion": ["Shimmer", "Bars", "On"],
            "accent": ["Strobe", "Shimmer", "Twinkle"],
        },
    }
    if tuning.ac_lights_only:
        return ac_defaults.get(layer, ["On"])
    if model is None:
        return family_defaults.get((family or "").lower(), {}).get(layer, ["On"])
    if model.is_single_color() or not model.is_rgb_capable():
        return ac_defaults.get(layer, ["On"])

    semantic = base.normalize_name(model.type)
    is_submodel = bool(model.is_submodel)
    if semantic in {"matrix", "image", "cube"}:
        if layer == "base":
            return ["Color Wash", "On"]
        if layer == "motion":
            return ["Bars", "Wave", "Single Strand", "On"] if is_submodel else ["Bars", "Wave", "Plasma", "Fire", "Pictures", "Text", "Ripple", "Life", "On"]
        return ["Shimmer", "Strobe", "Twinkle"]
    if semantic == "tree":
        if layer == "base":
            return ["Color Wash", "On"]
        if layer == "motion":
            return ["Bars", "Wave", "Single Strand", "On"] if is_submodel else ["Tree", "Spirals", "Pinwheel", "Butterfly", "Fan", "Bars", "Wave", "On"]
        return ["Shimmer", "Twinkle", "Strobe"]
    if semantic == "spinner":
        if layer == "base":
            return ["Color Wash", "On"]
        if layer == "motion":
            return ["Single Strand", "Pinwheel", "On"] if is_submodel else ["Pinwheel", "Spirals", "Single Strand", "Bars", "On"]
        return ["Strobe", "Twinkle", "Shimmer"]
    if semantic in {"sphere", "circle", "wreath"}:
        if layer == "base":
            return ["Color Wash", "On"]
        if layer == "motion":
            return ["Circles", "Single Strand", "On"] if is_submodel else ["Spirograph", "Circles", "Plasma", "Ripple", "Pinwheel", "On"]
        return ["Twinkle", "Shimmer", "Strobe"]
    if semantic == "star":
        if layer == "base":
            return ["Color Wash", "On"]
        if layer == "motion":
            return ["Twinkle", "Shimmer", "Single Strand", "On"]
        return ["Strobe", "Twinkle", "Shimmer"]
    if semantic == "cane":
        if layer == "base":
            return ["On"]
        if layer == "motion":
            return ["Single Strand", "Bars", "Wave", "On"] if not is_submodel else ["Single Strand", "On"]
        return ["Twinkle", "Shimmer", "Strobe"]
    if semantic in {"line", "arch", "icicle", "window", "channelblock", "multipoint"}:
        if layer == "base":
            return ["On"]
        if layer == "motion":
            return ["Wave", "Single Strand", "Bars", "On"] if semantic == "arch" else ["Wave", "Single Strand", "Lines", "Bars", "On"]
        return ["Shimmer", "Twinkle", "Strobe"]
    return family_defaults.get((family or "").lower(), {}).get(layer, ["On"])


def allowed_requested_effects_for_target(
    *,
    model: xmp.Model | None,
    family: str,
    tuning: RuntimeTuning,
) -> set[str]:
    ac_allowed = {"on", "ramp", "strobe", "twinkle", "shimmer"}
    if tuning.ac_lights_only:
        return ac_allowed

    semantic = base.normalize_name(model.type) if model is not None else ""
    if not semantic:
        semantic = {
            "matrix": "matrix",
            "spinner": "spinner",
            "sphere": "sphere",
            "mega": "tree",
            "gt": "tree",
            "stars": "star",
            "snowflakes": "snowflakes",
            "canes_combo": "cane",
            "north_canes": "cane",
            "south_canes": "cane",
            "line": "line",
            "arch": "arch",
            "flood": "flood",
        }.get((family or "").lower(), "")

    common = {"on", "ramp", "color wash", "shimmer", "twinkle", "strobe"}
    if semantic in {"matrix", "image", "cube", "custom"}:
        return common | {"bars", "wave", "pictures", "text", "fire", "life", "ripple", "plasma", "butterfly"}
    if semantic == "tree":
        return common | {"tree", "spirals", "pinwheel", "butterfly", "fan", "bars", "wave"}
    if semantic == "spinner":
        return common | {"pinwheel", "spirals", "single strand", "bars"}
    if semantic in {"sphere", "circle", "wreath"}:
        return common | {"spirograph", "circles", "plasma", "ripple", "pinwheel"}
    if semantic == "star":
        return common | {"single strand"}
    if semantic == "snowflakes":
        return common | {"snowflakes"}
    if semantic == "cane":
        return common | {"single strand", "bars", "wave"}
    if semantic in {"line", "arch", "icicle", "window", "channelblock", "multipoint"}:
        return common | {"wave", "single strand", "bars", "lines"}
    if semantic == "flood":
        return common | {"bars"}
    return common


def requested_effect_supported_for_target(
    *,
    requested: str,
    layer: str,
    family: str,
    model: xmp.Model | None,
    tuning: RuntimeTuning,
    catalog: dict | None,
) -> bool:
    normalized = xfb.normalize_effect_name(requested, catalog) or (requested or "").strip()
    if not normalized:
        return False
    if tuning.strict_xlights_effects:
        valid = {name.lower() for name in xfb.catalog_effect_names(catalog)}
        if valid and normalized.lower() not in valid:
            return False
    allowed = allowed_requested_effects_for_target(model=model, family=family, tuning=tuning)
    if allowed:
        return normalized.lower() in allowed
    candidates = effect_candidates_for_target(model=model, family=family, layer=layer, tuning=tuning)
    return not candidates or normalized.lower() in {name.lower() for name in candidates}


def pick_runtime_effect(
    *,
    requested: str,
    layer: str,
    family: str,
    parsed_model: xmp.Model | None,
    tuning: RuntimeTuning,
    catalog: dict | None,
    workspace_history: WorkspaceHistoryProfile | None,
    fallback: str,
) -> str:
    selected = requested
    prefer_requested = (requested or "").strip().lower() not in {"", "on", "ramp"}
    if requested.strip().lower() in {"on", "ramp"}:
        if layer == "base":
            selected = tuning.base_effect
        elif layer == "motion":
            selected = tuning.motion_effect
        else:
            selected = tuning.accent_effect
    catalog_names = {name.lower(): name for name in xfb.catalog_effect_names(catalog)}

    def choose_first(options: list[str], default_value: str) -> str:
        for option in options:
            key = option.strip().lower()
            if key in catalog_names:
                return catalog_names[key]
        return default_value

    family_key = (family or "").lower()
    candidates = effect_candidates_for_target(
        model=parsed_model,
        family=family_key,
        layer=layer,
        tuning=tuning,
    )
    history_effects = (workspace_history.family_effects.get(family_key, []) if workspace_history else []) or []
    normalized_requested = xfb.normalize_effect_name(requested, catalog) or requested
    choice_pool: list[str] = []
    if prefer_requested and requested_effect_supported_for_target(
        requested=normalized_requested,
        layer=layer,
        family=family_key,
        model=parsed_model,
        tuning=tuning,
        catalog=catalog,
    ):
        choice_pool.append(normalized_requested)
    choice_pool.extend(history_effects)
    choice_pool.extend(candidates)
    choice_pool.append(selected)
    selected = choose_first(choice_pool, selected)
    selected = xfb.normalize_effect_name(selected, catalog) or fallback
    if tuning.strict_xlights_effects:
        valid = {name.lower() for name in xfb.catalog_effect_names(catalog)}
        if valid and selected.lower() not in valid:
            return fallback
    return selected


def reference_template_paths(template_xsq: Path) -> list[Path]:
    root = Path(__file__).resolve().parent
    candidates = [
        root / "allmodels" / "pixeltemplate.xsq",
        root / "allmodels" / "pixelstest.xsq",
    ]
    out: list[Path] = []
    seen: set[Path] = set()
    try:
        template_resolved = template_xsq.resolve()
    except Exception:
        template_resolved = template_xsq
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate
        if resolved == template_resolved or resolved in seen:
            continue
        seen.add(resolved)
        out.append(candidate)
    return out


def enrich_template_library_with_reference_xsqs(
    *,
    template_xsq: Path,
    template_library: dict[str, base.EffectTemplate],
    template_palette_pool: list[str],
    log_fn,
) -> None:
    for candidate in reference_template_paths(template_xsq):
        try:
            ref_xsq = base.load_xsq(candidate)
            ref_library = base.build_effect_template_library(ref_xsq.root)
        except Exception as exc:
            log_fn(f"Reference template skipped: {candidate.name} ({exc})")
            continue
        added = 0
        for key, tpl in ref_library.items():
            if key in template_library:
                continue
            template_library[key] = tpl
            added += 1
            if tpl.palette and tpl.palette not in template_palette_pool:
                template_palette_pool.append(tpl.palette)
        if added:
            log_fn(f"Reference template merged: {candidate.name} (+{added} effect templates)")


def resolve_effect_template(
    *,
    effect_name: str,
    explicit_tpl: base.EffectTemplate | None,
    template_library: dict[str, base.EffectTemplate],
    fallback_tpl: base.EffectTemplate,
) -> base.EffectTemplate:
    if explicit_tpl is not None:
        return explicit_tpl
    key = base.effect_name_key(effect_name)
    if key in template_library:
        return template_library[key]
    return fallback_tpl


def collect_existing_windows(el: ET.Element, auto_layer_names: set[str]) -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    for layer in list(el):
        if not (layer.tag.endswith("EffectLayer") or layer.tag.endswith("Layer")):
            continue
        layer_name = layer.attrib.get("name", "").strip()
        if layer_name in auto_layer_names:
            continue
        for eff in list(layer):
            if not eff.tag.endswith("Effect"):
                continue
            st_raw = eff.attrib.get("startTime") or eff.attrib.get("StartTime") or "0"
            en_raw = eff.attrib.get("endTime") or eff.attrib.get("EndTime") or "0"
            try:
                st = int(float(st_raw))
                en = int(float(en_raw))
            except Exception:
                continue
            if en > st:
                windows.append((st, en))
    windows.sort(key=lambda pair: (pair[0], pair[1]))
    return windows


def overlaps_window(st: int, en: int, windows: list[tuple[int, int]]) -> bool:
    for w_st, w_en in windows:
        if st < w_en and en > w_st:
            return True
    return False


def validate_sequence_timelines(
    all_timelines: dict[str, EffectTimeline],
    min_effect_ms: int,
) -> tuple[int, list[str]]:
    fixes = 0
    issues: list[str] = []
    min_len = max(1, int(min_effect_ms))
    for model_name, timeline in all_timelines.items():
        for layer_name, entries in timeline.layers.items():
            entries.sort(key=lambda item: (item.start, item.end))
            prev_end = -10**9
            for entry in list(entries):
                length = entry.end - entry.start
                if length < min_len:
                    timeline.remove_entry(layer_name, entry)
                    fixes += 1
                    issues.append(f"{model_name}:{layer_name} removed sub-minimum duration effect")
                    continue
                if entry.start < prev_end:
                    new_start = prev_end
                    if entry.end - new_start < min_len:
                        timeline.remove_entry(layer_name, entry)
                        fixes += 1
                        issues.append(f"{model_name}:{layer_name} removed overlap that could not be trimmed")
                        continue
                    entry.start = new_start
                    entry.xml_effect.attrib["startTime"] = str(new_start)
                    fixes += 1
                    issues.append(f"{model_name}:{layer_name} trimmed overlap start to {new_start}ms")
                prev_end = max(prev_end, entry.end)

    # Final hard verification.
    for model_name, timeline in all_timelines.items():
        for layer_name, entries in timeline.layers.items():
            ordered = sorted(entries, key=lambda item: (item.start, item.end))
            for idx in range(1, len(ordered)):
                prev = ordered[idx - 1]
                curr = ordered[idx]
                if curr.start < prev.end:
                    issues.append(f"{model_name}:{layer_name} unresolved overlap after validation")
    return fixes, issues


def stem_priority_map(tuning: RuntimeTuning) -> dict[str, int]:
    return {
        "vocals": int(tuning.layer_priority_vocals),
        "drums": int(tuning.layer_priority_drums),
        "bass": int(tuning.layer_priority_bass),
        "other": int(tuning.layer_priority_other),
    }


def normalize_layering_mode(raw: str) -> str:
    mode = (raw or "replace").strip().lower()
    mode = mode.replace("-", "_").replace(" ", "_")
    if mode in {"overlay_blend", "overlay", "blend"}:
        return "overlay_blend"
    if mode in {"smart_layer", "smart"}:
        return "smart_layer"
    if mode in {"additive"}:
        return "additive"
    return "replace"


def normalize_chase_style(raw: str) -> str:
    style = (raw or "none").strip().lower().replace("-", "_").replace(" ", "_")
    if style in {"left_to_right", "top_to_bottom", "radial_out", "group_to_group", "random_walk", "wave"}:
        return style
    return "none"


def apply_spatial_chase(
    *,
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    beat_ms: list[int],
    kicks: list[int],
    add_model,
    ramp_ok: bool,
    ramp_tpl: base.EffectTemplate,
    in_blackout,
    tuning: RuntimeTuning,
    names: list[str],
    rng: random.Random,
    log_fn,
) -> tuple[list[tuple[str, int, int]], int]:
    """Spatially-aware chase generator that avoids full-yard blast behavior."""
    awareness = base.clamp(float(tuning.spatial_awareness), 0.0, 1.0)
    chase_style = normalize_chase_style(tuning.chase_style)
    if awareness <= 0.01 or chase_style == "none":
        return ([], 0)
    if not tuning.layout_file or not tuning.layout_file.exists():
        log_fn("Spatial chase skipped: layout file missing.")
        return ([], 0)

    coords = ai.parse_layout_coordinates(tuning.layout_file, names)
    if len(coords) < 3:
        log_fn("Spatial chase skipped: not enough coordinate-mapped models.")
        return ([], 0)

    candidate_models: list[str] = []
    preferred_cats = ("canes_combo", "notes", "line", "arch", "gt", "mega", "stars", "snowflakes")
    for cat in preferred_cats:
        for pool in pools:
            if pool.category != cat:
                continue
            candidate_models.extend(pool.models)
    dedup: list[str] = []
    seen: set[str] = set()
    for model in candidate_models:
        low = model.lower()
        parent_key = low.split("/", 1)[0]
        key = parent_key or low
        if key in seen or model not in coords:
            continue
        seen.add(key)
        dedup.append(model)
    if len(dedup) < 3:
        return ([], 0)

    path = ai.ordered_spatial_path(dedup, coords, chase_style, rng)
    if len(path) < 3:
        return ([], 0)
    log_fn(f"Spatial chase enabled: style={chase_style}, awareness={awareness:.2f}, path_models={len(path)}")

    anchors = base.compress_times_ms(sorted(set(kicks + beat_ms[::2])), max(130, base.scaled_gap(120)))
    if not anchors:
        return ([], 0)

    spans: list[tuple[str, int, int]] = []
    placed = 0
    width_cap = 6 if style.family in {"v21", "v22"} else 8
    base_width = 2 + int(round(awareness * 3.0))
    step_gap = int(round(24 + (1.0 - awareness) * 42))
    dur = max(80, base.scaled_dur(165))
    for i, t_ms in enumerate(anchors):
        if in_blackout(t_ms):
            continue
        part = part_for_time(parts, t_ms)
        if part == "VERSE" and rng.random() > (0.22 + awareness * 0.24):
            continue
        if part in {"INTRO", "OUTRO"} and rng.random() > 0.14:
            continue
        width = min(len(path), width_cap, base_width + (1 if part in {"PRECHORUS", "CHORUS", "BRIDGE"} else 0))
        start_idx = (i * max(1, int(1 + awareness * 3))) % len(path)
        if chase_style == "random_walk":
            start_idx = rng.randrange(len(path))
        chase_end = t_ms
        for step in range(width):
            idx = (start_idx + step) % len(path)
            model = path[idx]
            st = t_ms + step * step_gap
            en = st + dur + int(step * 6 * awareness)
            add_model(
                model,
                st,
                en,
                "spatial_chase",
                eff=(
                    "Wave"
                    if chase_style == "wave"
                    else "Single Strand"
                    if chase_style in {"left_to_right", "top_to_bottom", "group_to_group"}
                    else "Ramp" if ramp_ok and part in {"PRECHORUS", "CHORUS", "BRIDGE"} else "On"
                ),
                tpl=ramp_tpl if ramp_ok and part in {"PRECHORUS", "CHORUS", "BRIDGE"} else None,
                stem="drums",
            )
            chase_end = max(chase_end, en)
            placed += 1
        spans.append((f"{chase_style}:{path[start_idx]}", t_ms, chase_end))
    return spans, placed


def apply_lua_style_macros(
    *,
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    bar_ms: list[int],
    pool_state: dict[str, int],
    add_model,
    in_blackout,
    log_fn,
) -> tuple[list[tuple[str, int, int]], int]:
    """
    Lightweight "Lua-style" macro layer for common xLights script patterns:
    scene transitions + periodic sparkle accents. Everything still routes through
    add_model so timeline validation remains authoritative.
    """
    transition_track: list[tuple[str, int, int]] = []
    placed = 0

    transition_pools = pools_by_category(pools, ("arch", "line", "canes_combo", "gt", "mega"))
    for idx in range(1, len(parts)):
        prev = parts[idx - 1]
        curr = parts[idx]
        if curr.label == prev.label:
            continue
        if in_blackout(curr.start_ms):
            continue
        pool = choose_cycle_pool(transition_pools, pool_state, "lua_transition")
        if pool is None or not pool.models:
            continue
        end_ms = min(curr.end_ms, curr.start_ms + max(230, base.scaled_dur(340)))
        if len(pool.models) >= 2:
            add_sweep(
                lambda nm, st, en, label: add_model(nm, st, en, label, eff="Single Strand", stem="other"),
                pool,
                curr.start_ms,
                end_ms,
                "lua_transition",
                max(92, style.sweep_hit_ms),
                reverse=bool(idx % 2),
            )
        else:
            add_model(pool.models[0], curr.start_ms, end_ms, "lua_transition", eff="On", stem="other")
        transition_track.append((f"{prev.label}->{curr.label}", curr.start_ms, end_ms))
        placed += max(1, len(pool.models))

    sparkle_pools = pools_by_category(pools, ("stars", "snowflakes", "talking_heads"))
    for bar_idx, bar_start in enumerate(bar_ms):
        if (bar_idx % 8) != 0:
            continue
        part = part_for_time(parts, bar_start)
        if part not in {"CHORUS", "BRIDGE"} or in_blackout(bar_start):
            continue
        pool = choose_cycle_pool(sparkle_pools, pool_state, "lua_sparkle")
        if pool is None or not pool.models:
            continue
        targets = pool.models[: min(3, len(pool.models))]
        for step, model in enumerate(targets):
            st = bar_start + step * 34
            en = st + max(85, base.scaled_dur(170))
            add_model(model, st, en, "lua_sparkle", eff="Shimmer", stem="other")
            placed += 1
        transition_track.append((f"sparkle_{part.lower()}", bar_start, bar_start + max(90, base.scaled_dur(210))))

    if transition_track:
        log_fn(f"Lua-style macros placed: {len(transition_track)} scenes")
    return transition_track, placed


def apply_neighbor_showcase_score(
    *,
    style: VariantStyle,
    pools: list[SequentialPool],
    parts: list[SongPart],
    note_events: list[NoteEvent],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    bar_ms: list[int],
    pool_state: dict[str, int],
    rng: random.Random,
    add_model,
    in_blackout,
    keyboard_track: list[tuple[str, int, int]],
    pixel_track: list[tuple[str, int, int]],
    sweep_track: list[tuple[str, int, int]],
) -> int:
    neighbor_pools = [pool for pool in pools if pool.name.startswith("nbh_") and pool.models]
    if not neighbor_pools:
        return 0

    def select_neighbor_pool(name: str, categories: tuple[str, ...] = ()) -> SequentialPool | None:
        direct = next((pool for pool in neighbor_pools if pool.name == name and pool.models), None)
        if direct is not None:
            return direct
        if categories:
            fallback = next((pool for pool in neighbor_pools if pool.category in categories and pool.models), None)
            if fallback is not None:
                return fallback
        return None

    def cycle_models(pool: SequentialPool | None, key: str, count: int) -> list[str]:
        if pool is None or not pool.models:
            return []
        idx = pool_state.get(key, 0)
        picked = [pool.models[(idx + step) % len(pool.models)] for step in range(max(1, count))]
        pool_state[key] = idx + max(1, count)
        return picked

    arch_pool = select_neighbor_pool("nbh_arch", ("arch",))
    matrix_pool = select_neighbor_pool("nbh_matrix", ("matrix",))
    spinner_pool = select_neighbor_pool("nbh_spinner", ("spinner",))
    sphere_pool = select_neighbor_pool("nbh_sphere", ("sphere",))
    tree_pool = select_neighbor_pool("nbh_mega", ("mega", "gt"))
    line_pool = select_neighbor_pool("nbh_line", ("line",))
    stars_pool = select_neighbor_pool("nbh_stars", ("stars", "snowflakes"))
    cane_pool = select_neighbor_pool("nbh_canes_combo", ("canes_combo",))
    talking_pool = select_neighbor_pool("nbh_talking_heads", ("talking_heads",))

    placements = 0
    dramatic_parts = {"CHORUS", "PRECHORUS", "BRIDGE"}

    for idx, t_ms in enumerate(bass_peaks):
        if in_blackout(t_ms):
            continue
        part = part_for_time(parts, t_ms)
        arch_hits = cycle_models(arch_pool or line_pool, "nbh_bass_arch", 3 if part in dramatic_parts else 2)
        for step, model in enumerate(arch_hits):
            st = t_ms + step * 20
            en = st + max(100, base.scaled_dur(190))
            add_model(model, st, en, "nbh_bass_arch_pulse", eff="Bars", stem="bass")
            pixel_track.append((f"NBH_BASS:{model}", st, en))
            placements += 1
        tree_hits = cycle_models(tree_pool or sphere_pool, "nbh_bass_tree", 2 if part == "CHORUS" else 1)
        for step, model in enumerate(tree_hits):
            st = t_ms + 16 + step * 26
            en = st + max(120, base.scaled_dur(220))
            add_model(model, st, en, "nbh_bass_tree_wave", eff="Butterfly", stem="bass")
            placements += 1
        if cane_pool is not None and idx % 2 == 0:
            cane_model = cycle_models(cane_pool, "nbh_bass_cane", 1)[0]
            st = t_ms + 8
            en = st + max(95, base.scaled_dur(160))
            add_model(cane_model, st, en, "nbh_bass_cane_snap", eff="Wave", stem="bass")
            placements += 1

    for idx, t_ms in enumerate(kicks):
        if in_blackout(t_ms):
            continue
        spin_models = cycle_models(spinner_pool or sphere_pool, "nbh_kick_spin", 2 if idx % 3 == 0 else 1)
        for step, model in enumerate(spin_models):
            st = t_ms + step * 18
            en = st + max(90, base.scaled_dur(155))
            add_model(model, st, en, "nbh_kick_spinner", eff="Pinwheel", stem="drums")
            placements += 1

    for idx, t_ms in enumerate(snares):
        if in_blackout(t_ms):
            continue
        matrix_hits = cycle_models(matrix_pool or line_pool, "nbh_snare_matrix", 2 if idx % 4 == 0 else 1)
        for step, model in enumerate(matrix_hits):
            st = t_ms + step * 14
            en = st + max(110, base.scaled_dur(180))
            add_model(model, st, en, "nbh_snare_matrix_bars", eff="Bars", stem="drums")
            pixel_track.append((f"NBH_SNARE:{model}", st, en))
            placements += 1

    for idx, t_ms in enumerate(hats):
        if in_blackout(t_ms) or (idx % 3) != 0:
            continue
        line_hits = cycle_models(line_pool or arch_pool, "nbh_hat_line", 1)
        for model in line_hits:
            st = t_ms
            en = st + max(70, base.scaled_dur(120))
            add_model(model, st, en, "nbh_hat_sine", eff="Wave", stem="other")
            placements += 1

    keyboard_events = note_events[::2] if len(note_events) > 220 else note_events
    for idx, event in enumerate(keyboard_events):
        if in_blackout(event.start_ms):
            continue
        dur = max(80, min(event.end_ms - event.start_ms, base.scaled_dur(240)))
        matrix_target = cycle_models(matrix_pool, "nbh_keyboard_matrix", 1)
        arch_target = cycle_models(arch_pool, "nbh_keyboard_arch", 1)
        for model in matrix_target:
            st = event.start_ms
            en = st + dur
            add_model(model, st, en, "nbh_keyboard_matrix_wave", eff="Wave", stem="other")
            keyboard_track.append((f"NBH_KEYS:{model}", st, en))
            placements += 1
        for model in arch_target:
            st = event.start_ms + 22
            en = st + max(75, int(dur * 0.85))
            add_model(model, st, en, "nbh_keyboard_arch_flow", eff="Butterfly", stem="other")
            placements += 1
        if (idx % 5) == 0:
            sparkle = cycle_models(stars_pool, "nbh_keyboard_stars", 1)
            for model in sparkle:
                st = event.start_ms + 12
                en = st + max(65, int(dur * 0.65))
                add_model(model, st, en, "nbh_keyboard_star", eff="Shimmer", stem="other")
                placements += 1

    for i in range(0, max(0, len(bar_ms) - 1), 4):
        st = bar_ms[i]
        en = bar_ms[min(i + 3, len(bar_ms) - 1)]
        if en <= st or in_blackout(st):
            continue
        part = part_for_time(parts, st)
        if part not in dramatic_parts:
            continue
        sweep_pool = choose_cycle_pool(
            [pool for pool in (line_pool, arch_pool, matrix_pool, spinner_pool, tree_pool, cane_pool) if pool is not None and pool.models],
            pool_state,
            "nbh_sweep_pool",
        )
        if sweep_pool is None or not sweep_pool.models:
            continue
        reverse = ((i // 4) % 2) == 1
        add_sweep(
            lambda nm, a, b, label: add_model(nm, a, b, label, eff="Wave", stem="other"),
            sweep_pool,
            st,
            en,
            "nbh_directional_sweep",
            max(78, style.sweep_hit_ms - 18),
            reverse=reverse,
        )
        sweep_track.append((f"NBH_SWEEP_{'R' if reverse else 'L'}", st, en))
        placements += max(1, len(sweep_pool.models))

    for idx, t_ms in enumerate(vocal_peaks):
        if in_blackout(t_ms) or (idx % 2) != 0:
            continue
        targets = cycle_models(talking_pool or stars_pool or matrix_pool, "nbh_vocal", 1)
        for model in targets:
            st = t_ms
            en = st + max(95, base.scaled_dur(160))
            add_model(model, st, en, "nbh_vocal_spotlight", eff="Butterfly", stem="vocals")
            placements += 1

    return placements


def build_all_models_all_effects_sequence(
    *,
    style: VariantStyle,
    template_xsq: Path,
    audio_path: Path,
    out_path: Path,
    tuning: RuntimeTuning,
    catalog: dict | None,
) -> Path:
    """
    Build a deterministic showcase sequence that exercises all available models
    and effect types discovered from xLights capabilities.
    """
    portable_audio = ensure_audio_sidecar(audio_path, out_path)
    xsq = base.load_xsq(template_xsq)
    active_layout_file = resolve_layout_file(template_xsq, tuning.layout_file, Path(".").resolve())
    base.normalize_display_views(xsq.root, force=True)
    if active_layout_file and active_layout_file.exists():
        base.sync_xsq_to_layout(xsq, active_layout_file)
    base.replace_audio_references(xsq.root, portable_audio)
    names = sorted(xsq.elements.keys())
    if not names:
        raise RuntimeError("No models available to build all-effects showcase.")

    template_library = base.build_effect_template_library(xsq.root)
    palette_pool = [tpl.palette for tpl in template_library.values() if tpl.palette]
    if not palette_pool and xsq.on_tpl.palette:
        palette_pool = [xsq.on_tpl.palette]
    effect_names = xfb.catalog_effect_names(catalog)
    if tuning.ac_lights_only:
        ac_only = {"on", "ramp", "strobe", "twinkle", "shimmer"}
        effect_names = [name for name in effect_names if name.strip().lower() in ac_only]
    if not effect_names:
        effect_names = ["On", "Ramp", "Strobe", "Twinkle", "Shimmer"]

    auto_layer_name = f"AUTO_ALL_MODELS_ALL_EFFECTS_{style.version.replace('.', '_')}"
    layers: dict[str, ET.Element] = {}
    for nm, el in xsq.elements.items():
        base.clear_effects(el, "layer", auto_layer_name)
        layers[nm] = base.ensure_layer(el, auto_layer_name)

    rng = random.Random(base.SEED + base.stable_name_seed(style.version + "_all_effects"))
    slot_ms = max(90, int(tuning.min_effect_ms) + 40)
    cursor_by_model: dict[str, int] = {nm: 0 for nm in names}
    touched_models: set[str] = set()
    effect_track: list[tuple[str, int, int]] = []
    max_end = 0

    for idx, effect_name_raw in enumerate(effect_names):
        effect_name = xfb.normalize_effect_name(effect_name_raw, catalog) or "On"
        model = names[idx % len(names)]
        st = cursor_by_model[model]
        en = st + slot_ms + int((idx % 4) * 24)
        fallback_tpl = xsq.ramp_tpl if effect_name.strip().lower() == "ramp" else xsq.on_tpl
        tpl = resolve_effect_template(
            effect_name=effect_name,
            explicit_tpl=None,
            template_library=template_library,
            fallback_tpl=fallback_tpl,
        )
        if palette_pool:
            palette = palette_pool[(idx + rng.randrange(len(palette_pool))) % len(palette_pool)]
            tpl = base.EffectTemplate(settings=tpl.settings, palette=palette)
        base.add_effect(layers[model], st, en, effect_name, tpl)
        cursor_by_model[model] = en + 15
        touched_models.add(model)
        effect_track.append((effect_name, st, en))
        max_end = max(max_end, en)

    for idx, model in enumerate(names):
        if model in touched_models:
            continue
        st = cursor_by_model[model]
        en = st + max(slot_ms, 120)
        tpl = base.EffectTemplate(settings=xsq.on_tpl.settings, palette=palette_pool[idx % len(palette_pool)] if palette_pool else xsq.on_tpl.palette)
        base.add_effect(layers[model], st, en, "On", tpl)
        effect_track.append((f"{model}:On", st, en))
        max_end = max(max_end, en)

    all_models_track = [("ALL_MODELS_GENERIC", 0, max_end if max_end > 0 else slot_ms)]
    if effect_track:
        base.write_timing_track(xsq.root, f"AUTO All Effects {style.version}", effect_track[:2000], active=False)
    base.write_timing_track(xsq.root, f"AUTO All Models {style.version}", all_models_track, active=False)

    payload = {
        "version": style.version,
        "type": "all_models_all_effects_showcase",
        "audio": portable_audio.name,
        "template": template_xsq.name,
        "output": out_path.name,
        "models_count": len(names),
        "effects_count": len(effect_names),
        "effects_used": effect_names,
        "ac_lights_only": bool(tuning.ac_lights_only),
    }
    write_report(report_path(out_path), payload)
    base.normalize_display_views(xsq.root, force=True)
    if active_layout_file and active_layout_file.exists():
        base.sync_xsq_to_layout(xsq, active_layout_file)
    base.ensure_master_view_models(xsq.root)
    try:
        base.indent_xml(xsq.root)
    except Exception:
        pass
    xsq.tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path


def run_variant(
    style: VariantStyle,
    template_xsq: Path,
    audio_path: Path,
    out_path: Path,
    profile: base.UserProfile,
    tuning: RuntimeTuning | None = None,
) -> None:
    tuning = tuning or RuntimeTuning()
    style = apply_runtime_style(style, tuning)
    rng = random.Random(base.SEED + base.stable_name_seed(style.version + audio_path.stem.lower()))
    auto_layer_name = f"AUTO_DreamSequenceWeaver_{style.version.replace('.', '_')}"
    portable_audio = ensure_audio_sidecar(audio_path, out_path)
    active_layout_file = resolve_layout_file(template_xsq, tuning.layout_file, Path(".").resolve())
    if active_layout_file is not None and (tuning.layout_file is None or tuning.layout_file.resolve() != active_layout_file):
        tuning.layout_file = active_layout_file

    log(f"[1/8] Loading template for {style.version}")
    xsq = base.load_xsq(template_xsq)
    normalized_views = base.normalize_display_views(xsq.root, force=True)
    if normalized_views:
        log(f"Display view normalization: updated {normalized_views} rows")
    if active_layout_file and active_layout_file.exists():
        sync_report = base.sync_xsq_to_layout(xsq, active_layout_file)
        log(
            "Layout sync: "
            f"layout_names={sync_report['layout_names']}, "
            f"matched_display={sync_report['display_updated']}, "
            f"matched_effect_rows={sync_report['effect_rows_updated']}, "
            f"stale_removed={sync_report['stale_removed']}"
        )
    elif tuning.layout_file is None:
        log("[WARN] No layout file found. Falling back to template model rows only.")
    replaced = base.replace_audio_references(xsq.root, portable_audio)
    log(f"Audio ref replacements: {replaced}")

    names = sorted(xsq.elements.keys())
    parsed_layout: xmp.ParsedLayout | None = None
    if active_layout_file and active_layout_file.exists():
        try:
            parsed_layout = xmp.parse_layout(active_layout_file)
            parsed_types: dict[str, int] = {}
            for model in parsed_layout.models.values():
                parsed_types[model.type] = parsed_types.get(model.type, 0) + 1
            type_summary = ", ".join(f"{kind}:{count}" for kind, count in sorted(parsed_types.items()))
            pixel_models = sum(1 for model in parsed_layout.models.values() if model.is_pixel_model())
            log(
                "Parsed layout model map: "
                f"models={len(parsed_layout.models)}, groups={len(parsed_layout.groups)}, "
                f"pixel_models={pixel_models}" + (f", types={type_summary}" if type_summary else "")
            )
        except Exception as exc:
            log(f"Layout parser unavailable, falling back to legacy discovery: {exc}")
            parsed_layout = None
    layout = enrich_layout_with_parsed(base.discover_layout(names), names, parsed_layout)
    pools = discover_sequential_pools(names, layout, parsed_layout)
    layout_updates, pool_updates, lane_override = apply_model_overrides(
        layout,
        pools,
        names,
        tuning.model_overrides or {},
    )
    hints = base.inspect_template_hints(xsq, layout)
    if tuning.template_guidance:
        template_profile = build_template_profile(xsq, pools)
        style = apply_template_profile(style, template_profile)
    else:
        template_profile = TemplateProfile(
            category_scores={},
            category_effect_families={},
            discovered_effect_families=[],
        )
        log("Template analysis disabled by runtime option.")
    if layout_updates or pool_updates or lane_override:
        log(
            f"Applied overrides: layout={layout_updates}, pools={pool_updates}, "
            f"keyboard_lane={len(lane_override)}"
        )
    if template_profile.category_scores:
        ranked = sorted(template_profile.category_scores.items(), key=lambda item: (-item[1], item[0]))
        top = ", ".join(f"{category}:{score}" for category, score in ranked[:5])
        families = ", ".join(template_profile.discovered_effect_families[:6])
        log(f"Template profile categories: {top}")
        if families:
            log(f"Template effect families: {families}")
    log(f"Sequential pools found: {len(pools)}")
    for pool in pools:
        log("  - " + detailed_pool_summary(pool))

    layering_mode = normalize_layering_mode(tuning.layering_mode)
    priorities = stem_priority_map(tuning)
    guide_targets = {nm for nm in hints.guide_models if nm}
    auto_layer_names = {
        "base": f"{auto_layer_name}_base",
        "motion": f"{auto_layer_name}_motion",
        "accent": f"{auto_layer_name}_accent",
    }
    auto_layer_name_set = set(auto_layer_names.values())
    auto_layer_name_set.add(auto_layer_name)
    xlights_catalog = xfb.load_or_build_catalog(
        Path(".").resolve(),
        repo_root=tuning.xlights_repo,
        cache_path=tuning.xlights_features_json,
    )
    if xlights_catalog:
        log(f"xLights catalog loaded: effects={xlights_catalog.get('effect_count', 0)}")
    template_library = base.build_effect_template_library(xsq.root)
    template_palette_pool = [tpl.palette for tpl in template_library.values() if tpl.palette]
    if xsq.on_tpl.palette and xsq.on_tpl.palette not in template_palette_pool:
        template_palette_pool.append(xsq.on_tpl.palette)
    enrich_template_library_with_reference_xsqs(
        template_xsq=template_xsq,
        template_library=template_library,
        template_palette_pool=template_palette_pool,
        log_fn=log,
    )
    workspace_history = scan_workspace_preferences(
        template_xsq=template_xsq,
        output_dir=out_path.parent,
        tuning=tuning,
    )
    if not tuning.workspace_history_enabled:
        log("Workspace history: disabled.")
    elif workspace_history.family_effects or workspace_history.palette_pool:
        log(
            "Workspace history loaded: "
            f"families={len(workspace_history.family_effects)}, palettes={len(workspace_history.palette_pool)}"
        )
    else:
        log("Workspace history: no prior XSQ patterns found.")
    existing_windows_by_model: dict[str, list[tuple[int, int]]] = {}
    removed_blips = 0
    for nm, el in xsq.elements.items():
        if layering_mode == "replace":
            clear_mode = "all" if nm in guide_targets else base.CLEAR_MODE
            for auto_name in auto_layer_name_set:
                base.clear_effects(el, clear_mode, auto_name)
        else:
            for auto_name in auto_layer_name_set:
                base.clear_effects(el, "layer", auto_name)
            if layering_mode == "smart_layer":
                existing_windows_by_model[nm] = collect_existing_windows(el, auto_layer_name_set)
        if base.REMOVE_STARTUP_BLIP:
            removed_blips += base.remove_startup_blip(el, base.STARTUP_BLIP_WINDOW_MS)
    if removed_blips:
        log(f"Removed startup blip effects: {removed_blips}")
    log(f"Layering mode: {layering_mode}")

    layers = {
        nm: {
            layer_key: base.ensure_layer(el, layer_name)
            for layer_key, layer_name in auto_layer_names.items()
        }
        for nm, el in xsq.elements.items()
    }
    timelines = {nm: EffectTimeline() for nm in layers}
    cooldowns = base.Cooldowns()
    stats = base.PlacementStats()
    total = 0
    ramp_ok = (xsq.ramp_tpl.settings is not None or xsq.ramp_tpl.palette is not None)
    validation_rejections: list[dict] = []
    used_targets: set[str] = set()
    used_groups: set[str] = set()
    used_root_models: set[str] = set()
    used_submodels: set[str] = set()
    model_category_map: dict[str, str] = {}
    if parsed_layout is not None:
        for nm in names:
            model = parsed_layout.model_for(nm)
            if model is None:
                continue
            family = family_from_parsed_model(model)
            if family:
                model_category_map.setdefault(nm, family)
    for pool in pools:
        for model in pool.models:
            model_category_map[model] = pool.category

    log("[2/8] Analyzing audio and polyphony")
    audio = base.analyze(audio_path)
    song_length_ms = max(1000, int(audio.dur_s * 1000.0))
    harmonic = analyze_harmonic(audio)
    sections = base.detect_sections(audio)
    parts = infer_song_parts(sections)
    if parts:
        log("Song parts: " + ", ".join(f"{part.label}:{part.start_ms/1000:.1f}-{part.end_ms/1000:.1f}s" for part in parts))

    log("[3/8] Reading timing tracks")
    beats_tt = sanitize_template_marks(base.read_timing_track_marks_ms(xsq.root, base.TT_BEATS), song_length_ms)
    bars_tt = sanitize_template_marks(base.read_timing_track_marks_ms(xsq.root, base.TT_BARS), song_length_ms)
    onsets_tt = sanitize_template_marks(base.read_timing_track_marks_ms(xsq.root, base.TT_ONSETS), song_length_ms)
    notes_tt = sanitize_template_marks(base.read_timing_track_marks_ms(xsq.root, base.TT_NOTE_ONSETS), song_length_ms)

    audio_beats = base.compress_times_ms(audio.beat_ms, 40)
    audio_onsets = base.compress_times_ms(audio.onset_ms, base.scaled_gap(28))
    beat_ms = beats_tt if timing_marks_usable(beats_tt, song_length_ms, 5) else audio_beats
    if beats_tt and beat_ms is audio_beats:
        log("Template beats ignored: offset/coverage mismatch; using audio-detected beats.")
    bar_ms = bars_tt if timing_marks_usable(bars_tt, song_length_ms, 5) else base.bar_from_beats(beat_ms, base.BAR_BEATS)
    if bars_tt and bar_ms and bars_tt != bar_ms:
        log("Template bars ignored: offset/coverage mismatch; rebuilding bars from beats.")
    onset_ms = onsets_tt if timing_marks_usable(onsets_tt, song_length_ms, 9) else audio_onsets
    note_onset_ms = notes_tt if timing_marks_usable(notes_tt, song_length_ms, 9) else onset_ms
    event_times_ms = choose_event_times(style, beat_ms, onset_ms, note_onset_ms, bar_ms)

    hats: list[int] = []
    snares: list[int] = []
    kicks: list[int] = []
    for t_ms in onset_ms:
        centroid = base.nearest(audio.times_s, audio.centroid, t_ms / 1000.0)
        if not np.isfinite(centroid):
            continue
        if centroid >= 4500:
            hats.append(t_ms)
        elif centroid >= 2200:
            snares.append(t_ms)
        else:
            kicks.append(t_ms)
    hats = base.compress_times_ms(hats, base.scaled_gap(24))
    snares = base.compress_times_ms(snares, base.scaled_gap(36))
    kicks = base.compress_times_ms(kicks, base.scaled_gap(46))

    vocal_peaks = base.compress_times_ms(
        [base.ms(t) for t in base.peak_times(audio.times_s, audio.vocal01, 0.15, 10)],
        base.scaled_gap(110),
    )
    bass_peaks = base.compress_times_ms(
        [base.ms(t) for t in base.peak_times(audio.times_s, audio.bass01, 0.16, 8)],
        base.scaled_gap(80),
    )
    stem_analysis = ai.build_stem_analysis(
        audio_path=audio_path,
        use_moises=bool(tuning.use_moises),
        api_key=(tuning.moises_api_key or ""),
        cache_dir=Path("RenderCache") / "stems",
        log_fn=log,
    )
    if stem_analysis.bass_peaks_ms:
        bass_peaks = base.compress_times_ms(stem_analysis.bass_peaks_ms, base.scaled_gap(75))
    if stem_analysis.vocal_peaks_ms:
        vocal_peaks = base.compress_times_ms(stem_analysis.vocal_peaks_ms, base.scaled_gap(95))
    if stem_analysis.drum_kicks_ms:
        kicks = base.compress_times_ms(stem_analysis.drum_kicks_ms, base.scaled_gap(44))
    if stem_analysis.drum_snares_ms:
        snares = base.compress_times_ms(stem_analysis.drum_snares_ms, base.scaled_gap(32))
    if stem_analysis.drum_hats_ms:
        hats = base.compress_times_ms(stem_analysis.drum_hats_ms, base.scaled_gap(22))
    energy_peaks, build_lifts, releases = derive_dynamic_marks(audio)
    log(
        "Stem analysis source="
        f"{stem_analysis.source}; bass_peaks={len(bass_peaks)}, vocal_peaks={len(vocal_peaks)}, "
        f"kicks={len(kicks)}, snares={len(snares)}, hats={len(hats)}"
    )

    def _snap_to_grid(t_ms: int, grid: list[int], max_shift: int) -> int:
        if not grid:
            return t_ms
        idx = bisect_left(grid, t_ms)
        candidates: list[int] = []
        if idx > 0:
            candidates.append(grid[idx - 1])
        if idx < len(grid):
            candidates.append(grid[idx])
        if not candidates:
            return t_ms
        best = min(candidates, key=lambda g: abs(g - t_ms))
        return int(best) if abs(best - t_ms) <= max_shift else t_ms

    def _snap_range(
        start_ms: int,
        end_ms: int,
        grid: list[int],
        max_shift_start: int,
        max_shift_end: int,
        min_dur: int,
    ) -> tuple[int, int]:
        st = _snap_to_grid(start_ms, grid, max_shift_start)
        en = _snap_to_grid(end_ms, grid, max_shift_end)
        if en <= st + min_dur:
            en = st + min_dur
        return st, en

    def _select_snap_grid(stem_key: str, layer_key: str) -> tuple[list[int], int]:
        if stem_key == "drums":
            base_shift = 24 if style.family == "v26" else 26
            return (kicks or snares or hats or onset_ms), (base_shift if layer_key == "accent" else base_shift + 10)
        if stem_key == "bass":
            base_shift = 36 if style.family == "v26" else 40
            return (bass_peaks or beat_ms or onset_ms), (base_shift if layer_key == "accent" else base_shift + 12)
        if stem_key == "vocals":
            base_shift = 34 if style.family == "v26" else 38
            return (vocal_peaks or note_onset_ms or onset_ms), (base_shift if layer_key == "accent" else base_shift + 12)
        base_shift = 46 if style.family == "v26" else 50
        return (beat_ms or onset_ms), (base_shift if layer_key == "accent" else base_shift + 15)

    lyric_events: list[ai.LyricEvent] = []
    if tuning.sync_lyrics_heads:
        lyric_events = ai.extract_lyrics_events(
            audio_path=audio_path,
            use_moises=bool(tuning.use_moises),
            api_key=tuning.moises_api_key,
            log_fn=log,
        )
        if lyric_events:
            log(f"Lyric events detected: {len(lyric_events)}")
        else:
            log("Lyric sync requested but no lyric events were detected.")

    note_events = extract_polyphonic_events(audio, harmonic, event_times_ms, sections, parts, style)
    keyboard_style = replace(style, polyphony=max(style.polyphony, 3), piano_echo=True)
    keyboard_event_times = base.compress_times_ms(
        (note_onset_ms[:] if note_onset_ms else event_times_ms[:]),
        max(26, base.scaled_gap(24)),
    )
    keyboard_note_events = extract_polyphonic_events(audio, harmonic, keyboard_event_times, sections, parts, keyboard_style)

    def reject_effect(
        nm: str,
        st_i: int,
        en_i: int,
        eff_name: str,
        layer_key: str,
        reason: str,
    ) -> None:
        if not tuning.debug_validation:
            return
        validation_rejections.append(
            {
                "model": nm,
                "effect": eff_name,
                "layer": layer_key,
                "time_ms": st_i,
                "end_ms": en_i,
                "reason": reason,
            }
        )

    def attempt_place_effect(
        *,
        nm: str,
        layer_key: str,
        start_ms: int,
        end_ms: int,
        effect_name: str,
        template_to_use: base.EffectTemplate,
        stem_priority: int,
    ) -> bool:
        nonlocal total
        duration = end_ms - start_ms
        if duration < max(50, int(tuning.min_effect_ms)):
            reject_effect(nm, start_ms, end_ms, effect_name, layer_key, "duration below minimum threshold")
            return False
        if end_ms <= 0 or start_ms >= song_length_ms:
            reject_effect(nm, start_ms, end_ms, effect_name, layer_key, "effect outside song timing bounds")
            return False
        st_i = max(0, start_ms)
        en_i = min(song_length_ms, end_ms)
        if en_i - st_i < max(50, int(tuning.min_effect_ms)):
            reject_effect(nm, st_i, en_i, effect_name, layer_key, "trimmed duration below minimum threshold")
            return False
        if layering_mode == "smart_layer":
            existing = existing_windows_by_model.get(nm, [])
            if overlaps_window(st_i, en_i, existing):
                reject_effect(nm, st_i, en_i, effect_name, layer_key, "smart-layer blocked by existing template content")
                return False
        timeline = timelines[nm]
        if timeline.would_exceed_layers(st_i, en_i, max(1, int(tuning.max_layers_per_prop))):
            reject_effect(nm, st_i, en_i, effect_name, layer_key, "max concurrent layers reached")
            return False
        overlapping_entries = timeline.overlapping(layer_key, st_i, en_i)
        if overlapping_entries:
            higher_or_equal = [entry for entry in overlapping_entries if entry.priority >= stem_priority]
            if higher_or_equal:
                reject_effect(nm, st_i, en_i, effect_name, layer_key, "same-layer conflict with equal/higher priority effect")
                return False
            for entry in overlapping_entries:
                timeline.remove_entry(layer_key, entry)
                total = max(0, total - 1)

        family = prop_family(nm, model_category_map.get(nm))
        blocked, reason = violates_prop_rules(
            family=family,
            layer=layer_key,
            start_ms=st_i,
            end_ms=en_i,
            effect_name=effect_name,
            settings=template_to_use.settings,
            timeline=timeline,
        )
        if blocked:
            reject_effect(nm, st_i, en_i, effect_name, layer_key, reason)
            return False

        layer_el = layers[nm][layer_key]
        xml_effect = base.add_effect(layer_el, st_i, en_i, effect_name, template_to_use)
        timeline.add(
            layer_key,
            TimelineEntry(
                start=st_i,
                end=en_i,
                effect_name=effect_name,
                priority=stem_priority,
                xml_layer=layer_el,
                xml_effect=xml_effect,
            ),
        )
        used_targets.add(nm)
        if parsed_layout is not None:
            if nm in parsed_layout.groups:
                used_groups.add(nm)
            model = parsed_layout.model_for(nm)
            if model is not None:
                if model.is_submodel:
                    used_submodels.add(model.name)
                    used_root_models.add(model.parent_name or model.name)
                else:
                    used_root_models.add(model.name)
        total += 1
        return True

    def add_model(
        nm: str | None,
        st: int,
        en: int,
        label: str,
        eff: str = "On",
        tpl: base.EffectTemplate | None = None,
        cd_key: str | None = None,
        cd_ms: int = 0,
        stem: str = "other",
    ) -> None:
        if nm is None or nm not in layers:
            return
        st_i = int(st)
        en_i = int(max(st_i + 1, en))
        min_dur = max(1, int(tuning.min_effect_ms))
        if cd_key and not cooldowns.allow(cd_key, st_i):
            reject_effect(nm, st_i, en_i, eff, "cooldown", f"cooldown active for key {cd_key}")
            return
        stem_key = stem if stem in priorities else "other"
        stem_priority = priorities.get(stem_key, priorities["other"])
        layer_key = stem_to_choreo_layer(stem_key, label)
        snap_grid, snap_shift = _select_snap_grid(stem_key, layer_key)
        st_i, en_i = _snap_range(st_i, en_i, snap_grid, snap_shift, snap_shift + 12, min_dur)
        if (en_i - st_i) >= 800 and bar_ms:
            en_i = _snap_to_grid(en_i, bar_ms, 140)
            if en_i <= st_i + min_dur:
                en_i = st_i + min_dur
        family_key = prop_family(nm, model_category_map.get(nm))
        parsed_model = parsed_layout.model_for(nm) if parsed_layout is not None else None
        runtime_effect = pick_runtime_effect(
            requested=eff,
            layer=layer_key,
            family=family_key,
            parsed_model=parsed_model,
            tuning=tuning,
            catalog=xlights_catalog,
            workspace_history=workspace_history,
            fallback=eff if eff else "On",
        )
        fallback_tpl = xsq.ramp_tpl if runtime_effect.strip().lower() == "ramp" else xsq.on_tpl
        template_to_use = resolve_effect_template(
            effect_name=runtime_effect,
            explicit_tpl=tpl,
            template_library=template_library,
            fallback_tpl=fallback_tpl,
        )
        palette_choice = pick_palette_for_effect(
            mode=tuning.palette_mode,
            template_palette=template_to_use.palette,
            template_pool=template_palette_pool,
            history_pool=workspace_history.palette_pool,
            rng=rng,
            effect_index=total,
        )
        if palette_choice and palette_choice != template_to_use.palette:
            template_to_use = base.EffectTemplate(
                settings=template_to_use.settings,
                palette=palette_choice,
            )
        layer_candidates = [layer_key]
        if layer_key == "motion":
            layer_candidates.append("accent")
        attempts: list[tuple[int, int]] = []
        for shift in (0, 50, -50, 100, -100, 150, -150):
            attempts.append((st_i + shift, en_i + shift))
        base_duration = max(1, en_i - st_i)
        for factor in (0.92, 0.84, 0.72):
            dur = max(int(tuning.min_effect_ms), int(round(base_duration * factor)))
            attempts.append((st_i, st_i + dur))
        seen_attempts: set[tuple[str, int, int]] = set()
        for candidate_layer in layer_candidates:
            for cand_st, cand_en in attempts:
                key = (candidate_layer, cand_st, cand_en)
                if key in seen_attempts:
                    continue
                seen_attempts.add(key)
                if attempt_place_effect(
                    nm=nm,
                    layer_key=candidate_layer,
                    start_ms=cand_st,
                    end_ms=cand_en,
                    effect_name=runtime_effect,
                    template_to_use=template_to_use,
                    stem_priority=stem_priority,
                ):
                    stats.bump(label)
                    if cd_key and cd_ms > 0:
                        cooldowns.block(cd_key, st_i, cd_ms)
                    return
        reject_effect(nm, st_i, en_i, runtime_effect, layer_key, "placement skipped after conflict resolution attempts")

    blackout_windows: list[tuple[int, int]] = []
    for part in parts:
        if part.label == "PRECHORUS":
            blackout_windows.append((max(0, part.end_ms - style.drop_blackout_ms[0]), part.end_ms))
        if part.label == "CHORUS":
            blackout_windows.append((part.start_ms, min(part.start_ms + style.drop_blackout_ms[1], part.end_ms)))

    def in_blackout(t_ms: int) -> bool:
        for st, en in blackout_windows:
            if st <= t_ms <= en:
                return True
        return False

    pool_state: dict[str, int] = {}
    piano_track: list[tuple[str, int, int]] = []
    keyboard_track: list[tuple[str, int, int]] = []
    sweep_track: list[tuple[str, int, int]] = []
    lua_track: list[tuple[str, int, int]] = []
    pixel_track: list[tuple[str, int, int]] = []
    part_track: list[tuple[str, int, int]] = [(part.label, part.start_ms, part.end_ms) for part in parts]
    drop_track: list[tuple[str, int, int]] = []
    coords: dict[str, tuple[float, float]] = {}
    reference_poly_xsq = resolve_reference_poly_xsq(template_xsq)
    reference_scale_midis = load_reference_scale_midis(reference_poly_xsq)
    if reference_poly_xsq is not None:
        log(f"Reference poly map: {reference_poly_xsq.name}")
    if parsed_layout is not None:
        coords = parsed_layout.coordinate_map(names)
    elif tuning.layout_file and tuning.layout_file.exists():
        coords = ai.parse_layout_coordinates(tuning.layout_file, names)
    keyboard_routes = adapt_keyboard_routes_for_style(style, build_spatial_keyboard_routes(layout, pools, coords, rng))
    keyboard_lane = build_keyboard_lane_with_routes(pools, override=lane_override, preferred_routes=keyboard_routes)
    arch_keyboard_lane = next((pool.models for pool in pools if pool.category == "arch" and pool.models), [])
    cane_focus = base.clamp(float(tuning.cane_focus), 0.50, 2.50)
    flash_guard = base.clamp(float(tuning.flash_guard), 0.00, 1.00)
    keyboard_mix = base.clamp(float(tuning.keyboard_mix), 0.00, 2.00)
    global_flash_prob = base.clamp(1.0 - flash_guard, 0.05, 1.0)
    family_factor = 1.10 + (0.05 * min(6, len(template_profile.discovered_effect_families)))
    dynamic_random = base.clamp(profile.randomness * family_factor, 0.05, 1.0)
    dramatic_parts = {"CHORUS", "PRECHORUS", "BRIDGE"}
    stem_max = max(1, max(priorities.values()))
    bass_priority_gain = 0.80 + (priorities["bass"] / stem_max) * 0.45
    drums_priority_gain = 0.80 + (priorities["drums"] / stem_max) * 0.45
    vocals_priority_gain = 0.80 + (priorities["vocals"] / stem_max) * 0.45
    other_priority_gain = 0.80 + (priorities["other"] / stem_max) * 0.45
    structured_mode = style.family in {"v14", "v15", "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23"}
    focused_mode = style.family in {"v14", "v16", "v19", "v22", "v23", "v25", "v26", "v27"} or style.placement_mode in {"xtreme_essentials", "xtreme_submodel"}
    premium_mode = style.family in {"v15", "v17", "v20", "v22", "v23", "v25", "v26", "v27"} or style.placement_mode == "xtreme_showcase"
    if structured_mode:
        dynamic_random = min(dynamic_random, 0.12 if focused_mode else 0.18)
        global_flash_prob = min(global_flash_prob, 0.16 if focused_mode else 0.24)

    log("[4/8] Placing effects")
    if ramp_ok:
        for part in parts:
            if part.label in {"PRECHORUS", "BRIDGE"}:
                add_model(
                    layout.house,
                    part.start_ms,
                    part.end_ms,
                    "build_ramp",
                    eff="Ramp",
                    tpl=xsq.ramp_tpl,
                    cd_key="house",
                    cd_ms=100,
                    stem="other",
                )
                add_model(
                    layout.garage,
                    part.start_ms,
                    part.end_ms,
                    "build_ramp",
                    eff="Ramp",
                    tpl=xsq.ramp_tpl,
                    cd_key="garage",
                    cd_ms=100,
                    stem="other",
                )

    bass_focus_pools = pools_by_category(pools, ("canes_combo", "north_canes", "south_canes", "gt", "mega", "line"))
    if premium_mode:
        for i, t_ms in enumerate(bass_peaks):
            part = part_for_time(parts, t_ms)
            dur = max(90, int(base.scaled_dur(220) * bass_priority_gain))
            if part == "CHORUS":
                dur = int(dur * 1.35)
            part_blueprint = intentional_scene_blueprint(part)
            purposeful_bass_pools = [pool for pool in pools if pool.category in (part_blueprint["foundation"] + part_blueprint["rhythm"]) and pool.models]
            if structured_mode and purposeful_bass_pools:
                focus_pool = purposeful_bass_pools[i % len(purposeful_bass_pools)]
            elif bass_focus_pools and rng.random() < dynamic_random:
                focus_pool = rng.choice(bass_focus_pools)
            else:
                focus_pool = bass_focus_pools[i % len(bass_focus_pools)] if bass_focus_pools else None
            if focus_pool and focus_pool.models:
                idx = pool_state.get(f"bass_focus_{focus_pool.name}", 0) % len(focus_pool.models)
                if not structured_mode and rng.random() < dynamic_random:
                    idx = rng.randrange(len(focus_pool.models))
                steps = 1 + (1 if (structured_mode and part in dramatic_parts and len(focus_pool.models) > 2) or (cane_focus >= 1.30 and len(focus_pool.models) > 2) else 0)
                for step in range(steps):
                    model = focus_pool.models[(idx + step) % len(focus_pool.models)]
                    st = t_ms + step * 18 + (0 if structured_mode else base.rng_jitter(rng, dynamic_random * 0.45, 14))
                    en = st + max(70, dur - (step * 18))
                    add_model(model, st, en, "bass_focus", stem="bass")
                pool_state[f"bass_focus_{focus_pool.name}"] = idx + 1
            color_targets: list[tuple[str | None, str, str, int]] = [
                (layout.all_red, "bass_red", "red", 120),
                (layout.all_green, "bass_green", "green", 105),
                (layout.all_white, "bass_white", "white", 95),
            ]
            if style.version == "v7.2":
                target = color_targets[i % len(color_targets)]
                if target[0]:
                    add_model(target[0], t_ms, t_ms + dur, target[1], cd_key=target[2], cd_ms=target[3], stem="bass")
            elif structured_mode:
                target = color_targets[i % len(color_targets)]
                if part == "VERSE" and color_targets[2][0]:
                    target = color_targets[2]
                elif part in {"PRECHORUS", "BRIDGE"} and color_targets[1][0]:
                    target = color_targets[1]
                elif part == "CHORUS" and color_targets[0][0]:
                    target = color_targets[0]
                if target[0] and (part != "VERSE" or (i % 2) == 0):
                    add_model(target[0], t_ms, t_ms + dur, target[1], cd_key=target[2], cd_ms=target[3], stem="bass")
            elif rng.random() < base.clamp(0.58 + bass_priority_gain * 0.25, 0.35, 0.98):
                target = color_targets[0]
                if rng.random() < 0.24 and color_targets[1][0]:
                    target = color_targets[1]
                elif rng.random() < 0.18 and color_targets[2][0]:
                    target = color_targets[2]
                if target[0]:
                    add_model(target[0], t_ms, t_ms + dur, target[1], cd_key=target[2], cd_ms=target[3], stem="bass")
            if not structured_mode and part in dramatic_parts and flash_guard < 0.45 and rng.random() < (global_flash_prob * 0.35):
                add_model(layout.house, t_ms, t_ms + dur, "bass_red", cd_key="house", cd_ms=110, stem="bass")
                add_model(layout.garage, t_ms, t_ms + dur, "bass_red", cd_key="garage", cd_ms=110, stem="bass")

    gt_pool = next((pool for pool in pools if pool.category == "gt"), None)
    if gt_pool and style.placement_mode == "classic":
        gt_index = 0
        for t_ms in sorted(set(kicks + beat_ms[::2])):
            if in_blackout(t_ms):
                continue
            duration = max(75, int(base.scaled_dur(150) * drums_priority_gain))
            model = gt_pool.models[gt_index % len(gt_pool.models)]
            add_model(model, t_ms, t_ms + duration, "gt_bounce", stem="drums")
            gt_index += 1

    if style.placement_mode == "zone_riff":
        place_zone_riff(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "percussion_relay":
        place_percussion_relay(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "scene_morph":
        place_scene_morph(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "director_ai":
        place_director_ai(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            bar_ms=bar_ms,
            kicks=kicks,
            snares=snares,
            hats=hats,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "constellation_story":
        place_constellation_story(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "pinball_relay":
        place_pinball_relay(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "vocal_spotlight":
        place_vocal_spotlight(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            vocal_peaks=vocal_peaks,
            bass_peaks=bass_peaks,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "mirror_duel":
        place_mirror_duel(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "orbital_sweep":
        place_orbital_sweep(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "pulse_matrix":
        place_pulse_matrix(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            bass_peaks=bass_peaks,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "phrase_architect":
        place_phrase_architect(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "stem_storyboard":
        place_stem_storyboard(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "primetime_director":
        place_primetime_director(
            style=style,
            pools=pools,
            layout=layout,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "wave_burst_director":
        place_wave_burst_director(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            beat_ms=beat_ms,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "showcase_arc":
        place_showcase_arc(
            style=style,
            pools=pools,
            layout=layout,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            vocal_peaks=vocal_peaks,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "showcase_stems":
        place_showcase_stems(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "showcase_motion":
        place_showcase_motion(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            beat_ms=beat_ms,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "showcase_signature":
        place_showcase_signature(
            style=style,
            pools=pools,
            layout=layout,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            beat_ms=beat_ms,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "piano_lights":
        place_showcase_signature(
            style=style,
            pools=pools,
            layout=layout,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            beat_ms=beat_ms,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
        place_piano_lights(
            style=style,
            note_events=note_events,
            pools=pools,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            keyboard_track=keyboard_track,
        )
    elif style.placement_mode == "xtreme_essentials":
        place_xtreme_essentials(
            style=style,
            pools=pools,
            layout=layout,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            vocal_peaks=vocal_peaks,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "xtreme_submodel":
        place_xtreme_submodel(
            style=style,
            pools=pools,
            layout=layout,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            beat_ms=beat_ms,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "xtreme_showcase":
        place_xtreme_showcase(
            style=style,
            pools=pools,
            layout=layout,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            beat_ms=beat_ms,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    elif style.placement_mode == "hierarchy_roles":
        place_hierarchy_roles(
            style=style,
            pools=pools,
            layout=layout,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            beat_ms=beat_ms,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            piano_track=piano_track,
            sweep_track=sweep_track,
        )
    else:
        for idx, event in enumerate(note_events):
            if in_blackout(event.start_ms):
                continue
            pool = choose_pool(style, pools, event.part, idx, rng)
            targets = map_notes_to_models(pool, event, pool_state, style, rng)
            duration = max(50, min(event.end_ms - event.start_ms, base.scaled_dur(260)))
            _placed, phrase_end = place_note_phrase(
                add_model,
                pool,
                event,
                targets,
                style,
                rng,
                ramp_ok,
                xsq.ramp_tpl,
            )
            if style.piano_echo and event.part in {"CHORUS", "PRECHORUS"} and len(targets) >= 1:
                echo_pool = choose_pool(style, pools, "CHORUS", idx + 1, rng)
                if echo_pool.name != pool.name:
                    echo_targets = map_notes_to_models(echo_pool, event, pool_state, style, rng)
                    echo_start = event.start_ms + 70
                    echo_end = echo_start + max(65, duration - 10)
                    for model in echo_targets[:2]:
                        add_model(
                            model,
                            echo_start,
                            echo_end,
                            "digital_piano_echo",
                            eff="Ramp" if ramp_ok and echo_pool.category in {"arch", "line", "mega"} else "On",
                            tpl=xsq.ramp_tpl if ramp_ok and echo_pool.category in {"arch", "line", "mega"} else None,
                        )
                    phrase_end = max(phrase_end, echo_end)
            piano_track.append((f"{pool.name}:{note_label(event.notes)}", event.start_ms, phrase_end))

        sweep_pools = pools_by_category(pools, style.sweep_categories)
        if bar_ms and sweep_pools:
            for i in range(len(bar_ms) - 1):
                st = bar_ms[i]
                en = bar_ms[i + 1]
                part = part_for_time(parts, st)
                if part in {"INTRO", "OUTRO"} and style.family == "v2":
                    continue
                if part == "VERSE" and i % 2 == 1:
                    continue
                if part == "CHORUS" or (style.section_emphasis and part in {"PRECHORUS", "BRIDGE"}):
                    pool = sweep_pools[i % len(sweep_pools)]
                    add_sweep(
                        lambda nm, a, b, label: add_model(nm, a, b, label),
                        pool,
                        st,
                        en,
                        "sequential_sweep",
                        style.sweep_hit_ms,
                        reverse=((i % 2) == 1),
                    )
                    sweep_track.append((pool.name, st, en))

    if premium_mode:
        wave_marks = base.compress_times_ms(sorted(set(build_lifts + energy_peaks[::2])), base.scaled_gap(120))
        if wave_marks:
            place_intensity_waves(
                style=style,
                pools=pools,
                parts=parts,
                note_events=note_events,
                energy_marks=wave_marks,
                pool_state=pool_state,
                rng=rng,
                add_model=add_model,
                in_blackout=in_blackout,
                sweep_track=sweep_track,
            )

    spatial_keyboard_mix = base.clamp((0.82 if focused_mode else max(0.62, keyboard_mix)) * other_priority_gain, 0.0, 2.0)
    if style.family == "v19":
        spatial_keyboard_mix = max(spatial_keyboard_mix, 1.18)
    elif style.family == "v20":
        spatial_keyboard_mix = max(spatial_keyboard_mix, 1.06)
    elif style.family == "v22":
        cap = 0.36 if style.placement_mode == "showcase_stems" else 0.48 if style.placement_mode == "showcase_arc" else 0.54
        spatial_keyboard_mix = min(spatial_keyboard_mix, cap)
    elif style.family == "v23":
        cap = 0.24 if style.placement_mode == "showcase_stems" else 0.34 if style.placement_mode == "showcase_arc" else 0.38
        spatial_keyboard_mix = min(spatial_keyboard_mix, cap)

    spatial_keyboard_placed = place_spatial_keyboard_routes(
        style=keyboard_style,
        note_events=keyboard_note_events,
        routes=keyboard_routes,
        reference_scale_midis=reference_scale_midis,
        keyboard_mix=spatial_keyboard_mix,
        ramp_ok=ramp_ok,
        ramp_tpl=xsq.ramp_tpl,
        add_model=add_model,
        in_blackout=in_blackout,
        keyboard_track=keyboard_track,
    )
    if spatial_keyboard_placed:
        log(f"Spatial keyboard routes placed: {spatial_keyboard_placed} effects across {len(keyboard_routes)} lanes")

    if style.keyboard_overlay and keyboard_lane:
        effective_keyboard_mix = keyboard_mix
        if premium_mode:
            effective_keyboard_mix = min(effective_keyboard_mix, 0.34)
        if style.family == "v19":
            effective_keyboard_mix = min(effective_keyboard_mix, 0.24)
        elif style.family == "v20":
            effective_keyboard_mix = min(effective_keyboard_mix, 0.30)
        elif style.family == "v22":
            effective_keyboard_mix = min(effective_keyboard_mix, 0.16 if style.placement_mode == "showcase_stems" else 0.22)
        elif style.family == "v23":
            effective_keyboard_mix = min(effective_keyboard_mix, 0.10 if style.placement_mode == "showcase_stems" else 0.16)
        place_polyphonic_keyboard(
            style=style,
            note_events=keyboard_note_events,
            keyboard_lane=keyboard_lane,
            arch_lane=arch_keyboard_lane,
            keyboard_mix=base.clamp((0.26 if style.family == "v23" else 0.38 if style.family == "v22" else 0.52 if focused_mode else effective_keyboard_mix) * other_priority_gain, 0.0, 2.0),
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            add_model=add_model,
            in_blackout=in_blackout,
            keyboard_track=keyboard_track,
        )

    if layout.all_green and hints.green_has_vu and not structured_mode:
        vu_targets = gt_pool.models if gt_pool else []
        vu_windows = base.build_vu_windows(audio, profile.density, profile.darkness, max(1, len(vu_targets)))
        for st, en, bars in vu_windows:
            if in_blackout(st):
                continue
            if flash_guard < 0.35 and part_for_time(parts, st) in dramatic_parts:
                add_model(layout.all_green, st, en, "green_vu", cd_key="green_all", cd_ms=70, stem="drums")
            for model in vu_targets[:bars]:
                add_model(model, st, en, "green_vu", stem="drums")

    vocal_focus_pools = pools_by_category(pools, ("stars", "snowflakes", "line", "arch", "talking_heads"))
    if premium_mode:
        for i, t_ms in enumerate(vocal_peaks):
            part = part_for_time(parts, t_ms)
            dur = max(80, int(base.scaled_dur(170) * vocals_priority_gain))
            part_blueprint = intentional_scene_blueprint(part)
            purposeful_vocal_pools = [pool for pool in pools if pool.category in (part_blueprint["lead"] + part_blueprint["accent"]) and pool.models]
            if structured_mode and purposeful_vocal_pools:
                vocal_pool = purposeful_vocal_pools[i % len(purposeful_vocal_pools)]
            elif vocal_focus_pools and rng.random() < dynamic_random:
                vocal_pool = rng.choice(vocal_focus_pools)
            else:
                vocal_pool = vocal_focus_pools[i % len(vocal_focus_pools)] if vocal_focus_pools else None
            if vocal_pool and vocal_pool.models:
                v_idx = pool_state.get(f"vocal_focus_{vocal_pool.name}", 0) % len(vocal_pool.models)
                if not structured_mode and rng.random() < dynamic_random:
                    v_idx = rng.randrange(len(vocal_pool.models))
                st = t_ms + (0 if structured_mode else base.rng_jitter(rng, dynamic_random * 0.50, 16))
                add_model(
                    vocal_pool.models[v_idx],
                    st,
                    st + dur,
                    "white_vocal_focus",
                    eff="Wave" if structured_mode and vocal_pool.category in {"matrix", "line", "mega"} and part in dramatic_parts else "On",
                    stem="vocals",
                )
                pool_state[f"vocal_focus_{vocal_pool.name}"] = v_idx + 1
            if not structured_mode and part in dramatic_parts and flash_guard < 0.55 and rng.random() < (global_flash_prob * 0.25):
                add_model(layout.all_white, t_ms, t_ms + dur, "white_vocal", cd_key="white", cd_ms=100, stem="vocals")

    lyric_track: list[tuple[str, int, int]] = []
    if tuning.sync_lyrics_heads and lyric_events:
        lyric_targets_pool = next((pool for pool in pools if pool.category == "talking_heads" and pool.models), None)
        lyric_text_pool = next((pool for pool in pools if pool.category == "matrix" and pool.models), None)
        lyric_text_targets = lyric_text_pool.models if lyric_text_pool else []
        text_template_source = template_library.get("text")
        lyric_targets = lyric_targets_pool.models if lyric_targets_pool else discover_talking_heads(names)
        if lyric_targets:
            for idx, ev in enumerate(lyric_events):
                st = max(0, int(ev.start_ms))
                en = max(st + 80, int(ev.end_ms))
                if in_blackout(st):
                    continue
                target = lyric_targets[idx % len(lyric_targets)]
                text = ev.text.strip()
                if not text:
                    continue
                syllables = max(1, min(7, len(re.findall(r"[aeiouy]+", text.lower()))))
                mouth_step = max(55, int((en - st) / syllables))
                for hit in range(syllables):
                    hit_st = st + hit * mouth_step
                    hit_en = min(en, hit_st + max(45, int(mouth_step * 0.72)))
                    add_model(target, hit_st, hit_en, "lyric_mouth_sync", stem="vocals")
                if lyric_text_targets and (idx % 2) == 0:
                    text_target = lyric_text_targets[idx % len(lyric_text_targets)]
                    text_tpl = text_template_with_phrase(base_template=text_template_source, phrase=text)
                    add_model(
                        text_target,
                        st,
                        min(en + 140, st + max(150, base.scaled_dur(280))),
                        "lyric_text_pixel",
                        eff="Text",
                        tpl=text_tpl,
                        stem="vocals",
                    )
                lyric_track.append((text[:36], st, en))
            log(f"Lyric prop sync events placed: {len(lyric_track)}")
        else:
            log("Lyric sync requested but no head/lyric props were discovered.")

    spatial_track: list[tuple[str, int, int]] = []
    if not structured_mode:
        spatial_spans, spatial_count = apply_spatial_chase(
            style=style,
            pools=pools,
            parts=parts,
            beat_ms=beat_ms,
            kicks=kicks,
            add_model=add_model,
            ramp_ok=ramp_ok,
            ramp_tpl=xsq.ramp_tpl,
            in_blackout=in_blackout,
            tuning=tuning,
            names=names,
            rng=rng,
            log_fn=log,
        )
        if spatial_spans:
            spatial_track.extend(spatial_spans)
        if spatial_count:
            log(f"Spatial chase placements added: {spatial_count}")

    if premium_mode:
        lua_spans, lua_count = apply_lua_style_macros(
            style=style,
            pools=pools,
            parts=parts,
            bar_ms=bar_ms,
            pool_state=pool_state,
            add_model=add_model,
            in_blackout=in_blackout,
            log_fn=log,
        )
        if lua_spans:
            lua_track.extend(lua_spans)
        if lua_count:
            log(f"Lua-style accent placements added: {lua_count}")

    if tuning.pixel_reactive and style.family in {"v20", "v21", "v22", "v23", "v24", "v25", "v26", "v27"}:
        pixel_attempts = place_pixel_reactive_score(
            style=style,
            pools=pools,
            parts=parts,
            note_events=note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            build_lifts=build_lifts,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            add_model=add_model,
            in_blackout=in_blackout,
            pixel_track=pixel_track,
        )
        if pixel_attempts:
            log(f"Pixel reactive score cues scheduled: {pixel_attempts}")

    if style.family in {"v19", "v20", "v21", "v22", "v23", "v24", "v25", "v26", "v27"}:
        neighbor_attempts = apply_neighbor_showcase_score(
            style=style,
            pools=pools,
            parts=parts,
            note_events=keyboard_note_events,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            bar_ms=bar_ms,
            pool_state=pool_state,
            rng=rng,
            add_model=add_model,
            in_blackout=in_blackout,
            keyboard_track=keyboard_track,
            pixel_track=pixel_track,
            sweep_track=sweep_track,
        )
        if neighbor_attempts:
            log(f"Neighbor showcase placements added: {neighbor_attempts}")

    for part in parts:
        if part.label == "CHORUS":
            drop_track.append(("Drop", part.start_ms, min(part.start_ms + 500, part.end_ms)))
            drop_pool = choose_cycle_pool(
                pools_by_category(pools, ("canes_combo", "arch", "line", "gt", "mega")),
                pool_state,
                "drop_focus",
            )
            if drop_pool and len(drop_pool.models) >= 2:
                add_sweep(
                    lambda nm, a, b, label: add_model(nm, a, b, label, stem="drums"),
                    drop_pool,
                    part.start_ms,
                    min(part.end_ms, part.start_ms + max(220, base.scaled_dur(340))),
                    "drop_focus",
                    max(95, style.sweep_hit_ms),
                    reverse=bool((part.start_ms // 1000) % 2),
                )
            elif drop_pool and drop_pool.models:
                add_model(drop_pool.models[0], part.start_ms, min(part.end_ms, part.start_ms + 280), "drop_focus", stem="drums")
            if rng.random() < (0.85 * max(0.35, global_flash_prob)):
                add_model(
                    layout.all_white,
                    part.start_ms,
                    min(part.end_ms, part.start_ms + 220),
                    "drop_flash",
                    cd_key="white",
                    cd_ms=80,
                    stem="drums",
                )
            if rng.random() < (0.95 * max(0.45, global_flash_prob)):
                add_model(
                    layout.all_red,
                    part.start_ms,
                    min(part.end_ms, part.start_ms + 240),
                    "drop_flash",
                    cd_key="red",
                    cd_ms=80,
                    stem="bass",
                )

    if parsed_layout is not None and style.family in {"v20", "v21", "v22", "v23"}:
        coverage_models: list[str] = []
        for model in parsed_layout.models.values():
            if model.is_submodel:
                continue
            if model.name not in layers:
                continue
            if model.name in used_root_models:
                continue
            family_key = family_from_parsed_model(model) or model_category_map.get(model.name, "")
            if not family_key:
                continue
            coverage_models.append(model.name)
        if coverage_models:
            coverage_window_ms = max(3600, min(12000, max(4800, song_length_ms // 5)))
            coverage_start_ms = max(0, song_length_ms - coverage_window_ms)
            slots = max(1, min(len(coverage_models), 48))
            slot_step_ms = max(70, coverage_window_ms // slots)
            coverage_track: list[tuple[str, int, int]] = []
            for idx, model_name in enumerate(coverage_models):
                slot_idx = idx % slots
                cycle_idx = idx // slots
                start_ms = coverage_start_ms + slot_idx * slot_step_ms + cycle_idx * 16
                end_ms = min(song_length_ms, start_ms + max(95, base.scaled_dur(140)))
                add_model(model_name, start_ms, end_ms, "coverage_footer", stem="other")
                coverage_track.append((model_name, start_ms, end_ms))
            if coverage_track:
                keyboard_track.extend(coverage_track[:256])
                log(f"Coverage footer placements attempted: {len(coverage_track)}")

    validation_fixes, validation_issues = validate_sequence_timelines(
        timelines,
        min_effect_ms=max(50, int(tuning.min_effect_ms)),
    )
    if validation_fixes:
        log(f"Validation auto-fixes applied: {validation_fixes}")
    if validation_issues and tuning.debug_validation:
        for issue in validation_issues[:12]:
            log(f"Validation note: {issue}")
        if len(validation_issues) > 12:
            log(f"Validation note: +{len(validation_issues) - 12} more")

    log("[5/8] Writing timing tracks and report")
    if tuning.auto_timing_tracks:
        write_auto_timing_tracks(
            style=style,
            xsq_root=xsq.root,
            song_length_ms=song_length_ms,
            beat_ms=beat_ms,
            bar_ms=bar_ms,
            onset_ms=onset_ms,
            note_onset_ms=note_onset_ms,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            energy_peaks=energy_peaks,
            build_lifts=build_lifts,
            releases=releases,
            sections=sections,
            parts=parts,
            blackout_windows=blackout_windows,
        )
    if part_track:
        base.write_timing_track(xsq.root, f"AUTO Song Parts {style.version}", part_track, active=False)
    if piano_track:
        base.write_timing_track(xsq.root, f"AUTO Piano {style.version}", piano_track, active=False)
    if keyboard_track:
        base.write_timing_track(xsq.root, f"AUTO Keyboard {style.version}", keyboard_track, active=False)
    if sweep_track:
        base.write_timing_track(xsq.root, f"AUTO Sweeps {style.version}", sweep_track, active=False)
    if lua_track:
        base.write_timing_track(xsq.root, f"AUTO Lua Macros {style.version}", lua_track, active=False)
    if pixel_track:
        base.write_timing_track(xsq.root, f"AUTO Pixel Score {style.version}", pixel_track[:2000], active=False)
    if spatial_track:
        base.write_timing_track(xsq.root, f"AUTO Spatial Chase {style.version}", spatial_track, active=False)
    if lyric_track:
        base.write_timing_track(xsq.root, f"AUTO Lyrics {style.version}", lyric_track, active=False)
    if drop_track:
        base.write_timing_track(xsq.root, f"AUTO Drops {style.version}", drop_track, active=False)

    legacy_removed = base.remove_legacy_timing_tracks(xsq.root, current_version=style.version)
    if legacy_removed:
        log(f"Timing cleanup: removed {legacy_removed} legacy timing rows.")

    removed_tracks = base.prune_empty_timing_tracks(
        xsq.root,
        keep_prefixes=(
            f"AUTO QM {style.version}",
            f"AUTO Song Parts {style.version}",
            f"AUTO Piano {style.version}",
            f"AUTO Keyboard {style.version}",
            f"AUTO Sweeps {style.version}",
            f"AUTO Lua Macros {style.version}",
            f"AUTO Pixel Score {style.version}",
            f"AUTO Spatial Chase {style.version}",
            f"AUTO Lyrics {style.version}",
            f"AUTO Drops {style.version}",
            f"AUTO All Effects {style.version}",
            f"AUTO All Models {style.version}",
        ),
    )
    if removed_tracks:
        log(f"Timing cleanup: removed {removed_tracks} empty legacy timing rows.")

    layout_manifest_hash = _layout_manifest_hash(parsed_layout)
    watermark_signature = build_watermark_signature(
        style=style,
        audio_path=audio_path,
        template_xsq=template_xsq,
        out_path=out_path,
        song_length_ms=song_length_ms,
        root_model_count=len(parsed_layout.root_models()) if parsed_layout is not None else len(names),
        layout_manifest_hash=layout_manifest_hash,
    )
    watermark_track = build_watermark_track(watermark_signature, song_length_ms)
    if watermark_track:
        base.write_timing_track(
            xsq.root,
            f"AUTO Dream Signature {style.version}",
            watermark_track,
            active=False,
        )

    available_family_counts: dict[str, int] = {}
    used_family_counts: dict[str, int] = {}
    if parsed_layout is not None:
        available_counter: Counter[str] = Counter()
        used_counter: Counter[str] = Counter()
        for model in parsed_layout.models.values():
            if model.is_submodel:
                continue
            family_key = family_from_parsed_model(model)
            if family_key:
                available_counter[family_key] += 1
        for name in sorted(used_root_models):
            model = parsed_layout.model_for(name)
            if model is None:
                continue
            family_key = family_from_parsed_model(model) or model_category_map.get(name, "")
            if family_key:
                used_counter[family_key] += 1
        available_family_counts = {key: value for key, value in sorted(available_counter.items(), key=lambda item: item[0])}
        used_family_counts = {key: value for key, value in sorted(used_counter.items(), key=lambda item: item[0])}

    payload = {
        "version": style.version,
        "title": style.title,
        "placement_mode": style.placement_mode,
        "audio": audio_path.name,
        "duration_seconds": round(float(audio.dur_s), 3),
        "template": template_xsq.name,
        "output": out_path.name,
        "profile": {
            "feel": profile.feel,
            "density": profile.density,
            "speed": profile.speed,
            "randomness": profile.randomness,
            "bass_bias": profile.bass_bias,
            "melody_density": profile.melody_density,
            "darkness": profile.darkness,
        },
        "runtime_tuning": {
            "polyphony": style.polyphony,
            "cane_focus": cane_focus,
            "flash_guard": flash_guard,
            "keyboard_mix": keyboard_mix,
            "layering_mode": layering_mode,
            "stem_priorities": priorities,
            "max_layers_per_prop": int(tuning.max_layers_per_prop),
            "min_effect_ms": int(tuning.min_effect_ms),
            "sync_lyrics_heads": bool(tuning.sync_lyrics_heads),
            "spatial_awareness": float(tuning.spatial_awareness),
            "chase_style": normalize_chase_style(tuning.chase_style),
            "strict_xlights_effects": bool(tuning.strict_xlights_effects),
            "pixel_reactive": bool(tuning.pixel_reactive),
            "ac_lights_only": bool(tuning.ac_lights_only),
            "base_effect": str(tuning.base_effect),
            "motion_effect": str(tuning.motion_effect),
            "accent_effect": str(tuning.accent_effect),
            "palette_mode": normalize_palette_mode(tuning.palette_mode),
            "auto_timing_tracks": bool(tuning.auto_timing_tracks),
            "workspace_history_enabled": bool(tuning.workspace_history_enabled),
            "workspace_history_limit": int(tuning.workspace_history_limit),
            "workspace_history_folder": str(tuning.workspace_history_folder) if tuning.workspace_history_folder else "",
            "model_override_keys": sorted((tuning.model_overrides or {}).keys()),
        },
        "xlights_catalog": {
            "effect_count": int(xlights_catalog.get("effect_count", 0)) if xlights_catalog else 0,
            "source_repo": xlights_catalog.get("source_repo", "") if xlights_catalog else "",
        },
        "stem_analysis": {
            "source": stem_analysis.source,
            "available_stems": sorted(stem_analysis.stems.keys()),
            "bass_peaks": len(bass_peaks),
            "vocal_peaks": len(vocal_peaks),
            "kicks": len(kicks),
            "snares": len(snares),
            "hats": len(hats),
        },
        "lyrics": {
            "count": len(lyric_events),
            "synced_track_events": len(lyric_track),
        },
        "template_profile": {
            "category_scores": template_profile.category_scores,
            "category_effect_families": template_profile.category_effect_families,
            "discovered_effect_families": template_profile.discovered_effect_families,
        },
        "workspace_history": {
            "families": {key: values[:6] for key, values in workspace_history.family_effects.items()},
            "palette_pool_count": len(workspace_history.palette_pool),
            "palette_pool_preview": workspace_history.palette_pool[:24],
        },
        "parsed_layout": {
            "model_count": len(parsed_layout.models) if parsed_layout is not None else 0,
            "root_model_count": len(parsed_layout.root_models()) if parsed_layout is not None else 0,
            "submodel_count": len(parsed_layout.submodel_names()) if parsed_layout is not None else 0,
            "group_count": len(parsed_layout.groups) if parsed_layout is not None else 0,
            "multi_node_models": sum(1 for model in parsed_layout.models.values() if (not model.is_submodel) and model.is_pixel_model()) if parsed_layout is not None else 0,
            "rgb_models": sum(1 for model in parsed_layout.models.values() if (not model.is_submodel) and model.is_rgb_capable()) if parsed_layout is not None else 0,
            "virtual_region_count": (
                sum(len(model.virtual_regions()) for model in parsed_layout.models.values() if not model.is_submodel)
                if parsed_layout is not None
                else 0
            ),
            "available_family_count": len(available_family_counts),
            "available_families": available_family_counts,
            "type_counts": (
                {
                    key: value
                    for key, value in sorted(
                        Counter(model.type for model in parsed_layout.models.values()).items(),
                        key=lambda item: item[0],
                    )
                }
                if parsed_layout is not None
                else {}
            ),
        },
        "used_targets": {
            "total": len(used_targets),
            "groups": len(used_groups),
            "root_models": len(used_root_models),
            "submodels": len(used_submodels),
            "family_count": len(used_family_counts),
            "families": used_family_counts,
            "preview": sorted(used_targets)[:30],
        },
        "pools": [{"name": pool.name, "category": pool.category, "count": len(pool.models)} for pool in pools],
        "keyboard_lane_count": len(keyboard_lane),
        "parts": [{"label": part.label, "start_ms": part.start_ms, "end_ms": part.end_ms} for part in parts],
        "placements": stats.counts,
        "lua_macro_events": len(lua_track),
        "effects_total": total,
        "validation": {
            "auto_fixes": validation_fixes,
            "issues": validation_issues[:200],
            "rejected_effects_count": len(validation_rejections),
            "rejected_effects": validation_rejections[:500],
        },
        "watermark": {
            "version": WATERMARK_POLICY_VERSION,
            "signature": watermark_signature,
            "signature_short": watermark_signature[:16],
            "layout_manifest_hash": layout_manifest_hash,
            "track_marks": len(watermark_track),
        },
    }
    payload["quality"] = compute_quality_score(payload)
    write_report(report_path(out_path), payload)
    write_sequence_notes(notes_path(out_path), payload)

    log("[6/8] Writing sequence")
    base.normalize_display_views(xsq.root, force=True)
    if active_layout_file and active_layout_file.exists():
        final_sync = base.sync_xsq_to_layout(xsq, active_layout_file)
        log(
            "Final layout sync: "
            f"layout_names={final_sync['layout_names']}, "
            f"matched_display={final_sync['display_updated']}, "
            f"matched_effect_rows={final_sync['effect_rows_updated']}, "
            f"stale_removed={final_sync['stale_removed']}"
        )
    master_report = base.ensure_master_view_models(xsq.root)
    if master_report["display_added"] or master_report["effects_added"] or master_report["rows_touched"]:
        log(
            "Master View fixup: "
            f"display_added={master_report['display_added']}, "
            f"effects_added={master_report['effects_added']}, "
            f"rows_touched={master_report['rows_touched']}"
        )
    try:
        base.indent_xml(xsq.root)
    except Exception:
        pass
    xsq.tree.write(out_path, encoding="utf-8", xml_declaration=True)

    if GENERATE_SHOWCASE:
        showcase_path = out_path.with_name(f"{out_path.stem}.showcase.xsq")
        try:
            log("[7/8] Building final all-models/all-effects output")
            build_all_models_all_effects_sequence(
                style=style,
                template_xsq=out_path,
                audio_path=audio_path,
                out_path=showcase_path,
                tuning=tuning,
                catalog=xlights_catalog,
            )
            log(f"Showcase output saved: {showcase_path.name}")
        except Exception as exc:
            log(f"Final all-models generation skipped: {exc!r}")

    log(f"[8/8] Saved: {out_path.name} | effects added: {total}")
    log(f"Placement report: {stats.summary()}")
    log(
        "Quality score: "
        f"{payload['quality'].get('score', '')} "
        f"({payload['quality'].get('grade', '')})"
    )
    log(f"Report saved: {report_path(out_path).name}")


def parse_args(style: VariantStyle, argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"Dream Sequence Weaver xLights sequencer {style.version} - {style.title}")
    parser.add_argument("--template", help="Path to template .xsq")
    parser.add_argument("--audio", nargs="*", help="Optional audio file(s) to process")
    parser.add_argument("--single", action="store_true", help="Process only the first audio file")
    parser.add_argument("--feel", choices=sorted(base.FEEL_PRESETS.keys()))
    parser.add_argument("--density", type=float)
    parser.add_argument("--speed", type=float)
    parser.add_argument("--randomness", type=float)
    parser.add_argument("--bass-bias", type=float, dest="bass_bias")
    parser.add_argument("--melody-density", type=float, dest="melody_density")
    parser.add_argument("--darkness", type=float)
    parser.add_argument("--polyphony", type=int, help="Override polyphony depth (1-8)")
    parser.add_argument("--cane-focus", type=float, dest="cane_focus", help="Prioritize canes/note-like lanes")
    parser.add_argument("--flash-guard", type=float, dest="flash_guard", help="Reduce all-house/all-group flash behavior")
    parser.add_argument("--keyboard-mix", type=float, dest="keyboard_mix", help="Polyphonic keyboard intensity")
    parser.add_argument("--model-overrides-file", dest="model_overrides_file", help="Optional JSON file for group/model mapping overrides")
    parser.add_argument("--layout-file", dest="layout_file", help="xLights layout XML/XBKP for spatial routing")
    parser.add_argument("--use-moises", action="store_true", help="Use Moises stem separation when possible")
    parser.add_argument("--moises-api-key", dest="moises_api_key", help="Moises API key")
    parser.add_argument("--sync-lyrics-heads", action="store_true", help="Sync lyric timing to head/face props")
    parser.add_argument("--template-guidance", dest="template_guidance", action="store_true", help="Analyze the selected template to guide effect-family choices")
    parser.add_argument("--no-template-guidance", dest="template_guidance", action="store_false", help="Disable template-guided effect analysis")
    parser.add_argument("--spatial-awareness", type=float, dest="spatial_awareness", help="0.0-1.0 spatial chase intensity")
    parser.add_argument("--chase-style", dest="chase_style", help="none/left_to_right/radial_out/group_to_group/random_walk/wave")
    parser.add_argument("--layering-mode", dest="layering_mode", help="replace/overlay_blend/smart_layer/additive")
    parser.add_argument("--layer-priority-vocals", type=int, dest="layer_priority_vocals", help="Stem priority weight for vocals")
    parser.add_argument("--layer-priority-drums", type=int, dest="layer_priority_drums", help="Stem priority weight for drums")
    parser.add_argument("--layer-priority-bass", type=int, dest="layer_priority_bass", help="Stem priority weight for bass")
    parser.add_argument("--layer-priority-other", type=int, dest="layer_priority_other", help="Stem priority weight for other")
    parser.add_argument("--xlights-repo", dest="xlights_repo", help="Optional local xLights source repo root")
    parser.add_argument("--xlights-features-json", dest="xlights_features_json", help="Optional xLights feature catalog JSON path")
    parser.add_argument("--strict-xlights-effects", dest="strict_xlights_effects", action="store_true", help="Allow only effect names known to xLights catalog")
    parser.add_argument("--allow-unknown-effects", dest="strict_xlights_effects", action="store_false", help="Allow non-catalog effect names")
    parser.add_argument("--base-effect", dest="base_effect", help="Preferred effect name for base layer")
    parser.add_argument("--motion-effect", dest="motion_effect", help="Preferred effect name for motion layer")
    parser.add_argument("--accent-effect", dest="accent_effect", help="Preferred effect name for accent layer")
    parser.add_argument("--max-layers-per-prop", type=int, dest="max_layers_per_prop", help="Maximum concurrent choreography layers per prop")
    parser.add_argument("--min-effect-ms", type=int, dest="min_effect_ms", help="Minimum effect duration in milliseconds")
    parser.add_argument("--debug-validation", dest="debug_validation", action="store_true", help="Log rejected effect placement attempts")
    parser.add_argument("--no-debug-validation", dest="debug_validation", action="store_false", help="Disable rejected placement logs")
    parser.add_argument("--ac-lights-only", dest="ac_lights_only", action="store_true", help="Restrict to AC-safe dumb-light effects")
    parser.add_argument(
        "--palette-mode",
        dest="palette_mode",
        help="template/christmas/warm/cool/neon/random/workspace_match",
    )
    parser.add_argument(
        "--workspace-history-folder",
        dest="workspace_history_folder",
        help="Optional local folder of finished XSQ files to scan for palette/effect history",
    )
    parser.add_argument("--workspace-history-limit", type=int, dest="workspace_history_limit", help="Max recent XSQ files to scan from workspace history")
    parser.add_argument("--workspace-history", dest="workspace_history_enabled", action="store_true", help="Enable local XSQ history scanning")
    parser.add_argument("--no-workspace-history", dest="workspace_history_enabled", action="store_false", help="Disable local XSQ history scanning")
    parser.add_argument("--auto-timing-tracks", dest="auto_timing_tracks", action="store_true", help="Write extended Queen Mary style timing tracks")
    parser.add_argument("--no-auto-timing-tracks", dest="auto_timing_tracks", action="store_false", help="Disable extended timing-track output")
    parser.add_argument("--pixel-reactive", dest="pixel_reactive", action="store_true", help="Enable family-aware reactive pixel choreography for compatible models")
    parser.add_argument("--no-pixel-reactive", dest="pixel_reactive", action="store_false", help="Disable the reactive pixel choreography pass")
    parser.add_argument("--settings", default=f"{style.version}.settings.json", help="Settings JSON path")
    parser.add_argument("--output-dir", help="Optional output folder override")
    parser.add_argument("--no-prompt", action="store_true", help="Run without interactive prompts")
    parser.add_argument("--no-save-settings", action="store_true", help="Do not save chosen settings")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output")
    parser.set_defaults(
        template_guidance=True,
        strict_xlights_effects=True,
        debug_validation=True,
        auto_timing_tracks=True,
        workspace_history_enabled=True,
        pixel_reactive=True,
    )
    return parser.parse_args(argv)


def resolve_path(folder: Path, raw: str | None) -> Path | None:
    if raw is None:
        return None
    p = Path(raw)
    return p if p.is_absolute() else folder / p


def resolve_audio_inputs(folder: Path, raw_files: list[str] | None) -> list[Path]:
    if not raw_files:
        return base.list_audio_files(folder)
    out: list[Path] = []
    for raw in raw_files:
        p = resolve_path(folder, raw)
        if p is None or not p.exists():
            base.die(f"Audio file not found: {raw}")
        out.append(p)
    return out


def merge_profile(base_profile: base.UserProfile, args: argparse.Namespace) -> base.UserProfile:
    return base.UserProfile(
        feel=(args.feel or base_profile.feel).lower(),
        density=float(args.density if args.density is not None else base_profile.density),
        speed=float(args.speed if args.speed is not None else base_profile.speed),
        randomness=float(args.randomness if args.randomness is not None else base_profile.randomness),
        bass_bias=float(args.bass_bias if args.bass_bias is not None else base_profile.bass_bias),
        melody_density=float(args.melody_density if args.melody_density is not None else base_profile.melody_density),
        darkness=float(args.darkness if args.darkness is not None else base_profile.darkness),
        save_settings=(False if args.no_save_settings else base_profile.save_settings),
    )


def main_for(version: str, argv: list[str] | None = None) -> None:
    style = VARIANTS[version]
    args = parse_args(style, argv)
    base.VERBOSE = not args.quiet

    folder = Path(".").resolve()
    settings_path = resolve_path(folder, args.settings) or (folder / f"{style.version}.settings.json")
    default_profile = base.UserProfile(
        feel="balanced",
        density=base.DENSITY,
        speed=base.SPEED,
        randomness=base.RANDOMNESS,
        bass_bias=1.0,
        melody_density=1.0,
        darkness=1.0,
        save_settings=not args.no_save_settings,
    )
    profile = merge_profile(base.load_profile(settings_path) if settings_path.exists() else default_profile, args)
    if not args.no_prompt:
        profile = base.prompt_for_profile(profile)
    profile.save_settings = not args.no_save_settings
    profile = base.apply_profile(profile)
    profile = clamp_profile(profile, style)
    if profile.save_settings:
        base.save_profile(settings_path, profile)
        log(f"Settings saved: {settings_path.name}")

    overrides_path = resolve_path(folder, args.model_overrides_file) if args.model_overrides_file else None
    overrides_payload = load_override_file(overrides_path)
    layout_file = resolve_path(folder, args.layout_file) if args.layout_file else None
    if layout_file is not None and not layout_file.exists():
        log(f"Layout file not found for spatial routing: {layout_file}")
        layout_file = None
    xlights_repo = resolve_path(folder, args.xlights_repo) if args.xlights_repo else xfb.discover_xlights_repo(folder)
    if xlights_repo is not None and not (xlights_repo / "xLights" / "effects").exists():
        log(f"xLights repo path missing expected effects folder: {xlights_repo}")
        xlights_repo = None
    xlights_features_json = (
        resolve_path(folder, args.xlights_features_json)
        if args.xlights_features_json
        else (folder / "xlights" / xfb.CATALOG_FILENAME)
    )
    workspace_history_folder = resolve_path(folder, args.workspace_history_folder) if args.workspace_history_folder else (folder / "outputs")
    if workspace_history_folder is not None and not workspace_history_folder.exists():
        workspace_history_folder = None
    moises_key = (args.moises_api_key or "").strip() or os.environ.get("MOISES_API_KEY", "")
    tuning = RuntimeTuning(
        polyphony_override=int(args.polyphony) if args.polyphony is not None else None,
        cane_focus=float(args.cane_focus if args.cane_focus is not None else 1.0),
        flash_guard=float(args.flash_guard if args.flash_guard is not None else 0.80),
        keyboard_mix=float(args.keyboard_mix if args.keyboard_mix is not None else 1.0),
        model_overrides=overrides_payload,
        use_moises=bool(args.use_moises),
        moises_api_key=(moises_key if moises_key else None),
        sync_lyrics_heads=bool(args.sync_lyrics_heads),
        template_guidance=bool(args.template_guidance),
        layout_file=layout_file,
        spatial_awareness=base.clamp(float(args.spatial_awareness if args.spatial_awareness is not None else 0.0), 0.0, 1.0),
        chase_style=normalize_chase_style(args.chase_style or "none"),
        layering_mode=normalize_layering_mode(args.layering_mode or "replace"),
        layer_priority_vocals=int(args.layer_priority_vocals if args.layer_priority_vocals is not None else 4),
        layer_priority_drums=int(args.layer_priority_drums if args.layer_priority_drums is not None else 3),
        layer_priority_bass=int(args.layer_priority_bass if args.layer_priority_bass is not None else 2),
        layer_priority_other=int(args.layer_priority_other if args.layer_priority_other is not None else 1),
        strict_xlights_effects=bool(args.strict_xlights_effects),
        xlights_repo=xlights_repo,
        xlights_features_json=xlights_features_json,
        base_effect=str(args.base_effect or "On"),
        motion_effect=str(args.motion_effect or "Ramp"),
        accent_effect=str(args.accent_effect or "On"),
        max_layers_per_prop=max(1, int(args.max_layers_per_prop if args.max_layers_per_prop is not None else 3)),
        min_effect_ms=max(50, int(args.min_effect_ms if args.min_effect_ms is not None else 50)),
        debug_validation=bool(args.debug_validation),
        ac_lights_only=bool(args.ac_lights_only),
        palette_mode=normalize_palette_mode(str(args.palette_mode or "template")),
        workspace_history_enabled=bool(args.workspace_history_enabled),
        workspace_history_folder=workspace_history_folder,
        workspace_history_limit=max(4, int(args.workspace_history_limit if args.workspace_history_limit is not None else 24)),
        auto_timing_tracks=bool(args.auto_timing_tracks),
        pixel_reactive=bool(args.pixel_reactive),
    )
    style = apply_runtime_style(style, tuning)

    template = resolve_path(folder, args.template) if args.template else base.find_template_xsq(folder)
    if template is None or not template.exists():
        base.die("Template .xsq not found.")
    resolved_layout = resolve_layout_file(template, tuning.layout_file, folder)
    if resolved_layout is not None:
        if tuning.layout_file is None or tuning.layout_file.resolve() != resolved_layout:
            tuning.layout_file = resolved_layout
            log(f"Layout auto-selected for sync: {resolved_layout}")
    else:
        tuning.layout_file = None
        log("[WARN] No layout file found near template/current folder. Model rows may not align with current layout.")

    audios = resolve_audio_inputs(folder, args.audio)
    if not audios:
        base.die("No audio files found.")
    if args.single:
        audios = audios[:1]

    output_dir = resolve_path(folder, args.output_dir) if args.output_dir else (folder / style.family)
    if output_dir is None:
        output_dir = folder / style.family
    output_dir.mkdir(parents=True, exist_ok=True)

    log(f"Template: {template.name}")
    log(
        "Profile: "
        f"feel={profile.feel}, density={profile.density:.2f}, speed={profile.speed:.2f}, "
        f"randomness={profile.randomness:.2f}, bass={profile.bass_bias:.2f}, "
        f"melody={profile.melody_density:.2f}, dark={profile.darkness:.2f}"
    )
    log(
        "Runtime: "
        f"polyphony={style.polyphony}, cane_focus={tuning.cane_focus:.2f}, "
        f"flash_guard={tuning.flash_guard:.2f}, keyboard_mix={tuning.keyboard_mix:.2f}, "
        f"layering={normalize_layering_mode(tuning.layering_mode)}, "
        f"spatial={tuning.spatial_awareness:.2f}/{normalize_chase_style(tuning.chase_style)}, "
        f"effects(base/motion/accent)={tuning.base_effect}/{tuning.motion_effect}/{tuning.accent_effect}, "
        f"palette={normalize_palette_mode(tuning.palette_mode)}, timing_tracks={int(bool(tuning.auto_timing_tracks))}, "
        f"strict_xlights={int(bool(tuning.strict_xlights_effects))}, "
        f"ac_only={int(bool(tuning.ac_lights_only))}, "
        f"max_layers={tuning.max_layers_per_prop}, min_ms={tuning.min_effect_ms}, "
        f"lyrics_sync={int(bool(tuning.sync_lyrics_heads))}, "
        f"workspace_history={int(bool(tuning.workspace_history_folder))}:{tuning.workspace_history_limit}, "
        f"overrides={len(overrides_payload)}"
    )
    log(f"Output folder: {output_dir.name}")
    log(f"Processing {len(audios)} audio file(s) with {style.version}...")

    for i, audio in enumerate(audios, 1):
        out = variant_output_name(audio, output_dir, style.version)
        log(f"\n[{i}/{len(audios)}] {audio.name} -> {out.name}")
        try:
            run_variant(style, template, audio, out, profile, tuning=tuning)
        except Exception as exc:
            log(f"FAILED: {audio.name}: {repr(exc)}")

    log("\nDone.")


def main(argv: list[str] | None = None) -> None:
    main_for(ACTIVE_STYLE_VERSION, argv)
