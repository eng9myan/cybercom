"""
TOTP (RFC 6238) over HOTP (RFC 4226).

Implemented directly rather than adding a dependency: the algorithm is small,
fully specified, and this keeps the supply-chain surface of an auth control to
the standard library. Compatible with Google Authenticator, Authy, 1Password
and any other RFC 6238 client.
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

DIGITS = 6
PERIOD = 30  # seconds per time step
SECRET_BYTES = 20  # 160 bits, the RFC 4226 recommendation for SHA-1 HMAC


def generate_secret() -> str:
    """A fresh base32 shared secret, unpadded (what authenticator apps expect)."""
    return base64.b32encode(secrets.token_bytes(SECRET_BYTES)).decode().rstrip("=")


def _decode_secret(secret: str) -> bytes:
    s = (secret or "").strip().replace(" ", "").upper()
    padding = "=" * (-len(s) % 8)  # b32decode requires correct padding
    return base64.b32decode(s + padding, casefold=True)


def counter_now(at: float | None = None) -> int:
    return int((at if at is not None else time.time()) // PERIOD)


def hotp(secret: str, counter: int, digits: int = DIGITS) -> str:
    """RFC 4226 HOTP with dynamic truncation."""
    key = _decode_secret(secret)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10 ** digits)).zfill(digits)


def totp(secret: str, at: float | None = None, digits: int = DIGITS) -> str:
    return hotp(secret, counter_now(at), digits)


def verify(secret: str, code: str, *, window: int = 1, at: float | None = None,
           after_counter: int = 0, digits: int = DIGITS) -> int | None:
    """
    Check `code` against the steps within +/- `window` of now.

    Returns the matching counter, or None. Two properties matter:

    * A one-step window absorbs clock skew between phone and server without
      widening the attack surface much (RFC 6238 §5.2 explicitly allows it).
    * `after_counter` enforces the replay watermark: a step at or below the last
      accepted one is refused, so capturing a code and reusing it inside its
      30-second life does not work.

    Comparison is constant-time to avoid leaking a prefix match by timing.
    """
    code = (code or "").strip().replace(" ", "")
    if not code.isdigit() or len(code) != digits:
        return None
    current = counter_now(at)
    for drift in range(-window, window + 1):
        candidate = current + drift
        if candidate <= after_counter:
            continue  # already used — replay
        if hmac.compare_digest(hotp(secret, candidate, digits), code):
            return candidate
    return None


def provisioning_uri(secret: str, *, account: str, issuer: str = "CyEd") -> str:
    """otpauth:// URI for QR enrolment."""
    label = quote(f"{issuer}:{account}")
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}"
        f"&algorithm=SHA1&digits={DIGITS}&period={PERIOD}"
    )
