"""Regression coverage for XSQ neon palette assignment and run integration."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

from core.sequence_builder import _apply_neon_palettes_to_generated_sequences
from tools.xsq_palette_repair import repair_xsq


def _fixture(path: Path) -> None:
    path.write_text(
        '<xsequence><head><sequenceDuration>5</sequenceDuration></head>'
        '<nextid>7</nextid>'
        '<ColorPalettes><ColorPalette>'
        'C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1'
        '</ColorPalette></ColorPalettes>'
        '<EffectDB><Effect /></EffectDB>'
        '<ElementEffects>'
        '<Element type="model" name="Test Tree"><EffectLayer>'
        '<Effect name="On" startTime="100" endTime="200" ref="0" palette="0" id="5" />'
        '<Effect name="Ramp" startTime="200" endTime="400" />'
        '<Effect name="Single Strand" startTime="500" endTime="700" />'
        '<Effect name="Pictures" startTime="900" endTime="1100" />'
        '</EffectLayer></Element>'
        '</ElementEffects></xsequence>',
        encoding="utf-8",
    )


def test_preserve_existing_palettes_and_assign_only_missing():
    with TemporaryDirectory() as td:
        source, dest = Path(td) / "raw.xsq", Path(td) / "neon.xsq"
        _fixture(source)
        untouched = source.read_bytes()
        audit = repair_xsq(source, dest)
        root = ET.parse(dest).getroot()
        effects = root.findall("./ElementEffects/Element/EffectLayer/Effect")
        assert source.read_bytes() == untouched
        assert audit["changes"]["palettes_assigned"] == 3
        assert audit["changes"]["original_palette_refs_preserved"] == 1
        assert effects[0].get("palette") == "0"
        assert effects[0].get("ref") == "0"
        assert effects[0].get("id") == "5"
        assert all(e.get("palette") is not None for e in effects)
        assert len(root.findall("./ColorPalettes/ColorPalette")) >= 7
        assert [e.get("name") for e in effects] == ["On", "Ramp", "Single Strand", "Pictures"]


def test_portable_fixes_names_without_moving_effects():
    with TemporaryDirectory() as td:
        source, dest = Path(td) / "raw.xsq", Path(td) / "portable.xsq"
        _fixture(source)
        audit = repair_xsq(source, dest, portable=True)
        root = ET.parse(dest).getroot()
        effects = root.findall("./ElementEffects/Element/EffectLayer/Effect")
        assert [e.get("name") for e in effects] == ["On", "On", "SingleStrand"]
        assert [e.get("startTime") for e in effects] == ["100", "200", "500"]
        assert audit["changes"]["ramp_converted_to_on_fade"] == 1
        assert audit["changes"]["omitted_resource_dependent"] == 1
        assert all(int(e.get("ref")) < len(root.findall("./EffectDB/Effect")) for e in effects)


def test_output_hook_is_opt_in_and_preserves_uncolored_copy():
    class FakeContext:
        def __init__(self):
            self.artifacts = []
        def record_artifact(self, kind, path):
            self.artifacts.append((kind, path))

    with TemporaryDirectory() as td:
        output = Path(td) / "demo.xsq"
        _fixture(output)
        original = output.read_bytes()
        ctx = FakeContext()
        _apply_neon_palettes_to_generated_sequences(
            ["--palette-mode", "template"], [Path(td)], {}, ctx
        )
        assert output.read_bytes() == original
        assert not ctx.artifacts
        _apply_neon_palettes_to_generated_sequences(
            ["--palette-mode", "neon"], [Path(td)], {}, ctx
        )
        assert output.read_bytes() != original
        assert output.with_name("demo.uncolored.xsq").read_bytes() == original
        assert any(kind == "xsq_uncolored_backup" for kind, _ in ctx.artifacts)
        assert all(e.get("palette") is not None for e in ET.parse(output).getroot().findall(
            "./ElementEffects/Element/EffectLayer/Effect"
        ))


def test_does_not_write_source_in_place():
    with TemporaryDirectory() as td:
        source = Path(td) / "raw.xsq"
        _fixture(source)
        try:
            repair_xsq(source, source)
        except ValueError:
            pass
        else:
            raise AssertionError("Expected in-place protection")
