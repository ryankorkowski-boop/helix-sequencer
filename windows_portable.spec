# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

root = Path(SPECPATH).resolve()
datas = []
for relative in ("template.xsq", "xlights_rgbeffects.xml", "xlights_rgbeffects.xbkp", "xlights/effect_catalog.json", "CUSTOMER_README.txt", "THIRD_PARTY_LICENSES.md", "NOTICE"):
    file = root / relative
    if file.is_file():
        datas.append((str(file), str(Path(relative).parent)))
for folder in ("allmodels", "helixville"):
    source = root / folder
    if source.is_dir():
        for file in source.rglob("*"):
            if file.is_file() and file.suffix.lower() in (".xsq", ".xml", ".xbkp", ".json", ".png", ".jpg"):
                datas.append((str(file), str(file.parent.relative_to(root))))
datas += collect_data_files("imageio_ffmpeg")
hiddenimports = []
for package in ("core", "xlights", "tools", "librosa", "imageio_ffmpeg"):
    hiddenimports += collect_submodules(package)
a = Analysis(
    ["windows_portable_entry.py"],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Helix", console=False, debug=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Helix")
