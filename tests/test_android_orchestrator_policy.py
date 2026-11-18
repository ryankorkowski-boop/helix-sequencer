"""Exercise the production mobile argument builder without Android dependencies."""
import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

SOURCE = Path(__file__).resolve().parents[1] / "android/app/src/main/python/helix_mobile.py"


class AndroidOrchestratorPolicyTests(TestCase):
    def test_mobile_orchestration_policy(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == "build_args")
        scope = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), "exec"), scope)
        with TemporaryDirectory() as directory:
            job = Path(directory)
            (job / "input").mkdir()
            (job / "input/source.lms").touch()
            for mode, ac, opt_in, enabled in [
                ("xlights", False, False, False),
                ("xlights", False, True, True),
                ("xlights", True, True, False),
                ("lor", False, True, False),
                ("xlights", False, "false", False),
            ]:
                with self.subTest(mode=mode, ac=ac, opt_in=opt_in):
                    args = scope["build_args"]({
                        "mode": mode, "ac_compatible": ac,
                        "effects_orchestrator": opt_in,
                    }, job, job)
                    self.assertEqual("--no-effects-orchestrator" not in args, enabled)
                    self.assertEqual("--no-orchestrator-template-promotion" in args, enabled)
                    self.assertNotIn("--promote-orchestrated-template", args)
                    if ac or mode == "lor":
                        self.assertIn("--ac-lights-only", args)
                        self.assertIn("--no-birdsong", args)
