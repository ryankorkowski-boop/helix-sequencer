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


@pytest.mark.parametrize('compression',[0,1])
def test_selected_native_channels_are_decoded_without_expanding_the_movie(tmp_path,compression):
    path=tmp_path/'actual.fseq';native(path,bytes([0,0,255,0,128,64]),compression)
    report=inspect_stream(path,selectors={'lead':[0],'backing':[1],'empty':[]})
    assert report['selected_channel_max']==dict(lead=[0,255,128],backing=[0,0,64],empty=[0,0,0])
    with pytest.raises(ValueError,match='valid zero-based'):inspect_stream(path,selectors={'bad':[2]})


def test_selected_sparse_native_channels_keep_their_real_destinations(tmp_path):
    path=tmp_path/'sparse.fseq';payload=bytes([0,0,255,0,128,64])
    header=bytearray(46);header[:4]=b'PSEQ';struct.pack_into('<H',header,4,46)
    header[7]=2;header[18]=50;header[21]=1;header[22]=1
    struct.pack_into('<II',header,10,2,3);struct.pack_into('<II',header,32,0,len(payload))
    header[40:43]=(30).to_bytes(3,'little');header[43:46]=(2).to_bytes(3,'little')
    path.write_bytes(header+payload)
    report=inspect_stream(path,selectors={'lead':[30],'backing':[31],'unmapped':[0]})
    assert report['selected_channel_max']==dict(lead=[0,255,128],backing=[0,0,64],unmapped=[0,0,0])
