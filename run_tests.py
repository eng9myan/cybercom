"""
Test runner that pre-fixes the 'platform' stdlib shadowing issue.
The backend has a 'platform/' Django apps directory that shadows stdlib 'platform'.
This script imports and patches stdlib platform before pytest loads any plugins.
"""
import sys
import importlib
import importlib.util
from pathlib import Path

# ── Fix stdlib 'platform' shadowing ──────────────────────────────────────────
# Load the real stdlib 'platform' module by spec (bypasses sys.path lookup)
import sysconfig
stdlib_dir = sysconfig.get_paths()["stdlib"]
_plat_spec = importlib.util.spec_from_file_location(
    "_stdlib_platform",
    Path(stdlib_dir) / "platform.py",
)
_stdlib_platform = importlib.util.module_from_spec(_plat_spec)
_plat_spec.loader.exec_module(_stdlib_platform)

# Register under 'platform' in sys.modules BEFORE any plugin/library imports it
# but only do this temporarily during import bootstrap
sys.modules["platform"] = _stdlib_platform

# ── Now run pytest ────────────────────────────────────────────────────────────
import pytest

if __name__ == "__main__":
    import os
    os.environ.setdefault("DJANGO_DEBUG", "True")
    os.environ.setdefault("DJANGO_SECRET_KEY", "dev-test-secret-key-cyidentity-2026")
    os.environ.setdefault("KEYCLOAK_ENABLED", "False")

    args = sys.argv[1:] if len(sys.argv) > 1 else [
        "platform/cyidentity/tests/",
        "-v",
        "--tb=short",
        "--no-cov",
    ]
    raise SystemExit(pytest.main(args))
