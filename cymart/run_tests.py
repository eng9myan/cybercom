"""
Test runner that pre-fixes the 'platform' stdlib shadowing issue.
The repo has a top-level 'platform/' shared-package directory that shadows
stdlib 'platform'. This script imports and patches stdlib platform before
pytest loads any plugins. Mirrors cymed/run_tests.py.
"""

import importlib
import importlib.util
import sys

import sysconfig
from pathlib import Path

stdlib_dir = sysconfig.get_paths()["stdlib"]
_plat_spec = importlib.util.spec_from_file_location(
    "_stdlib_platform",
    Path(stdlib_dir) / "platform.py",
)
_stdlib_platform = importlib.util.module_from_spec(_plat_spec)
_plat_spec.loader.exec_module(_stdlib_platform)
_stdlib_platform.__path__ = [str(Path(__file__).resolve().parent.parent / "platform")]

sys.modules["platform"] = _stdlib_platform

import pytest

if __name__ == "__main__":
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
    os.environ.setdefault("DJANGO_DEBUG", "True")
    os.environ.setdefault("DJANGO_SECRET_KEY", "dev-test-secret-key-cymart-2026")

    args = sys.argv[1:] if len(sys.argv) > 1 else ["products/cymart", "-v", "--tb=short"]
    raise SystemExit(pytest.main(args))
