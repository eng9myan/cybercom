"""
Pluggable key management with dev / AWS-KMS backends and stubs for Azure / GCP.

Backend selection via env var ``PLATFORM_KMS_BACKEND``:
    local_dev          -> LocalDevKeyStore (default; insecure — filesystem)
    aws_kms            -> AWSKmsKeyStore   (boto3 required)
    azure_key_vault    -> AzureKeyVaultKeyStore (stub)
    gcp_kms            -> GCPKeyStore      (stub)

All backends implement the same abstract surface: ``sign``, ``verify``,
``wrap`` (envelope encrypt), ``unwrap`` (envelope decrypt). Bytes-in / bytes-out.
"""

from __future__ import annotations

import base64
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger("cybercom.security.keys")


class KeyStore(ABC):
    """Abstract key store contract used across the platform."""

    backend_name: str = "abstract"

    @abstractmethod
    def sign(self, data: bytes, key_id: str) -> bytes:
        """Return a detached signature over ``data`` using ``key_id``."""

    @abstractmethod
    def verify(self, data: bytes, sig: bytes, key_id: str) -> bool:
        """Return True iff ``sig`` verifies ``data`` under ``key_id``."""

    @abstractmethod
    def wrap(self, plaintext: bytes, key_id: str) -> bytes:
        """Envelope-encrypt ``plaintext`` under ``key_id``."""

    @abstractmethod
    def unwrap(self, ciphertext: bytes, key_id: str) -> bytes:
        """Reverse of ``wrap``."""


