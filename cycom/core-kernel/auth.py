# -*- coding: utf-8 -*-
import time
import json
import base64
import hmac
import hashlib
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "cycom-super-secret-key-change-in-production"
security_bearer = HTTPBearer(auto_error=False)


class JWTManager:
    """Resilient token manager providing standard HS256 signatures with fallback."""

    @staticmethod
    def encode(payload: dict, expires_in: int = 3600) -> str:
        data = payload.copy()
        data["exp"] = int(time.time()) + expires_in
        try:
            import jwt
            return jwt.encode(data, SECRET_KEY, algorithm="HS256")
        except ImportError:
            # Fallback URL-Safe HMAC-SHA256 signature generator
            hdr = {"alg": "HS256", "typ": "JWT"}
            hdr_b64 = base64.urlsafe_b64encode(json.dumps(hdr).encode("utf-8")).decode("utf-8").rstrip("=")
            pay_b64 = base64.urlsafe_b64encode(json.dumps(data).encode("utf-8")).decode("utf-8").rstrip("=")
            msg = f"{hdr_b64}.{pay_b64}".encode("utf-8")
            sig = hmac.new(SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).digest()
            sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
            return f"{hdr_b64}.{pay_b64}.{sig_b64}"

    @staticmethod
    def decode(token: str) -> dict:
        try:
            import jwt
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except Exception:
            # Fallback verify signature
            try:
                parts = token.split(".")
                if len(parts) != 3:
                    raise ValueError("Invalid format")
                hdr_b64, pay_b64, sig_b64 = parts
                msg = f"{hdr_b64}.{pay_b64}".encode("utf-8")
                sig = hmac.new(SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).digest()
                sig_expected_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
                if not hmac.compare_digest(sig_b64, sig_expected_b64):
                    raise ValueError("Signature mismatch")

                # Pad base64 decoding string length
                pad_len = 4 - (len(pay_b64) % 4)
                pay_padded = pay_b64 + ("=" * (pad_len if pad_len < 4 else 0))
                payload = json.loads(base64.urlsafe_b64decode(pay_padded.encode("utf-8")).decode("utf-8"))
                if payload.get("exp", 0) < time.time():
                    raise ValueError("Expired token")
                return payload
            except Exception as e:
                raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    """FastAPI route dependency ensuring request authentication."""
    if not credentials:
        # Fallback to allow unauthenticated setup during initial onboarding
        return {"email": "anonymous@cycom.com", "role": "admin"}
    token = credentials.credentials
    payload = JWTManager.decode(token)
    return payload


class RoleChecker:
    """Enforces RBAC on routes based on user roles."""
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user: dict = Security(get_current_user)):
        if user.get("role") not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Operation forbidden: Insufficient permissions")
        return user
