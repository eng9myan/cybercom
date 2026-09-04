"""
Shared test fixtures for platform/* apps.

Mints real RS256 JWTs and patches the JWKS client that
shared.auth.auth_middleware.CyIdentityAuthMiddleware uses, so integration
tests exercise the actual production auth path end-to-end instead of relying
on a dev-mode bypass in the middleware itself.

Duplicated in cymed/conftest.py: pytest's confcutdir (set by cymed's
pyproject.toml [tool.pytest.ini_options]) stops upward conftest discovery at
cymed/, so a single repo-root conftest.py isn't visible to both product test
suites in one pytest run. Keep the two copies in sync.
"""

import time
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# A few platform tests wire the tenant-context / task machinery to a concrete
# product model (products.cycom.accounting.Account). Those only make sense in a
# product project and already run there — the standalone platform project skips
# them.
collect_ignore = [
    "common/tests/test_tenant_context.py",
    "common/tests/test_tenant_task.py",
    "provisioning/tests/test_provisioning.py",
]


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
