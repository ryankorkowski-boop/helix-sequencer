# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

block_cipher = None
root = Path(globals().get("SPECPATH", ".")).resolve()
version_file = root / "pyinstaller_version_info.txt"

datas = [
    (str(root / "SEQUENCER_INSTRUCTIONS.txt"), "."),
    (str(root / "launch_sequencer_app.cmd"), "."),
    (str(root / "launch_sequencer_app.vbs"), "."),
    (str(root / "app_icon.ico"), "."),
    (str(root / "c82.ico"), "."),
    (str(root / "c82.png"), "."),
    (str(root / "xlights" / "effect_catalog.json"), "xlights"),
]
for mascot_name in ("helixmascot.jpg", "helixmascot.jpeg", "helixmascot.png"):
    mascot_path = root / mascot_name
    if mascot_path.exists():
        datas.append((str(mascot_path), "."))
        break
for helix_media_name in (
    "helix_twist.mp4",
    "grok-video-9256730a-68a5-49ec-855c-ad156e1fa006.mp4",
):
    helix_media_path = root / helix_media_name
    if helix_media_path.exists():
        datas.append((str(helix_media_path), "."))
        break
datas += collect_data_files("imageio_ffmpeg")
datas += copy_metadata("imageio")
datas += copy_metadata("imageio_ffmpeg")
try:
    datas += copy_metadata("scikit-learn")
except Exception:
    pass

hiddenimports = [
    "core.audio_intelligence",
    "core.chronoflow",
    "core.effect_engine",
    "core.gui_launcher",
    "core.engine_profiles",
    "core.model_parser",
    "core.sequence_builder",
    "core.snowman_band",
    "tools.preview_renderer",
    "tools.utilities",
    "xlights.layout_sync",
    "xlights.timing_tracks",
    "xlights.xml_io",
    "xlights.xsq_writer",
    "imageio_ffmpeg",
    "requests",
    "librosa",
    "numpy",
    "scipy",
    "sklearn",
    "sklearn.decomposition",
    "sklearn.preprocessing",
]

a = Analysis(
    ["main.py"],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch",
        "torchaudio",
        "torchvision",
        "whisper",
        # Numba's TBB backend is optional; excluding it avoids unresolved tbb12.dll warnings.
        "numba.np.ufunc.tbbpool",
    ],
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
    # The active maintained entrypoint is currently CLI-based.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "app_icon.ico"),
    version=str(version_file),
)
