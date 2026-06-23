# Compatibility shim: ensures 'from platform import X' works for stdlib consumers
# when this package shadows the stdlib platform module.
import sys as _sys
import os as _os
import importlib.util as _ilu

def _load_stdlib_platform():
    """Load the real stdlib platform module, bypassing this package."""
    _pkg_dir = _os.path.dirname(_os.path.abspath(__file__))
    # Find stdlib platform.py by scanning sys.path excluding this package's parent
    for _p in _sys.path:
        if _p == _pkg_dir or _p == _os.path.dirname(_pkg_dir):
            continue
        _candidate = _os.path.join(_p, "platform.py")
        if _os.path.isfile(_candidate):
            _spec = _ilu.spec_from_file_location("_stdlib_platform", _candidate)
            if _spec:
                _mod = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                return _mod
    return None

_stdlib = _load_stdlib_platform()
if _stdlib is not None:
    system = _stdlib.system
    node = _stdlib.node
    release = _stdlib.release
    version = _stdlib.version
    machine = _stdlib.machine
    processor = _stdlib.processor
    python_implementation = _stdlib.python_implementation
    python_version = _stdlib.python_version
    python_version_tuple = _stdlib.python_version_tuple
    python_build = _stdlib.python_build
    python_compiler = _stdlib.python_compiler
    architecture = _stdlib.architecture
    uname = _stdlib.uname
    try:
        platform = _stdlib.platform
    except AttributeError:
        pass

del _stdlib, _load_stdlib_platform, _sys, _os, _ilu
