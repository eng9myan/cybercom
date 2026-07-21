"""
Resets KeycloakAdminClient's shared in-memory fake store between tests.

That store moved from per-instance to module-level (see
services.py::_FAKE_KEYCLOAK_STORE) so separately-constructed clients
within one test see each other's state, the same way independently
constructed real clients would all see one real out-of-process Keycloak
server. Without this reset it would otherwise persist for the whole test
process and leak state across test functions.
"""

import pytest

from platform.cyidentity.services import reset_fake_keycloak_store


@pytest.fixture(autouse=True)
def _reset_fake_keycloak():
    reset_fake_keycloak_store()
    yield
