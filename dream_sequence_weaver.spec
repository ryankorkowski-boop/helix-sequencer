# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
root = Path(globals().get("SPECPATH", ".")).resolve()

datas = [
    (str(root / "SEQUENCER_INSTRUCTIONS.txt"), "."),
    (str(root / "launch_sequencer_app.cmd"), "."),
    (str(root / "launch_sequencer_app.vbs"), "."),
    (str(root / "app_icon.ico"), "."),
    (str(root / "c82.ico"), "."),
    (str(root / "c82.png"), "."),
]
for mascot_name in ("helixmascot.jpg", "helixmascot.jpeg", "helixmascot.png"):
    mascot_path = root / mascot_name
    if mascot_path.exists():
        datas.append((str(mascot_path), "."))
        break
datas += collect_data_files("imageio_ffmpeg")

hiddenimports = [
    "v1",
    "variant_engine",
    "audio_intelligence",
    "xlights_feature_bridge",
    "imageio_ffmpeg",
    "requests",
    "librosa",
    "numpy",
]

a = Analysis(
    ["sequencer_launcher.py"],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["torch", "torchaudio", "torchvision", "whisper"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="HelixSequenceWeaverBeta",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "app_icon.ico"),
)
