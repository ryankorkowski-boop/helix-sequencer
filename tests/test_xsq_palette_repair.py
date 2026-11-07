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


def test_duplicate_palette_entries_use_actual_native_table_index(tmp_path):
    source, dest = tmp_path / 'raw.xsq', tmp_path / 'neon.xsq'
    _fixture(source)
    tree = ET.parse(source)
    palettes = tree.getroot().find('ColorPalettes')
    ET.SubElement(palettes, 'ColorPalette').text = palettes[0].text
    tree.write(source)
    repair_xsq(source, dest)
    root = ET.parse(dest).getroot()
    table = root.findall('./ColorPalettes/ColorPalette')
    effects = root.findall('./ElementEffects/Element/EffectLayer/Effect')
    assert effects[0].get('palette') == '0'
    assert all('#FF2ED1' in table[int(e.get('palette'))].text for e in effects[1:])


def test_neon_target_guard_excludes_ac_mixed_groups_and_unknowns(tmp_path):
    source, dest, layout = tmp_path/'raw.xsq', tmp_path/'neon.xsq', tmp_path/'layout.xml'
    _fixture(source)
    tree=ET.parse(source); rows=tree.getroot().find('ElementEffects'); rows.clear()
    for name in ['RGB','AC','Mixed','RGB Group','Unknown']:
        row=ET.SubElement(rows,'Element',type='model',name=name)
        layer=ET.SubElement(row,'EffectLayer')
        ET.SubElement(layer,'Effect',name='On',startTime='0',endTime='500')
    tree.write(source)
    layout.write_text('<xrgb><models><model name="RGB" StringType="RGB Nodes"/>'
                      '<model name="AC" StringType="Single Color Red"/></models><modelGroups>'
                      '<modelGroup name="Mixed" models="RGB,AC"/>'
                      '<modelGroup name="RGB Group" models="RGB"/></modelGroups></xrgb>')
    audit=repair_xsq(source,dest,layout_file=layout)
    root=ET.parse(dest).getroot(); table=root.findall('./ColorPalettes/ColorPalette')
    colors={r.get('name'):table[int(r.find('./EffectLayer/Effect').get('palette'))].text
            for r in root.findall('./ElementEffects/Element')}
    assert '#FF2ED1' in colors['RGB'] and '#FF2ED1' in colors['RGB Group']
    assert all('#FFFFFF' in colors[n] for n in ['AC','Mixed','Unknown'])
    assert audit['changes']['non_rgb_neon_assignments_skipped']==3


def test_prechorus_uses_build_palette_not_chorus():
    from tools.xsq_palette_repair import _scene
    effect=ET.Element('Effect',startTime='100',endTime='500')
    assert _scene('RGB',effect,[(0,1000,'PRECHORUS')])==4
    assert _scene('RGB',effect,[(0,1000,'CHORUS')])==2
