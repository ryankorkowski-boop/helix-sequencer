"""Build pure msgpack and adapt librosa dependency metadata, preserving its code."""
from __future__ import annotations
import argparse
import base64
import csv
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

def build(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','--no-binary','msgpack',
                    'msgpack==1.0.8','-w',str(output)],check=True,
                   env={**os.environ,'MSGPACK_PUREPYTHON':'1'})
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable,'-m','pip','download','--no-deps','--only-binary',':all:',
                        'librosa==0.10.2.post1','-d',tmp],check=True)
        source=next(Path(tmp).glob('librosa*.whl'))
        with zipfile.ZipFile(source) as z:
            files={name:z.read(name) for name in z.namelist()}
        metadata=next(n for n in files if n.endswith('/METADATA'))
        lines=files[metadata].decode().splitlines(keepends=True)
        removed=[line for line in lines if line.startswith('Requires-Dist: numba')]
        if not removed:raise RuntimeError('Unexpected librosa dependency metadata')
        files[metadata]=''.join(line for line in lines if line not in removed).encode()
        record=next(n for n in files if n.endswith('/RECORD'))
        buf=io.StringIO();writer=csv.writer(buf)
        for name,data in files.items():
            if name!=record:
                digest=base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
                writer.writerow([name,'sha256='+digest,len(data)])
        writer.writerow([record,'','']);files[record]=buf.getvalue().encode()
        target=output/source.name
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
            for name,data in files.items():z.writestr(name,data)
        with zipfile.ZipFile(source) as a,zipfile.ZipFile(target) as b:
            assert all(a.read(n)==b.read(n) for n in a.namelist() if n.endswith(('.py','.pyi','.msgpack')))
        print('librosa source preserved; Android-only Numba dependency metadata adapted')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);build(p.parse_args().output)
