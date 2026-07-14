"""
Root pytest configuration for CyMart.

Mints real RS256 JWTs and patches the JWKS client that shared.auth.
auth_middleware.CyIdentityAuthMiddleware validates against — same pattern
as cymed/conftest.py and platform/conftest.py (duplicated for the same
confcutdir reason documented there).

Note: the stdlib 'platform' shadowing fix (platform/ dir vs stdlib module)
lives in run_tests.py, not here — it has to run before pytest itself
loads, which conftest.py is too late for. Use `python run_tests.py`, not
bare `pytest`, to run this project's tests.
"""

import sys
import time
import uuid
from pathlib import Path
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

repo_root = str(Path(__file__).resolve().parent.parent)
if repo_root not in sys.path:
    sys.path.append(repo_root)


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
