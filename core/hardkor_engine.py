from __future__ import annotations

from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass, field
import re
from typing import Callable, Iterable, Sequence

from core import model_parser as xmp


_NUM_RE = re.compile(r"(\d+)")


@dataclass
class HardKorResult:
    enabled: bool
    placements: int
    timing_spans: list[tuple[str, int, int]] = field(default_factory=list)
    group_counts: dict[str, int] = field(default_factory=dict)
    reason: str = ""


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _num_key(value: str) -> tuple[int, str]:
    match = _NUM_RE.search(value)
    if match:
        try:
            return (int(match.group(1)), _norm(value))
        except Exception:
            return (10**9, _norm(value))
    return (10**9, _norm(value))


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _sorted_spatial(models: list[str], parsed_layout: xmp.ParsedLayout | None, *, reverse: bool = False) -> list[str]:
    if parsed_layout is None:
        ordered = sorted(models, key=_num_key)
        return list(reversed(ordered)) if reverse else ordered
    ranked: list[tuple[float, float, str]] = []
    fallback: list[str] = []
    for model in models:
        parsed = parsed_layout.model_for(model)
        if parsed is None:
            fallback.append(model)
            continue
        cx, cy, _cz = parsed.center()
        ranked.append((cx, cy, model))
    ranked.sort(key=lambda item: (item[0], item[1], _num_key(item[2])[0], _norm(item[2])))
    ordered = [item[2] for item in ranked] + sorted(fallback, key=_num_key)
    return list(reversed(ordered)) if reverse else ordered


def _part_label_for_time(parts: Sequence[object], t_ms: int) -> str:
    for part in parts:
        start_ms = int(getattr(part, "start_ms", 0) or 0)
        end_ms = int(getattr(part, "end_ms", 0) or 0)
        if start_ms <= t_ms < end_ms:
            return str(getattr(part, "label", "") or "").strip().upper()
    return ""


def _pick_by_tokens(names: Sequence[str], include: Sequence[str], *, exclude: Sequence[str] = ()) -> list[str]:
    include_norm = tuple(_norm(token) for token in include)
    exclude_norm = tuple(_norm(token) for token in exclude)
    picked: list[str] = []
    for name in names:
        key = _norm(name)
        if include_norm and not any(token in key for token in include_norm):
            continue
        if any(token in key for token in exclude_norm):
            continue
        picked.append(name)
    return picked


def _match_series(names: Sequence[str], pattern: str) -> list[str]:
    regex = re.compile(pattern, re.IGNORECASE)
    return [name for name in names if regex.search(name)]


