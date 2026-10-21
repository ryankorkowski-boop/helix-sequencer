"""Opt-in native House Preview sizing for the unmodified Linux xLights build.

Float the owned House Preview pane, resize its real canvas, then restore the
show's saved 3D viewpoint. This does not capture, upscale or draw movie frames.
"""
from __future__ import annotations
import re
import subprocess
import time
from pathlib import Path


def command(args):
    return subprocess.check_output(args, text=True, timeout=10)


def tree_windows(tree):
    result = []
    for line in tree.splitlines():
        m = re.match(r'^(\s+)(0x[0-9a-fA-F]+)\s.*?\s(\d+)x(\d+)[+-]\d+[+-]\d+\s+([+-]\d+)([+-]\d+)\s*$', line)
        if m:
            result.append(dict(depth=len(m[1]), id=m[2], width=int(m[3]),
                               height=int(m[4]), x=int(m[5]), y=int(m[6])))
    return result


def prepare_canvas(pid: int, staged: Path, width: int, height: int):
    lines = [line.split(None, 4) for line in command(['wmctrl', '-lp']).splitlines()]
    owned = [row for row in lines if len(row) == 5 and row[2] == str(pid)]
    main = [row[0] for row in owned if str(staged) in row[4]]
    if len(main) != 1:
        raise ValueError('Cannot identify owned xLights sequence window')
    floating = [row[0] for row in owned if row[4] == 'House Preview']
    if not floating:
        windows = tree_windows(command(['xwininfo', '-id', main[0], '-tree']))
        # Fresh xLights sequencer docks Model Preview and House Preview down
        # the left edge. Select the lower canvas, then drag only its caption.
        canvases = [w for w in windows if 200 <= w['width'] <= 300
                    and w['height'] > 200 and w['x'] < 10]
        if not canvases:
            raise ValueError('Fresh xLights House Preview dock is not identifiable')
        pane = max(canvases, key=lambda w: w['y'])
        command(['xdotool', 'mousemove', str(pane['x'] + 60), str(pane['y'] - 10),
                 'mousedown', '1', 'mousemove', '650', '350', 'mouseup', '1'])
        time.sleep(1)
        owned = [line.split(None, 4) for line in command(['wmctrl', '-lp']).splitlines()]
        floating = [row[0] for row in owned if len(row) == 5
                    and row[2] == str(pid) and row[4] == 'House Preview']
    if len(floating) != 1:
        raise ValueError('Owned floating House Preview is absent or ambiguous')
    window = floating[0]
    entries = [w for w in tree_windows(command(['xwininfo', '-id', window, '-tree']))
               if w['width'] > 100 and w['height'] > 100]
    deepest = max(w['depth'] for w in entries)
    candidates = [w for w in entries if w['depth'] == deepest]
    if len(candidates) != 1:
        raise ValueError('Ambiguous native House Preview canvas')
    canvas = candidates[0]
    info = command(['xwininfo', '-id', window])
    fw = int(re.search(r'Width:\s*(\d+)', info)[1])
    fh = int(re.search(r'Height:\s*(\d+)', info)[1])
    command(['xdotool', 'windowmove', window, '0', '0', 'windowsize', window,
             str(fw + width - canvas['width']), str(fh + height - canvas['height'])])
    time.sleep(1)
    info = command(['xwininfo', '-id', canvas['id']])
    actual = tuple(int(re.search(key + r':\s*(\d+)', info)[1]) for key in ('Width', 'Height'))
    if actual != (width, height):
        raise ValueError('Native House Preview canvas did not retain requested size')
    command(['xdotool', 'mousemove', '--window', canvas['id'], '40', '40', 'click', '3'])
    time.sleep(.2)
    # xLights 2026.18: 3D, House Preview, Reset, Restore Default ViewPoint.
    command(['xdotool', 'key', 'Home', 'Down', 'Down', 'Down', 'Return'])
    time.sleep(.5)
    return dict(method='native floating House Preview', window=window,
                canvas=canvas['id'], width=width, height=height, saved_viewpoint_restored=True)
