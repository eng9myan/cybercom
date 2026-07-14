"""
Pharmacy test runner that bypasses coverage addopts issue.
"""

import importlib
import importlib.util
import sys

# ── Fix stdlib 'platform' shadowing ──────────────────────────────────────────
import sysconfig
from pathlib import Path

stdlib_dir = sysconfig.get_paths()["stdlib"]
_plat_spec = importlib.util.spec_from_file_location(
    "_stdlib_platform",
    Path(stdlib_dir) / "platform.py",
)
_stdlib_platform = importlib.util.module_from_spec(_plat_spec)
_plat_spec.loader.exec_module(_stdlib_platform)
_stdlib_platform.__path__ = [str(Path(__file__).resolve().parent / "platform")]
sys.modules["platform"] = _stdlib_platform

import pytest

if __name__ == "__main__":
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
    os.environ.setdefault("DJANGO_DEBUG", "True")
    os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-pharmacy-2026")
    os.environ.setdefault("KEYCLOAK_ENABLED", "False")

    test_paths = (
        sys.argv[1:]
        if len(sys.argv) > 1
        else [
            "products/cymed/pharmacy/tests/",
        ]
    )

    raise SystemExit(
        pytest.main(
            [
                *test_paths,
                "-v",
                "--tb=short",
                "-p",
                "no:cacheprovider",
                "--override-ini=addopts=--tb=short",
            ]
        )
    )
