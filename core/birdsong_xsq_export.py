from __future__ import annotations

from pathlib import Path
from typing import Iterable
from xml.etree.ElementTree import Element, SubElement, tostring

from core.birdsong_behavior_planner import EffectIntent
from core.birdsong_layout_targets import build_target_plan, load_helixville3_target_pool
from core.xsq_emitter import XSQSequence


DEFAULT_BIRDSONG_MODEL = "Helix_Birdsong_Group"


def _ms(seconds: float) -> str:
    return str(int(round(seconds * 1000.0)))


def _intent_mapping(intent: EffectIntent) -> dict[str, object]:
    return {
        "effect_name": intent.effect_name,
        "motif": intent.motif,
        "direction": intent.direction,
        "start_time": intent.start_time,
    }


def emit_birdsong_xsq_sequence(
    *,
    intents: Iterable[EffectIntent],
    sequence_name: str = "HelixBirdsongDemo",
    model_name: str = DEFAULT_BIRDSONG_MODEL,
    model_pool: tuple[str, ...] | None = None,
) -> XSQSequence:
    ordered = sorted(intents, key=lambda item: (item.start_time, item.effect_name, item.score))
    targets = model_pool or load_helixville3_target_pool()

    root = Element("xsequence")
    root.set("name", sequence_name)
    root.set("model", model_name)

    head = SubElement(root, "head")
    duration = max((intent.end_time for intent in ordered), default=0.0)
    SubElement(head, "sequenceDuration").text = f"{duration:.6f}"

    timing_track = SubElement(root, "timingtrack")
    timing_track.set("name", "BirdsongIntentTrack")

    effects = SubElement(root, "effects")
    element_effects = SubElement(root, "ElementEffects")

    timing_element = SubElement(element_effects, "Element")
    timing_element.set("name", "Birdsong Intent Track")
    timing_element.set("type", "timing")
    timing_layer = SubElement(timing_element, "EffectLayer")

    model_layers: dict[str, Element] = {}
    for target in targets:
        model_element = SubElement(element_effects, "Element")
        model_element.set("name", target)
        model_element.set("type", "model")
        model_layers[target] = SubElement(model_element, "EffectLayer")

    for idx, intent in enumerate(ordered):
        target_plan = build_target_plan(_intent_mapping(intent), targets)
        target_model = target_plan.model_name
        start = f"{intent.start_time:.6f}"
        duration_text = f"{intent.duration:.6f}"
        strength = f"{intent.strength:.4f}"

        entry = SubElement(timing_track, "phoneme")
        entry.set("index", str(idx))
        entry.set("performer", "birdsong")
        entry.set("phoneme", intent.effect_name)
        entry.set("start", start)
        entry.set("duration", duration_text)
        entry.set("intensity", strength)
        entry.set("motif", intent.motif)
        entry.set("direction", intent.direction)
        entry.set("score", f"{intent.score:.6f}")
        entry.set("target_model", target_model)

        effect = SubElement(effects, "effect")
        effect.set("index", str(idx))
        effect.set("type", intent.effect_name)
        effect.set("start", start)
        effect.set("duration", duration_text)
        effect.set("motif", intent.motif)
        effect.set("direction", intent.direction)
        effect.set("score", f"{intent.score:.6f}")
        effect.set("target_model", target_model)

        timing_marker = SubElement(timing_layer, "Effect")
        timing_marker.set("name", f"{intent.motif}:{intent.effect_name}")
        timing_marker.set("label", f"{intent.motif}:{target_model}:{intent.effect_name}")
        timing_marker.set("startTime", _ms(intent.start_time))
        timing_marker.set("endTime", _ms(intent.end_time))

        model_effect = SubElement(model_layers[target_model], "Effect")
        model_effect.set("name", intent.effect_name)
        model_effect.set("label", f"{intent.motif}:{intent.direction}")
        model_effect.set("startTime", _ms(intent.start_time))
        model_effect.set("endTime", _ms(intent.end_time))
        model_effect.set("settings", f"E_VALUECURVE_Intensity=Active=TRUE,Start={int(round(intent.strength * 100))},End=0")
        model_effect.set("palette", "C_BUTTON_Palette1=#ffffff,C_BUTTON_Palette2=#4dabff,C_CHECKBOX_Palette1=1,C_CHECKBOX_Palette2=1")

    return XSQSequence(
        sequence_name=sequence_name,
        model_name=model_name,
        xml_text=tostring(root, encoding="utf-8").decode("utf-8"),
    )


def write_birdsong_xsq(
    path: Path,
    intents: Iterable[EffectIntent],
    *,
    sequence_name: str = "HelixBirdsongDemo",
    model_name: str = DEFAULT_BIRDSONG_MODEL,
    model_pool: tuple[str, ...] | None = None,
) -> Path:
    sequence = emit_birdsong_xsq_sequence(
        intents=intents,
        sequence_name=sequence_name,
        model_name=model_name,
        model_pool=model_pool,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sequence.xml_text, encoding="utf-8")
    return path
