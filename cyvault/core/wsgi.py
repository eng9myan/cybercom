import os
import sys
from pathlib import Path

# Namespace bridging — see cycom/core/wsgi.py for the full explanation of
# why these inserts must be unconditional under gunicorn's real invocation.
script_dir = str(Path(__file__).resolve().parent.parent)
repo_root = str(Path(__file__).resolve().parent.parent.parent)

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import platform as std_platform

platform_pkg_path = os.path.join(repo_root, "platform")
if not hasattr(std_platform, "__path__") or std_platform.__path__ is None:
    std_platform.__path__ = [platform_pkg_path]
elif platform_pkg_path not in std_platform.__path__:
    std_platform.__path__.append(platform_pkg_path)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
application = get_wsgi_application()
