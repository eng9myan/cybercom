#!/usr/bin/env python
"""manage.py for the standalone platform project (see run_tests.py for the
stdlib-`platform`-shadow rationale — the same graft is applied here)."""
import importlib.util
import os
import sys
import sysconfig
from pathlib import Path

script_dir = Path(__file__).resolve().parent
repo_root = script_dir.parent

_plat_spec = importlib.util.spec_from_file_location(
    "_stdlib_platform", Path(sysconfig.get_paths()["stdlib"]) / "platform.py"
)
_stdlib_platform = importlib.util.module_from_spec(_plat_spec)
_plat_spec.loader.exec_module(_stdlib_platform)
_stdlib_platform.__path__ = [str(script_dir)]
sys.modules["platform"] = _stdlib_platform

for p in (str(repo_root), str(script_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    os.environ.setdefault("DJANGO_SECRET_KEY", "platform-tests-not-a-real-secret")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
