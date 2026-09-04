"""
Test runner for the standalone platform project.

Same stdlib-`platform`-shadow fix as cymed/run_tests.py: this directory *is*
the `platform` package, so `import platform` from any test dependency would
pick up the package and lose `platform.system()` etc. We load the real stdlib
module first, graft this directory onto its __path__ so `platform.common`
still imports, and only then hand off to pytest.

    cd platform && python run_tests.py               # the whole suite
    cd platform && python run_tests.py security/tests -q
"""
import importlib.util
import os
import sys
import sysconfig
from pathlib import Path

script_dir = Path(__file__).resolve().parent          # the platform/ dir
repo_root = script_dir.parent

# ── Step 1: real stdlib platform, grafted with this package's __path__ ────────
_plat_spec = importlib.util.spec_from_file_location(
    "_stdlib_platform", Path(sysconfig.get_paths()["stdlib"]) / "platform.py"
)
_stdlib_platform = importlib.util.module_from_spec(_plat_spec)
_plat_spec.loader.exec_module(_stdlib_platform)
_stdlib_platform.__path__ = [str(script_dir)]
sys.modules["platform"] = _stdlib_platform

# ── Step 2: import paths — repo root (platform.*, shared.*) + this dir (core) ─
for p in (str(repo_root), str(script_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Step 3: environment ─────────────────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "platform-tests-not-a-real-secret")
os.environ.setdefault("DJANGO_DEBUG", "True")

import pytest  # noqa: E402

if __name__ == "__main__":
    args = sys.argv[1:] or ["."]
    raise SystemExit(pytest.main([*args, "--no-header"]))
