import os
import sys
from pathlib import Path

# Namespace bridging to prevent local 'platform' folder from shadowing standard library 'platform'
# asgi.py lives at cymed/core/asgi.py - one directory deeper than manage.py
# (cymed/manage.py) - needs a 3rd .parent to reach the same repo root
# manage.py computes with 2. Off by one here broke gunicorn/uvicorn boot
# in production (worked everywhere else only because manage.py or
# conftest.py always primed sys.path first in the same process before
# this module was ever imported standalone).
script_dir = str(Path(__file__).resolve().parent.parent.parent)
sys_path_removed = False
if script_dir in sys.path:
    sys.path.remove(script_dir)
    sys_path_removed = True
elif "" in sys.path:
    sys.path.remove("")
    sys_path_removed = True

import platform as std_platform

platform_pkg_path = os.path.join(script_dir, "platform")
if not hasattr(std_platform, "__path__") or std_platform.__path__ is None:
    std_platform.__path__ = [platform_pkg_path]
elif platform_pkg_path not in std_platform.__path__:
    std_platform.__path__.append(platform_pkg_path)

if sys_path_removed:
    sys.path.insert(0, script_dir)

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
application = get_asgi_application()