def _build_group_catalog(names: Sequence[str]) -> dict[str, list[str]]:
    red_tree = _pick_by_tokens(names, ("red",), exclude=("roof", "flood", "wreath", "candy cane", "north candy cane", "south candy cane"))
    red_tree = _pick_by_tokens(red_tree, ("tree", "blvd", "linden"))
    green_tree = _pick_by_tokens(names, ("green",), exclude=("roof", "flood", "wreath", "candy cane", "north candy cane", "south candy cane"))
    green_tree = _pick_by_tokens(green_tree, ("tree", "blvd", "linden"))
    white_tree = _pick_by_tokens(names, ("white",), exclude=("roof", "flood", "wreath", "candy cane", "north candy cane", "south candy cane"))
    white_tree = _pick_by_tokens(white_tree, ("tree", "blvd", "linden"))

    mega_red = _pick_by_tokens(names, ("mega tree", "red"))
    mega_green = _pick_by_tokens(names, ("mega tree", "green"))
    mega_white = _pick_by_tokens(names, ("mega tree", "white"))
    line_green = _pick_by_tokens(names, ("line tree", "green"))
    line_red = _pick_by_tokens(names, ("line tree", "red"))
    line_white = _pick_by_tokens(names, ("line tree", "white"))

    arches = _match_series(names, r"\barch\b")
    north_canes = _match_series(names, r"\bnorth\s*candy\s*cane\b")
    south_canes = _match_series(names, r"\bsouth\s*candy\s*cane\b")
    canes = north_canes + south_canes
    stars = _match_series(names, r"\bstar\s*\d+\b")
    snowflakes = _match_series(names, r"\bsf\s*\d+\b")
    big_snowflakes = _match_series(names, r"big\s*snowflake")

    left_tree_green = _pick_by_tokens(names, ("left tree", "green"))
    left_blvd_green = _pick_by_tokens(names, ("left blvd", "green"))
    center_blvd_green = _pick_by_tokens(names, ("center blvd", "green"))
    right_blvd_green = _pick_by_tokens(names, ("right blvd", "green"))
    right_linden_green = _pick_by_tokens(names, ("right linden", "green"))
    garage_green = _pick_by_tokens(names, ("garage trees", "green"))

    return {
        "red_tree_backbone": _dedupe(red_tree),
        "green_tree_backbone": _dedupe(green_tree),
        "white_tree_backbone": _dedupe(white_tree),
        "mega_red": _dedupe(mega_red),
        "mega_green": _dedupe(mega_green),
        "mega_white": _dedupe(mega_white),
        "line_green": _dedupe(line_green),
        "line_red": _dedupe(line_red),
        "line_white": _dedupe(line_white),
        "arches": _dedupe(arches),
        "north_canes": _dedupe(north_canes),
        "south_canes": _dedupe(south_canes),
        "canes": _dedupe(canes),
        "stars": _dedupe(stars),
        "snowflakes": _dedupe(snowflakes + big_snowflakes),
        "green_route_left_tree": _dedupe(left_tree_green),
        "green_route_left_blvd": _dedupe(left_blvd_green),
        "green_route_center_blvd": _dedupe(center_blvd_green),
        "green_route_right_blvd": _dedupe(right_blvd_green),
        "green_route_right_linden": _dedupe(right_linden_green),
        "green_route_garage": _dedupe(garage_green),
    }


