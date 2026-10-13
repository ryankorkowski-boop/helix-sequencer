from pathlib import Path
import xml.etree.ElementTree as ET
from helix_ui_text import INSTRUCTIONS,LEGAL,TAGLINE

ROOT=Path(__file__).resolve().parents[1]


def test_both_guis_package_the_original_h_and_matching_guidance():
    from PIL import Image
    a=Image.open(ROOT/'app_icon.ico').convert('RGB')
    for path in ['helix_h_logo.png','android/app/src/main/res/drawable/helix_h_logo.png']:
        assert Image.open(ROOT/path).convert('RGB').tobytes()==a.tobytes()
    assets=ROOT/'android/app/src/main/assets'
    assert (assets/'helix_instructions.txt').read_text()==INSTRUCTIONS
    assert (assets/'helix_legal.txt').read_text()==LEGAL
    assert TAGLINE=='Audio in. Lights out.'


def test_help_activity_is_internal_and_mit_permissions_are_preserved():
    ns='{http://schemas.android.com/apk/res/android}'
    root=ET.parse(ROOT/'android/app/src/main/AndroidManifest.xml').getroot()
    activity=next(e for e in root.findall('.//activity') if e.get(ns+'name')=='.InfoActivity')
    assert activity.get(ns+'exported')=='false'
    assert 'does not revoke' in LEGAL and 'commercial use/resale' in LEGAL
    assert 'rights-cleared' in LEGAL and 'exclusively owned' in LEGAL
