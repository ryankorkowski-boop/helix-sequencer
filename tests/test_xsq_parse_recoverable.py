import xml.etree.ElementTree as ET

import pytest

from xlights.xml_io import XsqParseError, load_xsq


def test_malformed_xsq_is_recoverable(tmp_path):
    path = tmp_path / 'broken.xsq'
    path.write_text('<xsequence>', encoding='utf-8')
    with pytest.raises(XsqParseError, match='broken.xsq') as caught:
        load_xsq(path)
    assert isinstance(caught.value.__cause__, ET.ParseError)


def test_missing_xsq_is_recoverable(tmp_path):
    with pytest.raises(XsqParseError, match='missing.xsq') as caught:
        load_xsq(tmp_path / 'missing.xsq')
    assert isinstance(caught.value.__cause__, FileNotFoundError)
