"""Command routing and responsive worker behavior in the combined GUI."""
import queue
import sys
from unittest.mock import patch

import pytest
import gui_launcher as gui


@pytest.mark.parametrize('module,flag',gui.TOOL_MODES.items())
def test_frozen_tools_use_bundled_worker(module,flag):
    with patch.object(sys,'frozen',True,create=True),patch.object(sys,'executable','/portable/Helix.exe'):
        assert gui._module_command(module)==['/portable/HelixCLI.exe',flag]


def test_unlisted_module_cannot_launch():
    with pytest.raises(ValueError):gui._module_command('unlisted.module')


def test_log_drain_yields_after_bounded_batch():
    class App:
        _events=queue.Queue()
        seen=[]
        def _log(self,text):self.seen.append(text)
        def after(self,*args):self.scheduled=args
        def _drain_events(self):pass
    app=App()
    for i in range(200):app._events.put(('log',str(i)))
    gui.HelixGui._drain_events(app)
    assert len(app.seen)==100 and app._events.qsize()==100
    assert app.scheduled[0]==100


def test_subprocess_worker_never_calls_tk():
    class App:
        _events=queue.Queue()
    app=App()
    gui.HelixGui._run_subprocess(app,[sys.executable,'-c','print("worker output")'])
    assert app._events.get(timeout=1)==('log','worker output')
    assert app._events.get(timeout=1)==('run_done',0)
