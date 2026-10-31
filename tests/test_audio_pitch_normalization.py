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


def test_pitch_candidates_validate_finite_hz_before_midi_conversion():
    source = Path(__file__).resolve().parents[1] / "core" / "audio_intelligence.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    fn = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_extract_note_candidates")
    midi_calls = [
        node for node in ast.walk(fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "hz_to_midi"
    ]
    assert len(midi_calls) == 1
    checks = [
        node for node in ast.walk(fn)
        if isinstance(node, ast.If) and node.lineno < midi_calls[0].lineno
        and "isfinite(best_hz)" in ast.unparse(node.test)
    ]
    assert checks


def test_nonfinite_pitch_magnitudes_are_masked_before_argmax():
    source = Path(__file__).resolve().parents[1] / "core" / "audio_intelligence.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    fn = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_extract_note_candidates")
    assignments = [
        node for node in ast.walk(fn)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "finite_column" for t in node.targets)
    ]
    assert len(assignments) == 1
    assert "isfinite(mags)" in ast.unparse(assignments[0])
    argmax_calls = [
        node for node in ast.walk(fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "argmax"
    ]
    assert len(argmax_calls) == 1
    assert "finite_column" in ast.unparse(argmax_calls[0])


def test_pitch_sanitization_uses_frame_bounded_buffers():
    source = Path(__file__).resolve().parents[1] / "core" / "audio_intelligence.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    fn = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_extract_note_candidates")
    body = ast.unparse(fn)
    assert "finite_peaks = np.zeros(stft_mag.shape[1]" in body
    assert "peak_indices = np.zeros(stft_mag.shape[1]" in body
    assert "np.where(np.isfinite(pitch_mag)" not in body
