"""
Root pytest configuration for CyVault backend.
Provides shared fixtures used across all test modules — mirrors cycom's
conftest.py exactly (same namespace-bridging trick, same real-JWT auth
fixtures against the shared CyIdentityAuthMiddleware).
"""

import os
import sys
from pathlib import Path

script_dir = str(Path(__file__).resolve().parent)
repo_root = str(Path(script_dir).parent)
sys_path_removed = False
if script_dir in sys.path:
    sys.path.remove(script_dir)
    sys_path_removed = True
elif "" in sys.path:
    sys.path.remove("")
    sys_path_removed = True

import platform as std_platform

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

platform_pkg_path = os.path.join(repo_root, "platform")
if not hasattr(std_platform, "__path__") or std_platform.__path__ is None:
    std_platform.__path__ = [platform_pkg_path]
elif platform_pkg_path not in std_platform.__path__:
    std_platform.__path__.append(platform_pkg_path)

if sys_path_removed:
    sys.path.insert(0, script_dir)

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