# ---------------------------------------------------------------------------
# Local dev backend — ECDSA P-256 + AES-GCM, keys on disk.
# ---------------------------------------------------------------------------
class LocalDevKeyStore(KeyStore):
    """
    File-system keystore for local development.

    Signing keys are ECDSA on the NIST P-256 curve. Wrap keys are 256-bit AES-GCM
    keys generated deterministically per ``key_id``.

    WARNING: This backend stores private keys unencrypted on disk. It exists
    ONLY for development. Never enable it in production — the factory logs a
    loud warning if it is loaded outside ``ENVIRONMENT=development``.
    """

    backend_name = "local_dev"

    def __init__(self, key_dir: Optional[str] = None) -> None:
        self.key_dir = Path(
            key_dir
            or os.environ.get("PLATFORM_KEY_DIR")
            or Path.home() / ".cybercom" / "dev-keys"
        )
        self.key_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.get("ENVIRONMENT", "development").lower()
        if env != "development":
            logger.error(
                "LocalDevKeyStore instantiated in ENVIRONMENT=%s — refuse to use "
                "this backend outside development. Set PLATFORM_KMS_BACKEND.",
                env,
            )

    # -- helpers -----------------------------------------------------------
    def _sign_key_path(self, key_id: str) -> Path:
        return self.key_dir / f"{key_id}.ecdsa.pem"

    def _wrap_key_path(self, key_id: str) -> Path:
        return self.key_dir / f"{key_id}.aesgcm.key"

    def _load_or_create_sign_key(self, key_id: str):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        path = self._sign_key_path(key_id)
        if path.exists():
            return serialization.load_pem_private_key(path.read_bytes(), password=None)
        priv = ec.generate_private_key(ec.SECP256R1())
        path.write_bytes(
            priv.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        return priv

    def _load_or_create_wrap_key(self, key_id: str) -> bytes:
        path = self._wrap_key_path(key_id)
        if path.exists():
            return path.read_bytes()
        key = os.urandom(32)
        path.write_bytes(key)
        return key

    # -- interface ---------------------------------------------------------
    def sign(self, data: bytes, key_id: str) -> bytes:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec

        priv = self._load_or_create_sign_key(key_id)
        return priv.sign(data, ec.ECDSA(hashes.SHA256()))

    def verify(self, data: bytes, sig: bytes, key_id: str) -> bool:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec

        priv = self._load_or_create_sign_key(key_id)
        pub = priv.public_key()
        try:
            pub.verify(sig, data, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False

    def wrap(self, plaintext: bytes, key_id: str) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = self._load_or_create_wrap_key(key_id)
        aes = AESGCM(key)
        nonce = os.urandom(12)
        ct = aes.encrypt(nonce, plaintext, None)
        # wire format: 1-byte version || 12-byte nonce || ct+tag, all b64.
        return base64.b64encode(b"\x01" + nonce + ct)

    def unwrap(self, ciphertext: bytes, key_id: str) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        raw = base64.b64decode(ciphertext)
        if not raw or raw[0] != 1:
            raise ValueError("unsupported ciphertext version")
        nonce, ct = raw[1:13], raw[13:]
        key = self._load_or_create_wrap_key(key_id)
        return AESGCM(key).decrypt(nonce, ct, None)


# ---------------------------------------------------------------------------
# AWS KMS backend — real HSM-backed KMS keys.
# ---------------------------------------------------------------------------
class AWSKmsKeyStore(KeyStore):
    """
    AWS KMS-backed keystore.

    ``key_id`` must be a KMS key alias (``alias/my-key``), key ID, or ARN.
    Requires an IAM identity with ``kms:Sign``, ``kms:Verify``, ``kms:Encrypt``,
    and ``kms:Decrypt`` permissions on the referenced keys.

    Signing uses ``ECDSA_SHA_256`` (requires an EC signing key on KMS).
    Wrap uses direct ``kms:Encrypt`` — for large payloads switch to
    ``kms:GenerateDataKey`` + AES-GCM envelope encryption at the caller.
    """

    backend_name = "aws_kms"

    def __init__(self, region: Optional[str] = None) -> None:
        try:
            import boto3  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "AWSKmsKeyStore requires boto3. Install with `pip install boto3`."
            ) from exc
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client("kms", region_name=self.region)
        return self._client

    def sign(self, data: bytes, key_id: str) -> bytes:
        resp = self.client.sign(
            KeyId=key_id,
            Message=data,
            MessageType="RAW",
            SigningAlgorithm="ECDSA_SHA_256",
        )
        return resp["Signature"]

    def verify(self, data: bytes, sig: bytes, key_id: str) -> bool:
        try:
            resp = self.client.verify(
                KeyId=key_id,
                Message=data,
                MessageType="RAW",
                Signature=sig,
                SigningAlgorithm="ECDSA_SHA_256",
            )
            return bool(resp.get("SignatureValid"))
        except Exception as exc:  # pragma: no cover
            logger.warning("aws_kms.verify_failed: %s", exc)
            return False

    def wrap(self, plaintext: bytes, key_id: str) -> bytes:
        resp = self.client.encrypt(KeyId=key_id, Plaintext=plaintext)
        return base64.b64encode(resp["CiphertextBlob"])

    def unwrap(self, ciphertext: bytes, key_id: str) -> bytes:
        blob = base64.b64decode(ciphertext)
        resp = self.client.decrypt(KeyId=key_id, CiphertextBlob=blob)
        return resp["Plaintext"]


# ---------------------------------------------------------------------------
# Azure / GCP stubs
# ---------------------------------------------------------------------------
class AzureKeyVaultKeyStore(KeyStore):
    """Stub — implementation pending. See docs/security/kms-onboarding.md."""

    backend_name = "azure_key_vault"
    ONBOARDING_DOCS = (
        "https://docs.cybercom.local/security/kms-onboarding#azure-key-vault"
    )

    def _fail(self):
        raise NotImplementedError(
            "AzureKeyVaultKeyStore is not yet implemented. Onboarding: "
            f"{self.ONBOARDING_DOCS}"
        )

    def sign(self, data: bytes, key_id: str) -> bytes:  # noqa: D401,ARG002
        self._fail()

    def verify(self, data: bytes, sig: bytes, key_id: str) -> bool:  # noqa: ARG002
        self._fail()

    def wrap(self, plaintext: bytes, key_id: str) -> bytes:  # noqa: ARG002
        self._fail()

    def unwrap(self, ciphertext: bytes, key_id: str) -> bytes:  # noqa: ARG002
        self._fail()


class GCPKeyStore(KeyStore):
    """Stub — implementation pending. See docs/security/kms-onboarding.md."""

    backend_name = "gcp_kms"
    ONBOARDING_DOCS = (
        "https://docs.cybercom.local/security/kms-onboarding#gcp-kms"
    )

    def _fail(self):
        raise NotImplementedError(
            "GCPKeyStore is not yet implemented. Onboarding: "
            f"{self.ONBOARDING_DOCS}"
        )

    def sign(self, data: bytes, key_id: str) -> bytes:  # noqa: ARG002
        self._fail()

    def verify(self, data: bytes, sig: bytes, key_id: str) -> bool:  # noqa: ARG002
        self._fail()

    def wrap(self, plaintext: bytes, key_id: str) -> bytes:  # noqa: ARG002
        self._fail()

    def unwrap(self, ciphertext: bytes, key_id: str) -> bytes:  # noqa: ARG002
        self._fail()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
_BACKENDS = {
    "local_dev": LocalDevKeyStore,
    "aws_kms": AWSKmsKeyStore,
    "azure_key_vault": AzureKeyVaultKeyStore,
    "gcp_kms": GCPKeyStore,
}

_singleton: Optional[KeyStore] = None


def get_keystore() -> KeyStore:
    """
    Return the process-wide KeyStore selected by ``PLATFORM_KMS_BACKEND``.

    Cached for the lifetime of the interpreter. Use ``reset_keystore()`` in tests.
    """
    global _singleton
    if _singleton is not None:
        return _singleton

    name = os.environ.get("PLATFORM_KMS_BACKEND", "local_dev").lower()
    cls = _BACKENDS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown PLATFORM_KMS_BACKEND={name!r}. "
            f"Valid choices: {sorted(_BACKENDS)}"
        )
    _singleton = cls()
    logger.info("keystore.selected backend=%s", _singleton.backend_name)
    return _singleton


def reset_keystore() -> None:
    """Clear the cached backend — testing hook."""
    global _singleton
    _singleton = None
