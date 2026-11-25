"""Opt-in official xLights 2026.18 GTK House Preview sizing on isolated Xvfb.

No post-export spatial upscaling. Never use on an interactive user desktop.
The stock fresh-profile dock geometry is a version-specific contract; fail
closed on unknown/ambiguous geometry. Native video dimensions still require
ffprobe verification. Camera fit is a diagnostic, not visual acceptance.
"""
import ctypes as C
import os
from pathlib import Path
import re
import subprocess
import time


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT, timeout=10)


def rect(window):
    text = run('xwininfo', '-id', window)
    return tuple(int(re.search(pattern, text)[1]) for pattern in (
        r'Absolute upper-left X:\s*(-?\d+)', r'Absolute upper-left Y:\s*(-?\d+)',
        r'Width:\s*(\d+)', r'Height:\s*(\d+)'))


def children(window):
    return [(m[1], *(int(m[i]) for i in range(2, 6))) for m in re.finditer(
        r'^\s+(0x[0-9a-f]+) \(has no name\): \(\)\s+(\d+)x(\d+)([+-]\d+)([+-]\d+)\s',
        run('xwininfo', '-id', window, '-tree'), re.M | re.I)]


def house_pane(candidates):
    left = [c for c in candidates if 160 <= c[1] <= 400 and c[2] >= 250 and 0 <= c[3] <= 4]
    pairs = [(a, b) for a in left for b in left
             if a[1:4] == b[1:4] and b[4] > a[4]+a[2]]
    if len(pairs) != 1:
        raise ValueError('Unknown or ambiguous stock xLights dock geometry')
    return pairs[0][1][0]


def click_or_scroll(x, y, button, count=1):
    lib = C.CDLL('libX11.so.6'); xt = C.CDLL('libXtst.so.6')
    lib.XOpenDisplay.restype = C.c_void_p
    lib.XFlush.argtypes = [C.c_void_p]; lib.XCloseDisplay.argtypes = [C.c_void_p]
    d = lib.XOpenDisplay(None)
    if not d:
        raise RuntimeError('Cannot open isolated X11 display')
    try:
        xt.XTestFakeMotionEvent.argtypes = [C.c_void_p, C.c_int, C.c_int, C.c_int, C.c_ulong]
        xt.XTestFakeButtonEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
        xt.XTestFakeMotionEvent(d, 0, int(x), int(y), 0); lib.XFlush(d); time.sleep(.08)
        for _ in range(count):
            xt.XTestFakeButtonEvent(d, button, 1, 0); xt.XTestFakeButtonEvent(d, button, 0, 0)
            lib.XFlush(d); time.sleep(.045)
    finally:
        lib.XCloseDisplay(d)


def capture(r):
    import numpy as np
    x, y, w, h = r
    data = subprocess.check_output(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'x11grab',
        '-video_size', f'{w}x{h}', '-i', f'{os.environ["DISPLAY"]}.0+{x},{y}',
        '-frames:v', '1', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'], timeout=10)
    return np.frombuffer(data, np.uint8).reshape(h, w, 3)


def bbox(rgb):
    import numpy as np
    yy, xx = np.where(rgb.max(2) > 35)
    if len(xx):
        return [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())]
    return None


def configure(staged, pid, desired, version):
    if os.environ.get('HELIX_NATIVE_X11_DOCKED_REVIEW') != '1' or not os.environ.get('DISPLAY'):
        raise ValueError('Explicit isolated-Xvfb opt-in required')
    if version != '2026.18':
        raise ValueError('Stock GUI sizing calibrated only for xLights 2026.18')
    matches = []
    for line in run('wmctrl', '-lp').splitlines():
        fields = line.split(None, 4)
        if len(fields) == 5 and fields[2] == str(pid) and fields[4] == f'xLights - {Path(staged)}':
            matches.append(fields[0])
    if len(matches) != 1:
        raise ValueError('Cannot uniquely identify owned sequence window')
    window = matches[0]
    run('wmctrl', '-i', '-a', window)
    run('wmctrl', '-i', '-r', window, '-b', 'add,maximized_vert,maximized_horz'); time.sleep(.8)
    lower = house_pane(children(window))
    x, y, w, h = rect(lower)
    # Stock 2026.18 wxAUI caption maximize control; actual lower pane verified.
    click_or_scroll(x+w-26, y-10, 1); time.sleep(.5)
    main = rect(window)
    large = [c for c in children(window) if c[1] >= main[2]*.8 and c[2] >= main[3]*.6 and 0 <= c[3] <= 4]
    if len(large) != 1:
        raise ValueError('House pane did not maximize uniquely')
    canvas = large[0][0]; current = rect(canvas)
    dw, dh = desired
    run('wmctrl', '-i', '-r', window, '-b', 'remove,maximized_vert,maximized_horz')
    run('wmctrl', '-i', '-r', window, '-e', f'0,0,0,{dw+main[2]-current[2]},{dh+main[3]-current[3]}')
    time.sleep(.7); r = rect(canvas)
    if r[2:] != tuple(desired):
        raise ValueError(f'Native canvas dimensions differ: {r[2:]}')
    framing = []
    for _ in range(12):
        b = bbox(capture(r)); framing.append(b)
        if b is None:
            break
        x0, y0, x1, y1 = b; w, h = x1-x0+1, y1-y0+1
        center = (r[0]+dw//2, r[1]+dh//2)
        if min(x0, y0, dw-1-x1, dh-1-y1) < min(dw, dh)*.017:
            click_or_scroll(*center, 5, 2); break
        if w >= dw*.68 or h >= dh*.68:
            break
        click_or_scroll(*center, 4, 3 if max(w/dw, h/dh) < .45 else 1); time.sleep(.15)
    framing.append(bbox(capture(r)))
    return dict(window=window, canvas=canvas, geometry=list(r), framing=framing,
                visual_review='pending', native_size_verified_by_window_only=True)
