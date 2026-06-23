"""
Root pytest configuration for CyberCom backend.
Provides shared fixtures used across all test modules.
"""
import os
import sys
from pathlib import Path

# ── Platform namespace fix ────────────────────────────────────────────────────
# The local platform/ package shadows stdlib's platform module.
# We need stdlib platform (for system(), python_implementation(), etc.)
# AND we need the local platform/ to be importable as platform.common, etc.
# Solution: graft the local platform/ directory onto the stdlib platform module.

script_dir = str(Path(__file__).resolve().parent)
platform_pkg_path = os.path.join(script_dir, "platform")

# Step 1: Remove any already-cached platform from sys.modules (may be local package)
if "platform" in sys.modules:
    existing = sys.modules["platform"]
    existing_file = getattr(existing, "__file__", "") or ""
    if "CyberCom" in existing_file or platform_pkg_path in existing_file:
        del sys.modules["platform"]
    elif not hasattr(existing, "system"):
        # Missing stdlib functions — wrong platform in cache
        del sys.modules["platform"]

# Step 2: Temporarily remove backend dir so stdlib platform loads cleanly
sys_path_removed = False
for entry in [script_dir, ""]:
    if entry in sys.path:
        sys.path.remove(entry)
        sys_path_removed = True
        break

# Step 3: Import stdlib platform (now that backend dir is removed)
import platform as std_platform  # noqa: E402

# Step 4: Graft local platform/ onto stdlib module so both work
if not hasattr(std_platform, "__path__") or std_platform.__path__ is None:
    std_platform.__path__ = [platform_pkg_path]
elif platform_pkg_path not in std_platform.__path__:
    std_platform.__path__.append(platform_pkg_path)

# Step 5: Ensure sys.modules["platform"] = stdlib module (not local package)
sys.modules["platform"] = std_platform

# Step 6: Restore backend dir to sys.path
if sys_path_removed:
    sys.path.insert(0, script_dir)

# Add the repository root directory to sys.path
repo_root = str(Path(script_dir).parent)
if repo_root not in sys.path:
    sys.path.append(repo_root)

import uuid
import pytest
from django.test import RequestFactory


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


@pytest.fixture
def user_session(tenant_id):
    return {
        "user_id": str(uuid.uuid4()),
        "email": "test@cybercom.io",
        "tenant_id": str(tenant_id),
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }


@pytest.fixture
def authenticated_request(rf, user_session):
    request = rf.get("/")
    request.user_session = user_session
    request.tenant_id = user_session["tenant_id"]
    return request
