"""Guard the one-variant default without importing heavyweight audio modules."""
import ast
import unittest
from pathlib import Path


ENGINE = Path(__file__).resolve().parents[1] / "core" / "effect_engine.py"


class PrimeVariantDefaultsTests(unittest.TestCase):
    def test_variant_default_is_one(self):
        tree = ast.parse(ENGINE.read_text(encoding="utf-8"))
        matches = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "add_argument":
                continue
            if not node.args or not isinstance(node.args[0], ast.Constant):
                continue
            if node.args[0].value != "--variants":
                continue
            matches.append({kw.arg: kw.value for kw in node.keywords})
        self.assertEqual(len(matches), 1)
        self.assertEqual(ast.literal_eval(matches[0]["default"]), 1)
        self.assertEqual(ast.literal_eval(matches[0]["dest"]), "variant_count")

    def test_shortlist_remains_opt_in(self):
        tree = ast.parse(ENGINE.read_text(encoding="utf-8"))
        defaults = [
            kw.value for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "set_defaults"
            for kw in node.keywords if kw.arg == "auto_shortlist"
        ]
        self.assertEqual(len(defaults), 1)
        self.assertIs(ast.literal_eval(defaults[0]), False)


if __name__ == "__main__":
    unittest.main()
