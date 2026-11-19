"""The PyInstaller spec is Python; a syntax error breaks every Windows build."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_spec_parses_and_passes_each_analysis_keyword_once():
    tree = ast.parse((ROOT / "windows_portable.spec").read_text(encoding="utf-8"))
    analysis = next(node for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and getattr(node.func, "id", "") == "Analysis")
    names = [keyword.arg for keyword in analysis.keywords]
    assert len(names) == len(set(names)), names
    assert {"datas", "hiddenimports", "excludes"} <= set(names)


def test_required_separation_and_transcription_tools_are_bundled():
    spec = (ROOT / "windows_portable.spec").read_text(encoding="utf-8")
    hidden = spec.split("hiddenimports = [", 1)[1].split("]", 1)[0]
    assert '"whisper"' in hidden and '"demucs"' in hidden
    excludes = spec.split("excludes=[", 1)[1].split("]", 1)[0]
    assert "whisper" not in excludes and "torch" not in excludes


def test_every_catalog_layout_is_a_real_file_the_spec_can_package():
    options = json.loads((ROOT / "config/gui_options.json").read_text(encoding="utf-8"))
    for item in options["layouts"] + options["stages"]:
        assert (ROOT / item["path"]).is_file(), item["key"]
