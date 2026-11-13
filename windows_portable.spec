# -*- mode: python ; coding: utf-8 -*-
"""One-folder Windows portable build: Helix.exe plus HelixCLI.exe."""
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

root = Path(SPECPATH).resolve()
datas = []


def add_file(relative):
    file = root / relative
    if file.is_file():
        datas.append((str(file), str(Path(relative).parent if Path(relative).parent.parts else ".")))


for relative in (
    "template.xsq",
    "xlights_rgbeffects.xml",
    "xlights_rgbeffects.xbkp",
    "xlights/effect_catalog.json",
    "CUSTOMER_README.txt",
    "WINDOWS_PORTABLE_README.txt",
    "THIRD_PARTY_LICENSES.md",
    "NOTICE",
    "LICENSE",
    "packaging/release_manifest.json",
    "CHANGELOG.md",
):
    add_file(relative)

for folder in (
    "allmodels",
    "helixville",
    "helixville2",
    "helixville3",
    "helixville4",
    "config",
    "data",
    "fixtures/band_geometry",
    "assets/drummers",
    "LICENSES",
):
    source = root / folder
    if source.is_dir():
        for file in source.rglob("*"):
            if file.is_file() and file.suffix.lower() in {
                ".xsq", ".xml", ".xbkp", ".json", ".yaml", ".yml",
                ".png", ".jpg", ".jpeg", ".gif", ".txt", ".md", ".xmodel",
            }:
                datas.append((str(file), str(file.parent.relative_to(root))))

datas += collect_data_files("imageio_ffmpeg")
datas += collect_data_files("imageio")
for distribution in ("imageio", "imageio-ffmpeg", "librosa", "zstandard"):
    datas += copy_metadata(distribution, recursive=True)

hiddenimports = ["imageio.plugins.ffmpeg", "imageio.plugins.pillow", "zstandard"]
for package in (
    "core", "xlights", "tools", "audio", "helix", "helix_composers",
    "helix_intent", "helix_knowledge", "helix_layout", "helix_mapping",
    "helix_music", "helix_preview", "helix_render", "helix_sequencer",
    "helix_spatial", "helix_style", "librosa", "imageio_ffmpeg",
):
    hiddenimports.extend(collect_submodules(package, on_error="warn once"))

a = Analysis(
    ["windows_portable_entry.py"],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["whisper", "torch", "torchaudio", "torchvision", "tensorflow"],
    noarchive=False,
)
pyz = PYZ(a.pure)
icon = str(root / "app_icon.ico")
version_file = str(root / "packaging" / "helix_version_info.txt")

gui_exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Helix",
    console=False,
    debug=False,
    icon=icon,
    version=version_file,
)
worker_exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="HelixCLI",
    console=True,
    debug=False,
    icon=icon,
    version=version_file,
)
coll = COLLECT(
    gui_exe, worker_exe, a.binaries, a.datas,
    strip=False, upx=False, name="Helix",
)
