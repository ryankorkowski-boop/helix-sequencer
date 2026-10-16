"""Exact source-score channel export, independently readable as FSEQ v2.

This is Helix-generated channel data, not a claim of native xLights rendering.
The matching native layout can import this file as a channel data layer.
"""
import struct
from pathlib import Path
import numpy as np
import zstandard
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_helpers.ultimate_showcase_preview import _rgb


def export_channels(g,levels,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);write_layout(g,folder)
    if levels.shape!=(len(g.models),720):raise ValueError('expected model/720-frame score')
    count=720;channels=max(m.start-1+m.channels for m in g.models);chunks=[]
    for begin in range(0,count,80):
        n=min(80,count-begin);frames=np.zeros((n,channels),'u1')
        for j,m in enumerate(g.models):
            if m.kind!='pixel':continue
            colors=_rgb(m.colors).astype('f4')
            frames[:,m.start-1:m.start-1+m.channels]=(colors[None]*levels[j,begin:begin+n,None,None]).astype('u1').reshape(n,-1)
        chunks.append((begin,zstandard.ZstdCompressor(level=3).compress(frames.tobytes())))
    offset=32+len(chunks)*8;header=bytearray(32);header[:4]=b'PSEQ'
    struct.pack_into('<HBBHII',header,4,offset,0,2,32,channels,count)
    header[18]=50;header[20]=1;header[21]=len(chunks);path=folder/'source_score.fseq'
    with path.open('wb') as f:
        f.write(header)
        for start,chunk in chunks:f.write(struct.pack('<II',start,len(chunk)))
        for start,chunk in chunks:f.write(chunk)
    np.savez_compressed(folder/'model_score.npz',levels=levels)
    return path
