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


    def test_demucs_is_explicit_opt_in(self):
        source = (ENGINE.parent / "audio_intelligence.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "build_stem_analysis")
        calls = [node for node in ast.walk(fn) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name)
                 and node.func.id == "_try_demucs_stem_separation"]
        self.assertEqual(len(calls), 1)
        parents = {}
        for node in ast.walk(fn):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        current = calls[0]
        guards = []
        while current in parents:
            current = parents[current]
            if isinstance(current, ast.If):
                guards.append(ast.unparse(current.test))
        self.assertTrue(any("HELIX_USE_DEMUCS" in guard for guard in guards))

    def test_local_stem_cache_requires_source_identity(self):
        source = (ENGINE.parent / "audio_intelligence.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "build_stem_analysis")
        body = ast.unparse(fn)
        self.assertIn('hashlib.sha256()', body)
        self.assertIn("source_sha256", body)
        self.assertIn("manifest.get(", body)
        self.assertIn("st_mtime_ns", body)
        self.assertIn("audio_path.stat()", body)
        self.assertIn('all(p.is_file()', body)

if __name__ == "__main__":
    unittest.main()
