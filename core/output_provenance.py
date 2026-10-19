"""Local output credit and integrity notices; no DRM or network tracking."""
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
from functools import lru_cache

NOTICE='Made with Helix | Audio in. Lights out.'


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def notice():
    return dict(schema='helix.output-provenance.v1',generator='Helix',credit=NOTICE,
                software_license='PolyForm Noncommercial 1.0.0; historical and third-party rights retained',
                music_ownership_asserted=False,music_rights='Source-specific permission and evidence recorded separately',
                tracking=False,drm=False)


@lru_cache(maxsize=8)
def _logo(width,height,path):
    from PIL import Image
    logo=Image.open(path).convert('RGBA');size=max(18,round(width*.027))
    logo.thumbnail((size,size),Image.Resampling.LANCZOS)
    logo.putalpha(logo.getchannel('A').point(lambda a:round(a*.055)))
    return logo


def brand_frame(image,logo_path=None):
    """Tiny 5.5%-opacity original H, confined to a lower corner."""
    path=Path(logo_path) if logo_path else Path(__file__).resolve().parents[1]/'helix_h_logo.png'
    if not path.is_file():return image
    logo=_logo(image.width,image.height,str(path));result=image.convert('RGBA')
    result.alpha_composite(logo,(image.width-logo.width-8,image.height-logo.height-8))
    return result.convert('RGB')


def stamp_mp4(path, *, refresh=False):
    """Append a valid ISO free box; existing media positions stay unchanged.

    Refuse a terminal EOF-sized box instead of extending it with notice bytes.
    The mobile MediaMuxer path uses explicit, validated box lengths.
    """
    path=Path(path);payload=b'HELIX_PROVENANCE_V1\0'+json.dumps(notice(),sort_keys=True).encode()
    size=path.stat().st_size
    with path.open('rb') as stream:
        stream.seek(max(0,size-4096))
        tail=stream.read()
        if b'HELIX_PROVENANCE_V1\0' in tail and not refresh:return
        position=0
        old_notice=None
        while position<size:
            stream.seek(position);header=stream.read(8)
            if len(header)!=8:raise ValueError('truncated MP4 header')
            length,kind=struct.unpack('>I4s',header)
            if length==0:raise ValueError('EOF-sized MP4 requires a finite box before branding')
            minimum=8
            if length==1:
                extended=stream.read(8)
                if len(extended)!=8:raise ValueError('truncated extended box')
                length=struct.unpack('>Q',extended)[0];minimum=16
            if length<minimum or position+length>size:raise ValueError('invalid MP4 bounds')
            if kind==b'free' and position+length==size:
                stream.seek(position+minimum)
                if stream.read(len(b'HELIX_PROVENANCE_V1\0'))==b'HELIX_PROVENANCE_V1\0':old_notice=position
            position+=length
    if refresh and old_notice is not None:
        # Only a terminal Helix-owned metadata box is replaced. All media bytes,
        # offsets, decoder timing and third-party boxes retain their positions.
        with path.open('r+b') as stream:stream.truncate(old_notice)
    with path.open('ab') as stream:stream.write(struct.pack('>I4s',8+len(payload),b'free')+payload)


def stamp_xml(path):
    """Insert a legal ASCII comment without reserializing sequence data."""
    import xml.etree.ElementTree as ET
    path=Path(path);data=path.read_bytes()
    if b'Made with Helix | Audio in. Lights out.' in data:return
    ET.fromstring(data)
    if data.startswith((b'\xff\xfe',b'\xfe\xff')):return
    marker=b'<!-- '+NOTICE.encode()+b' | Music rights are separate. -->\n'
    offset=3 if data.startswith(b'\xef\xbb\xbf') else 0
    if data[offset:].startswith(b'<?xml'):
        declaration_end=data.find(b'?>',offset)
        if declaration_end<0:raise ValueError('unterminated XML declaration')
        offset=declaration_end+2
    temporary=path.with_name(path.name+'.provenance.tmp')
    temporary.write_bytes(data[:offset]+b'\n'+marker+data[offset:]);ET.fromstring(temporary.read_bytes());temporary.replace(path)


def write_manifest(folder,files):
    folder=Path(folder);payload=notice();payload['files']={str(Path(p).relative_to(folder)):sha256(p) for p in files if Path(p).is_file()}
    (folder/'HELIX_PROVENANCE.json').write_text(json.dumps(payload,indent=2)+'\n')
    return payload
