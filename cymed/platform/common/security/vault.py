import logging
from typing import Any

logger = logging.getLogger("cybercom.security.vault")


class VaultClient:
    """
    Client wrapper for HashiCorp Vault key-value secret store.
    Provides local in-memory fallback for development and testing.
    """

    _local_store: dict[str, dict[str, Any]] = {}

    @classmethod
    def get_secret(cls, path: str) -> dict[str, Any]:
        # Mock retrieval of secrets
        # In production: reads from hvac.Client authenticated via Kubernetes workload identity
        if path in cls._local_store:
            return cls._local_store[path]

        # Default mock values
        logger.info(f"Vault path '{path}' not found in local cache, returning mock credentials.")
        if "database" in path:
            return {"username": "postgres", "password": "dev-unsafe-password"}
        elif "keycloak" in path:
            return {"client_secret": "fake-vault-keycloak-secret"}
        return {"value": "mock-secret-value"}

    @classmethod
    def write_secret(cls, path: str, secrets: dict[str, Any]) -> None:
        cls._local_store[path] = secrets
        logger.info(f"Secret written to Vault path: {path}")
