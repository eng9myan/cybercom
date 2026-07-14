"""
Licensing Service — validates, activates, and manages CyMed licenses.
Supports online, offline, and air-gapped delivery modes.
"""

import base64
import hashlib
import hmac
import json
import uuid
from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone

from products.cymed.commercial.licensing.models import (
    License,
    LicenseAudit,
    LicenseUsage,
    OfflineActivationPackage,
)


class LicensingService:
    @staticmethod
    def generate_license_number(product_code: str, edition_code: str) -> str:
        uid = uuid.uuid4().hex[:12].upper()
        product_slug = product_code.replace("_", "").upper()[:6]
        edition_slug = edition_code.replace("_", "").upper()[:4]
        return f"CYM-{product_slug}-{edition_slug}-{uid}"

    @staticmethod
    def generate_key_string(license_number: str, index: int = 0) -> str:
        raw = f"{license_number}:{index}:{uuid.uuid4().hex}"
        digest = hashlib.sha256(raw.encode()).hexdigest().upper()
        # Format XXXX-XXXX-XXXX-XXXX-XXXX
        return "-".join(digest[i : i + 5] for i in range(0, 25, 5))

    @staticmethod
    def check_compliance(license: License) -> dict:
        """Returns compliance state including grace period status."""
        today = timezone.now().date()
        result = {
            "license_number": license.license_number,
            "is_valid": license.is_valid(),
            "status": license.status,
            "valid_until": str(license.valid_until) if license.valid_until else None,
            "days_remaining": None,
            "in_grace_period": False,
        }
        if license.valid_until:
            delta = (license.valid_until - today).days
            result["days_remaining"] = delta
            if delta < 0 and abs(delta) <= license.grace_period_days:
                result["in_grace_period"] = True
        return result

    @staticmethod
    def create_offline_package(
        license: License, machine_fingerprint: str, validity_days: int = 365
    ) -> OfflineActivationPackage:
        """Generate a signed offline activation bundle for air-gapped deployments."""
        payload = {
            "license_number": license.license_number,
            "product_code": license.product_code,
            "edition_code": license.edition_code,
            "organization_name": license.organization_name,
            "machine_fingerprint": machine_fingerprint,
            "valid_until": str(license.valid_until),
            "max_users": license.max_users,
            "max_beds": license.max_beds,
        }
        secret = getattr(settings, "LICENSE_SIGNING_SECRET", "cymed-default-signing-key")
        payload_json = json.dumps(payload, sort_keys=True)
        sig = hmac.new(secret.encode(), payload_json.encode(), hashlib.sha256).hexdigest()
        signed = base64.b64encode(json.dumps({"payload": payload, "sig": sig}).encode()).decode()

        return OfflineActivationPackage.objects.create(
            tenant_id=license.tenant_id,
            license=license,
            package_token=uuid.uuid4().hex,
            machine_fingerprint=machine_fingerprint,
            signed_payload=signed,
            expires_at=timezone.now() + timedelta(days=validity_days),
        )

    @staticmethod
    def record_usage_snapshot(license: License, metrics: dict) -> LicenseUsage:
        today = timezone.now().date()
        usage, _ = LicenseUsage.objects.update_or_create(
            tenant_id=license.tenant_id,
            license=license,
            snapshot_date=today,
            defaults={
                "active_users": metrics.get("active_users", 0),
                "active_providers": metrics.get("active_providers", 0),
                "active_beds": metrics.get("active_beds", 0),
                "api_calls": metrics.get("api_calls", 0),
                "storage_gb": metrics.get("storage_gb", 0),
                "is_over_limit": (
                    (license.max_users > 0 and metrics.get("active_users", 0) > license.max_users)
                    or (license.max_beds > 0 and metrics.get("active_beds", 0) > license.max_beds)
                ),
            },
        )
        return usage

    @staticmethod
    def renew_license(license: License, new_valid_until: date, performed_by=None) -> License:
        license.valid_until = new_valid_until
        license.status = "active"
        license.save()
        LicenseAudit.objects.create(
            tenant_id=license.tenant_id,
            license=license,
            event_type="renewed",
            performed_by=performed_by,
            metadata={"new_valid_until": str(new_valid_until)},
        )
        return license
