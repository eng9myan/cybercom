"""
Usage Metering Service — collects and evaluates tenant usage metrics against license limits.
"""

import uuid
from decimal import Decimal

from django.utils import timezone

from products.cymed.commercial.licensing.models import License
from products.cymed.commercial.usage_metering.models import UsageAlert, UsageMeter


class UsageMeteringService:
    ALERT_THRESHOLD_PCT = Decimal("80.0")

    @classmethod
    def record_snapshot(
        cls,
        tenant_id: uuid.UUID,
        product_code: str,
        edition_code: str,
        metrics: dict,
    ) -> UsageMeter:
        today = timezone.now().date()
        meter, _ = UsageMeter.objects.update_or_create(
            tenant_id=tenant_id,
            snapshot_date=today,
            product_code=product_code,
            defaults={
                "edition_code": edition_code,
                "active_users": metrics.get("active_users", 0),
                "active_providers": metrics.get("active_providers", 0),
                "active_facilities": metrics.get("active_facilities", 0),
                "active_clinics": metrics.get("active_clinics", 0),
                "active_hospitals": metrics.get("active_hospitals", 0),
                "licensed_beds": metrics.get("licensed_beds", 0),
                "occupied_beds": metrics.get("occupied_beds", 0),
                "api_calls": metrics.get("api_calls", 0),
                "storage_gb": metrics.get("storage_gb", Decimal("0")),
                "total_transactions": metrics.get("total_transactions", 0),
                "is_over_user_limit": False,
                "is_over_bed_limit": False,
                "is_over_api_limit": False,
            },
        )
        cls._check_limits(meter, tenant_id, product_code)
        return meter

    @classmethod
    def _check_limits(cls, meter: UsageMeter, tenant_id, product_code: str) -> None:
        from django.core.exceptions import ObjectDoesNotExist

        try:
            license_obj = License.objects.get(
                tenant_id=tenant_id, product_code=product_code, status__in=["active", "grace"]
            )
        except ObjectDoesNotExist:
            return

        def _check(resource: str, current: int, limit: int, over_field: str) -> None:
            if limit == 0:
                return
            pct = Decimal(current * 100) / Decimal(limit)
            if pct >= 100:
                setattr(meter, over_field, True)
                cls._create_alert(meter, "over_limit", "critical", resource, current, limit, pct)
            elif pct >= cls.ALERT_THRESHOLD_PCT:
                cls._create_alert(
                    meter, "approaching_limit", "warning", resource, current, limit, pct
                )

        _check("users", meter.active_users, license_obj.max_users, "is_over_user_limit")
        _check("beds", meter.occupied_beds, license_obj.max_beds, "is_over_bed_limit")
        _check("api_calls", meter.api_calls, license_obj.max_api_calls_per_day, "is_over_api_limit")
        meter.save()

    @staticmethod
    def _create_alert(
        meter: UsageMeter,
        alert_type: str,
        severity: str,
        resource: str,
        current: int,
        limit: int,
        pct: Decimal,
    ) -> UsageAlert:
        return UsageAlert.objects.get_or_create(
            tenant_id=meter.tenant_id,
            meter=meter,
            alert_type=alert_type,
            resource=resource,
            defaults={
                "severity": severity,
                "current_value": current,
                "limit_value": limit,
                "percentage_used": pct,
                "is_resolved": False,
            },
        )[0]
