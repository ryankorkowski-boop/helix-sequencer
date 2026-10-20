import unittest
from core.model_effect_policy import ModelCapability, choose_effect

class TestModelEffectPolicy(unittest.TestCase):
    def test_ac_never_uses_spatial_effect(self):
        for role in ('melody','build','hit','ambient','vocal'):
            self.assertIn(choose_effect(ModelCapability('AC16','line',16,False),role).effect,('On','Ramp'))
    def test_matrix_can_use_shader(self):
        self.assertEqual(choose_effect(ModelCapability('Matrix','matrix',1024,True,32,32),'build').effect,'Shader')
    def test_low_resolution_matrix_fallback(self):
        self.assertEqual(choose_effect(ModelCapability('Tiny','matrix',16,True,4,4),'build').effect,'Twinkle')
    def test_arch_render_style(self):
        self.assertEqual(choose_effect(ModelCapability('Arch','arch',50),'melody').render_style,'Single Line')
    def test_icicles(self):
        self.assertEqual(choose_effect(ModelCapability('Icicles','icicle',100),'melody').effect,'Meteors')
    def test_face_vocals(self):
        self.assertEqual(choose_effect(ModelCapability('Singer','face',120),'vocal').effect,'Faces')
    def test_reject_empty_model(self):
        with self.assertRaises(ValueError):
            choose_effect(ModelCapability('Empty','tree',0),'hit')

if __name__ == '__main__': unittest.main()
