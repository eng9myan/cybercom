"""
NFC scan verification + emergency profile helpers.

Verifies ECDSA P-256 signatures from NFC card's secure element.
Isolated in its own module so views stay thin and this is unit-testable.
"""
from __future__ import annotations

import base64
import secrets

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from django.core.cache import cache

from .models import NFCCard


CHALLENGE_TTL_SECONDS = 60


def issue_challenge(card_uuid: str) -> str:
    """Return a base64 nonce to be signed by the card."""
    nonce = secrets.token_bytes(32)
    nonce_b64 = base64.b64encode(nonce).decode()
    cache.set(f"nfc:challenge:{card_uuid}", nonce_b64, CHALLENGE_TTL_SECONDS)
    return nonce_b64


def verify_scan(card: NFCCard, nonce_b64: str, signature_b64: str) -> bool:
    """
    Verify an ECDSA P-256 signature of the nonce using the card's stored public key.
    Returns True iff signature is valid AND the nonce matches an outstanding challenge.
    """
    cached = cache.get(f"nfc:challenge:{card.card_uuid}")
    if not cached or cached != nonce_b64:
        return False
    try:
        pub = serialization.load_pem_public_key(card.public_key_pem.encode())
        if not isinstance(pub, ec.EllipticCurvePublicKey):
            return False
        sig = base64.b64decode(signature_b64)
        nonce = base64.b64decode(nonce_b64)
        pub.verify(sig, nonce, ec.ECDSA(hashes.SHA256()))
        cache.delete(f"nfc:challenge:{card.card_uuid}")
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def build_summary_for_purpose(profile, purpose: str) -> dict:
    """Return the appropriate patient summary payload for the given scan purpose."""
    patient = profile.patient
    if purpose == "emergency":
        try:
            ep = profile.emergency_profile
            return {
                "blood_type": ep.blood_type,
                "allergies": ep.allergies,
                "current_medications": ep.current_medications,
                "chronic_conditions": ep.chronic_conditions,
                "emergency_contacts": ep.emergency_contacts,
                "dnr_status": ep.dnr_status,
                "organ_donor": ep.organ_donor,
                "religious_preferences": ep.religious_preferences,
                "preferred_language": ep.preferred_language,
                "updated_from_ehr_at": ep.updated_from_ehr_at,
            }
        except Exception:
            return {"blood_type": "", "allergies": [], "current_medications": [],
                    "chronic_conditions": [], "emergency_contacts": []}

    if purpose == "reception":
        return {
            "name": str(patient),
            "mrn": getattr(patient, "mrn", ""),
            "dob": str(getattr(patient, "dob", "")),
            "phone": getattr(patient, "phone", ""),
        }

    if purpose == "pharmacy":
        return {
            "name": str(patient),
            "mrn": getattr(patient, "mrn", ""),
            "allergies": [a.get("substance") for a in
                          (getattr(profile.emergency_profile, "allergies", []) if hasattr(profile, "emergency_profile") else [])
                          if isinstance(a, dict)],
        }

    # lab / imaging / other
    return {
        "name": str(patient),
        "mrn": getattr(patient, "mrn", ""),
        "dob": str(getattr(patient, "dob", "")),
    }
