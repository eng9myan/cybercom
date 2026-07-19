import os
import sys
from pathlib import Path

# Namespace bridging to prevent the shared 'platform/' package (repo root,
# shared across cycom/cyshop/cymed) from shadowing standard library
# 'platform', AND to make cymed's own top-level packages (e.g. 'shared')
# importable. Mirrors manage.py's logic exactly, adjusted for asgi.py
# living one directory deeper (cymed/core/asgi.py vs cymed/manage.py):
# manage.py's "script_dir" (its own dir, cymed/) is here .parent.parent;
# manage.py's "repo_root" (one level up from cymed/) is here
# .parent.parent.parent. gunicorn imports this module directly as the
# app's true entry point - unlike manage.py/conftest.py, nothing else
# primes sys.path first in that process, so both insertions are required
# here, not just the platform one.
cymed_dir = str(Path(__file__).resolve().parent.parent)
repo_root = str(Path(__file__).resolve().parent.parent.parent)
sys_path_removed = False
if cymed_dir in sys.path:
    sys.path.remove(cymed_dir)
    sys_path_removed = True
elif "" in sys.path:
    sys.path.remove("")
    sys_path_removed = True

import platform as std_platform

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

platform_pkg_path = os.path.join(repo_root, "platform")
if not hasattr(std_platform, "__path__") or std_platform.__path__ is None:
    std_platform.__path__ = [platform_pkg_path]
elif platform_pkg_path not in std_platform.__path__:
    std_platform.__path__.append(platform_pkg_path)

if sys_path_removed:
    sys.path.insert(0, cymed_dir)

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
application = get_asgi_application()
