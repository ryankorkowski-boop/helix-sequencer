import ast
from pathlib import Path


def test_piano_black_keys_are_farther_from_snowman():
    """BandPerformanceScene's local +Z is forward/audience-facing."""
    tree=ast.parse(Path('models/band_performance_scene.py').read_text())
    piano=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id=='z' for t in n.targets)
               and isinstance(n.value,ast.IfExp)
               and isinstance(n.value.test,ast.Attribute)
               and n.value.test.attr=='is_black')
    black=ast.literal_eval(piano.value.body)
    white=ast.literal_eval(piano.value.orelse)
    assert black>white, 'Black keys must be behind white-key fronts, away from the performer'
    assert black-white>=.15
