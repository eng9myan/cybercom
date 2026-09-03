"""Boot Django dev server on SQLite for the CyMed demo."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_CYMED_ROOT = _HERE.parent.parent.parent
_REPO_ROOT = _CYMED_ROOT.parent
for p in (str(_CYMED_ROOT), str(_REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

_removed = None
if "" in sys.path:
    sys.path.remove(""); _removed = ""
import platform as _std_platform
for _p in (str(_REPO_ROOT / "platform"), str(_CYMED_ROOT / "platform")):
    if os.path.isdir(_p):
        if not hasattr(_std_platform, "__path__") or _std_platform.__path__ is None:
            _std_platform.__path__ = [_p]
        elif _p not in _std_platform.__path__:
            _std_platform.__path__.append(_p)
if _removed is not None:
    sys.path.insert(0, _removed)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_SECRET_KEY", "dev-unsafe")
os.environ.setdefault("ALLOWED_HOSTS", "127.0.0.1,localhost")

import django
from django.conf import settings
if not settings.configured:
    settings._setup()
settings.DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(_CYMED_ROOT / "dev_smoke.db")}
}
django.setup()

from django.core.management import call_command

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = os.environ.get("PORT", "8000")
    call_command("runserver", f"{host}:{port}", use_reloader=False)
