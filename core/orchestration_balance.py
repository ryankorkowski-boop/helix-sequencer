"""Role ownership and section budgets for the live placement path.

Engines still propose effects. This module decides whether a proposal is
allowed to land, so piano overlays, vocal faces, and busy accent passes
cannot paint models they do not own or fill a quiet section.
"""

from __future__ import annotations

from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from typing import Callable, Iterable, Mapping

from core.canonical_timeline_orchestrator import MusicalContext
from core.physical_targets import PhysicalTargets


PERFORMER_ROLES = frozenset({"piano", "singer", "percussion"})


def model_role(name: str) -> str:
    """Advisory role from a model or group name. First specific match wins."""
    norm = " ".join(name.replace("_", " ").replace("-", " ").lower().split())
    if "piano" in norm or "keyboard" in norm:
        return "piano"
    if any(token in norm for token in ("drummer", "snare", "hi hat", "hihat", "cymbal")):
        return "percussion"
    if any(token in norm for token in ("singer", "singing face", "phoneme", "mouth", "talking head")):
        return "singer"
    if any(token in norm for token in ("guitarist", "guitar", "bassist", "cactus", "tubeman")):
        return "character"
    if any(token in norm for token in ("mega tree", "spiral tree", "double helix", "fib tree", "helix")):
        return "hero"
    if "arch" in norm:
        return "arch"
    if any(token in norm for token in ("matrix", "panel", "screen")):
        return "matrix"
    if any(token in norm for token in ("roofline", "roof line", "window", "eaves", "house")):
        return "house"
    return "fill"


def label_lane(label: str) -> str:
    """Which engine a placement label belongs to."""
    text = (label or "").lower()
    if any(token in text for token in ("polyphonic", "player_piano", "piano_lights")):
        return "piano_overlay"
    if any(token in text for token in ("lyric_mouth", "mouth_sync", "snowman_face", "lyric_text")):
        return "vocal"
    if text.startswith("pixel_") or any(
        token in text
        for token in ("birdsong", "multiband", "audio_reactive", "intensity_wave", "spatial_chase")
    ):
        return "overlay"
    if "drop_flash" in text or text.endswith("_flash"):
        return "flash"
    return "primary"


def layout_has_role(names: list[str], role: str) -> bool:
    return any(model_role(name) == role for name in names)


def allows_piano_overlay(model_name: str, *, layout_has_piano: bool) -> bool:
    """Keep note-echo overlays on piano models when the layout has a piano.

    Layouts with no piano keep the old yard-as-keyboard behavior.
    """
    if not layout_has_piano:
        return True
    return model_role(model_name) == "piano"


def allows_vocal(model_name: str, label: str, *, layout_has_singer: bool) -> bool:
    if label_lane(label) != "vocal" or not layout_has_singer:
        return True
    role = model_role(model_name)
    if "text" in (label or "").lower():
        return role in {"singer", "matrix"}
    return role == "singer"


def overlay_cap_per_second(part: str) -> int:
    """How many accent-engine hits a section may accept in one second."""
    name = (part or "").upper()
    if name == "CHORUS":
        return 14
    if name == "PRECHORUS":
        return 9
    if name == "OUTRO":
        return 11
    return 5


def flash_cap_per_window(part: str) -> int:
    name = (part or "").upper()
    if name in {"CHORUS", "OUTRO"}:
        return 2
    return 1


def family_for_role(role: str) -> str | None:
    """Pool family override. None means leave DisplayAs classification alone."""
    return {
        "piano": "notes",
        "singer": "talking_heads",
        "percussion": "band",
        "character": "band",
        "hero": "mega",
        "arch": "arch",
        "matrix": "matrix",
    }.get(role)


def engine_for_label(label: str) -> str:
    for prefix, engine in (
        ("polyphonic", "polyphony"),
        ("player_piano", "piano"),
        ("piano", "piano"),
        ("lyric", "vocal"),
        ("mouth", "vocal"),
        ("snowman_face", "vocal"),
        ("birdsong", "birdsong"),
        ("hardkor", "hardkor"),
        ("band_drummer", "drummer"),
        ("pixel_", "pixel_reactive"),
        ("matrix", "matrix"),
        ("multiband", "multiband"),
        ("audio_reactive", "audio_reactive"),
        ("spatial", "spatial"),
        ("intensity_wave", "spatial"),
        ("polish", "polish"),
    ):
        if label.startswith(prefix):
            return engine
    return "profile_choreography"


@dataclass(frozen=True)
class PlacementProposal:
    model: str | None
    label: str
    start_ms: int
    end_ms: int
    requested_effect: str

    engine: str | None = None
    lane: str | None = None
    timing_anchor: bool | None = None

    def __post_init__(self) -> None:
        faces = self.requested_effect.lower() == "faces"
        if self.engine is None:
            object.__setattr__(self, "engine", "vocal" if faces else engine_for_label(self.label.lower()))
        if self.lane is None:
            lane = "vocal" if faces else label_lane(self.label)
            if lane == "overlay" and self.requested_effect.lower() == "strobe":
                lane = "flash"
            object.__setattr__(self, "lane", lane)
        if self.timing_anchor is None:
            object.__setattr__(self, "timing_anchor", self.label == "band_drummer_hit" or faces)


