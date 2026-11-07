from pathlib import Path
import json
from tools.support_links import links
ROOT=Path(__file__).resolve().parents[1]

def test_shared_destinations_preserve_original_and_all_current_guis_expose_buttons():
    support=links();archived=(ROOT/'archive/legacy_versions/sequencer_launcher.py').read_text()
    assert set(support)=={'xlights','helix'}
    assert all(url in archived for url in support.values())
    desktop=(ROOT/'gui_launcher.py').read_text()
    native=(ROOT/'android/app/src/main/java/org/helixsequencer/android/SupportLinks.java').read_text()
    for label in ('Donate to xLights','Donate to Helix'):
        assert label in desktop and label in native
    for file in ('MainActivity.java','RemoteActivity.java'):
        assert 'SupportLinks.add(this,' in (ROOT/'android/app/src/main/java/org/helixsequencer/android'/file).read_text()


def test_android_staging_includes_same_support_configuration(tmp_path):
    from tools.stage_android_engine import stage
    stage(tmp_path)
    assert json.loads((tmp_path/'support-links.json').read_text())==links()
