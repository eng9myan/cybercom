"""
Migration runner — replicates conftest.py sys.path + platform namespace fix.
Prevents local platform/ package from shadowing stdlib platform module,
while still allowing 'from platform.common.models import BaseModel' to work.
"""

import os
import sys
from pathlib import Path

script_dir = str(Path(__file__).resolve().parent)

# Step 1: Remove script_dir from sys.path so stdlib 'platform' loads first
sys_path_removed = False
if script_dir in sys.path:
    sys.path.remove(script_dir)
    sys_path_removed = True
elif "" in sys.path:
    sys.path.remove("")
    sys_path_removed = True

# Step 2: Import stdlib platform, then graft local platform/ onto it
import platform as std_platform

platform_pkg_path = os.path.join(script_dir, "platform")
if not hasattr(std_platform, "__path__") or std_platform.__path__ is None:
    std_platform.__path__ = [platform_pkg_path]
elif platform_pkg_path not in std_platform.__path__:
    std_platform.__path__.append(platform_pkg_path)

# Step 3: Restore script_dir so all project modules are importable
if sys_path_removed:
    sys.path.insert(0, script_dir)

repo_root = str(Path(script_dir).parent)
if repo_root not in sys.path:
    sys.path.append(repo_root)

# Step 4: Configure environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
os.environ.setdefault("DJANGO_SECRET_KEY", "dev-unsafe-secret-key-do-not-use-in-prod")
os.environ.setdefault("DJANGO_DEBUG", "True")

import django

django.setup()

from django.core.management import execute_from_command_line

execute_from_command_line(sys.argv)
