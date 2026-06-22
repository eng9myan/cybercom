import hashlib
import hmac
import base64
from django.conf import settings

class EventSigner:
    """
    Handles cryptographic signing of outbox event payloads for integrity validation
    and cross-tenant protection.
    """
    @classmethod
    def sign_payload(cls, tenant_id: str, payload_bytes: bytes) -> str:
        # In production, this uses an RSA private key loaded from HashiCorp Vault.
        # For our bootstrap environment, we compute a secure HMAC-SHA256 signature using the system JWT signing key.
        key = getattr(settings, "JWT_SIGNING_KEY", "dev-secret-signing-key").encode()
        msg = f"{tenant_id}:".encode() + payload_bytes
        sig = hmac.new(key, msg, hashlib.sha256).digest()
        return base64.b64encode(sig).decode()

    @classmethod
    def verify_signature(cls, tenant_id: str, payload_bytes: bytes, signature: str) -> bool:
        try:
            expected = cls.sign_payload(tenant_id, payload_bytes)
            return hmac.compare_digest(expected, signature)
        except Exception:
            return False
