"""Full-song channel evidence stays bounded without expanding sparse movies."""
import hashlib
import json
from pathlib import Path
import struct
from unittest.mock import patch
import zlib

import numpy as np
import pytest
from tools.quality import native


def write_v2(path, channels, frames, blocks, *, ranges=(), compression=2):
    header = bytearray(32 + len(blocks)*8 + len(ranges)*6)
    header[:4] = b'PSEQ'
    struct.pack_into('<H',header,4,len(header))
    header[6:8] = bytes([2,2])
    struct.pack_into('<II',header,10,channels,frames)
    header[18] = 50
    count=len(blocks)
    header[20:23]=bytes([compression | ((count >> 8) << 4), count & 255,len(ranges)])
    for i,(first,payload) in enumerate(blocks):struct.pack_into('<II',header,32+i*8,first,len(payload))
    for i,(first,count) in enumerate(ranges):
        offset=32+len(blocks)*8+i*6
        header[offset:offset+6]=first.to_bytes(3,'little')+count.to_bytes(3,'little')
    with path.open('wb') as stream:
        stream.write(header)
        for _,payload in blocks:stream.write(payload)
        stream.write(b'embedded native metadata')


def test_full_song_larger_than_old_128mib_limit_streams_every_frame(tmp_path):
    channels,frames,per_block=65536,2200,50
    block=(b'\x80'+bytes(channels-1))*per_block
    payload=zlib.compress(block)
    path=tmp_path/'full-song.fseq'
    write_v2(path,channels,frames,[(i,payload) for i in range(0,frames,per_block)])
    assert channels*frames > native.MAX_BYTES
    with pytest.raises(ValueError,match='oversized'):
        native.read_frames(path)  # Legacy diagnostic/full-memory API stays bounded.
    with patch.object(Path,'read_bytes',side_effect=AssertionError('whole-file read forbidden')):
        report=native.inspect_fseq(path)
    assert report['frames']==report['nonzero_frames']==frames
    assert report['nonzero_samples']==frames
    assert report['peak_lit_channels']==1
    assert report['dark_windows']==[]
    assert report['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()


def test_sparse_high_channel_span_never_allocates_full_movie(tmp_path):
    path=tmp_path/'sparse.fseq'
    write_v2(path,2,1000,[(0,zlib.compress(b'\xff\0'*1000))],ranges=[(499998,2)])
    with pytest.raises(ValueError,match='expanded sparse'):
        native.read_frames(path)
    report=native.inspect_fseq(path)
    assert report['channels']==500000
    assert report['nonzero_samples']==report['nonzero_frames']==1000
    assert report['mean_lit_fraction']==.000002


@pytest.mark.parametrize('compression',[0,1,2])
def test_streamed_counts_match_decoded_reference_for_native_codecs(tmp_path,compression):
    data=bytes([0,0,0,0,1,0,0,0,0,4,3,0,0,0,0,0])
    if compression==0:
        header=bytearray(32);header[:4]=b'PSEQ';struct.pack_into('<H',header,4,32)
        header[7]=2;struct.pack_into('<II',header,10,4,4);header[18]=25
        path=tmp_path/'raw.fseq';path.write_bytes(header+data+b'embedded metadata')
    else:
        compressor=(zlib.compress if compression==2 else pytest.importorskip('zstandard').ZstdCompressor().compress)
        path=tmp_path/'compressed.fseq'
        write_v2(path,4,4,[(0,compressor(data[:8])),(2,compressor(data[8:]))],compression=compression)
    decoded,channels,frames,step=native.read_frames(path)
    lit=np.count_nonzero(np.frombuffer(decoded,np.uint8).reshape(frames,channels),axis=1)
    report=native.inspect_fseq(path)
    assert report['nonzero_samples']==int(lit.sum())
    assert report['nonzero_frames']==int(np.count_nonzero(lit))
    assert report['peak_lit_channels']==int(lit.max())
    assert report['duration_ms']==frames*step


def test_single_compressed_block_cannot_exceed_original_memory_bound(tmp_path):
    path=tmp_path/'oversized-block.fseq'
    write_v2(path,65536,2200,[(0,zlib.compress(b'\0'))])
    with pytest.raises(ValueError,match='bounded inspection memory'):
        native.inspect_fseq(path)


def test_truncated_block_cannot_generate_partial_evidence(tmp_path):
    path=tmp_path/'truncated.fseq'
    write_v2(path,4,4,[(0,zlib.compress(bytes(16)))])
    path.write_bytes(path.read_bytes()[:42])
    with pytest.raises(ValueError,match='Truncated'):
        native.inspect_fseq(path)
