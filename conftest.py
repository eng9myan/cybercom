"""
Root pytest configuration for CyberCom backend.
Provides shared fixtures used across all test modules.
"""
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

# Add the repository root directory to sys.path to allow importing from the sibling 'shared' directory
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
