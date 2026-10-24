import struct
import pytest
from tools.quality.native import inspect_fseq
from tools.quality.native_stream import inspect_stream


def native(path,payload,compression=0):
    header=bytearray(40);header[:4]=b'PSEQ';struct.pack_into('<H',header,4,40)
    header[7]=2;header[18]=50;header[20]=compression;header[21]=1
    struct.pack_into('<II',header,10,2,3)
    if compression:
        import zstandard
        payload=zstandard.ZstdCompressor().compress(payload)
    struct.pack_into('<II',header,32,0,len(payload));path.write_bytes(header+payload)


@pytest.mark.parametrize('compression',[0,1])
def test_streamed_actual_bytes_match_existing_inspector(tmp_path,compression):
    path=tmp_path/'actual.fseq';native(path,bytes([0,0,255,0,128,64]),compression)
    assert inspect_stream(path)==inspect_fseq(path)


def test_streaming_rejects_truncated_and_extra_decoded_channels(tmp_path):
    path=tmp_path/'bad.fseq';native(path,bytes(5),1)
    with pytest.raises(ValueError,match='Truncated'):inspect_stream(path)
    native(path,bytes(7),1)
    with pytest.raises(ValueError,match='Oversized'):inspect_stream(path)
