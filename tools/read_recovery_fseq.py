"""Read native xLights frame data for recovery comparisons."""
from pathlib import Path
import struct
import zlib

import numpy as np


def read_fseq(path: Path) -> tuple[np.ndarray,int]:
    """Read native xLights v2 (zstd/zlib/raw), including sparse channel ranges."""
    data=path.read_bytes()
    if data[:4]!=b"PSEQ" or len(data)<32 or data[7]!=2:
        raise ValueError("Expected xLights FSEQ v2")
    offset,header=struct.unpack_from("<H2xH",data,4)
    channels,frames=struct.unpack_from("<II",data,10)
    step,compression,blocks,ranges=data[18],data[20]&15,data[21]+((data[20]&240)<<4),data[22]
    if not channels or not frames or offset>len(data) or header<32:
        raise ValueError("Invalid FSEQ header")
    sparse=[];position=32+blocks*8
    for _ in range(ranges):
        start=int.from_bytes(data[position:position+3],"little")
        count=int.from_bytes(data[position+3:position+6],"little")
        sparse.append((start,count));position+=6
    payload=bytearray()
    if compression==0:
        payload.extend(data[offset:])
    else:
        for i in range(blocks):
            _,size=struct.unpack_from("<II",data,32+i*8)
            chunk=data[offset:offset+size];offset+=size
            if not size:continue
            if len(chunk)!=size:raise ValueError("Truncated FSEQ block")
            if compression==1:
                import zstandard
                payload.extend(zstandard.ZstdDecompressor().decompress(chunk))
            elif compression==2:
                payload.extend(zlib.decompress(chunk))
            else:raise ValueError(f"Unsupported FSEQ compression {compression}")
    if len(payload)!=frames*channels:
        raise ValueError(f"FSEQ data length {len(payload)} != {frames*channels}")
    packed=np.frombuffer(payload,dtype=np.uint8).reshape(frames,channels)
    if sparse:
        if sum(n for _,n in sparse)!=channels:raise ValueError("Sparse FSEQ channel mismatch")
        result=np.zeros((frames,max(s+n for s,n in sparse)),dtype=np.uint8)
        position=0
        for start,count in sparse:
            result[:,start:start+count]=packed[:,position:position+count];position+=count
    else:result=packed
    return result,step
