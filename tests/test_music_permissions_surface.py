from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_music_permissions_separate_from_software_license():
    music = (ROOT / "MUSIC_PERMISSIONS.md").read_text()
    software = (ROOT / "COMMERCIAL_LICENSING.md").read_text()
    assert "hardKor" in music and "Helix Music Mix" in music
    assert "commercial" in music.lower() and "monetized" in music.lower()
    assert "PolyForm Noncommercial" in music
    assert "MUSIC_PERMISSIONS.md" in software


def test_desktop_and_android_legal_disclose_music_terms():
    desktop = (ROOT / "helix_ui_text.py").read_text()
    android = (ROOT / "android/app/src/main/assets/helix_legal.txt").read_text()
    for content in (desktop, android):
        assert "Helix Music Mix by hardKor" in content
        assert "MUSIC_PERMISSIONS.md" in content
        assert "standalone resale" in content


def test_windows_package_includes_music_notice():
    spec = (ROOT / "windows_portable.spec").read_text()
    workflow = (ROOT / ".github/workflows/windows-portable.yml").read_text()
    packager = (ROOT / "tools/package_beta_installers.py").read_text()
    for content in (spec, workflow, packager):
        assert "MUSIC_PERMISSIONS.md" in content
