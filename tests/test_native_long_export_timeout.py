from tools import native_preview
import http.client
from types import SimpleNamespace
from unittest.mock import Mock,patch
import pytest


def test_long_export_timeout_is_transport_only_not_an_xlights_setting(monkeypatch):
    calls=[]
    def request(method,url,payload,timeout):
        calls.append((payload,timeout));return {'res':200}
    monkeypatch.setattr(native_preview.rest,'_request_json',request)
    native_preview._command('http://localhost:49914','exportVideoPreview',timeout=1024,filename='movie.mp4')
    assert calls==[({'cmd':'exportVideoPreview','filename':'movie.mp4'},1024)]


def test_malformed_startup_http_is_retried_until_real_version_response(tmp_path):
    staged=tmp_path/'pilot.xsq';staged.write_text('<xsequence/>')
    app=SimpleNamespace(pid=123,poll=Mock(return_value=None),terminate=Mock(),wait=Mock())
    with patch.object(native_preview.subprocess,'Popen',return_value=app), \
         patch.object(native_preview.rest,'_request_json',side_effect=[http.client.BadStatusLine('GET /getVersion'),{'res':200}]) as request, \
         patch.object(native_preview,'_command',side_effect=[{'folder':str(tmp_path)},{'fullseq':str(staged)}]), \
         patch.object(native_preview,'_dismiss_startup_dialogs'), \
         patch.object(native_preview,'_assert_native_ready',side_effect=RuntimeError('validated handshake reached')):
        with pytest.raises(RuntimeError,match='validated handshake reached'):
            native_preview._native_export('/bin/xLights',tmp_path,staged,0)
    assert request.call_count==2
    app.terminate.assert_called_once()
