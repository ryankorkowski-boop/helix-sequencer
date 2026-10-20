"""Headless GUI command behavior, including cancellation before any work."""
from types import SimpleNamespace
from unittest.mock import patch
import gui_launcher as gui


class Var:
    def __init__(self, value): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


def app(tmp_path):
    audio, layout, template = [tmp_path / n for n in ('song.wav', 'layout.xml', 'template.xsq')]
    for path in (audio, layout, template): path.write_text('test input')
    values = dict(export_format='Both', sequence_mode='xLights', ac_on_only=False,
        lor_compatible=False, variants='1', audio=str(audio), layout=str(layout),
        template=str(template), output=str(tmp_path/'output'), profile='master',
        model_routing='', generate_mp4=False, vendor_bar=False, matrix=False,
        polish=False, shortlist=False, learn_xsq=False, birdsong=False, pitched_props=True)
    obj = SimpleNamespace(**{k+'_var': Var(v) for k,v in values.items()})
    obj._busy = False
    obj._log = lambda text: None
    obj.run_button = obj.status_label = SimpleNamespace(configure=lambda **kw: None)
    obj._run_subprocess = lambda cmd: None
    return obj


def test_both_build_passes_explicit_map_and_on_only_to_normal_worker(tmp_path):
    obj = app(tmp_path)
    with patch.object(gui.filedialog, 'askopenfilename', return_value='/chosen/verified.csv'), \
         patch.object(gui.threading, 'Thread') as thread:
        gui.HelixGui._run_sequence(obj)
    command = thread.call_args.kwargs['args'][0]
    index = command.index('--helix-dual-channel-map')
    assert command[index+1] == '/chosen/verified.csv'
    assert '--helix-ac-on-only' in command
    assert '--palette-mode' not in command
    assert obj._busy is True
    thread.return_value.start.assert_called_once()


def test_cancelled_map_selection_does_not_start_build(tmp_path):
    obj = app(tmp_path)
    with patch.object(gui.filedialog, 'askopenfilename', return_value=''), \
         patch.object(gui.threading, 'Thread') as thread:
        gui.HelixGui._run_sequence(obj)
    thread.assert_not_called()
    assert obj._busy is False
