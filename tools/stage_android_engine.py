"""Stage unchanged, tracked engine modules; never ship repository media/history."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {'core', 'audio', 'animation', 'effects', 'music', 'mapping', 'models',
            'xlights', 'tools', 'export', 'config', 'configs', 'profiles', 'presets',
            'knowledge', 'helix_knowledge', 'schemas', 'standards', 'ai', 'data',
            'learning', 'legacy_ac', 'render', 'showcase', 'helix', 'helix_composers'}
DATA_EXTENSIONS = {'.py', '.json', '.yaml', '.yml', '.csv', '.txt', '.xml'}

def stage(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    selected = []
    for name in names:
        p = Path(name)
        if not name or not (ROOT / p).is_file():
            continue
        if (p.parts[0] in PACKAGES or p.parts[0].startswith('helix_')) and p.suffix.lower() in DATA_EXTENSIONS:
            selected.append(name)
        elif name in {'template.xsq', 'xlights_rgbeffects.xml', 'LICENSE', 'NOTICE'}:
            selected.append(name)
        elif name.startswith('fixtures/band_geometry/') and p.suffix == '.json':
            selected.append(name)
    manifest = {'schema': 'helix.android.engine.v1', 'commit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(), 'files': {}}
    (output / "support-links.json").write_bytes((ROOT / "config/support_links.json").read_bytes())
    archive = output / 'helix-engine.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(selected):
            data = (ROOT / name).read_bytes()
            manifest['files'][name] = hashlib.sha256(data).hexdigest()
            info = zipfile.ZipInfo(name, (2026, 10, 13, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
        z.writestr('android-engine-manifest.json', json.dumps(manifest, indent=2))
    manifest['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'helix-engine-build.json').write_text(json.dumps(manifest, indent=2))
    print(f'Staged {len(selected)} tracked engine files ({archive.stat().st_size} bytes)')
    return manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    stage(parser.parse_args().output)
