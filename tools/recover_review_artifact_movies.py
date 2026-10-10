"""Recover original MP4 bytes recursively from downloaded CI archives."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import zipfile


def members(data, name, prefix='', depth=0):
    if depth > 5:
        raise ValueError('Unexpected archive nesting depth')
    if name.lower().endswith('.mp4'):
        yield prefix+name, data
    elif name.lower().endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            assert z.testzip() is None
            for item in z.infolist():
                if not item.is_dir():
                    yield from members(z.read(item), item.filename,
                                       prefix+name+'::' if depth else '', depth+1)
    elif name.lower().endswith(('.tar', '.tgz', '.tar.gz')):
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as t:
            for item in t:
                if item.isfile():
                    yield from members(t.extractfile(item).read(), item.name,
                                       prefix+name+'::', depth+1)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--downloads', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, default=Path('/workspace/runtime'))
    args=parser.parse_args()
    inventory=args.runtime/'recovered_ci_mp4_inventory.json'
    old=json.loads(inventory.read_text()) if inventory.exists() else []
    seen={(i['artifact_id'],i['original_archive_path']) for i in old}
    added=[]
    for a in json.loads(args.selection.read_text()):
        path=args.downloads/f'{a["id"]}.zip'
        for original,data in members(path.read_bytes(),path.name):
            if (a['id'],original) in seen:
                continue
            h=hashlib.sha256(data).hexdigest()
            target=args.runtime/'recovered_recent_ci_mp4s'/str(a['id'])/(h[:8]+'_'+Path(original.split('::')[-1]).name)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            item={'path':str(target),'artifact_id':a['id'],'artifact_name':a['name'],
                  'artifact_created_at':a['created_at'],'original_archive_path':original,
                  'bytes':len(data),'sha256':h}
            added.append(item);seen.add((a['id'],original))
    inventory.write_text(json.dumps(old+added,indent=2)+'\n')
    print(json.dumps({'archives_crc_checked':len(json.loads(args.selection.read_text())),
                      'additional_mp4_copies':len(added),'total_mp4_copies':len(old+added)}))


if __name__=='__main__':
    main()
