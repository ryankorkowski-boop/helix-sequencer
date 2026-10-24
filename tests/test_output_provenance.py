import json,struct
from pathlib import Path
import pytest
from PIL import Image
from core.output_provenance import stamp_mp4,stamp_xml,brand_frame,write_manifest


def test_internal_mp4_notice_keeps_every_existing_byte_and_is_idempotent(tmp_path):
    p=tmp_path/'movie.mp4';original=struct.pack('>I4s',16,b'ftyp')+b'isom0000'+struct.pack('>I4sQ',1,b'mdat',24)+b'12345678'
    p.write_bytes(original);stamp_mp4(p);first=p.read_bytes();stamp_mp4(p)
    assert first.startswith(original) and p.read_bytes()==first
    assert first[len(original)+4:len(original)+8]==b'free'


def test_bad_or_eof_mp4_is_not_silently_corrupted(tmp_path):
    p=tmp_path/'movie.mp4'
    for original in (struct.pack('>I4s',0,b'mdat')+b'data',struct.pack('>I4s',100,b'mdat')+b'data'):
        p.write_bytes(original)
        with pytest.raises(ValueError):stamp_mp4(p)
        assert p.read_bytes()==original


def test_xml_notice_preserves_existing_sequence_and_lor_addresses(tmp_path):
    p=tmp_path/'show.lms';original=b'<?xml version="1.0"?><sequence><channel unit="3" circuit="7"/></sequence>'
    p.write_bytes(original);stamp_xml(p);first=p.read_bytes();stamp_xml(p)
    assert b'<channel unit="3" circuit="7"/>' in first and first==p.read_bytes()
    import xml.etree.ElementTree as ET
    assert ET.parse(p).find('.//channel').attrib=={'unit':'3','circuit':'7'}


def test_faint_logo_changes_only_its_small_corner(tmp_path):
    logo=tmp_path/'logo.png';Image.new('RGB',(100,100),'white').save(logo)
    image=Image.new('RGB',(640,360),'black');marked=brand_frame(image,logo)
    import numpy as np
    a=np.asarray(marked);assert a.max()<=15 and not a[:320].any() and not a[:,:600].any()


def test_manifest_does_not_claim_song_ownership_or_track_users(tmp_path):
    p=tmp_path/'show.xsq';p.write_text('<xsequence/>');a=write_manifest(tmp_path,[p])
    assert not a['music_ownership_asserted'] and not a['tracking'] and not a['drm']
    assert len(a['files']['show.xsq'])==64


def test_utf8_bom_and_declaration_remain_valid(tmp_path):
    import xml.etree.ElementTree as ET
    p=tmp_path/'show.xsq'
    original=b'\xef\xbb\xbf<?xml version="1.0" encoding="UTF-8"?><xsequence BaseChannel="4"/>'
    p.write_bytes(original);stamp_xml(p)
    assert p.read_bytes().startswith(b'\xef\xbb\xbf<?xml')
    assert ET.parse(p).getroot().get('BaseChannel')=='4'


def test_current_license_refresh_replaces_only_terminal_helix_notice(tmp_path):
    from core.output_provenance import notice
    p=tmp_path/'movie.mp4';media=struct.pack('>I4s',16,b'ftyp')+b'isom0000'+struct.pack('>I4s',12,b'mdat')+b'data'
    old=b'HELIX_PROVENANCE_V1\0'+json.dumps(dict(software_license='MIT')).encode()
    p.write_bytes(media+struct.pack('>I4s',8+len(old),b'free')+old)
    stamp_mp4(p,refresh=True);first=p.read_bytes();stamp_mp4(p,refresh=True)
    assert p.read_bytes()==first and first.startswith(media)
    assert first.count(b'HELIX_PROVENANCE_V1\0')==1
    assert b'PolyForm Noncommercial 1.0.0' in first
    assert not notice()['music_ownership_asserted']
