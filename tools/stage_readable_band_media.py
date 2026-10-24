"""Stage verified movies and bounded ZIP transport parts in a media checkout."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil
from pathlib import Path
from tools.package_readable_band import ROOT,OUT,expected_movies,sha


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['movies','archive']);p.add_argument('--checkout',type=Path,required=True);args=p.parse_args()
    root=args.checkout.resolve();assert (root/'.git').exists()
    dest=root/'band_instrument_review';dest.mkdir(exist_ok=True)
    evidence=ROOT/'evidence/band_instrument_review'
    if args.mode=='movies':
        files=expected_movies()
        for source in files:
            for source,folder in [(source,'movies'),(source.with_suffix('.verification.json'),'verification')]:
                target=dest/folder/source.name;target.parent.mkdir(exist_ok=True)
                if target.exists():assert sha(target)==sha(source)
                else:
                    try:os.link(source,target)
                    except OSError:shutil.copyfile(source,target)
        shutil.copyfile(evidence/'delivery_manifest.json',dest/'manifest.json')
        shutil.copyfile(ROOT/'docs/BAND_INSTRUMENT_REVIEW_HANDOFF.md',dest/'HANDOFF.md')
        print('STAGED',len(files),'movies and proofs',flush=True)
    else:
        report=json.loads((evidence/'archive_verification.json').read_text());archive=OUT/report['file']
        assert sha(archive)==report['sha256'] and archive.stat().st_size==report['bytes']
        folder=root/'archive_parts/Band_Instrument_Review';folder.mkdir(parents=True,exist_ok=True)
        parts=[]
        with archive.open('rb') as source:
            n=0
            while data:=source.read(47*1024*1024):
                n+=1;path=folder/f'part_{n:03}.bin';path.write_bytes(data)
                parts.append(dict(file=path.relative_to(root).as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        transport=dict(archives=[dict(file=report['file'],bytes=report['bytes'],sha256=report['sha256'],parts=parts)])
        (root/'archive_transport.json').write_text(json.dumps(transport,indent=2)+'\n')
        shutil.copyfile(ROOT/'docs/BAND_INSTRUMENT_REVIEW_DOWNLOADS.md',root/'RELEASE.md')
        shutil.copyfile(ROOT/'docs/BAND_INSTRUMENT_REVIEW_DOWNLOADS.md',dest/'README.md')
        shutil.copyfile(ROOT/'docs/BAND_INSTRUMENT_REVIEW_HANDOFF.md',dest/'HANDOFF.md')
        shutil.copyfile(evidence/'archive_verification.json',dest/'archive_verification.json')
        print('STAGED',len(parts),'parts',report['bytes'],report['sha256'],flush=True)


if __name__=='__main__':main()
