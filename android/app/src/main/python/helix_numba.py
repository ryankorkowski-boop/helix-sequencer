"""Android-only execution of librosa 0.10.2 kernels without LLVM.

This is a deliberately bounded compatibility layer, not a replacement analyser.
It executes the original Python kernel bodies and preserves gufunc broadcasting,
output buffers, type signatures and stencil boundary conditions. Unsupported APIs
fail explicitly. Desktop imports never see this module unless install() is called.
"""
from __future__ import annotations
import builtins
import functools
import re
import sys
import types
import numpy as np


def _kernel(fn):
    # Numba accepts integer-valued NumPy float loop bounds. CPython range does not.
    scope = dict(fn.__globals__)
    scope['range'] = lambda *args: builtins.range(*(int(a) for a in args))
    return types.FunctionType(fn.__code__, scope, fn.__name__, fn.__defaults__, fn.__closure__)


def jit(*args, **kwargs):
    if args and callable(args[0]):
        return _kernel(args[0])
    return _kernel


def guvectorize(signatures, dimensions, **options):
    left, right = dimensions.split('->')
    ins = [tuple(filter(None, s.split(','))) for s in re.findall(r'\(([^)]*)\)', left)]
    outs = [tuple(filter(None, s.split(','))) for s in re.findall(r'\(([^)]*)\)', right)]
    def decorate(fn):
        kernel = _kernel(fn)
        @functools.wraps(fn)
        def call(*args, **kwargs):
            input_arrays = [np.asarray(a) for a in args[:len(ins)]]
            dims, outer = {}, []
            for arr, core in zip(input_arrays, ins):
                if arr.ndim < len(core):
                    raise ValueError('Insufficient gufunc input dimensions')
                outer.append(arr.shape[:arr.ndim-len(core)] if core else arr.shape)
                for key, size in zip(core, arr.shape[-len(core):] if core else ()):
                    if key in dims and dims[key] != size:
                        raise ValueError('Inconsistent gufunc core dimensions')
                    dims[key] = size
            broadcast = np.broadcast_shapes(*outer)
            supplied = args[len(ins):] or kwargs.pop('out', ())
            if supplied and not isinstance(supplied, tuple):
                supplied = (supplied,)
            if kwargs:
                raise TypeError(f'Unsupported gufunc options: {kwargs}')
            sig = next((s for s in signatures if input_arrays[0].dtype.name in s.split(',')[0]), signatures[-1])
            type_names = re.findall(r'(bool_|u?int\d+|float\d+|complex\d+)', sig)
            outputs = list(supplied) if supplied else [np.zeros(broadcast + tuple(dims[d] for d in core),
                dtype=np.dtype(type_names[len(ins)+i].replace('bool_', 'bool'))) for i, core in enumerate(outs)]
            if len(outputs) != len(outs):
                raise TypeError('Wrong gufunc output count')
            expanded = [np.broadcast_to(a, broadcast + tuple(dims[d] for d in core))
                        for a, core in zip(input_arrays, ins)]
            for index in np.ndindex(broadcast):
                inputs = [a[index] for a in expanded]
                buffers = [a[index] if core else a[index + (None,)] for a, core in zip(outputs, outs)]
                kernel(*inputs, *buffers)
            return outputs[0] if len(outputs) == 1 else tuple(outputs)
        return call
    return decorate


def vectorize(signatures, **options):
    def decorate(fn):
        # These original librosa elementwise formulas also operate on NumPy arrays.
        if fn.__name__ in {'_cabs2', '_phasor_angles'}:
            return fn
        return np.vectorize(fn)
    return decorate


def stencil(fn):
    def call(x, *args):
        result = np.zeros(x.shape, dtype=bool if fn.__name__ in {'_localmax_sten', '_localmin_sten', '_zc_stencil'} else x.dtype)
        if fn.__name__ == '_localmax_sten':
            result[1:-1] = (x[1:-1] > x[:-2]) & (x[1:-1] >= x[2:])
        elif fn.__name__ == '_localmin_sten':
            result[1:-1] = (x[1:-1] < x[:-2]) & (x[1:-1] <= x[2:])
        elif fn.__name__ == '_pi_stencil':
            a = x[2:] + x[:-2] - 2*x[1:-1]
            b = (x[2:] - x[:-2])/2
            np.divide(-b, a, out=result[1:-1], where=np.abs(b) < np.abs(a))
        elif fn.__name__ == '_zc_stencil':
            threshold, zero_pos = args
            clean = np.where(np.abs(x) <= threshold, 0, x)
            signs = np.signbit(clean) if zero_pos else np.sign(clean)
            result[1:] = signs[1:] != signs[:-1]
        else:
            raise NotImplementedError(f'Android stencil is not validated: {fn.__name__}')
        return result
    return call


def install():
    """Install only before librosa is imported in the dedicated engine process."""
    if getattr(sys.modules.get('numba'), '__version__', '') == '0.0.android-python-kernels':
        return
    if 'librosa' in sys.modules:
        raise RuntimeError('Install Android numerical compatibility before importing librosa')
    module = types.ModuleType('numba')
    module.__version__ = '0.0.android-python-kernels'
    for name in ('jit', 'guvectorize', 'vectorize', 'stencil'):
        setattr(module, name, globals()[name])
    module.njit = jit
    module.prange = range
    for dtype in ('uint32', 'uint64', 'int32', 'int64', 'float32', 'float64', 'complex64', 'complex128', 'bool_'):
        setattr(module, dtype, getattr(np, dtype))
    sys.modules['numba'] = module
