import unittest
from core.helix_effect_adapter import select_placement, normalize_kind

class AdapterTests(unittest.TestCase):
    def test_tree_name_alias(self):
        self.assertEqual(normalize_kind('Custom', 'Mega Tree 1'), 'tree')
    def test_kick_is_hit(self):
        result = select_placement(name='Arch 1', display_as='Arches', pixel_count=50, rgb=True, event='kick')
        self.assertEqual((result.target, result.choice.effect), ('Arch 1', 'Bars'))
    def test_matrix_shader_with_native_catalog(self):
        result = select_placement(name='Matrix', display_as='Matrix', pixel_count=1024, rgb=True,
                                  width=32, height=32, event='build', supported_effects={'Shader', 'On'})
        self.assertEqual(result.choice.effect, 'Shader')
        self.assertFalse(result.requires_native_validation)
    def test_native_catalog_fallback(self):
        result = select_placement(name='Matrix', display_as='Matrix', pixel_count=1024, rgb=True,
                                  width=32, height=32, event='build', supported_effects={'On'})
        self.assertEqual(result.choice.effect, 'On')
    def test_ac_never_receives_shader(self):
        result = select_placement(name='AC Channel 1', display_as='Matrix', pixel_count=1, rgb=False,
                                  width=32, height=32, event='build')
        self.assertEqual(result.choice.effect, 'Ramp')
    def test_invalid_event_fails(self):
        with self.assertRaises(ValueError):
            select_placement(name='Arch', display_as='Arch', pixel_count=50, rgb=True, event='unknown')
    def test_unknown_native_catalog_fails_closed(self):
        with self.assertRaises(ValueError):
            select_placement(name='Arch', display_as='Arch', pixel_count=50, rgb=True,
                             event='kick', supported_effects={'Unrelated'})

if __name__ == '__main__': unittest.main()
