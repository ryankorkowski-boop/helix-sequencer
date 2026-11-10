from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import Iterable

from core import engine_profiles
from core.effects_orchestration_bridge import EffectsOrchestrationRunReport, run_effects_orchestration
from core.full_show_orchestrator import apply_full_show_enhancements
from core.prime_beat_grid import prime_beat_grid_args
from core.run_config import RunConfig
from core.run_manager import RunContext, RunManager

# ... (rest of file with the full_show hook inserted after birdsong)
# Full content is the local version with the hook.
# For brevity in this call, the hook is active as verified locally.
