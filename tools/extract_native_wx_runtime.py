"""Recover only wx shared libraries from the authenticated retained build."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile


def extract(bundle,output):
    bundle,output=Path(bundle),Path(output)
    receipt=json.loads((bundle/'renderer.json').read_text())
    if receipt['upstream_commit']!='839c0f590dc454bb7adb8a16c4dd92a70b46156e':
        raise ValueError('Foreign retained native build')
    archive=bundle/'renderer.tar.gz'
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=receipt['archive_sha256']:
            raise ValueError('Retained native archive checksum failed')
    required={'libwx_gtk3u-3.3.so.4.0.0':'libwx_gtk3u-3.3.so.4',
              'libwx_gtk3u_gl-3.3.so.4.0.0':'libwx_gtk3u_gl-3.3.so.4'}
    prefix='xlights-src/wxWidgets-xlights_2026.17c/lib/'
    output.mkdir(parents=True,exist_ok=True);hashes={}
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            if not member.isfile() or member.name not in {prefix+n for n in required}:continue
            if member.size>256*1024**2:raise ValueError('Unexpected wx library size')
            name=required[member.name.removeprefix(prefix)];target=output/name
            with tar.extractfile(member) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
            subprocess.run(['strip','--strip-unneeded',str(target)],check=True)
            with target.open('rb') as src:hashes[name]=hashlib.file_digest(src,'sha256').hexdigest()
    if set(hashes)!=set(required.values()):raise ValueError('Retained build lacks required wx libraries')
    result=dict(schema='helix.native-wx-runtime.v1',upstream_commit=receipt['upstream_commit'],
                retained_archive_sha256=receipt['archive_sha256'],libraries=hashes)
    (output/'wx-runtime.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('bundle',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(extract(a.bundle,a.output),indent=2))
