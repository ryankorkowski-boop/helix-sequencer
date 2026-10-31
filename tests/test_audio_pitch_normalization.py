"""Regression guard: pitch normalization scans the matrix once per extraction."""
import ast
from pathlib import Path


def test_pitch_matrix_max_is_outside_frame_loop():
    source = Path(__file__).resolve().parents[1] / "core" / "audio_intelligence.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    fn = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_extract_note_candidates")
    loops = [node for node in ast.walk(fn) if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "frame_idx"]
    assert len(loops) == 1
    frame_loop = loops[0]
    assert any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "max_mag" for t in node.targets)
        for node in fn.body if getattr(node, "lineno", 0) < frame_loop.lineno
    )
    assert not any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "max_mag" for t in node.targets)
        for node in ast.walk(frame_loop)
    )