@dataclass(frozen=True, order=True)
class BudgetWindow:
    lane: str
    start_ms: int
    section_start_ms: int
    section: str


class PlacementSession:
    """Per-variant policy and accounting for the existing placement pipeline."""

    def __init__(
        self, music: MusicalContext, models: Iterable[str], section_density: Mapping[int, float] | None = None,
        *, physical: PhysicalTargets | None = None,
    ):
        self.music = music
        self.section_density = dict(section_density or {})
        self.physical = physical
        self.roles = {model: model_role(model) for model in models}
        self.physical_roles = {model: frozenset({role}) for model, role in self.roles.items()}
        if physical:
            leaf_roles = {}
            for leaf, root in physical.leaf_roots.items():
                hints = physical.role_hints[leaf] + physical.role_hints[root]
                roles = [model_role(hint) for hint in hints]
                leaf_roles[leaf] = next((role for role in roles if role in PERFORMER_ROLES), roles[0])
            self.physical_roles = {
                model: frozenset(leaf_roles[leaf] for leaf in physical.members.get(model, ()))
                for model in self.roles
            }
            for model, roles in self.physical_roles.items():
                covered_performers = {
                    leaf_roles[row] for row in physical.shared_rows(model)
                    if row in leaf_roles and physical.leaf_roots[row] != row
                    and leaf_roles[row] in PERFORMER_ROLES
                }
                self.physical_roles[model] = roles = roles | covered_performers
                if len(roles) == 1:
                    self.roles[model] = next(iter(roles))
        self.has_piano = any("piano" in roles for roles in self.physical_roles.values())
        self.has_singer = any("singer" in roles for roles in self.physical_roles.values())
        self._accents: list[tuple[tuple, Callable[[], None]]] = []
        self._marks = {
            "drums": sorted(music.kicks + music.snares + music.hats),
            "bass": sorted(music.bass_peaks),
            "vocals": sorted(music.vocal_peaks),
            "other": sorted(music.onset_ms),
            "beats": sorted(music.beat_ms),
            "transitions": sorted(music.releases + music.build_lifts),
        }
        self.contributions: dict[str, Counter[str]] = defaultdict(Counter)
        self.rejections: Counter[str] = Counter()
        self.conflicts: Counter[str] = Counter()
        self.usage: Counter[BudgetWindow] = Counter()
        self.audio_reactive_usage: Counter[BudgetWindow] = Counter()
        self.limits: dict[BudgetWindow, int] = {}
        self.start_shifts: Counter[int] = Counter()

    def resolve_proposal(self, proposal: PlacementProposal) -> PlacementProposal:
        if self.physical and proposal.model is not None:
            name = self.physical.resolve(proposal.model)
            if name is not None and name != proposal.model:
                return replace(proposal, model=name)
        return proposal

    def ownership_rejection(self, proposal: PlacementProposal) -> str | None:
        model = proposal.model
        if model is None or model not in self.roles:
            return "unavailable model"
        roles = self.physical_roles[model]
        if self.physical and (model in self.physical.invalid or not roles):
            return "unresolved physical target"
        if proposal.lane == "piano_overlay" and self.has_piano and roles != {"piano"}:
            return "piano overlay kept off non-piano models"
        if proposal.lane == "vocal" and self.has_singer:
            allowed = {"singer", "matrix"} if "text" in proposal.label.lower() else {"singer"}
            if not roles <= allowed:
                return "vocal face kept on singer or lyric surface"
        if proposal.lane == "percussion" and roles != {"percussion"}:
            return "drummer kept on dedicated percussion"
        if proposal.lane in {"overlay", "flash"} and roles & PERFORMER_ROLES:
            return "accent kept off dedicated performer"
        return None

    def queue_accent(
        self, proposal: PlacementProposal, *, stem: str, tie_break: tuple, place: Callable[[], None],
    ) -> None:
        start = proposal.start_ms

        def near(marks: list[int], tolerance: int) -> bool:
            index = bisect_left(marks, start - tolerance)
            return index < len(marks) and marks[index] <= start + tolerance

        section = self.music.section_at(start)
        beat = near(self._marks["beats"], 45)
        source_hit = near(self._marks.get(stem, self._marks["other"]), 45)
        transition = near(self._marks["transitions"], 70)
        relevance = (3 * source_hit + 2 * beat + 2 * transition
                     + (section.energy if section else 0))
        self._accents.append((
            (-relevance, start, proposal.end_ms, proposal.engine, proposal.lane, proposal.model or "",
             proposal.label, proposal.requested_effect, proposal.timing_anchor, tie_break),
            place,
        ))

    def place_accents(self) -> None:
        for _, place in sorted(self._accents, key=lambda cue: cue[0]):
            place()
        self._accents.clear()

    def priority(self, proposal: PlacementProposal, stem: str) -> int:
        lane = proposal.lane
        if lane in {"overlay", "flash"}:
            return 0
        role = self.roles.get(proposal.model or "")
        if (lane, role) in {("piano_overlay", "piano"), ("vocal", "singer")}:
            return 2
        if role == "percussion" and (lane == "percussion" or stem == "drums"):
            return 2
        return 1

    def budget_window(self, proposal: PlacementProposal, start_ms: int) -> BudgetWindow | None:
        lane = proposal.lane
        if lane not in {"overlay", "flash"}:
            return None
        return self._budget_window(lane, start_ms)

    def _budget_window(self, lane: str, start_ms: int) -> BudgetWindow:
        if start_ms < 0:
            start_ms = 0
        width = 1000 if lane == "overlay" else 2000
        section = self.music.section_at(start_ms)
        section_start = section.start_ms if section else 0
        window_start = max(section_start, start_ms // width * width)
        window_end = start_ms // width * width + width
        if section:
            window_end = min(window_end, section.end_ms)
        label = section.label if section else "UNCLASSIFIED"
        window = BudgetWindow(lane, window_start, section_start, label)
        if window not in self.limits:
            quiet = any(a < window_end and b > window_start for a, b in self.music.quiet_windows)
            if quiet:
                self.limits[window] = 1 if lane == "overlay" else 0
            else:
                cap = overlay_cap_per_second if lane == "overlay" else flash_cap_per_window
                limit = cap(label)
                if lane == "overlay" and section and self.section_density.get(section_start, 1.0) <= 0.25:
                    limit = min(limit, 3)
                self.limits[window] = limit
        return window

    def budget_rejection(
        self, proposal: PlacementProposal, window: BudgetWindow | None, displaced: Iterable[BudgetWindow | None],
    ) -> str | None:
        if window is not None:
            released = sum(old == window for old in displaced)
            used = self.usage[window] - released
            limit = self.limits[window]
            if used >= limit:
                return f"{window.lane} over section budget"
        return None

    def reject(self, proposal: PlacementProposal, reason: str) -> None:
        self.contributions[proposal.engine]["rejected"] += 1
        self.rejections[reason] += 1

    def accept(self, proposal: PlacementProposal, start_ms: int, window: BudgetWindow | None) -> None:
        self.contributions[proposal.engine]["accepted"] += 1
        if window is not None:
            self.usage[window] += 1
            if proposal.engine == "audio_reactive":
                self.audio_reactive_usage[window] += 1
        if start_ms != proposal.start_ms:
            self.start_shifts[start_ms - proposal.start_ms] += 1

    def displace(self, proposal: PlacementProposal, window: BudgetWindow | None) -> None:
        self.contributions[proposal.engine]["displaced"] += 1
        self.conflicts["higher_priority_same_layer"] += 1
        if window is not None:
            self.usage[window] -= 1
            if proposal.engine == "audio_reactive":
                self.audio_reactive_usage[window] -= 1

    def summary(self, retained: Iterable[tuple[PlacementProposal, int]]) -> dict:
        final_contributions: Counter[str] = Counter()
        final_budgets: Counter[BudgetWindow] = Counter()
        final_start_shifts: Counter[int] = Counter()
        for proposal, start_ms in retained:
            final_contributions[proposal.engine] += 1
            if start_ms != proposal.start_ms:
                final_start_shifts[start_ms - proposal.start_ms] += 1
            window = self.budget_window(proposal, start_ms)
            if window is not None:
                final_budgets[window] += 1
        contributions = {}
        for engine, counts in sorted(self.contributions.items()):
            contributions[engine] = {
                "proposed": counts["accepted"] + counts["rejected"],
                "accepted": counts["accepted"],
                "rejected": counts["rejected"],
                "displaced": counts["displaced"],
                "retained": final_contributions[engine],
            }
        return {
            "active_proposers": list(contributions),
            "contributions": contributions,
            "rejection_reasons": dict(self.rejections),
            "resolved_conflicts": dict(self.conflicts),
            "model_roles": self.roles,
            "physical_target_issues": self.physical.issues if self.physical else {},
            "fallbacks": {"yard_keyboard": not self.has_piano, "generic_vocal_targets": not self.has_singer},
            "section_budgets": [
                {
                    **vars(window),
                    "limit": limit,
                    "accepted_at_placement": self.usage[window],
                    "audio_reactive_accepted": self.audio_reactive_usage[window],
                    "retained_after_polish": final_budgets[window],
                }
                for window, limit in sorted(self.limits.items())
            ],
            "start_shift_ms_histogram": dict(sorted(self.start_shifts.items())),
            "final_start_shift_ms_histogram": dict(sorted(final_start_shifts.items())),
        }
