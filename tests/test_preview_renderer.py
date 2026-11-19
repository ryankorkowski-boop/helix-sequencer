from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.preview_renderer import parse_models


def test_native_note_export_remains_visible_only_on_its_selected_rung(tmp_path):
    import numpy as np
    from core.native_pitched_props import apply_native_pitched_props
    from tests.test_magic_keyboard_export import fixture
    from tools.preview_renderer import parse_sequence, LayoutData, ModelGeom, build_leaf_intensity_matrix
    import json

    source, layout = fixture(tmp_path)
    tree = ET.parse(source)
    ET.SubElement(tree.find('head'), 'sequenceDuration').text = '1.0'
    tree.write(source)
    plan = tmp_path/'band.json'
    plan.write_text(json.dumps({'cues': {'keyboardist': [
        dict(start_ms=100, end_ms=140, pitch_midi=60, pitch_source='helix_harmonic_polyphony'),
        dict(start_ms=180, end_ms=220, pitch_midi=60, pitch_source='helix_harmonic_polyphony')]}}))
    apply_native_pitched_props(source, layout, plan)
    name = 'HX_CENTER_KEYBOARD_HELIX/KEY_MIDI_060'
    parsed = parse_sequence(source)
    assert [(e.start_ms, e.end_ms) for e in parsed.model_effects[name]] == [(100, 140), (180, 220)]
    assert parsed.model_effects[name][0].settings.startswith('E_TEXTCTRL_Eff_On_Start=100')
    geometry = {n: ModelGeom(n, i, 0, i, 1, ((i, 0), (i, 1)), 'Custom', (255, 255, 255))
                for i, n in enumerate([name, 'HX_CENTER_KEYBOARD_HELIX/KEY_MIDI_064'])}
    names, values = build_leaf_intensity_matrix(LayoutData(geometry, {}, (0, 0, 1, 1)), parsed, fps=100)
    assert np.all(values[names.index(name), 10:14] > 0)
    assert not np.any(values[names.index(name), 14:18])
    assert np.all(values[names.index(name), 18:22] > 0)
    assert not np.any(values[names.index('HX_CENTER_KEYBOARD_HELIX/KEY_MIDI_064')])


def test_nested_native_submodel_layers_share_named_preview_target(tmp_path):
    from tools.preview_renderer import parse_sequence

    path = tmp_path/'nested.xsq'
    path.write_text('<xsequence><head><sequenceDuration>1</sequenceDuration></head>'
                    '<ElementEffects><Element type="model" name="Keys">'
                    '<SubModelEffectLayer name="KEY_60"><EffectLayer>'
                    '<Effect name="On" startTime="100" endTime="140"/>'
                    '</EffectLayer></SubModelEffectLayer></Element></ElementEffects></xsequence>')
    assert set(parse_sequence(path).model_effects) == {'Keys/KEY_60'}


class PreviewRendererTests(unittest.TestCase):
    def _write_layout(self, root: ET.Element) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        layout_path = Path(tempdir.name) / "xlights_rgbeffects.xml"
        ET.ElementTree(root).write(layout_path, encoding="utf-8", xml_declaration=True)
        return layout_path

    def test_parse_models_uses_polyline_pointdata_for_arch_segment(self) -> None:
        layout_path = Path(__file__).resolve().parents[1] / "xlights_rgbeffects.xml"
        layout = parse_models(layout_path)
        self.assertIn("Arch 2 Sec 5", layout.leaf_models)
        model = layout.leaf_models["Arch 2 Sec 5"]
        self.assertGreaterEqual(len(model.points), 3)
        self.assertNotEqual((model.x1, model.y1), (model.x2, model.y2))

    def test_parse_models_includes_helixia_submodels_for_dense_previews(self) -> None:
        layout_path = Path(__file__).resolve().parents[1] / "helixville4" / "xlights_rgbeffects.xml"
        layout = parse_models(layout_path)

        self.assertIn("HX_HOUSE_1_2_MATRIX/TOP", layout.leaf_models)
        self.assertEqual(layout.resolve_leaves("HX_HOUSE_1_2_MATRIX/TOP"), ["HX_HOUSE_1_2_MATRIX/TOP"])

    def test_parse_models_projects_3d_points_into_front_view(self) -> None:
        root = ET.Element("xrgb")
        models = ET.SubElement(root, "models")
        ET.SubElement(
            models,
            "model",
            {
                "name": "Depth Ribbon",
                "DisplayAs": "Custom",
                "WorldPosX": "10",
                "WorldPosY": "20",
                "WorldPosZ": "30",
                "PointData": "0,0,0,20,15,40,40,0,80",
                "StringType": "RGB Nodes",
            },
        )
        layout = parse_models(self._write_layout(root))
        model = layout.leaf_models["Depth Ribbon"]
        self.assertEqual(model.points[0], (10.0, 20.0))
        self.assertEqual(model.points[-1], (50.0, 20.0))
        self.assertGreaterEqual(len(model.points), 3)


if __name__ == "__main__":
    unittest.main()
