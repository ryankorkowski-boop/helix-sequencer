"""Retain the compiled renderer's actual wxWidgets dependencies and hashes."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess


def collect(binary, output):
    binary, output = Path(binary), Path(output)
    report = subprocess.check_output(['ldd', str(binary)], text=True)
    if 'not found' in report:
        raise ValueError('Renderer has missing dependencies; cannot preserve a partial runtime')
    selected = {}
    for line in report.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[0].startswith('libwx_') and fields[1] == '=>':
            source = Path(fields[2])
            if not source.is_absolute() or not source.is_file():
                raise ValueError('Invalid resolved wxWidgets library')
            selected[fields[0]] = source
    if not selected:
        raise ValueError('No wxWidgets dependencies found on native renderer')
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, source in sorted(selected.items()):
        target = output / name
        shutil.copyfile(source, target)
        subprocess.run(['strip', '--strip-unneeded', str(target)], check=True)
        with target.open('rb') as stream:
            hashes[name] = hashlib.file_digest(stream, 'sha256').hexdigest()
    receipt = dict(schema='helix.native-wx-runtime.v1', source_binary=str(binary), libraries=hashes)
    (output / 'wx-runtime.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(collect(args.binary, args.output), indent=2))