def place_hardkor_sequence(
    *,
    names: Sequence[str],
    parsed_layout: xmp.ParsedLayout | None,
    parts: Sequence[object],
    beat_ms: Sequence[int],
    bar_ms: Sequence[int],
    kicks: Sequence[int],
    snares: Sequence[int],
    hats: Sequence[int],
    bass_peaks: Sequence[int],
    vocal_peaks: Sequence[int],
    build_lifts: Sequence[int],
    releases: Sequence[int],
    add_model: Callable[..., None],
    in_blackout: Callable[[int], bool],
    ramp_ok: bool,
    intensity: float = 1.0,
) -> HardKorResult:
    if not names:
        return HardKorResult(enabled=False, placements=0, reason="no_models")

    intensity = max(0.25, min(2.5, float(intensity)))
    catalog = _build_group_catalog(names)
    group_counts = Counter({key: len(values) for key, values in catalog.items() if values})
    placements = 0
    timing_spans: list[tuple[str, int, int]] = []

    red_backbone = _sorted_spatial(catalog["red_tree_backbone"], parsed_layout)
    green_backbone = _sorted_spatial(catalog["green_tree_backbone"], parsed_layout)
    white_backbone = _sorted_spatial(catalog["white_tree_backbone"], parsed_layout)
    arches = _sorted_spatial(catalog["arches"], parsed_layout)
    stars = sorted(catalog["stars"], key=_num_key)
    snowflakes = sorted(catalog["snowflakes"], key=_num_key)
    north_canes = sorted(catalog["north_canes"], key=_num_key)
    south_canes = sorted(catalog["south_canes"], key=_num_key)
    line_green = sorted(catalog["line_green"], key=_num_key)
    line_red = sorted(catalog["line_red"], key=_num_key)
    line_white = sorted(catalog["line_white"], key=_num_key)
    mega_red = sorted(catalog["mega_red"], key=_num_key)
    mega_green = sorted(catalog["mega_green"], key=_num_key)
    mega_white = sorted(catalog["mega_white"], key=_num_key)

    white_fx = _dedupe(line_white + north_canes + south_canes + arches + stars + snowflakes)
    yard_all = _dedupe(red_backbone + green_backbone + white_backbone + white_fx + line_green + line_red)

    green_route = _dedupe(
        _sorted_spatial(catalog["green_route_left_tree"], parsed_layout)
        + _sorted_spatial(catalog["green_route_left_blvd"], parsed_layout)
        + _sorted_spatial(catalog["green_route_center_blvd"], parsed_layout)
        + _sorted_spatial(catalog["green_route_right_blvd"], parsed_layout)
        + _sorted_spatial(catalog["green_route_right_linden"], parsed_layout)
        + _sorted_spatial(catalog["green_route_garage"], parsed_layout)
        + _sorted_spatial(mega_green, parsed_layout)
    )

    def place_many(
        models: Sequence[str],
        st: int,
        en: int,
        label: str,
        *,
        eff: str = "On",
        stem: str = "other",
    ) -> None:
        nonlocal placements
        if en <= st:
            return
        for model in models:
            add_model(model, st, en, label, eff=eff, stem=stem)
            placements += 1

    # 1) Red backbone follows bass/stem impacts.
    bass_marks = sorted(set(int(v) for v in kicks) | set(int(v) for v in bass_peaks[::2]))
    bass_dur = int(95 + (95 * intensity))
    for t_ms in bass_marks:
        if in_blackout(t_ms):
            continue
        place_many(red_backbone, t_ms, t_ms + bass_dur, "hardkor_bass_red_backbone", stem="bass")
        if mega_red:
            accent = mega_red[(t_ms // max(1, bass_dur)) % len(mega_red)]
            place_many([accent], t_ms, t_ms + max(80, bass_dur - 20), "hardkor_bass_mega_pulse", stem="bass")
        timing_spans.append(("hardkor_bass", t_ms, t_ms + bass_dur))

    # 2) Arches run deterministic beat chases; direction flips each bar.
    beat_marks = sorted(set(int(v) for v in beat_ms) or set(int(v) for v in kicks))
    if arches and beat_marks:
        beat_dur = int(70 + (35 * intensity))
        for beat_idx, t_ms in enumerate(beat_marks):
            if in_blackout(t_ms):
                continue
            bar_idx = max(0, bisect_right(list(bar_ms), t_ms) - 1)
            reverse = (bar_idx % 2) == 1
            ordered = list(reversed(arches)) if reverse else arches
            step_ms = max(22, int(46 / max(0.3, intensity)))
            for idx, model in enumerate(ordered):
                st = t_ms + idx * step_ms
                en = st + beat_dur
                add_model(model, st, en, "hardkor_arch_wave", eff="On", stem="drums")
                placements += 1
            if (beat_idx % 4) == 0:
                timing_spans.append(("hardkor_arch_bar", t_ms, t_ms + beat_dur))

    # 3) Green channels jump spatially with mids/vocals.
    vocal_marks = sorted(set(int(v) for v in vocal_peaks) | set(int(v) for v in snares[::2]))
    if green_route and vocal_marks:
        jump_dur = int(100 + (90 * intensity))
        route_len = len(green_route)
        for idx, t_ms in enumerate(vocal_marks):
            if in_blackout(t_ms):
                continue
            phrase_idx = max(0, bisect_right(list(bar_ms), t_ms) // 4)
            reverse = (phrase_idx % 2) == 1
            route = list(reversed(green_route)) if reverse else green_route
            model = route[idx % route_len]
            place_many([model], t_ms, t_ms + jump_dur, "hardkor_green_jump", stem="vocals")
            if line_green:
                line_model = line_green[idx % len(line_green)]
                place_many([line_model], t_ms + 20, t_ms + jump_dur + 40, "hardkor_green_line_tail", stem="vocals")
            timing_spans.append(("hardkor_mid_jump", t_ms, t_ms + jump_dur))

    # 4) High frequencies tick white channels and white-only props.
    high_marks = sorted(set(int(v) for v in hats) | set(int(v) for v in releases[::2]))
    if high_marks and white_fx:
        tick_dur = int(60 + (40 * intensity))
        for idx, t_ms in enumerate(high_marks):
            if in_blackout(t_ms):
                continue
            white_model = white_fx[idx % len(white_fx)]
            place_many([white_model], t_ms, t_ms + tick_dur, "hardkor_white_tick", stem="other")
            if white_backbone:
                tree_model = white_backbone[idx % len(white_backbone)]
                place_many([tree_model], t_ms + 16, t_ms + tick_dur + 32, "hardkor_white_tree", stem="other")

    # 5) Sequential "VU bar" style for line trees and canes.
    seq_marks = beat_marks or sorted(set(int(v) for v in kicks))
    line_seq = line_red or line_green or line_white
    cane_seq = north_canes + south_canes
    if seq_marks and (line_seq or cane_seq):
        for idx, t_ms in enumerate(seq_marks):
            if in_blackout(t_ms):
                continue
            part_label = _part_label_for_time(parts, t_ms)
            scale = 1.0 if part_label in {"VERSE", "INTRO"} else 1.35 if part_label in {"PRECHORUS", "BRIDGE"} else 1.65
            active_count = max(1, int(round((1 + (idx % 5)) * scale)))
            if line_seq:
                count = min(len(line_seq), active_count)
                place_many(line_seq[:count], t_ms, t_ms + 120, "hardkor_line_vu", stem="drums")
            if cane_seq and (idx % 2) == 0:
                count = min(len(cane_seq), max(1, active_count // 2))
                place_many(cane_seq[:count], t_ms + 10, t_ms + 115, "hardkor_cane_vu", stem="drums")

    # 6) Build-up + pre-drop shimmer + drop full-yard burst.
    for part in parts:
        label = str(getattr(part, "label", "") or "").upper()
        start_ms = int(getattr(part, "start_ms", 0) or 0)
        end_ms = int(getattr(part, "end_ms", 0) or 0)
        if end_ms <= start_ms:
            continue
        if label in {"PRECHORUS", "BRIDGE"}:
            whirl_targets = _dedupe(stars + arches + white_fx + green_route + line_seq + mega_green + mega_white)
            if whirl_targets:
                whirl_start = max(start_ms, end_ms - max(720, int(1200 / max(0.35, intensity))))
                span = max(220, end_ms - whirl_start)
                step = max(18, span // max(1, len(whirl_targets)))
                for idx, model in enumerate(whirl_targets):
                    st = whirl_start + (idx * step)
                    en = min(end_ms, st + max(75, step + 40))
                    use_ramp = ramp_ok and idx >= max(1, len(whirl_targets) // 3)
                    add_model(model, st, en, "hardkor_whirl_build", eff=("Ramp" if use_ramp else "On"), stem="other")
                    placements += 1
                timing_spans.append(("hardkor_build_whirl", whirl_start, end_ms))

            shimmer_start = max(start_ms, end_ms - 180)
            shimmer_end = max(shimmer_start + 30, end_ms - 25)
            pulse_marks = list(range(shimmer_start, shimmer_end, 42))
            for idx, pulse in enumerate(pulse_marks):
                if in_blackout(pulse):
                    continue
                target = white_fx[idx % len(white_fx)] if white_fx else None
                if target:
                    place_many([target], pulse, pulse + 56, "hardkor_predrop_twinkle", stem="other")
            timing_spans.append(("hardkor_predrop", shimmer_start, shimmer_end))

        if label == "CHORUS":
            burst_end = min(end_ms, start_ms + int(220 + (120 * intensity)))
            if yard_all:
                place_many(yard_all, start_ms, burst_end, "hardkor_drop_full", stem="drums")
            timing_spans.append(("hardkor_drop", start_ms, burst_end))

    return HardKorResult(
        enabled=True,
        placements=placements,
        timing_spans=timing_spans[:2800],
        group_counts=dict(sorted(group_counts.items(), key=lambda item: item[0])),
        reason="ok",
    )
