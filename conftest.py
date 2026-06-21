"""
Root pytest configuration for CyberCom backend.
Provides shared fixtures used across all test modules.
"""
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
