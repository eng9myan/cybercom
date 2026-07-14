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
# platform/ now lives at the monorepo root (shared across cycom/cyshop/cymed),
# one level above this backend project, not inside it.
platform_pkg_path = os.path.join(str(Path(script_dir).parent), "platform")

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
import platform as std_platform

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

import time
import uuid
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import RequestFactory


@pytest.fixture
def rf():
    return RequestFactory()


# ── Auth fixtures: mint real RS256 JWTs and mock the JWKS client that ────────
# shared.auth.auth_middleware.CyIdentityAuthMiddleware validates against, so
# tests exercise the actual production auth path. Duplicated in
# platform/conftest.py — see that file's docstring for why.
@pytest.fixture(scope="session")
def _rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


@pytest.fixture
def mint_token(_rsa_keypair):
    """Signs a payload as a real RS256 JWT with the test session's key pair."""
    private_pem, _ = _rsa_keypair

    def _mint(payload: dict) -> str:
        claims = {**payload}
        now = int(time.time())
        claims.setdefault("iat", now)
        claims.setdefault("exp", now + 3600)
        return jwt.encode(claims, private_pem, algorithm="RS256")

    return _mint


@pytest.fixture
def mock_jwks(_rsa_keypair):
    """Patches the middleware's JWKS client to serve this session's public key."""
    _, public_pem = _rsa_keypair
    fake_signing_key = type("FakeSigningKey", (), {"key": public_pem})()
    fake_client = type(
        "FakeJWKClient",
        (),
        {"get_signing_key_from_jwt": lambda self, token: fake_signing_key},
    )()
    with patch("shared.auth.auth_middleware._get_jwks_client", return_value=fake_client):
        yield


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
