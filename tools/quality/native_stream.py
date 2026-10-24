"""Bounded-memory inspection for long, large native V2 sequences.

Every packed channel byte is decoded and counted. Sparse destinations need no
expanded zero array. Existing read_frames allocation guards remain unchanged.
"""
import hashlib
import io
import struct
from pathlib import Path
import numpy as np


def inspect_stream(path):
    path=Path(path);lit=[]
    with path.open('rb') as stream:
        header=stream.read(32)
        if len(header)!=32 or header[:4]!=b'PSEQ' or header[7]!=2:raise ValueError('Expected native V2 FSEQ')
        offset=int.from_bytes(header[4:6],'little')
        packed,frames=struct.unpack_from('<II',header,10);step=header[18]
        compression=header[20]&15;blocks=header[21]+((header[20]&240)<<4);count=header[22]
        if not 0<packed<=1_000_000 or not 0<frames<=200_000 or not step:
            raise ValueError('FSEQ streaming frame resource budget exceeded')
        if compression not in (0,1):raise ValueError('Large sequence streaming supports raw/ZSTD V2 only')
        if 32+blocks*8+count*6>offset or offset>path.stat().st_size:raise ValueError('FSEQ tables overlap data')
        table=stream.read(blocks*8)
        if len(table)!=blocks*8:raise ValueError('Truncated FSEQ block table')
        ranges=[]
        for i in range(count):
            value=stream.read(6)
            if len(value)!=6:raise ValueError('Truncated sparse range')
            ranges.append((int.from_bytes(value[:3],'little'),int.from_bytes(value[3:],'little')))
        if ranges and (sum(n for _,n in ranges)!=packed or any(n==0 for _,n in ranges)
                       or any(a+n>b for (a,n),(b,_) in zip(ranges,ranges[1:]))):
            raise ValueError('Invalid sparse FSEQ ranges')
        channels=max(a+n for a,n in ranges) if ranges else packed
        if channels>1_000_000:raise ValueError('Expanded sparse channel budget exceeded')
        stream.seek(offset)
        entries=[struct.unpack_from('<II',table,i*8) for i in range(blocks)]
        entries=[(a,b) for a,b in entries if b]
        if compression==0:entries=[(0,frames*packed)]
        if not entries or entries[0][0]!=0 or entries[-1][0]>=frames or any(a>=b for (a,_),(b,_) in zip(entries,entries[1:])):
            raise ValueError('Invalid FSEQ block frame boundaries')
        for i,(first,size) in enumerate(entries):
            final=entries[i+1][0] if i+1<len(entries) else frames
            if stream.tell()+size>path.stat().st_size:raise ValueError('Truncated FSEQ block')
            if compression==0:
                reader=stream
            else:
                # Bound compressed storage independently of the expanded show.
                if size>64*1024*1024:raise ValueError('Compressed FSEQ block budget exceeded')
                encoded=stream.read(size)
                import zstandard
                reader=zstandard.ZstdDecompressor().stream_reader(io.BytesIO(encoded))
            for frame in range(first,final):
                value=reader.read(packed)
                if len(value)!=packed:raise ValueError('Truncated decoded FSEQ frame')
                lit.append(int(np.count_nonzero(np.frombuffer(value,dtype=np.uint8))))
            if compression==1:
                if reader.read(1):raise ValueError('Oversized decoded FSEQ block')
                reader.close()
    dark=[];start=None
    for i,value in enumerate(lit+[1]):
        if not value and start is None:start=i
        elif value and start is not None:dark.append(dict(start_ms=start*step,end_ms=i*step));start=None
    with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
    return dict(schema='helix.fseq_channel_evidence.v1',basis='decoded_rendered_channel_bytes',sha256=sha,
        channels=channels,frames=frames,frame_ms=step,duration_ms=frames*step,
        nonzero_samples=sum(lit),nonzero_frames=sum(n>0 for n in lit),peak_lit_channels=max(lit),
        mean_lit_fraction=round(sum(lit)/(frames*channels),6),dark_windows=dark,
        visual_review='pending',controller_validation='not_tested')
