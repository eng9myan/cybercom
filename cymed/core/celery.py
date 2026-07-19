import os
import sys
from pathlib import Path

# Namespace bridging to prevent the shared 'platform/' package (repo root,
# shared across cycom/cyshop/cymed) from shadowing standard library
# 'platform', AND to make cymed's own top-level packages importable.
# celery's console-script ("celery -A core worker") loads this module
# directly, same as gunicorn loads asgi.py/wsgi.py - none of manage.py's
# path setup runs first in that process. See asgi.py/wsgi.py for the
# same fix and the full story of why unconditional inserts are required.
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

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("cybercom_core")

# Read config from django settings under CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks across apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    pass
