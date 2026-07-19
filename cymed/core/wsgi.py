import os
import sys
from pathlib import Path

# Namespace bridging to prevent the shared 'platform/' package (repo root,
# shared across cycom/cyshop/cymed) from shadowing standard library
# 'platform', AND to make cymed's own top-level packages (e.g. 'shared')
# importable. gunicorn imports this module directly as the app's true
# entry point via its console-script - unlike "python -c"/"python -m",
# that invocation does NOT put "" (cwd) on sys.path, so a fix that only
# re-inserted these dirs conditionally on having first removed "" from
# sys.path silently never ran under gunicorn (worked under manage.py and
# local "python -c" testing only, which is what hid this the first time).
# Unconditional inserts avoid that trap entirely.
cymed_dir = str(Path(__file__).resolve().parent.parent)
repo_root = str(Path(__file__).resolve().parent.parent.parent)

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if cymed_dir not in sys.path:
    sys.path.insert(0, cymed_dir)

import platform as std_platform

platform_pkg_path = os.path.join(repo_root, "platform")
if not hasattr(std_platform, "__path__") or std_platform.__path__ is None:
    std_platform.__path__ = [platform_pkg_path]
elif platform_pkg_path not in std_platform.__path__:
    std_platform.__path__.append(platform_pkg_path)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
application = get_wsgi_application()
