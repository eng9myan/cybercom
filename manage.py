#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

# Namespace bridging to prevent local 'platform' folder from shadowing standard library 'platform'
script_dir = str(Path(__file__).resolve().parent)
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

def main():

    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
